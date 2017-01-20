#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from app.models import *
from sqlalchemy import and_

"""门禁日期趋势，日期横轴，各门禁分类组成的门禁数纵轴"""


def GetJson_AcDateTrend(userID, startDate, endDate, modeDate):
    """
    返回Json：门禁日期趋势
    :param userID: 工号
    :param startDate: 限定数据起始日期
    :param endDate: 限定数据结束日期
    :param modeDate: 日期模式，决定数据按怎样的粒度合并
    :return json_response: Echarts格式字典{'axisLabels': , 'legendLabels': , 'seriesData': , 'statRows': }
    """
    strQuery = db.session.query(acrec.ac_datetime, ac_loc.category).filter(
        and_(acrec.user_id == userID, acrec.node_id == ac_loc.node_id)).order_by(acrec.ac_datetime)

    if startDate:
        strQuery = strQuery.filter(and_(acrec.ac_datetime >= startDate, acrec.ac_datetime <= endDate))
    results = strQuery.all()

    if not results:
        return {'errMsg': u'没有找到记录。'}

    # 处理数据，返回一个DataFrame
    datetimeList = [result.ac_datetime for result in results]
    recordList = [result.category for result in results]
    valList = [1] * len(recordList)

    from app.controllers.Pro_DateTrend import get_date_trend
    df, dfStat = get_date_trend(datetimeList, recordList, valList, modeDate)

    # 包装成Echarts需要的格式
    if int(modeDate) == 2:
        axisLabels = map(lambda x: x.strftime('%Y-%m'), df.index.tolist())
    else:
        axisLabels = map(lambda x: x.strftime('%Y-%m-%d'), df.index.tolist())  # 从dataframe 中取出作为索引的日期标签成为队列
    seriesData = []
    legendLabels = []

    for colName, col in df.iteritems():
        legendLabels.append(colName)
        data = map(lambda x: float(x), col.tolist())
        seriesData.append({'name': colName, 'data': data})

    # 把只需要用表格显示的统计数据单独用字典列表返回
    statRows = []
    for dfIndex, dfRow in dfStat.iterrows():
        dfRowDict = dfRow.to_dict()  # Series转为字典

        # 把np的float64转成python的float
        for k, v in dfRowDict.iteritems():
            dfRowDict[k] = float(v)

        dfRowDict["index"] = dfIndex  # 代表这条数据的索引，前端会用到"index" （耦合）
        statRows.append(dfRowDict)

    json_response = {'axisLabels': axisLabels, 'legendLabels': legendLabels, 'seriesData': seriesData,
                     'statRows': statRows}
    return json_response