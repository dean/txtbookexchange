from flask import request, render_template, flash, g, session, redirect, url_for
from flask.ext.login import login_required, login_user, logout_user, current_user
from flatterer import db, lm, app
from forms import AddGender, AddCompliment, AddUser, AddTheme
from models import Gender, Compliment, Theme, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from random import shuffle
import re

@app.route("/")
def home():
    return "Ready to be flattered? ^^"

@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    form = AddUser()
    msg = ""
    if request.method == "POST":
        db.session.add(User(form.name.data, form.greeting.data))
        db.session.commit()
        msg = form.name.data + " added successfully!"

    return render_template('add_user.html', form=form, msg=msg)

@app.route("/add_gender", methods=['GET', 'POST'])
def add_gender():
    form = AddGender()
    if request.method == "POST":
        #Add district to db.
        db.session.add(Gender(form.gender.data))
        db.session.commit()
    #return "Disabled currently."
    return render_template('add_gender.html', form=form)

@app.route("/add_compliment", methods=['GET', 'POST'])
def add_compliment():
    form = AddCompliment()
    msg = ""

    if request.method == "POST":
        add_compliment(form)
        msg = "Compliment successfully added!"
    return render_template('add_compliment.html', form=form,
                        msg=msg)

@app.route("/<name>/add_theme/", methods=['GET', 'POST'])
def add_theme(name):
    form = AddTheme()
    if request.method == "POST":
        db.session.add(Theme(name, form.theme_path.data, form.song_path.data))
        db.session.commit()
    
    return render_template('add_theme.html', form=form, name=name) 

def add_compliment(form):
    if form.gender.data != "None":
        db.session.add(Compliment(compliment=form.compliment.data, 
                        compliment_gender=form.gender.data))
        print "Gender specific compliment added"
    else:
        db.session.add(Compliment(compliment=form.compliment.data,
                        compliment_gender=form.gender.data,
                        user_name=form.name.data))    
        print "Personal compliment added."
    db.session.commit()


def remove_compliments(compliment_ids):
    for compliment_id in compliment_ids:
        remove = Compliment.query.filter_by(id=compliment_id)
        db.session.delete(remove[0])
    db.session.commit()

@app.route("/compliment/<_gender>/<name>", methods=['GET', 'POST'])
def compliment(_gender, name):

    gender_compliments = Compliment.query.filter_by(compliment_gender=_gender).all()
    compliments = Compliment.query.filter_by(compliment_gender="Any").all() + gender_compliments

    shuffle(compliments)
    return render_template("compliment.html", name=name, compliments=compliments)

@app.route("/control_panel", methods=['GET', 'POST'])
def compliment_control_panel():
    form = AddCompliment()
    msg = ""
    if request.method == "POST":
        if form.compliment.data:
            add_compliment(form)
            msg = "Compliment added successfully!"
        else:
            compliment_ids = request.form.getlist('checkbox')
            remove_compliments(compliment_ids)
            remove_msg = str(len(compliment_ids))+" compliments removed successfully!"            

    male_comps = Compliment.query.filter_by(compliment_gender="Male").all()
    female_comps = Compliment.query.filter_by(compliment_gender="Female").all()
    any_comps = Compliment.query.filter_by(compliment_gender="Any").all()

    personal_comps = Compliment.query.filter_by(compliment_gender="None").all()
    return render_template("remove_compliments.html", male_comps=male_comps, female_comps=female_comps, any_comps=any_comps, personal_comps=personal_comps, form=form, msg=msg)

@app.route("/<name>")
def compliment_individual(name):
        compliments = Compliment.query.filter_by(user_name=name).all()
        theme = Theme.query.filter_by(user_name=name).all()
        for x in range(10):
            for them in theme:
                print them
                print them.user_name
                print them.song_path
                print them.theme_path
        if compliments:
            greeting = User.query.filter_by(name=name)[0].greeting
            return render_template("compliment_individual.html", greeting=greeting, name=name, theme=theme[0], compliments=compliments)
        else:
            return "The name you provided is not in the database!"
           
