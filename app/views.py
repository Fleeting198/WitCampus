﻿#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# 02-09 Built
# 02-11 将数据处理交给controlls，日期查询筛选
# 02-12 acperiod, income
# 02-16 Implementing dateRangePicker. Saved lots of code.
# 02-20 acvalid, accategory

from app import app
from flask import render_template, request, jsonify
from app.models import *
from app.forms import *

from sqlalchemy import and_, func
from datetime import datetime
import json
import types

from app import helpers


@app.route('/')
def show_index():
    return render_template('index.html')


@app.route('/charts')
def show_charts():
    return render_template('charts.html')


@app.route('/charts/expenditure')
def show_chart_expenditure():
    form = Form_UserDaterangemode()
    return render_template('chart-expenditure.html', form=form)


@app.route('/charts/expenditure/getData', methods=['GET'])
def refresh_chart_expenditure():

    # 从GET获得表单值赋给wtform
    form = Form_UserDaterangemode()
    form.userID.data = request.args.get('userID')
    form.modeDate.data = request.args.get('modeDate')
    form.dateRange.data = request.args.get('dateRange')

    if form.validate():
        userID = form.userID.data
        modeDate = int(form.modeDate.data)
        startDate = form.dateRange.data[:10]
        endDate = form.dateRange.data[-10:]

        # Query.
        strQuery = db.session.query(consumption.con_datetime,consumption.amount).filter(
            consumption.user_id == userID).order_by(consumption.con_datetime)
        if len(startDate) != 0:
            strQuery = strQuery.filter(
                and_(consumption.con_datetime >= startDate, consumption.con_datetime <= endDate))
        results = strQuery.all()

        # Get columns.
        res_datetimes = [result.con_datetime for result in results]
        res_amounts = [result.amount for result in results]

        from app.controls.DateTimeValueProcess import DateTimeValueProcess
        process = DateTimeValueProcess(res_datetimes, res_amounts)

        # Get and pack dateTrend() return.
        axisLabels, accumulatedVals, pointVals = process.dateTrend(modeDate)
        json_dateTrend = {'axisLabels': axisLabels, 'accumulatedVals': accumulatedVals, 'pointVals': pointVals}
        # json_dateTrend = jsonify(axisLabels=axisLabels, accumulatedVals=accumulatedVals, pointVals=pointVals)

        # Get and pack timeDistribution() return.
        axisLabels, vals = process.timeDistribution()
        json_timeDistribution = {'axisLabels': axisLabels, 'vals':vals}
        # json_timeDistribution = jsonify(axisLabels=axisLabels, vals=vals)

        # 没有错误就不传errMsg。前端通过检查errMsg是否存在来判断查询是否成功。
        json_response = jsonify(json_dateTrend=json_dateTrend, json_timeDistribution=json_timeDistribution)
    else:
        json_response = jsonify(errMsg=form.errors)
    return json_response


@app.route('/charts/acperiod')
def show_chart_acperiod():
    form = Form_UserDaterangemode()
    return render_template('chart-acperiod.html', form=form)


@app.route('/charts/acperiod/getData', methods=['GET'])
def refresh_chart_acperiod():
    form = Form_UserDaterangemode()
    form.userID.data = request.args.get('userID')
    form.dateRange.data = request.args.get('dateRange')

    if form.validate():
        userID = form.userID.data
        startDate = form.dateRange.data[:10]
        endDate = form.dateRange.data[-10:]

        # Query.
        strQuery = db.session.query(acrec.ac_datetime).filter(acrec.user_id == userID).order_by(acrec.ac_datetime)
        if len(startDate) != 0:
            strQuery = strQuery.filter(and_(acrec.ac_datetime >= startDate, acrec.ac_datetime <= endDate))
        results = strQuery.all()
        res_datetimes = [result.ac_datetime for result in results]

        # Process data.
        from app.controls.DateTimeValueProcess import DateTimeValueProcess
        process = DateTimeValueProcess(res_datetimes)

        # 包装dateTrend 返回值。
        # 这个功能暂时不需要连续值，但还是必须获取，逻辑模块写一起了。
        axisLabels, accumulatedVals, pointVals = process.dateTrend(2)  # 暂时将日期模式直接设为月

        json_dateTrend = {'axisLabels': axisLabels, 'pointVals': pointVals}

        # timeDistribution 返回值
        axisLabels, vals = process.timeDistribution()
        json_timeDistribution = {'axisLabels': axisLabels, 'vals': vals}

        json_response = jsonify(json_dateTrend=json_dateTrend, json_timeDistribution=json_timeDistribution)
    else:
        json_response = jsonify(errMsg=form.errors)
    return json_response


