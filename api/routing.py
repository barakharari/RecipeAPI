from flask import Flask, jsonify, request
import pymongo
import ssl
import random
import regex as re

app = Flask(__name__)
client = pymongo.MongoClient("mongodb+srv://barak:barakh123@recipeappcluster-4ywv5.mongodb.net/test?retryWrites=true&w=majority", ssl=True, ssl_cert_reqs=ssl.CERT_NONE)
collection = client["Recipes"]["All"]

def getRecipes(meals, number, time, ingredients):

    regex = "(" + "|".join(ingredients) + ")"
    recipes = []

    if time is None:
        recipes = list(collection.aggregate([
        {"$match":{"meal": {"$in": meals}, "ingredients.name": {"$in":ingredients}}}
        ]))
    else:
        recipes = list(collection.aggregate([
        {"$match":{"meal": {"$in": meals}, "ingredients.name": {"$in":ingredients}, "prepTime": {"$lt" : str(time)}}}
        ]))

    if len(recipes) == 0: return recipes

    for recipe in recipes:
        recipe["matched"] = 0
        for ing in recipe["ingredients"]:
            if re.search(regex, ing["name"]) is not None:
                recipe["matched"] += 1

    recipes = sorted(recipes, key=lambda rec: rec["matched"], reverse=True)
    recipes = recipes[0:number]
    for rec in recipes:
        rec["_id"] = str(rec["_id"])
        rec["total"] = len(ingredients)
    return recipes

@app.route('/maxpreptime=<int:time>', defaults={'number': 5})
@app.route('/numresults=<int:number>', defaults={'time': None})
@app.route('/numresults=<int:number>/maxpreptime=<int:time>', methods=['GET', 'POST'])
def findByIngredients(number, time):

    if "ingredients" not in request.json or "meal" not in request.json:
        return {"response": "Request body formatted poorly"}
    ingredients = request.json["ingredients"]
    meals = request.json["meal"]
    recipes = getRecipes(meals, number, time, ingredients)

    return jsonify({"numResults": str(len(recipes)), "response": recipes})

if __name__ == "__main__":
    app.run(debug=True)
