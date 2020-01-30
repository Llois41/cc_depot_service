from flask import Flask
from flask_pymongo import PyMongo
import os

app = Flask(__name__)
# if app.config["ENV"] == "production":
#     app.config.from_object("config.ProductionConfig")
# else:
#     app.config.from_object("config.DevelopmentConfig")

app.config["MONGO_URI"] = os.environ['MONGO_URI']
app.config["STOCK_URI"] = os.environ['STOCK_URI']
app.config["DEBUG"] = False
app.config["TESTING"]= False

mongo = PyMongo(app)
# MONGO_URI = os.environ['MONGO_URI']
# mongo= PyMongo(app, uri=MONGO_URI)