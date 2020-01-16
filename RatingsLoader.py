
import leancloud
from surprise import Dataset
from surprise import Reader
from collections import defaultdict
import pandas as pd


class RatingsLoader:
    productID_to_name = {}
    name_to_productID = {}
    productID_to_product = {}
    ratingsPath = ''
    productsPath = 'styles4.csv'
    ratings_dict = {}

    def loadDataset(self):

        self.productID_to_name = {}
        self.name_to_productID = {}

        query = leancloud.Query('Rating')
        numOfRatings = query.count()
        ratings = query.select('objectId','uId', 'pId', 'rating','productStr', 'createAt').limit(numOfRatings).find()
        # print(ratings[0].get('productStr'))
        self.ratings_dict = {
            # 'objectId': [rating.get('objectId') for rating in ratings],
            'userID': [rating.get('uId') for rating in ratings],
            'itemID': [rating.get('pId') for rating in ratings],
            'rating': [rating.get('rating') for rating in ratings],
        }
        df = pd.DataFrame(self.ratings_dict)
        reader = Reader(rating_scale=(0.5, 5))
        data = Dataset.load_from_df(df[['userID', 'itemID', 'rating']], reader)


        # build a dictionary with products
        q_product = leancloud.Query('Product')
        num_of_products = q_product.count()
        prods = q_product.limit(num_of_products).find()
        for prod in prods:
            self.productID_to_name[prod.get('pId')] = prod.get('title')
            self.name_to_productID[prod.get('title')] = prod.get('pId')
            self.productID_to_product[prod.get('pId')] = {
                'objectId': prod.get('objectId'),
                'pId': prod.get('pId'),
                'articleType': prod.get('articleType'),
                'baseColour': prod.get('baseColour'),
                'createBy': prod.get('createBy'),
                'description': prod.get('description'),
                'gender': prod.get('gender'),
                'imageUrl': prod.get('imageUrl'),
                'mainCategory': prod.get('mainCategory'),
                'subCategory': prod.get('subCategory'),
                'numOfRating': prod.get('numOfRating'),
                'price': prod.get('price'),
                'rating': prod.get('rating'),
                'season': prod.get('season'),
                'title': prod.get('title'),
                'usage': prod.get('usage'),
                'year': prod.get('year'),
            }
        return data

    def get_products_dict(self):
        q_product = leancloud.Query('Product')
        num_of_products = q_product.count()
        prods = q_product.limit(num_of_products).find()
        for prod in prods:
            self.productID_to_name[prod.get('pId')] = prod.get('title')
            self.name_to_productID[prod.get('title')] = prod.get('pId')
            self.productID_to_product[prod.get('pId')] = {
                'objectId': prod.get('objectId'),
                'pId': prod.get('pId'),
                'articleType': prod.get('articleType'),
                'baseColour': prod.get('baseColour'),
                'createBy': prod.get('createBy'),
                'description': prod.get('description'),
                'gender': prod.get('gender'),
                'imageUrl': prod.get('imageUrl'),
                'mainCategory': prod.get('mainCategory'),
                'subCategory': prod.get('subCategory'),
                'numOfRating': prod.get('numOfRating'),
                'price': prod.get('price'),
                'rating': prod.get('rating'),
                'season': prod.get('season'),
                'title': prod.get('title'),
                'usage': prod.get('usage'),
                'year': prod.get('year'),
            }

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

    def getProduct(self,productID):
        if productID in self.productID_to_product:
            return self.productID_to_product[productID]
        else:
            return "NOT FOUND"
