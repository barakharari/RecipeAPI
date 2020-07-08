import csv
import pickle
import requests
import json
import pymongo
import random
import ssl
from bs4 import BeautifulSoup
from PIL import Image

ipath = "./ingredients.pickle"
apath = "./aisles.pickle"

def getIngredientAislesFromSpoonacular(ingredients):
    for i in range(0,len(ingredients)):
        url = "https://api.spoonacular.com/food/ingredients/" + ingredients[i]["id"] + "/information?apiKey=5a123a069b974d86a6f2bd116b694394&amount=1"
        ingInfo = requests.get(url).text
        if ingInfo is not None:
            ingInfo = json.loads(ingInfo)
            if 'aisle' in ingInfo:
                print(i)
                aisles = ingInfo['aisle'].split(";")
                ingredients[i]['aisle'] = aisles
        uploadToFile(ingredients, ipath)

def uploadToFile(elements, fileName):
    with open(fileName, 'wb') as file:
        pickle.dump(elements, file)

def getFromFile(fileName):
    with open(fileName, 'rb') as file:
        return pickle.load(file)

def getInfoFromCSV():
    with open('./top-1k-ingredients.csv') as file:
        categorizedIngredients = list(csv.reader(file))
        for i in range (0,len(categorizedIngredients)):
            info = categorizedIngredients[i][0].capitalize().split(';')
            categorizedIngredients[i] = {"name": info[0], "id": info[1]}
        return categorizedIngredients

def organizeAislesFromIngredients():
    ingredients = getFromFile(ipath)
    aisles = {}

    for i in ingredients:
        for a in i['aisle']:
            ing = i['name']
            if a in aisles:
                aisles[a].append(ing)
            else:
                aisles[a] = [ing]
    return aisles

def uploadToDB():
    client = pymongo.MongoClient("mongodb+srv://barak:barakh123@recipeappcluster-4ywv5.mongodb.net/test?retryWrites=true&w=majority", ssl=True, ssl_cert_reqs=ssl.CERT_NONE)
    db = client["Aisles"]
    aisles = getFromFile(apath)
    for key,value in aisles.items():
        print("Aisle: " + key)
        collection = db["All"]
        collection.insert_one({'aisle': key, 'ingredients': value})

def downloadAndSaveImage(name):
    url = "https://spoonacular.com/cdn/ingredients_250x250/" + name.replace(" ", "").lower() + ".jpg"
    imageData = requests.get(url).content
    with open("./temp.jpg", "wb") as tempImage:
        tempImage.write(imageData)

def getImageDimensions():
    image = Image.open("temp.jpg")
    width, height = image.size
    return width, height

def orderAislesBasedOnImageAvailability():
    aisles = getFromFile(apath)
    for k,v in aisles.items():
        print(k)
        newV = []
        for ing in v:
            downloadAndSaveImage(ing)
            width = getImageDimensions()[0]
            if width != 556:
                newV.insert(0, ing)
            else:
                newV.append(ing)

        aisles[k] = newV
        print(aisles[k])

        uploadToFile(aisles, apath)

uploadToDB()
