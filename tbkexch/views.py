from flask import Blueprint, request, render_template, flash, g, session, redirect
from flask.ext.login import login_user, logout_user, current_user, login_required
from tbkexch import db, app, login_manager
from forms import Register, LoginForm, ListBook, ConversationForm
from models import User, Listing, Book, Message, Conversation
from functools import wraps
import xml.etree.ElementTree as ET
import dateutil.parser
import urllib
import os
import re

#DECORATORS

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user.admin:
            return f(*args, **kwargs)
        return no_perms("You are not an admin!")
    return decorated_function

#TODO: Clean this method up a bit
#TODO: Include if any new messages are present for a user here, then notify.
@app.before_request
def before_request():
    g.user = current_user
    if g.user is None:
        g.user = User("", "Guest", "")
    g.login_form = LoginForm()

#VIEWS

@app.route("/")
def home():
    return render_template("home.html", login_form=g.login_form, user=g.user)

#TODO: Make this exclusively no_perms, and fix templates to use flashed text
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
        elif User.query.filter_by(username=form.username.data).all():
            message="This username is taken!"
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
    if g.user.is_anonymous():
        form=LoginForm(request.form, csrf_enabled=False)

        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            flash("Logged in successfully.")
    else:
        return no_perms("There is a user already logged in!")
    return redirect("/")

@app.route("/logout", methods=['POST'])
def logout():
    logout_user()
    flash("Logged out successfully!")
    return redirect("/")

#TODO: Sort most recent conversations to first
#TODO: Add in unread messages
@app.route("/inbox", methods=['GET'])
@login_required
def inbox():
    unsorted_conversations = Conversation.query.filter_by(sender_id=g.user.id).all() + \
                                Conversation.query.filter_by(receiver_id=g.user.id).all()

    if unsorted_conversations:
        conversations = []
        for conv in unsorted_conversations:
            if conv.receiver_id == g.user.id:
                conv.otherperson = User.query.filter_by(id=conv.sender_id).first()
            else:
                conv.otherperson = User.query.filter_by(id=conv.receiver_id).first()
            conversations.append(conv)

        #conversations = unsorted_conversations.sort(key=lambda r: r.messages[len(r.messages)-1].sent_at)
        return render_template('inbox.html', user=g.user, login_form=g.login_form,
                                conversations=conversations)
    return no_perms("You do not have any conversations!")


@app.route("/<user_id>/listings", methods=['GET', 'POST'])
def listings(user_id):
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return no_perms("The user your are looking for does not exist!")
    books = Listing.query.filter_by(user_id=user.id).all()
    if not g.user.is_anonymous():
        self = user.id == g.user.id
        if not self:
            return render_template("listings.html", lister=user, user=g.user, login_form=g.login_form, self=self, books=books)
    else:
        return render_template("listings.html", lister=user, user=g.user, login_form=g.login_form,self=False, books=books)
    return render_template("listings.html", lister=user, user=g.user, login_form=g.login_form, self=self, books=books)

