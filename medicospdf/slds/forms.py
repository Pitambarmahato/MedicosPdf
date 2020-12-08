from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, PasswordField, SubmitField, BooleanField, TextAreaField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from medicospdf.models import User, Category


# categories = Category.query.all()
# mychoices = []
# print(mychoices)
# for cat in categories:
# 	mychoices.append((cat.id, cat.name))

mychoices = [('1', 'Book')]

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