@app.route('/charts/acperiodcate')
def show_chart_acperiodcate():
    form = Form_UserDaterange()
    return render_template('chart-acperiodcate.html', form=form)


@app.route('/charts/acperiodcate/getData', methods=['GET'])
def refresh_chart_acperiodcate():
    form = Form_UserDaterange()
    form.userID.data = request.args.get('userID')
    form.dateRange.data = request.args.get('dateRange')

    if form.validate():
        userID = form.userID.data
        startDate = form.dateRange.data[:10]
        endDate = form.dateRange.data[-10:]

        # Query.
        strQuery = db.session.query(acrec.ac_datetime, ac_loc.category).filter(
            and_(acrec.user_id == userID, acrec.node_des==ac_loc.node_des)).order_by(acrec.ac_datetime)
        if len(startDate) != 0:
            strQuery = strQuery.filter(and_(acrec.ac_datetime >= startDate, acrec.ac_datetime <= endDate))
        results = strQuery.all()

        res_datetimes = [result.ac_datetime for result in results]
        res_categorys = [result.category for result in results]

        # Process data.
        from app.controls.CateDateTimeValue import DateTimeValueProcess
        process = DateTimeValueProcess(res_datetimes, res_categorys)

        # dateTrend
        axisLabels, pointVals = process.dateTrend(2)

        # 输出格式;
        # xAxis: ['date1', 'date2', ...]
        # legend: ['item1', 'item2', ...]

        # 图例项
        legendLabels = []
        for result in res_categorys:
            if result not in legendLabels:
                legendLabels.append(str(result))

        # 节点数据项
        # series: [{name:'item1', data:[data1, data2, ...]}, {name:'item2', data:[data1, data2, ...]}]
        def packSeriesData(Vals):
            seriesData = []
            for legendLabel in legendLabels:
                datumList = []
                for val in Vals:
                    if legendLabel in val:
                        datumList.append(val[legendLabel])
                    else:
                        datumList.append(0)

                seriesDatum = {'name': legendLabel, 'data': datumList}
                seriesData.append(seriesDatum)
            return seriesData

        pointSeriesData=packSeriesData(pointVals)
        # 翻译
        for val in pointSeriesData:
            val['name'] = helpers.translate(val['name'])

            # 备份
        tmp_legendLabels = legendLabels[:]
        # 翻译
        legendLabels = [helpers.translate(Label) for Label in legendLabels]
        # 打包
        json_dateTrend = {'axisLabels': axisLabels, 'legendLabels': legendLabels, 'pointSeriesData': pointSeriesData}

        # timeDistribution
        axisLabels, vals = process.timeDistribution()

        # 还原legendLabels
        legendLabels = tmp_legendLabels[:]
        del tmp_legendLabels
        # 处理
        vals = packSeriesData(vals)

        # 翻译
        legendLabels = [helpers.translate(Label) for Label in legendLabels]
        for val in vals:
            val['name'] = helpers.translate(val['name'])

        # 两个图表都传了图例标签队列以防以后要分开，流量占多一点点暂时没关系。
        json_timeDistribution = {'axisLabels': axisLabels, 'legendLabels': legendLabels, 'vals':vals}

        json_response = jsonify(json_dateTrend=json_dateTrend, json_timeDistribution=json_timeDistribution)
        # json_response = jsonify(json_dateTrend=json_dateTrend)

    else:
        json_response = jsonify(errMsg=form.errors)
    return json_response


@app.route('/charts/income')
def show_chart_income():
    form = Form_DevDaterangemode()
    return render_template('chart-income.html', form=form)


