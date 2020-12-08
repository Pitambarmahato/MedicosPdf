from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, PasswordField, SubmitField, BooleanField, TextAreaField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from medicospdf.models import User, Category

categories = Category.query.all()
mychoices = []
print(mychoices)
for cat in categories:
	mychoices.append((cat.id, cat.name))

# mychoices = [('1', 'book'), ('2', 'read')]

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

class UpdateUserForm(FlaskForm):
	username = StringField('Username',
		validators = [DataRequired(), Length(min = 2, max = 20)])
	picture = FileField('Update Profile Picture',
		validators = [FileAllowed(['jpg', 'png'])])
	submit = SubmitField('Update')

	def valid_username(self, username):
		if username.data != current_user.username:
			user = User.query.filter_by(username = username.data).first()
			if user:
				raise ValidationError('That Username is already taken. Please choose another one.')

class LoginForm(FlaskForm):
	email = StringField('Email', 
		validators = [DataRequired(), Email()])
	password = PasswordField('Password', validators = [DataRequired()])
	remember = BooleanField('Remember Me')
	submit = SubmitField('Login')


class SlideForm(FlaskForm):
	title = StringField('Title', validators = [DataRequired()], render_kw={"placeholder": "Title"})
	description = TextAreaField('Description', validators = [Length(min = 200), DataRequired()],
			render_kw={"placeholder": "Describe your slide with more than 300 characters."})
	category = SelectField(u'Select Category', 
		choices = mychoices, validators = [DataRequired()], coerce = int)
	file = FileField('Select a File To Upload', 
		validators = [FileAllowed(['pdf', 'ppt', 'pptx'])])
	submit = SubmitField('Post')

class CommentForm(FlaskForm):
	comment = TextAreaField(validators = [DataRequired()], 
							render_kw={"placeholder": "Write a Comment"})
	submit = SubmitField('Comment')

class SearchForm(FlaskForm):
	subject = StringField(validators = [DataRequired(), Length(min = 3, max = 60)], 
							render_kw = {'placeholder': 'Search'})
	submit = SubmitField('Search')

class RequestResetForm(FlaskForm):
	email = StringField('Email',
						validators = [DataRequired(), Email()])
	submit = SubmitField('Request Password Reset')

	def validate_email(self, email):
		email = User.query.filter_by(email = email.data).first()
		if email is None:
			raise ValidationError('There is no account with that email.')

class ResetPasswordForm(FlaskForm):
	password = PasswordField('Password', validators = [DataRequired()])
	confirm_password = PasswordField('Confirm Password', 
									validators = [DataRequired(), EqualTo('password')])
	submit = SubmitField('Reset Password')