import csv
import pickle
import requests
import json


def updateIngredientsFile(ingredients):
    with open("./ingredients.pickle", 'wb') as ings:
        pickle.dump(ingredients, ings)

def getIngredients():
    with open("./ingredients.pickle", 'rb') as ings:
        ingredients = pickle.load(ings)
        return ingredients

with open('./top-1k-ingredients.csv') as file:
    categorizedIngredients = list(csv.reader(file))
    for i in range (0,len(categorizedIngredients)):
        info = categorizedIngredients[i][0].capitalize().split(';')
        categorizedIngredients[i] = {"name": info[0], "id": info[1]}

ingredients = getIngredients()
checked = [i for i in ingredients if len(i['aisle']) > 0]
print(len(checked))
print(ingredients)

# for i in range(938,len(ingredients)):
#     url = "https://api.spoonacular.com/food/ingredients/" + ingredients[i]["id"] + "/information?apiKey=5a123a069b974d86a6f2bd116b694394&amount=1"
#     ingInfo = requests.get(url).text
#     if ingInfo is not None:
#         ingInfo = json.loads(ingInfo)
#         if 'aisle' in ingInfo:
#             print(i)
#             aisles = ingInfo['aisle'].split(";")
#             ingredients[i]['aisle'] = aisles
#     updateIngredientsFile(ingredients)