@app.route('/charts/income/getData', methods=['GET'])
def refresh_chart_income():
    # 从GET获得表单值赋给wtform
    form = Form_DevDaterangemode()
    form.devID.data = request.args.get('devID')
    form.modeDate.data = request.args.get('modeDate')
    form.dateRange.data = request.args.get('dateRange')

    if form.validate():
        # 赋值给变量
        devID = form.devID.data
        modeDate = int(form.modeDate.data)
        startDate = form.dateRange.data[:10]
        endDate = form.dateRange.data[-10:]

        # Query.
        strQuery = db.session.query(consumption.con_datetime,consumption.amount).filter(
            consumption.dev_id == devID).order_by(consumption.con_datetime)
        if len(startDate) != 0:
            strQuery = strQuery.filter(
                and_(consumption.con_datetime >= startDate, consumption.con_datetime <= endDate))
        results = strQuery.all()
        # Get columns.
        res_datetimes = [result.con_datetime for result in results]
        res_amounts = [result.amount for result in results]

        # Process data.
        from app.controls.DateTimeValueProcess import DateTimeValueProcess
        process = DateTimeValueProcess(res_datetimes, res_amounts)

        # Get and pack dateTrend() return.
        axisLabels, accumulatedVals, pointVals = process.dateTrend(modeDate)
        json_dateTrend = {'axisLabels': axisLabels, 'accumulatedVals': accumulatedVals, 'pointVals': pointVals}

        # Get and pack timeDistribution() return.
        axisLabels, vals = process.timeDistribution()
        json_timeDistribution = {'axisLabels': axisLabels, 'vals': vals}

        # 没有错误就不传errMsg
        json_response = jsonify(json_dateTrend=json_dateTrend, json_timeDistribution=json_timeDistribution)
    else:
        json_response = jsonify(errMsg=form.errors)
    return json_response


@app.route('/charts/acvalid')
def show_chart_acvalid():
    form = Form_UserDaterange()
    return render_template('chart-acvalid.html', form=form)


@app.route('/charts/acvalid/getData')
def refresh_chart_acvalid():
    form = Form_UserDaterange()
    form.userID.data = request.args.get('userID')
    form.dateRange.data = request.args.get('dateRange')

    if form.validate():
        userID = form.userID.data
        startDate = form.dateRange.data[:10]
        endDate = form.dateRange.data[-10:]

        # Query.
        strQuery = db.session.query(acrec.legal, func.count('*')).filter(acrec.user_id == userID).group_by(acrec.legal)
        if len(startDate) != 0:
            strQuery = strQuery.filter(and_(acrec.ac_datetime >= startDate, acrec.ac_datetime <= endDate))
        results = strQuery.all()

        # Process data.
        from controls.CategoryProcess import CategoryProcess
        titles, seriesData = CategoryProcess(results)

        json_response = {'titles': titles, 'seriesData': seriesData}
        json_response = jsonify(json_response)
    else:
        json_response = jsonify(errMsg=form.errors)
    return json_response


@app.route('/charts/accategory')
def show_chart_accategory():
    form = Form_UserDaterange()
    return render_template('chart-accategory.html', form=form)


@app.route('/charts/accategory/getData')
def refresh_chart_accategory():
    form = Form_UserDaterange()
    form.userID.data = request.args.get('userID')
    form.dateRange.data = request.args.get('dateRange')

    if form.validate():
        userID = form.userID.data
        startDate = form.dateRange.data[:10]
        endDate = form.dateRange.data[-10:]

        # Query.
        strQuery = db.session.query(ac_loc.category, func.count('*')).filter(
            and_(ac_loc.node_des==acrec.node_des, acrec.user_id==userID)).group_by(ac_loc.category)
        if len(startDate) != 0:
            strQuery = strQuery.filter(and_(acrec.ac_datetime >= startDate, acrec.ac_datetime <= endDate))
        results = strQuery.all()

        # Process data.
        from controls.CategoryProcess import CategoryProcess
        titles, seriesData = CategoryProcess(results)

        json_response = {'titles': titles, 'seriesData': seriesData}
        json_response = jsonify(json_response)
    else:
        json_response = jsonify(errMsg=form.errors)
    return json_response


@app.route('/charts/concategory')
def show_chart_concategory():
    form = Form_UserDaterange()
    return render_template('chart-concategory.html', form=form)