#TODO: Make sure the first message is sent with the listing title
#TODO: Implement read and unread messages.
#TODO: Clean up this method, it is messy as shit.
#TODO: Rework the url to be less redundant, and more proper.
@app.route("/<sender_id>/<receiver_id>/conversation", methods=['GET', 'POST'])
@login_required
def conversation(sender_id,receiver_id):
    form = ConversationForm()
    sender = User.query.filter_by(id=sender_id).first()
    receiver = User.query.filter_by(id=receiver_id).first()

    if not sender or not receiver:
        return no_perms("One of the users provided does not exist!")

    if sender.id != g.user.id:
        receiver = sender

    conv = Conversation.query.filter_by(sender_id=sender_id).filter_by(receiver_id=receiver_id).first() or Conversation.query.filter_by(sender_id=receiver_id).filter_by(receiver_id=sender_id).first()


    if request.method == "POST":
        if not conv:
            if form.content.data and form.subject.data:
                conv = Conversation(sender_id=sender_id, receiver_id=receiver_id, subject=form.subject.data)
                db.session.add(conv)
                db.session.commit()
                msg = Message(conversation_id=conv.id, sender=g.user.id, content=form.content.data)

                db.session.add(msg)
                db.session.commit()

            else:
                return no_perms("You didn't input a subject/message!")

        elif form.content.data:

            msg = Message(conversation_id=conv.id, sender=g.user.id, content=form.content.data)

            db.session.add(msg)
            db.session.commit()
        else:
            return no_perms("You didn't input a message!")
    if conv:
        for msg in conv.messages:
            msg.sent_at = msg.sent_at.strftime("%b %d, %Y")
        conv.messages = Message.query.filter_by(conversation_id=conv.id).all()

    return render_template("conversation.html", form=form, user=g.user, login_form=g.login_form, conversation=conv, receiver=receiver)

@app.route("/search", methods=['GET', 'POST'])
def search():
    if not request.method == "POST":
        return no_perms("You need to provide a term to search for!")

    term = request.form.get("search")
    books, book, listings = [], "", ""
    # Check for ISBN10, ISBN13, or by course
    isbn = False

    query = clean_isbn(term)
    if len(query) == 10:
        book = Book.query.filter_by(isbn10=query).first()
        isbn = True
    elif len(query) == 13:
        book = Book.query.filter_by(isbn13=query).first()
        isbn = True

    if not isbn:
        book = db.session.query(Book).filter(
                Book.title.like("%"+term+"%")).first()
        if book is None:
            book = db.session.query(Book).filter(
                    Book.author.like("%"+term+"%")).first()
            if book is None:
                listings = Listing.query.filter_by(course=term.replace(" ", "")).order_by("listing_ref").all()
                if not listings:  # Check for course as a search term.
                    term = filter_commons(term)
                    for qtype in [Book.author, Book.title]:
                        for word in filter_commons(term).split(" "):
                            if len(term) > 2:
                                new_book = db.session.query(Book).filter(
                                        qtype.like("%"+word+"%")).all()
                                if len(new_book) > 0 and new_book not in books:
                                    books.append(new_book)

        if not empty_list(books):
            books = truncate_list(books)
        else:
            books = []

        if listings:
            for listing in listings:
                book = Book.query.filter_by(id=listing.listing_ref).first()
                books.append(book)

    if book and not listings:
        listings = Listing.query.filter_by(listing_ref=book.id).all()
    elif books:
        ids = [b.id for b in books]
        if ids:
            listings = db.session.query(Listing).filter(
                            Listing.listing_ref.in_(ids)).all()

    if book or books:
        print "listings: " + str(listings)
        if len(books) > 1:
            return render_template("search.html", term=term, login_form=g.login_form,
                                    user=g.user, listings=listings, books=books)
        else:
            if len(books) == 1:
                book = books[0]
            return render_template("search.html", term=term, login_form=g.login_form,
                                    user=g.user, listings=listings, book=book)

    else:
        return no_perms("Sorry, the book you were searching for was not found.")

    """
    if len(term) == 10:
        book = Book.query.filter_by(isbn10=term).first()
    elif len(term) == 13:
        book = Book.query.filter_by(isbn13=term).first()
    else:
        listings = Listing.query.filter_by(course=term).order_by("listing_ref").all()

    if not listings:
        if book:
            listings = Listing.query.filter_by(listing_ref=book.id).order_by("listing_ref").all()
        else:
            return no_perms("That book is not available right now!")
    else:
        for listing in listings:
            if listing.book not in books:
                books.append(listing.book)

        return render_template("search.html", term=term, login_form=g.login_form, user=g.user, listings=listings, books=books)

    return render_template("search.html", term=term, login_form=g.login_form, user=g.user, listings=listings, book=book)
    """

