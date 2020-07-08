from flask import Flask, jsonify, request
import pymongo
import ssl
import random
import regex as re

app = Flask(__name__)
client = pymongo.MongoClient("mongodb+srv://barak:barakh123@recipeappcluster-4ywv5.mongodb.net/test?retryWrites=true&w=majority", ssl=True, ssl_cert_reqs=ssl.CERT_NONE)


def createRegex(data):
    return "(" + "|".join(data) + ")"

def getRecipes(ingredients, courses, cuisines, diets, number, time, c):

    collection = client["Recipes"]["All"]

    recipes = []

    ingredients += [Word(ing).pluralize() for ing in ingredients]

    ingredientRegex = createRegex(ingredients)
    cuisinesRegex = createRegex(cuisines)
    coursesRegex = createRegex(courses)
    dietsRegex = createRegex(diets)

    queryObject = {"ingredients": {"$regex": ingredientRegex, "$options": "i"},
                   "prepTime": {"$lt" : str(time)}}

    if len(courses) > 0: queryObject["courses"] = {"$regex": coursesRegex, "$options": "i"}
    if len(cuisines) > 0: queryObject["cuisines"] = {"$regex": cuisinesRegex, "$options": "i"}
    if len(diets) > 0: queryObject["diets"] = {"$regex": dietsRegex, "$options": "i"}

    results = collection.find(queryObject)
    recipes += list(results)

    if len(recipes) < number:
        queryObject.pop("ingredients", None)
        recipes += collection.find(queryObject)

    # if len(recipes) < number:
    #     queryObject = {"ingredients": {"$regex": ingredientRegex, "$options": "i"}}
    #     recipes += collection.find(queryObject)

    for recipe in recipes:
        recipe["_id"] = str(recipe["_id"])
        recipe["ingredientsMatched"] = []
        for ing in recipe["ingredients"]:
            findIng = re.search(ingredientRegex, ing, re.IGNORECASE)
            if findIng is not None:
                    recipe["ingredientsMatched"].append(findIng[0].lower())
        recipe["ingredientsMatched"] = list(set(recipe["ingredientsMatched"]))
        recipe["total"] = len(recipe["ingredients"])

    recipes = sorted(recipes, key=lambda rec: len(rec["ingredientsMatched"])/rec["total"], reverse=True)
    recipes = recipes[0:number]

    return recipes

#######################################################################
# request.json contents (arrays):
# ingredients, cuisines (optional), courses (optional), diets (optional)
#######################################################################

@app.route('/maxpreptime=<int:time>', defaults={'number': 5})
@app.route('/numresults=<int:number>', defaults={'time': 1440})
@app.route('/numresults=<int:number>/maxpreptime=<int:time>', methods=['GET', 'POST'])
def findByIngredients(number, time):

    ingredients = []
    courses = []
    cuisines = []
    diets = []

    if "ingredients" not in request.json: return {"response": "Missing ingredients field in request body"}
    else: ingredients = request.json["ingredients"]
    if "courses" in request.json: courses = request.json["courses"]
    if "cuisines" in request.json: cuisines = request.json["cuisines"]
    if "diets" in request.json: diets = request.json["diets"]

    recipes = getRecipes(ingredients, courses, cuisines, diets, number, time)

    return jsonify({"numResults": str(len(recipes)), "response": recipes})

@app.route('/ingredients/aisle=<string:aisle>', methods=['GET'])
def getIngredientsByAisle(aisle):
    if aisle is None: return

    collection = client["Aisles"]["All"]
    item = collection.find_one({"aisle": aisle})

    if item is not None:
        ingredients = item['ingredients']
    else:
        ingredients = []

    return jsonify({"ingredients": ingredients})

if __name__ == "__main__":
    app.run(debug=True)
