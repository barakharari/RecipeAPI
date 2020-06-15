import time
from bs4 import BeautifulSoup
import requests
import os
import regex as re
import pymongo
import ssl
import json
import pickle

#CLASSES

#REGEX
unitsRegex = """(teaspoons|teaspoon|tsps|tsp|ts|t|tablespoons|tablespoon|tbls|tbl|tbs|tb|tbsps|tbsp|
cup|cups|pint|p|pt|fl pt|quarts|qts|qt|quart|fl qts|fl qt|gallons|gallon|gs|g|
gals|gal|mls|ml|milliliters|milliliters|ls|l|liters|liter|dls|dl|
pounds|pound|lb|ounces|ounce|ozs|oz|mgs|mg|milligram|g|gram|kgs|kg|kilograms|kilogram)""".replace('\n', '')
nutrientRegex = "serving|calories|carbohydrates|protein|saturated fat|fat|cholesterol|sodium|fiber|sugar"
coursesRegex = """(main course|side dish|dessert|appetizer|dinner|salad|bread|breakfast|soup|beverage|sauce|marinade|fingerfood|snack|drink)"""
dietsRegex = """(gluten free|ketogenic|keto|vegetarian|vegan|pescetarian|paleo|primal|whole30)"""
cuisinesRegex = """(african|american|british|cajun|carribean|chinese|eastern european|european|french|german|greek|indian|irish|italian|japanese|jewish|korean|latin american|mediterranean|mexican|middle eastern|nordic|southern|spanish|thai|vietnamese)"""
mixedNumberRegex = "[0-9]+( [0-9]+)?(/[0-9]+)?"
removeBadChars = re.compile("[,.!?()]")

client = pymongo.MongoClient("mongodb+srv://barak:barakh123@recipeappcluster-4ywv5.mongodb.net/test?retryWrites=true&w=majority", ssl=True, ssl_cert_reqs=ssl.CERT_NONE)
headers = {"User-Agent":"Mozilla/5.0"}
db = client["Recipes"]
collection = db["All"]

class Recipe:

    def __init__(self):
        self.name = None
        self.servings = None
        self.prepTime = None
        self.imageURL = None
        self.ingredients = []
        self.directions = []
        self.nutrition = []
        self.cuisines = []
        self.courses = []
        self.diets = []

        
def parseNutrients(regex, data):
    
    amount = None
    unit = None
    name = None

    if re.search(regex, data) is None:
        search = re.search("[0-9]+", data)
        if search is not None:
            amount = search[0]
            name = removeBadChars.sub('', data[0:search.span()[0]] + data[search.span()[1]:len(data)]).strip()
        else:
            name = data
    else:
        matches = regex.finditer(data)
        for match in matches:
            name = removeBadChars.sub('', data[0:match.span()[0]] + data[match.span()[1]:len(data)]).strip()
            match = removeBadChars.sub('', match[0])
            aAndu = re.search(mixedNumberRegex, match)
            amount = handleNumber(aAndu[0])
            unit = match[0:aAndu.span()[0]] + match[aAndu.span()[1]:len(match)].strip()
            break

    return (name, amount, unit)
        