@app.route('/charts/concategory/getData')
def refresh_chart_concategory():
    form = Form_UserDaterange()
    form.userID.data = request.args.get('userID')
    form.dateRange.data = request.args.get('dateRange')

    if form.validate():
        userID = form.userID.data
        startDate = form.dateRange.data[:10]
        endDate = form.dateRange.data[-10:]

        # Query.
        strQuery = db.session.query(dev_loc.category, func.sum(consumption.amount)).filter(
            and_(consumption.user_id == userID, dev_loc.node_id == device.node_id, device.dev_id == consumption.dev_id)).group_by(dev_loc.category)
        if len(startDate) != 0:
            strQuery = strQuery.filter(and_(consumption.con_datetime >= startDate, consumption.con_datetime <= endDate))

        results = strQuery.all()

        # Process data.
        from controls.CategoryProcess import CategoryProcess
        titles, seriesData = CategoryProcess(results)

        json_response = {'titles': titles, 'seriesData': seriesData}
        json_response = jsonify(json_response)
    else:
        json_response = jsonify(errMsg=form.errors)
    return json_response


@app.route('/charts/number')
def show_chart_number():
    # return render_template('chart-number.html')
    return render_template('chart-numberBar.html')


@app.route('/charts/number/getData', methods=['GET'])
def refresh_chart_number():
    # query number of people by dividing into total & grades
    strQueryTotal = db.session.query(individual.role, func.count('*')).group_by(individual.role)
    # GradeB stands for 本科生的年级
    strQueryGradeB = db.session.query(individual.grade, func.count('*')).filter(individual.role == u'本科生').group_by(individual.grade)
    # GradePg stands for 研究生的年级
    strQueryGradePg = db.session.query(individual.grade, func.count('*')).filter(individual.role == u'研究生').group_by(individual.grade)
    # GradeDr stands for 博士生的年级
    strQueryGradeDr = db.session.query(individual.grade, func.count('*')).filter(individual.role == u'博士生').group_by(individual.grade)

    # try query grade at one time?
    # strQueryGrade = db.session.query(individual.grade, func.count('*')).filter(individual.role.in_(['本科生', '研究生', '博士生'])).group_by(individual.grade)

    # go
    resultsTotal = strQueryTotal.all()
    resultsGradeB = strQueryGradeB.all()
    resultsGradePg = strQueryGradePg.all()
    resultsGradeDr = strQueryGradeDr.all()

    # for test only
    # print resultsGradeB
    # print resultsGradeB[0][0]
    # print resultsGradeB[0][1]
    # sum = 0
    # for num in resultsGradeB:
    #     sum += num[1]
    # print sum

    # process numberTotal
    json_numberTotal = {}
    for result in resultsTotal:
        json_numberTotal[result[0]] = result[1]

    json_numberTotal['teacher'] = json_numberTotal.pop(u'老师')
    json_numberTotal['other'] = json_numberTotal.pop(u'其他')
    json_numberTotal['stuB'] = json_numberTotal.pop(u'本科生')
    json_numberTotal['stuPg'] = json_numberTotal.pop(u'研究生')
    json_numberTotal['stuDr'] = json_numberTotal.pop(u'博士生')

    # process numberGrade
    grade = {'10', '11', '12', '13', '14', '15'}

    # init json
    json_numberGradeB = {'unknown': 0}
    json_numberGradePg = {'unknown': 0}
    json_numberGradeDr = {'unknown': 0}

    # convert result to json func?
    def result_to_jsonUnicode(resultGrade):
        json = {'unknown': 0}
        for result in resultGrade:
            if result[0] in grade:
                json[result[0]] = result[1]
            else:
                json['unknown'] += result[1]
        return json

    # go
    json_numberGradeB = result_to_jsonUnicode(resultsGradeB)
    json_numberGradePg = result_to_jsonUnicode(resultsGradePg)
    json_numberGradeDr = result_to_jsonUnicode(resultsGradeDr)

    def result_to_jsonString(json):
        json['g10'] = json.pop(u'10')
        json['g11'] = json.pop(u'11')
        json['g12'] = json.pop(u'12')
        json['g13'] = json.pop(u'13')
        json['g14'] = json.pop(u'14')
        json['g15'] = json.pop(u'15')
        return json

    json_numberGradeB = result_to_jsonString(json_numberGradeB)
    json_numberGradePg = result_to_jsonString(json_numberGradePg)
    json_numberGradeDr = result_to_jsonString(json_numberGradeDr)

    # return
    json_response = jsonify(json_numberTotal = json_numberTotal, json_numberGradeB = json_numberGradeB, json_numberGradePg = json_numberGradePg, json_numberGradeDr = json_numberGradeDr)
    return json_response

