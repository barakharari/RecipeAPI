import time
from bs4 import BeautifulSoup
import requests
import os
import regex as re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import pymongo
import ssl
import json

#CLASSES

#REGEX
unitsRegex = """(teaspoons|teaspoon|tsps|tsp|ts|t|tablespoons|tablespoon|tbls|tbl|tbs|tb|tbsps|tbsp|
cup|cups|pint|p|pt|fl pt|quarts|qts|qt|quart|fl qts|fl qt|gallons|gallon|gs|g|
gals|gal|mls|ml|milliliters|milliliters|ls|l|liters|liter|dls|dl|
pounds|pound|lb|ounces|ounce|ozs|oz|mgs|mg|milligram|g|gram|kgs|kg|kilograms|kilogram)""".replace('\n', '')
nutrientsRegex = "serving|calories|carbohydrates|protein|saturated fat|fat|cholesterol|sodium|fiber|sugar"
coursesRegex = """(main course|side dish|dessert|appetizer|salad|bread|breakfast|soup|beverage|sauce|marinade|fingerfood|snack|drink)"""
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

def clickNCookCreateRecipe(soup):
    
    recipe = Recipe()
    recipe.prepTime = 0
    
    name = soup.find("div", class_="c-recipe")
    servings = soup.find("div", class_="serves")
    imageURL = soup.find("div", class_="c-recipe")
    if soup.find("ul", class_="wpurp-recipe-ingredients") is None: return None
    ingredients = [ing.find("span", class_="recipe-ingredient-quantity-unit").text + ing.find("span", class_="recipe-ingredient-name").text for ing in soup.find("ul", class_="wpurp-recipe-ingredients").find_all("li")]
    directions = [direction.text.strip() for direction in soup.find("ol", class_="wpurp-recipe-instructions").find_all("li")]
    nutrients = soup.find("div", class_="wpurp-nutrition-label")
    courseCuisineDiets = soup.find("div", class_="d-2of5").find("div", class_="tags")
    
    
    if name is None: return None
    recipe.name = name.find("h2").text.strip()
    
    if servings is not None:
        servings = servings.find_all("span", class_=lambda x: x != 'title')
        if servings is not None:
            servings = servings[0].text
            number = re.search("[0-9]+", servings.strip())
            if number is not None:
                recipe.servings = number[0]

    if imageURL is not None: 
        imageURL = imageURL.find("div", class_="img")
        if imageURL is not None:
            imageURL = re.search("http.+'", imageURL['style'])
            if imageURL is not None:
                recipe.imageURL = imageURL[0][0:len(imageURL[0]) - 1]
        
    if len(ingredients) > 0: recipe.ingredients = ingredients
    if len(directions) > 0: 
        recipe.directions = directions
        for d in directions:
            num = re.search('\d+\s', d)
            if num is None:
                recipe.prepTime += 4
            else:
                recipe.prepTime += int(num[0])

    if nutrients is not None:
        nutritionServing = nutrients.find("div", class_="nutrition-serving")
        if nutritionServing is not None:
            num = re.search(mixedNumberRegex, nutritionServing.text)
            if num is not None:
                num = num[0]
                recipe.nutrition.append({"label": "serving", "amount": num})
        nutrients = nutrients.find_all("div", class_=["nutrition-item", "nutrition-sub-item"])
        for nt in nutrients:
            main = nt.find("span", class_=["nutrition-main", "nutrition-sub"])
            if main is not None:
                nutrient = {}
                label = re.search(nutrientsRegex, main.text, re.IGNORECASE)
                amount = re.search("\d+(.\d+)?", main.text)
                if label is not None and amount is not None:
                    nutrient["label"] = label[0]
                    nutrient["amount"] = amount[0]
                    flag = 0
                    for n in recipe.nutrition:
                        if n["label"].lower() == nutrient["label"].lower(): flag = 1
                    if flag == 0: recipe.nutrition.append(nutrient)
        
            
    if courseCuisineDiets is not None: 
        courseCuisineDiets = [c.find("a").text for c in courseCuisineDiets.find("ul").find_all("li")]
        courseCuisineDietsString = ""
        for c in courseCuisineDiets:
            courseCuisineDietsString += c
        courseCuisineDietsString = courseCuisineDietsString.lower()
        courses = re.findall(coursesRegex, courseCuisineDietsString)
        cuisines = re.findall(cuisinesRegex, courseCuisineDietsString)
        diets = re.findall(dietsRegex, courseCuisineDietsString)
        if courses is not None:
            recipe.courses = courses
        if cuisines is not None:
            recipe.cuisines = cuisines
        if diets is not None:
            recipe.diets = diets
            
    return recipe.__dict__  


options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--incognito')
#options.add_argument('--headless')

browser = webdriver.Chrome('/Users/barakharari/bin/chromedriver', options = options)
browser.get("https://clickncook.org/search/?wpurp-search=&s=")

lastHeight = browser.execute_script("return document.body.scrollHeight")


while True:
    browser.execute_script("window.scrollBy(0, document.body.scrollHeight)")
    time.sleep(3)
    
    newHeight = browser.execute_script("return document.body.scrollHeight")
    if newHeight == lastHeight:
        break
    lastHeight = newHeight
    
    
#Clickncook upload
source = browser.page_source
soup = BeautifulSoup(source, "lxml")
links = [l['bad-fake-href'] for l in soup.find("div", class_="alm-ajax").find_all("div", class_="featured_recipe wpurp-container")]

recipes = []

print(len(links))

for link in links:
    page = requests.get(link).text
    soup = BeautifulSoup(page, "lxml")
    recipe = clickNCookCreateRecipe(soup)
    if recipe is not None:
        recipes.append(recipe)
    if len(recipes) % 100 == 0:
        collection.insert_many(recipes)  
        recipes = []
        
collection.insert_many(recipes)