def tasteOfHomeCreateRecipe(soup, courses, cuisines, diets):
    
    recipe = Recipe()
    
    recipe.courses = courses
    recipe.cuisines = cuisines
    recipe.diets = diets
    
    name = soup.find("h1", class_="recipe-title")
    if name is None: return None
    recipe.name = name.text
    servings = soup.find("div", class_="recipe-time-yield__label-servings")
    prepTime = soup.find("div", class_="recipe-time-yield__label-prep")
    quote = soup.find("div", class_="recipe-tagline__text")
    imageURL = soup.find("div", class_="recipe-image-and-meta-sidebar__featured-container")
    if soup.find("div", class_="recipe-ingredients") is None: return None
    ingredients = [ingredient.text.strip() for ingredient in soup.find("div", class_="recipe-ingredients").find_all("li") if ingredient.find("b") is None]
    if soup.find("ul", class_="recipe-directions__list") is None: return None
    directions = [direction.text.strip() for direction in soup.find("ul", class_="recipe-directions__list").find_all("li")]
    nutrients = soup.find("div", class_="recipe-nutrition-facts")
    
    if quote is not None:
        courses = re.findall(coursesRegex, quote.text, re.IGNORECASE)
        cuisines = re.findall(cuisinesRegex, quote.text, re.IGNORECASE)
        diets = re.findall(dietsRegex, quote.text, re.IGNORECASE)
        if len(courses) > 0: 
            recipe.courses += list(courses)
        if len(cuisines) > 0: 
            recipe.cuisines += list(set(cuisines))
        if len(diets) > 0: 
            recipe.diets += list(set(diets))
            
    for i in range(0,len(courses)):
        if courses[i].lower() == "dinner": courses[i] = "main course"
        elif courses[i].lower() == "brunch": courses[i] = "breakfast"
    
    recipe.courses = list(set(recipe.courses))
    recipe.cuisines = list(set(recipe.cuisines))
    recipe.diets = list(set(recipe.diets))
    
    if servings is not None:
        servings = re.search("[0-9]+\s", servings.text.strip())
        if servings is not None:
            recipe.servings = servings[0].strip()
            
    
    if imageURL is not None:
        recipe.imageURL = imageURL.find("img")['src']
        
    if prepTime is not None:
        mins = re.findall("\d+\smin", prepTime.text)
        hours = re.findall("\d+\shour", prepTime.text)
        time = 0
        if mins is not None:
            for m in mins:
                m = int(re.search("\d+", m)[0])
                time += int(m)
        if hours is not None:
            for h in hours:
                h = 60 * int(re.search("\d+", h)[0])
                time += h
        if time != 0: recipe.prepTime = time

    if nutrients is not None:   
        nutrients = re.split('[:,().]', nutrients.text)
        nutrients = [' '.join(nt.split()) for nt in nutrients if nt is not '']
        nutrients = [nt for nt in nutrients if re.search('[0-9]+', nt) is not None]
        if len(nutrients) > 0: 
            nservings = re.search(mixedNumberRegex, str(nutrients[0]))
            if nservings is not None:
                recipe.nutrition.append({"label": "serving", "amount": nservings[0]})
            for i in range(1, len(nutrients)):
                label = re.search(nutrientRegex, nutrients[i])
                amount = re.search("\d+", nutrients[i])
                if label is not None and amount is not None:
                    recipe.nutrition.append({"label": label[0], "amount": amount[0]})
                
    if len(ingredients) > 0: recipe.ingredients = ingredients
    if len(directions) > 0: recipe.directions = directions
            
    return recipe.__dict__

mainURLs = ["https://www.tasteofhome.com/recipe-collections/page/" + str(u) for u in range(1, 140)]

obj = {"recipeUrls": [], "collectionTitles": []}

#RESET
# with open("urls.pickle", 'rb') as f:
#     obj = pickle.load(f)
#     print("Num recipes:" + str(len(obj["recipeUrls"])))
#     obj = {"recipeUrls": [], "collectionTitles": []}
    
# with open("urls.pickle", "wb") as f:
#     pickle.dump(obj, f) 

p = 0

for main in mainURLs:
    
    p += 1
    print("Page: " + str(p))
 
    page = requests.get(main, headers=headers).text
    soup = BeautifulSoup(page, "lxml")
    lists = [url.find("ul") for url in soup.find_all("div", class_="tax-grid")]
    urls = []
    for l in lists: urls += l.find_all("li")
    urls = [u.find("a")['href'] for u in urls]
    titles = [u.find("h4").text for u in soup.find_all("div", class_="recipe-text")]
    
    with open("urls.pickle", 'rb') as f:
        obj = pickle.load(f)
        print("Num recipes: " + str(len(obj["recipeUrls"])))
        
    obj["collectionTitles"] += titles
    
    for i in range (0, len(urls)):
        
        if i < len(titles) - 1:    
            print(titles[i])
            courses = re.findall(coursesRegex, titles[i], re.IGNORECASE)
            cuisines = re.findall(cuisinesRegex, titles[i], re.IGNORECASE)
            diets = re.findall(dietsRegex, titles[i], re.IGNORECASE)

            page = requests.get(urls[i], headers=headers).text
            soup = BeautifulSoup(page, "lxml")
            recipeURLs = [u.find("h4").find("a")["href"] for u in soup.find_all("div", class_="listicle-page") if u.find("h4") is not None and u.find("h4").find("a") is not None]
            obj["recipeUrls"] += recipeURLs      
       
    with open("urls.pickle", "wb") as f:
        pickle.dump(obj, f) 
        

#     for recipe in recipeURLs:
#         page = requests.get(recipe, headers=headers).text
#         soup = BeautifulSoup(page, "lxml")
#         rec = tasteOfHomeCreateRecipe(soup, courses, cuisines, diets)
#         if rec is not None:
#             recipes.append(rec)
#         recipes = []

#     collection.insert_many(recipes)



# url = "https://www.tasteofhome.com/recipes/quick-chicken-piccata/"
# page = requests.get(url, headers=headers).text
# soup = BeautifulSoup(page, "lxml")
# print(tasteOfHomeCreateRecipe(soup))
