import os
import csv
import sys
import re
import leancloud
from surprise import Dataset
from surprise import Reader
from collections import defaultdict
import numpy as np
import pandas as pd


class RatingsLoader:
    productID_to_name = {}
    name_to_productID = {}
    ratingsPath = ''
    productsPath = 'styles4.csv'
    ratings_dict = {}

    def loadDataset(self):

        self.productID_to_name = {}
        self.name_to_productID = {}

        query = leancloud.Query('Rating')
        numOfRatings = query.count()
        ratings = query.select('uId', 'pId', 'rating', 'createAt').limit(numOfRatings).find()
        self.ratings_dict = {
            'userID': [rating.get('uId') for rating in ratings],
            'itemID': [rating.get('pId') for rating in ratings],
            'rating': [rating.get('rating') for rating in ratings],
        }
        df = pd.DataFrame(self.ratings_dict)
        reader = Reader(rating_scale=(0.5, 5))
        data = Dataset.load_from_df(df[['userID', 'itemID', 'rating']], reader)
        #build a dictionary with all products
        # with open(self.productsPath,newline='',encoding='ISO-8859-1') as csvfile:
        #     productReader = csv.reader(csvfile)
        #     next(productReader)
        #     for row in productReader:
        #         productID = int(row[1])
        #         productName = row[10]
        #         self.productID_to_name[productID] = productName
        #         self.name_to_productID[productName] = productID
        # print(len(self.name_to_productID))

        # build a dictionary with products
        q_product = leancloud.Query('Product')
        num_of_products = q_product.count()
        prods = q_product.select('pId','articleType','title').limit(num_of_products).find()
        for prod in prods:
            self.productID_to_name[prod.get('pId')] = prod.get('title')
            self.name_to_productID[prod.get('title')] = prod.get('pId')
        return data

    def getUserRatings(self, user):
        userRatings = []
        hitUser = False
        query = leancloud.Query('Rating')
        numOfRatings = query.count()
        ratings = query.select('uId', 'pId', 'rating', 'createAt').limit(numOfRatings).find()
        for rating in ratings:
            userID = int(str(rating.get('uId')))
            if (user == userID):
                productID = int(str(rating.get('pId')))
                rating = float(str(rating.get('rating')))
                userRatings.append((productID,rating))
                hitUser = True
            if (hitUser and (user != userID)):
                break
        return userRatings

    def getPopularityRanks(self):
        ratingsDict = defaultdict(int)
        rankingsDict = defaultdict(int)
        query = leancloud.Query('Rating')
        numOfRatings = query.count()
        ratings = query.select('uId', 'pId', 'rating', 'createAt').limit(numOfRatings).find()
        for rating in ratings:
            itemID = int(str(rating.get('pId')))
            ratingsDict[itemID] += 1
        rank = 1
        for itemID, ratingCount in sorted(ratingsDict.items(), key=lambda x: x[1], reverse=True):
            rankingsDict[itemID] = rank
            rank += 1
        return rankingsDict

    def getYears(self):
        pass

    def getProductName(self, productID):
        if productID in self.productID_to_name:
            return self.productID_to_name[productID]
        else:
            return "NOT FOUND"

    def getProductID(self, productName):
        if productName in self.name_to_productID:
            return self.name_to_productID[productName]
        else:
            return 0
