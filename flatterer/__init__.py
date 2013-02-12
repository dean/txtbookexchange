from flask import Flask, render_template, g
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
import sqlite3

app = Flask(__name__)
app.config.from_object('config')

lm = LoginManager()

db = SQLAlchemy(app)
db.init_app(app)
lm.setup_app(app)

import models, views

