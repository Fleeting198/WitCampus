#!/usr/bin/env python
# -*- coding: UTF-8 -*-

# 02-16 Created -C

from datetime import time, datetime
import types


class DateTimeValueProcess():
    """
    输入坐标（日期，可重复）与对应值，对其进行统计。
    """
    oriDate = []  # 日期
    oriValues = []  # 与日期对应的消费额

    def __init__(self, dates, vals=None):
        self.oriDate = dates
        self.oriValues = [1] * len(dates) if vals is None else vals  # 若不传值列表则设次数为 1

    def dateTrend(self, modeDate=2):
        """
        日期趋势，输入日期模式，输出合并后的日期、节点值和累积值。
        默认日期模式为月
        """
        # Copy source data.
        axisLables = self.oriDate[:]
        accumulatedVals = self.oriValues[:]

        # 日期降维，仅用字符串切片处理年、月。
        if modeDate == 0:
            axisLables = map(lambda d: d.date(), axisLables)
        elif modeDate == 2:
            axisLables = map(lambda d: str(d.date())[:7], axisLables)
        elif modeDate == 4:
            axisLables = map(lambda d: str(d.date())[:4], axisLables)

        # TODO: 生成按星期和季度分的数据，考虑到交互性可能由前端JS负责？
        elif modeDate == 1:
            # 输出周
            # for strdate in axisLables:
            #     print strdate.strftime('%w')
            pass
        elif modeDate == 3:
            pass

        # 遍历日期，合并相同日期以及对应的值
        i = 1
        while i < len(axisLables):  # 每轮循环都要获取长度，用以遍历这个动态改变长度的列表
            if axisLables[i] == axisLables[i - 1]:
                axisLables = axisLables[:i - 1] + axisLables[i:]  # 去除日期
                accumulatedVals[i] += accumulatedVals[i - 1]  # 合并值
                accumulatedVals = accumulatedVals[:i - 1] + accumulatedVals[i:]  # 去除值
            else:
                i += 1

        # 保存节点值
        pointVals = accumulatedVals[:]
        # 累加连续值
        for i in range(1, len(accumulatedVals)):
            accumulatedVals[i] += accumulatedVals[i - 1]

        # Make sure type.
        axisLables = map(lambda x: str(x), axisLables)
        accumulatedVals = map(lambda x: float(x), accumulatedVals)
        pointVals = map(lambda x: float(x), pointVals)

        return axisLables, accumulatedVals, pointVals

    def timeDistribution(self):
        """
        时间分布，输出各时间段总计数，目的在于对比。
        """
        # Copy source data.
        dates = self.oriDate[:]
        values = map(lambda x: float(x), self.oriValues)

        # Time periods：
        # 23~5 5~12 12~20 20~23
        period = (time(5), time(12), time(20), time(23))
        axisLables = ('23点~5点', '5点~12点', '12点~20点', '20点~23点')

        vals = [float(0)]*len(period)  # Init vals

        lTimes = map(lambda d: d.time(), dates)  # Keep time.

        # dates = map(lambda d: d.date(), dates)
        # len_mdates = len(list(set(dates)))  # Day count to divide.

        # Add to total vals.
        for i in range(len(lTimes)):
            if period[0] <= lTimes[i] < period[1]:
                vals[1] += values[i]
            elif period[1] <= lTimes[i] < period[2]:
                vals[2] += values[i]
            elif period[2] <= lTimes[i] < period[3]:
                vals[3] += values[i]
            else:
                vals[0] += values[i]

        for i in range(len(vals)):
            # vals[i] = vals[i] / len_mdates if len_mdates != 0 else 0
            vals[i] = round(vals[i], 2)

        return axisLables, vals