def filter_commons(search_term):
    common_words = ['the', 'a', 'is', 'of', 'an']
    for cw in common_words:
        search_term.replace(cw, "")
    return search_term

def truncate_list(l):
    return [[book for book in book_list if book] for book_list in books]

def empty_list(lists):
    for s in lists:
        if isinstance(s, Book):
            return False
        for l in s:
            if isinstance(s, Book):
                return False
    return True


def get_book_from_db(book_info):
    pass

#TODO: Check for other special characters Hint: Use regex
#TODO: Change notes to condition, and rate condition of book on a 1-5 scale.
@app.route("/list_book", methods=['GET', 'POST'])
@login_required
def list_book():
    form = ListBook()
    msg = ""
    if request.method == "POST":
        isbn = clean_isbn(form.isbn.data)
        if valid_isbn(isbn):
            book = get_book_by_isbn(isbn)
            print book
            if book is not None:
                listing = Listing(user_id=g.user.id, listing_ref=book.id, course=form.course.data.replace(" ", "").upper(), notes=form.notes.data, cost=form.cost.data)
                db.session.add(listing)
                db.session.commit()
                msg = "Listing added successfully!"
            else:
                msg = "Book not found!"
        else:
            msg = "ISBN was not 10 or 13 characters long!"

    return render_template("list_book.html", form=form, msg=msg, login_form=g.login_form, user=g.user)

#TODO: Create more readable logic
#TODO: Test if the db is querying and when found API is not called
def get_book_by_isbn(isbn):
    # First we check our db for the book, before utilizing the API
    if len(isbn) == 10:
        book = Book.query.filter_by(isbn10=isbn).first()
    elif len(isbn) == 13:
        book = Book.query.filter_by(isbn13=isbn).first()

    print "ISBN: "+ isbn
    print "In Book_by_isbn function, book=" + str(book)
    if not book:
        xml = urllib.urlopen("http://isbndb.com/api/books.xml?access_key=KI4B9RHN&index1=isbn&value1="+isbn)
        resp = xml.read()
        #TODO: Fix this hack -> Need to wait for xml to be sent properly
        #Hack for shitty formatted xml
        print "Results?: " + str("total_results\"=0\"" not in resp)
        print "total_results=\"0\""

        if "total_results=\"0\"" not in resp:
        #    return "Book with ISBN " + str(isbn) + " does not exist!"
            print resp
            formatted_xml = ''.join([None if line == "" else line for line in resp])
            #print "formatted_xml = " + formatted_xml
            data = get_xml_data(formatted_xml)
            book = Book(isbn10=data['isbn10'], isbn13=data['isbn13'], title=data['title'],
                    title_long=data['title_long'], author=data['author'], publisher=data['publisher'])

            db.session.add(book)
            db.session.commit()
        else:
            print "Returning none because somehow \"total_results=0\" was found..."
            return None

    return book

#UTILS

def clean_isbn(isbn):
    return isbn.replace("-", "").replace(" ", "")

def valid_isbn(isbn):
    return len(isbn) == 10 or len(isbn) == 13

def get_xml_data(xml, **data):
    book_data = ET.fromstring(xml)

    # elementtree is weird <.<
    for child in book_data:
        for children in child:
            data['isbn10'] = children.get('isbn')
            data['isbn13'] = children.get('isbn13')
            data['title'] = children[0].text
            data['title_long'] = children[1].text
            data['author'] = children[2].text
            data['publisher'] = children[3].text

    return data

def get_search_results(query):
    #Try an int first
    try:
        int(clean_isbn(query))
        return get_book_by_isbn
    except:
        query = query.replace(" ", "_")
        xml = urllib.urlopen("http://isbndb.com/api/v2/xml/KI4B9RHN/book/"+query)
        if "total_results\"=0\"" not in xml.read():
            return xml.read()
        return urllib.urlopen("http://isbndb.com/api/v2/xml/KI4B9RHN/author/"+query).read()

