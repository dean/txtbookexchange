from flask import Blueprint, request, render_template, flash, g, session, redirect
from flask.ext.login import login_required, login_user, logout_user, current_user
from flatterer import db, app, login_manager
from forms import Register, AddGender, AddCompliment, AddComplimentee, AddTheme, Get_Info, LoginForm, Relay
from models import User, Gender, Compliment, Theme, Complimentee, RelaySignup, Time
from random import shuffle
from functools import wraps

relay = Blueprint('relay', __name__, url_prefix='/relay')

@relay.route("/signup", methods=["GET", "POST"])
def signup_sheet():

    timeslot = Time.query.all()

    for time in timeslot:
        time.form = Relay()
        if request.method == "POST":
            if time.time in request.form:
                db.session.add(RelaySignup(name=time.form.name.data, house=time.form.house.data, time=time.time))
                db.session.commit()
            time.form.name.data = ""

        time.users = RelaySignup.query.filter_by(time=time.time).all()

    return render_template("relay_signup.html", user=g.user, timeslot=timeslot)

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user.is_anonymous():
            return no_perms("You must be logged in to access this page!")
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user.is_anonymous() or not g.user.admin():
            return no_perms("You are not an admin!")
        return f(*args, **kwargs)
    return decorated_function

def require_complimentee_perms(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        complimentee = Complimentee.query.filter_by(name=kwargs['name']).first()
        if complimentee:
            if complimentee.owner is not g.user.id:
                return no_perms("You can not edit a complimentee you did not create!")
        else:
            return no_perms("The complimentee you are looking for does not exist!")
        return f(*args, **kwargs)
    return decorated_function


@app.before_request
def before_request():
    g.user = current_user
    print current_user
    if g.user is None:
        g.user = User("", "Guest", "")
    g.login_form = LoginForm()

@app.route("/")
def home():
    return render_template("home.html", login_form=g.login_form, user=g.user)

@app.route("/no_perms")
def no_perms(msg):
    return render_template("message.html", login_form=g.login_form, user=g.user, msg=msg)

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = Register()
    message = ""

    if request.method == "POST":
        if form.password.data != form.confirm_pass.data:
            message="The passwords provided did not match!\n"
        else:
            #Add user to db
            user = User(name=form.name.data, username=form.username.data,
                password=form.password.data, admin=form.admin.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Registered and logged in successfully!")
            return render_template('home.html', user=g.user, login_form=g.login_form)

    return render_template('register.html', user=g.user, login_form=g.login_form, form=form, message=message)

@login_manager.user_loader
def load_user(userid):
    return User.query.filter_by(id=userid).first()

def get_user():
    # A user id is sent in, to check against the session
    # and based on the result of querying that id we
    # return a user (whether it be a sqlachemy obj or an
    # obj named guest

    if 'user_id' in session:
            return User.query.filter_by(id=session["user_id"]).first()
    return None

@app.route("/login", methods=['GET', 'POST'])
def login():
    form=LoginForm(request.form, csrf_enabled=False)
    if form.validate_on_submit():
        # login and validate the user...
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            flash("Logged in successfully.")
            print "User=" + user.name

    return redirect("/")

@app.route("/logout", methods=['POST'])
def logout():
    logout_user()
    flash("Logged out successfully!")
    return redirect("/")

@app.route("/get_info", methods=["GET", "POST"])
def get_info():
    form = Get_Info()
    if not g.user.is_anonymous():
        form.name.data = g.user.name
    if request.method == "POST":
        return compliment_gender_name(name=form.name.data, gender=form.gender.data)
    else:
        return render_template("get_info.html", login_form=g.login_form, form=form, user=g.user)

@app.route("/add_complimentee", methods=["GET", "POST"])
@require_login
def add_complimentee():
    form = AddComplimentee()
    msg = ""
    if request.method == "POST":
        db.session.add(Complimentee(form.name.data, form.greeting.data))
        db.session.commit()
        msg = form.name.data + " added successfully!"

    return render_template('add_complimentee.html', login_form=g.login_form, form=form, user=g.user, msg=msg)

@app.route("/add_gender", methods=['GET', 'POST'])
@require_admin
def add_gender():
    form = AddGender()
    if request.method == "POST":
        #Add district to db.
        db.session.add(Gender(form.gender.data))
        db.session.commit()
    return render_template('add_gender.html', login_form=g.login_form, form=form, user=g.user)

@app.route("/add_compliment", methods=['GET', 'POST'])
@require_login
def add_compliment():
    form = AddCompliment()
    msg = ""

    if request.method == "POST":
        add_compliment(form)
        msg = "Compliment successfully added!"
    return render_template('add_compliment.html', login_form=g.login_form, form=form,
                        user=g.user, msg=msg, general=True)

@app.route("/<name>/add_compliment", methods=['GET', 'POST'])
@require_login
@require_complimentee_perms
def add_individual_compliment(name):
    form = AddCompliment()
    msg = ""
    if request.method == "POST":
        add_compliment(form, name=name)
        msg = "Compliment successfully added!"
    return render_template('add_compliment.html', login_form=g.login_form, form=form,
                        user=g.user, msg=msg)

@app.route("/<name>/edit_theme/", methods=['GET', 'POST'])
@require_login
@require_complimentee_perms
def edit_theme(name):
    form = AddTheme()
    theme = Theme.query.filter_by(user_name=name).first()
    if not theme:
        return redirect('/'+name+'/add_theme')

    if request.method == "POST":
        theme.theme_path = form.theme_path.data
        theme.song_path = form.song_path.data
        db.session.commit()

    theme = Theme.query.filter_by(user_name=name).first()
    form.theme_path.data = theme.theme_path
    form.song_path.data = theme.song_path

    return render_template('edit_theme.html', login_form=g.login_form, form=form, user=g.user, name=name)

@app.route("/<name>/add_theme/", methods=['GET', 'POST'])
@require_login
@require_complimentee_perms
def add_theme(name):
    form = AddTheme()
    if request.method == "POST":
        db.session.add(Theme(name, form.theme_path.data, form.song_path.data))
        db.session.commit()

    return render_template('add_theme.html', login_form=g.login_form, form=form, user=g.user, name=name)

@require_login
@app.route("/list_complimentees", methods=['GET', 'POST'])
def list_complimentees():

    compliments =  Complimentee.query.filter_by(owner=g.user.id).all()
    complimentees = []
    for compliment in compliments:
        if compliment.user_name not in complimentees:
            complimentees.append(compliment.user_name)

    return render_template("list_complimentees.html", login_form=g.login_form, user=g.user, complimentees=complimentees)

@app.route("/compliment/<gender>/<name>", methods=['GET', 'POST'])
def compliment_gender_name(gender, name):

    gender_compliments = Compliment.query.filter_by(compliment_gender=gender).all()
    compliments = Compliment.query.filter_by(compliment_gender="Any").all() + gender_compliments

    shuffle(compliments)
    return render_template("compliment.html", login_form=g.login_form, name=name, user=g.user, compliments=compliments)

@app.route("/control_panel", methods=['GET', 'POST'])
@require_admin
def compliment_control_panel():
    msg = ""
    if request.method == "POST":
        remove_ids = request.form.getlist('remove')
        remove_compliments(remove_ids)
        msg = str(len(remove_ids))+" compliments removed successfully!\n"

        approved_ids = request.form.getlist('approve')
        approve_compliments(compliment_ids)
        msg += str(len(approve_ids))+" compliments approved!"

    male_comps = Compliment.query.filter_by(compliment_gender="Male").all()
    female_comps = Compliment.query.filter_by(compliment_gender="Female").all()
    any_comps = Compliment.query.filter_by(compliment_gender="Any").all()
    personal_comps = Compliment.query.filter_by(compliment_gender=None).all()

    compliment_titles = ["Male Compliments", "Female Compliments", "Any Gender Compliments", "Personal Compliments"]
    compliment_list = [male_comps, female_comps,  any_comps, personal_comps]

    compliment_info = zip(compliment_titles, compliment_list)
    unapproved_comps = Compliment.query.filter_by(approved=False).all()

    return render_template("control_panel.html", login_form=g.login_form, user=g.user,
                            compliment_info=compliment_info, unapproved_comps=unapproved_comps,
                            msg=msg)

def approve_compliments(compliment_ids):
    for compliment_id in compliment_ids:
        compliment = session.query(Compliment).filter_by(id=compliment_id).first()
        compliment.approved = True
        db.session.commit()

@app.route("/compliment/<name>")
def compliment_individual(name):
    complimentee = check_for_complimentee(name)
    if not complimentee:
        return no_perms("The user you are trying to compliment does not exist!")
    compliments = Compliment.query.filter_by(user_name=name).all()
    theme = Theme.query.filter_by(user_name=name).first()
    if compliments:
        greeting = Complimentee.query.filter_by(name=name).first().greeting
        return render_template("compliment_individual.html", user=g.user, login_form=g.login_form,
                                greeting=greeting, name=name, theme=theme, compliments=compliments)
    else:
        return "The name you provided is not in the database!"

def add_compliment(form, name=None):
    if name:
        db.session.add(Compliment(compliment=form.compliment.data,
                        user_name=name, approved=True))
        print "Personal compliment added."

    else:
        approved = g.user.admin
        db.session.add(Compliment(compliment=form.compliment.data,
                        compliment_gender=form.gender.data, approved=approved))
        print "Gender specific compliment added."
    db.session.commit()


def remove_compliments(compliment_ids):
    for compliment_id in compliment_ids:
        remove = Compliment.query.filter_by(id=compliment_id).first()
        db.session.delete(remove)
    db.session.commit()

def approve_compliments(compliment_ids):
    for compliment_id in compliment_ids:
        compliment = Compliment.query.filter_by(id=compliment_id).first()
        compliment.approved = True
    db.session.commit()

def check_for_complimentee(name):
    return Complimentee.query.filter_by(name=name).all()
