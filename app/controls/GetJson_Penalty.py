#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from app.models import *

def GetJson_Penalty(userID):
    # query
    strQuery = db.session.query(penalty.amount).filter(penalty.user_id == userID)
    strQueryLine = db.session.query(penalty_line.amount, penalty_line.num).order_by(penalty_line.amount)
    results = strQuery.first()
    resultsLine = strQueryLine.all()

    # unpacking results
    userAmount = float(results[0])

    # process conability for all
    amount = [float(result.amount) for result in resultsLine]
    num = [int(result.num) for result in resultsLine]

    # return
    json_response = {'userAmount': userAmount, 'amount': amount, 'num': num}

    return json_response