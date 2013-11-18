from tbkexch import db
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime, date, time, timedelta

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True)
    name = db.Column(db.String(20))
    password = db.Column(db.String(20))
    admin = db.Column(db.Boolean)

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def is_active(self):
        return True

    def get_id(self):
        return unicode(self.id)

    def __init__(self, username, name, password, admin=False):
        self.username = username
        self.name = name
        self.password = password
        self.admin = admin

class Listing(db.Model):
    __tablename__ = 'listings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    owner = db.relationship("User")
    listing_ref = db.Column(db.Integer, db.ForeignKey('books.id')) # For now, book id
    #trade_type = db.Column(db.Enum('Buying', 'Selling', name='trade_type'))
    book = db.relationship("Book", backref='listings')
    course = db.Column(db.String(15))
    notes = db.Column(db.String(60)) # Notes on condition
    cost = db.Column(db.String(10))

    def __init__(self, user_id, cost, listing_ref, course="N/A", notes="N/A"):
        self.user_id = user_id
        self.cost = cost
        self.listing_ref = listing_ref
        self.course = course
        self.notes = notes

    def __repr__(self):
        return "%s, %s, %s, %s, %s, %s" % (self.user_id, self.owner, self.listing_ref, self.course, self.notes, self.cost)

class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    isbn10 = db.Column(db.String(10))
    isbn13 = db.Column(db.String(13))
    title = db.Column(db.String(50))
    title_long = db.Column(db.String(250))
    author = db.Column(db.String(250))
    publisher = db.Column(db.String(250))

    def __init__(self, isbn10, isbn13, title, title_long, author, publisher):
        self.isbn10 = isbn10
        self.isbn13 = isbn13
        self.title = title
        self.title_long = title_long
        self.author = author
        self.publisher = publisher

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    sender = db.relationship('User')
    content = db.Column(db.String(511))
    sent_at = db.Column(db.DateTime(), default=datetime.utcnow)
    read = db.Column(db.Boolean())

    def read_msg(self):
        self.read = True

    def __init__(self, conversation_id, sender, content, read=False):
        self.conversation_id = conversation_id
        self.sender_id = sender
        self.content = content
        self.read = read

class Conversation(db.Model):
    __tablename__  = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer)
    receiver_id = db.Column(db.Integer)
    subject = db.Column(db.String(100))
    messages = db.relationship('Message', backref='conversation')

    def __init__(self, sender_id, receiver_id, subject):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.subject = subject

