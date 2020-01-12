from RatingsLoader import RatingsLoader
from surprise import KNNBasic
from surprise import NormalPredictor
from Evaluator import Evaluator

import random
import numpy as np

def LoadItemData():
    ml = RatingsLoader()
    print("Loading product ratings...")
    data = ml.loadDataset()
    print("\nComputing product items popularity ranks so we can measure novelty later...")
    rankings = ml.getPopularityRanks()
    return (ml, data, rankings)

np.random.seed(0)
random.seed(0)

(ml, evaluationData, rankings) = LoadItemData()


evaluator = Evaluator(evaluationData, rankings)


UserKNN = KNNBasic(sim_options = {'name': 'cosine', 'user_based': True})
evaluator.AddAlgorithm(UserKNN, "User KNN")


ItemKNN = KNNBasic(sim_options = {'name': 'cosine', 'user_based': False})
evaluator.AddAlgorithm(ItemKNN, "Item KNN")

# Just make random recommendations
Random = NormalPredictor()
evaluator.AddAlgorithm(Random, "Random")

# Fight!
evaluator.Evaluate(False)

evaluator.SampleTopNRecs(ml)