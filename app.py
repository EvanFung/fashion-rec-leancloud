# coding: utf-8
import sys
from datetime import datetime

import leancloud

from flask import Flask, jsonify, request
from flask import render_template
from flask_sockets import Sockets
from leancloud import LeanCloudError

from views.todos import todos_view
from RatingsLoader import RatingsLoader
import csv
import pandas as pd
from collections import defaultdict
import heapq
from surprise import NormalPredictor
from surprise import Dataset
from surprise import Reader
from surprise.model_selection import cross_validate
from surprise import SVD
from surprise import KNNBasic
from operator import itemgetter

app = Flask(__name__)
sockets = Sockets(app)

# 动态路由
app.register_blueprint(todos_view, url_prefix='/todos')


#
def get_top_n(predictions, n=10):
    top_n = defaultdict(list)
    for uid, iid, true_r, est, _ in predictions:
        top_n[uid].append((iid, est))

    for uid, user_ratings in top_n.items():
        user_ratings.sort(key=lambda x: x[1], reverse=True)
        top_n[uid] = user_ratings[:n]
    return top_n





@app.route('/')
def index():
    return render_template('index.html')


@app.route('/time')
def time():
    return str(datetime.now())


@app.route('/version')
def print_version():
    import sys
    return sys.version


@sockets.route('/echo')
def echo_socket(ws):
    while True:
        message = ws.receive()
        ws.send(message)


# REST API example
class BadGateway(Exception):
    status_code = 502

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_json(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return jsonify(rv)


class BadRequest(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_json(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return jsonify(rv)


@app.errorhandler(BadGateway)
def handle_bad_gateway(error):
    response = error.to_json()
    response.status_code = error.status_code
    return response


@app.errorhandler(BadRequest)
def handle_bad_request(error):
    response = error.to_json()
    response.status_code = error.status_code
    return response


@app.route('/api/python-version', methods=['GET'])
def python_version():
    return jsonify({"python-version": sys.version})


@app.route('/rec/<int:userID>')
def recommendItem(userID):
    ml = RatingsLoader()
    data = ml.loadDataset()
    trainset = data.build_full_trainset()
    sim_options = {'name': 'cosine', 'user_based': True}
    algo = KNNBasic(sim_options)
    algo.fit(trainset)
    simsMatrix = algo.compute_similarities()

    testUserInnerID = trainset.to_inner_uid('5')
    similarityRow = simsMatrix[testUserInnerID]
    similarUsers = []
    for innerID, score in enumerate(similarityRow):
        if (innerID != testUserInnerID):
            similarUsers.append((innerID, score))
    kNeighbors = heapq.nlargest(10, similarUsers, key=lambda t: t[1])
    candidates = defaultdict(float)
    for similarUser in kNeighbors:
        innerID = similarUser[0]
        userSimilarityScore = similarUser[1]
        theirRatings = trainset.ur[innerID]
        for rating in theirRatings:
            candidates[rating[0]] += (rating[1] / 5.0) * userSimilarityScore
    print(candidates)
    watched = {}
    for itemID, rating in trainset.ur[testUserInnerID]:
        watched[itemID] = 1
    pos = 0
    for itemID, ratingSum in sorted(candidates.items(), key=itemgetter(1), reverse=True):
        if not itemID in watched:
            productID = trainset.to_raw_iid(itemID)
            print(productID, ratingSum)
            pos += 1
            if (pos > 10):
                break
    # algo = SVD()
    # algo.fit(trainset)
    # testset = trainset.build_anti_testset()
    # predictions = algo.test(trainset)
    # top_n = get_top_n(predictions)
    # print(ml.getProductName(3213))
    # for uid, user_ratings in top_n.items():
    #     print(uid, [iid for (iid, _) in user_ratings])
    return jsonify({'Rec': 200})


@app.route('/api/todos', methods=['GET', 'POST'])
def todos():
    if request.method == 'GET':
        try:
            todo_list = leancloud.Query(leancloud.Object.extend('Todo')).descending('createdAt').find()
        except LeanCloudError as e:
            if e.code == 101:  # 服务端对应的 Class 还没创建
                return jsonify([])
            else:
                raise BadGateway(e.error, e.code)
        else:
            return jsonify([todo.dump() for todo in todo_list])
    elif request.method == 'POST':
        try:
            content = request.get_json()['content']
        except KeyError:
            raise BadRequest('''receives malformed POST content (proper schema: '{"content": "TODO CONTENT"}')''')
        todo = leancloud.Object.extend('Todo')()
        todo.set('content', content)
        try:
            todo.save()
        except LeanCloudError as e:
            raise BadGateway(e.error, e.code)
        else:
            return jsonify(success=True)
