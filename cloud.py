# coding: utf-8

import json
from leancloud import Engine
from leancloud import LeanEngineError
from leancloud import Object
from leancloud import Query
from surprise import KNNBasic
from RatingsLoader import RatingsLoader
from collections import defaultdict
from flask import jsonify
from leancloud import cloudfunc
engine = Engine()


@engine.define('hello')
def hello(**params):
    if 'name' in params:
        return 'Hello, {}!'.format(params['name'])
    else:
        return 'Hello, LeanCloud!'


@engine.define('build_rec_list')
def build_rec_list(**params):
    ml = RatingsLoader()
    data = ml.loadDataset()
    trainset = data.build_full_trainset()
    sim_options = {'name': 'cosine', 'user_based': True}
    algo = KNNBasic(sim_options=sim_options)
    algo.fit(trainset)
    testset = trainset.build_anti_testset()
    predictions = algo.test(testset)
    top_n = get_top_n(predictions)
    Recommend = Object.extend('Recommend')
    for uid, user_ratings in top_n.items():
        rec = Recommend()
        rec.set('uId', uid)
        rec.set('pIds', [iid for (iid, _) in user_ratings])
        rec.set('pTitles', [ml.getProductName(int(iid)) for (iid, _) in user_ratings])
        rec.set('products', [json.dumps(ml.getProduct(int(iid))) for (iid, _) in user_ratings])
        rec.save()
    print('is success run')


@engine.define('update_rec_list')
def update_rec_list(**params):
    qRec = Query('Recommend')
    num_of_user = qRec.count()
    results = qRec.limit(num_of_user).ascending('uId').find()
    list_of_rec = []
    for result in results:
        list_of_rec.append({
            'objectId': result.get('objectId'),
            'pIds': result.get('pIds'),
            'pTitles': result.get('pTitles'),
            'uId': result.get('uId'),
        })

    # delete all data in the database
    Recommend = Object.extend('Recommend')
    destroy_list = []
    for rec in list_of_rec:
        recommend = Recommend.create_without_data(rec.get('objectId'))
        destroy_list.append(recommend)
    Object.destroy_all(destroy_list)
    # update recommend data for each users
    cloudfunc.run.local('build_rec_list')



@engine.before_save('Todo')
def before_todo_save(todo):
    content = todo.get('content')
    if not content:
        raise LeanEngineError('内容不能为空')
    if len(content) >= 240:
        todo.set('content', content[:240] + ' ...')


def get_top_n(predictions, n=10):
    top_n = defaultdict(list)
    for uid, iid, true_r, est, _ in predictions:

        top_n[uid].append((iid, est))

    for uid, user_ratings in top_n.items():
        user_ratings.sort(key=lambda x: x[1], reverse=True)
        top_n[uid] = user_ratings[:n]
    return top_n
