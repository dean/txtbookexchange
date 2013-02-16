from flask.ext.wtf import Form, TextField, PasswordField, BooleanField, SelectField
from flask.ext.wtf import Required, Email, EqualTo
from models import User

class AddUser(Form):
    name = TextField('name', [Required()])
    greeting = TextField('greeting')

class AddTheme(Form):
    theme_path = TextField('theme_path')
    song_path = TextField('song_path')

class AddCompliment(Form):
    compliment = TextField('compliment', [Required()])
    gender = SelectField('gender', choices=[('None', 'None'), ('Male', 'Male'), ('Female', 'Female'), ('Any', 'Any')])

class AddGender(Form):
    gender = SelectField('gender', choices=[('Male', 'Male'), ('Female', 'Female'), ('Any', 'Any')])
