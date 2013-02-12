from flatterer import db
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime, date, time, timedelta

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    greeting = db.Column(db.String(1000))

    def __init__(self, name, greeting=None):
        self.name = name
        self.greeting = greeting

class Theme(db.Model):
    __tablename__ = "themes"
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), db.ForeignKey('users.name'))
    #Can be urls to a file on the local computer, or to an local file path
    theme_path = db.Column(db.String(255))
    song_path =  db.Column(db.String(255))

    def __init__(self, user_name, theme_path=None, song_path=None):
        self.user_name = user_name
        self.theme_path = theme_path
        self.song_path = song_path


class Gender(db.Model):
    __tablename__ = 'gender'
    id = db.Column(db.Integer, primary_key=True)
    gender = db.Column(db.String(50), unique=True)

    def __init__(self, gender):
        self.gender = gender

    def __repr__(self):
        return '<Gender %r>' % (self.gender)


class Compliment(db.Model):
    __tablename__ = 'compliments'
    id = db.Column(db.Integer, primary_key=True)
    compliment = db.Column(db.String(255))
    compliment_gender = db.Column(db.String(50), db.ForeignKey('gender.gender'))
    user_name = db.Column(db.Integer, db.ForeignKey('users.name'))

    def __init__(self, compliment, compliment_gender=None, user_name=None):
        self.compliment = compliment
        self.compliment_gender = compliment_gender
        self.user_name = user_name
    def __repr__(self):
        return "<Compliment('%s')>" % (self.compliment)

