#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# 02-09 Built -陈
# 02-11 将数据处理交给controlls，日期查询筛选
# 02-12 acperiod, income
# 02-16 Implementing dateRangePicker. Saved lots of code.

from app import app
from flask import render_template, request, jsonify
from app.models import *
from app.forms import *

from sqlalchemy import and_
from datetime import datetime
import json

import types


@app.route('/')
def show_index():
    return render_template('index.html')


# Ignore this.
@app.route('/test')
def show_test():
    return app.config['SQLALCHEMY_DATABASE_URI']


@app.route('/charts')
def show_charts():
    return render_template('charts.html')


@app.route('/charts/expenditure')
def show_chart_expenditure():
    form = form_expenditure()
    return render_template('chart-expenditure.html', form=form)


@app.route('/charts/expenditure/getData', methods=['GET'])
def refresh_chart_expenditure():

    # 从GET获得表单值赋给wtform
    form = form_expenditure()
    form.userID.data = request.args.get('userID')
    form.modeDate.data = request.args.get('modeDate')
    form.dateRange.data = request.args.get('dateRange')

    if form.validate():
        # 赋值给变量
        userID = form.userID.data
        modeDate = int(form.modeDate.data)
        startDate = form.dateRange.data[:10]
        endDate = form.dateRange.data[-10:]

        # 查询
        recordQuery = consumption.query.filter(consumption.user_id == userID).order_by(consumption.con_datetime)

        if len(startDate) != 0 and len(endDate) != 0:
            recordQuery = recordQuery.filter(
                and_(consumption.con_datetime >= startDate, consumption.con_datetime <= endDate))
        elif len(startDate) != 0 and len(endDate) == 0:
            recordQuery = recordQuery.filter(consumption.con_datetime >= startDate)
        elif len(startDate) == 0 and len(endDate) != 0:
            recordQuery = recordQuery.filter(consumption.con_datetime <= endDate)

        results = recordQuery.all()

        mdates = [result.con_datetime for result in results]  # 构造日期数组作为图表x轴标记
        mamounts = [result.amount for result in results]  # 构造对应的消费值

        # 调用Controls
        from app.controls.DataProcess import DateTimeValueProcess
        process = DateTimeValueProcess(mdates, mamounts)

        # 包装dateTrend 返回值
        axisLables, accumulatedVals, pointVals = process.dateTrend(modeDate)
        json_dateTrend = {'axisLables': axisLables, 'accumulatedVals': accumulatedVals, 'pointVals': pointVals}
        # json_dateTrend = jsonify(axisLables=axisLables, accumulatedVals=accumulatedVals, pointVals=pointVals)

        # timeDistribution 返回值
        axisLables, vals = process.timeDistribution(toCountAxis=False)
        json_timeDistribution = {'axisLables': axisLables, 'vals':vals}
        # json_timeDistribution = jsonify(axisLables=axisLables, vals=vals)

        # 没有错误就不传errMsg
        json_response = jsonify(json_dateTrend=json_dateTrend, json_timeDistribution=json_timeDistribution)
    else:
        json_response = jsonify(errMsg=form.errors)
    return json_response


@app.route('/charts/acperiod')
def show_chart_acperiod():
    form = form_acperiod()
    return render_template('chart-acperiod.html', form=form)


@app.route('/charts/acperiod/getData', methods=['GET'])
def refresh_chart_acperiod():
    form = form_acperiod()
    form.userID.data = request.args.get('userID')
    form.dateRange.data = request.args.get('dateRange')

    if form.validate():
        userID = form.userID.data
        startDate = form.dateRange.data[:10]
        endDate = form.dateRange.data[-10:]

        recordQuery = acrec.query.filter(acrec.user_id == userID).order_by(acrec.ac_datetime)
        if len(startDate) != 0 and len(endDate) != 0:
            recordQuery = recordQuery.filter(and_(acrec.ac_datetime >= startDate, acrec.ac_datetime <= endDate))
        elif len(startDate) != 0 and len(endDate) == 0:
            recordQuery = recordQuery.filter(acrec.ac_datetime >= startDate)
        elif len(startDate) == 0 and len(endDate) != 0:
            recordQuery = recordQuery.filter(acrec.ac_datetime <= endDate)

        results = recordQuery.all()

        mdates = [result.ac_datetime for result in results]

        from app.controls import acperiod
        mperiods, mcounts = acperiod.main(mdates)

        json_response = jsonify(mperiods=mperiods, mcounts=mcounts)
    else:
        json_response = jsonify(errMsg=form.errors)
    return json_response


@app.route('/charts/income')
def show_chart_income():
    form = form_income()
    return render_template('chart-income.html', form=form)


@app.route('/charts/income/getData', methods=['GET'])
def refresh_chart_income():
    form = form_income()
    form.devID.data = request.args.get('devID')
    form.dateRange.data = request.args.get('dateRange')
    form.modeDate.data = request.args.get('modeDate')

    if form.validate():
        devID = form.devID.data
        modeDate = int(form.modeDate.data)
        startDate = form.dateRange.data[:10]
        endDate = form.dateRange.data[-10:]

        # 查询
        recordQuery = consumption.query.filter(consumption.dev_id == devID).order_by(consumption.con_datetime)
        if len(startDate) != 0 and len(endDate) != 0:
            recordQuery = recordQuery.filter(
                and_(consumption.con_datetime >= startDate, consumption.con_datetime <= endDate))
        elif len(startDate) != 0 and len(endDate) == 0:
            recordQuery = recordQuery.filter(consumption.con_datetime >= startDate)
        elif len(startDate) == 0 and len(endDate) != 0:
            recordQuery = recordQuery.filter(consumption.con_datetime <= endDate)

        results = recordQuery.all()

        mdates = [result.con_datetime for result in results]
        mamounts = [result.amount for result in results]

        # 调用处理模块
        from app.controls import income
        mdates, mamounts, mamounts_point = income.main(mdates, mamounts, modeDate)

        # 构造返回json
        json_response = jsonify(valid=1, mdates=mdates, mamounts=mamounts, mamounts_point=mamounts_point)
    else:
        json_response = jsonify(errMsg=form.errors)
    return json_response
