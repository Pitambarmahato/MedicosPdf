from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, PasswordField, SubmitField, BooleanField, TextAreaField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from medicospdf.models import User

class RegistrationForm(FlaskForm):
	username = StringField('Username', 
		validators = [DataRequired(), Length(min = 2, max = 20)])
	email = StringField('Email', 
		validators = [DataRequired(), Email()])
	password = PasswordField('Password', validators = [DataRequired()])
	confirm_password = PasswordField('Confirm Password', 
						validators = [DataRequired(), EqualTo('password')])
	submit = SubmitField('Sign Up')
	def validate_username(self, username):
		user = User.query.filter_by(username=username.data).first()
		if user:
			raise ValidationError('That username is taken. Please choose a different one.')
	def validate_email(self, email):
		user = User.query.filter_by(email=email.data).first()
		if user:
			raise ValidationError('That email is taken. Please choose a different one.')

class LoginForm(FlaskForm):
	email = StringField('Email', 
		validators = [DataRequired(), Email()])
	password = PasswordField('Password', validators = [DataRequired()])
	remember = BooleanField('Remember Me')
	submit = SubmitField('Login')


class SlideForm(FlaskForm):
	title = StringField('Title', validators = [DataRequired()])
	description = TextAreaField('Description', validators = [Length(min = 200), DataRequired()])
	category = SelectField(u'Field Select', 
		choices = [('Book', 'Book'), ('Copy', 'Copy')], validators = [DataRequired()])
	file = FileField('Select a File To Upload', 
		validators = [FileAllowed(['pdf', 'ppt', 'pptx'])])
	submit = SubmitField('Post')