# RecipeAPI
Recipe REST API developed using Flask and Python. Pass in ingredients in your pantry and get back recipes!

Request Format:

URL:
"/maxpreptime=<int>"
"/numresults=<int>"
"/numresults=<int>&maxpreptime=<int>"

BODY:
"ingredients" : [array of ingredients]
