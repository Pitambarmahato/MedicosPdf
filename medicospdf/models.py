from datetime import datetime
from medicospdf import db, login_manager, app
from flask_login import UserMixin, current_user
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
import os
import sys
import secrets

admin = Admin(app, name = 'Control Panel')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    is_admin = db.Column(db.Boolean, default = False)
    posts = db.relationship('Post', backref='author', lazy=True)
    slides = db.relationship('Slide', backref = 'author', lazy = True)
    liked = db.relationship('SlideLike', foreign_keys = 'SlideLike.user_id', 
        backref = 'author', lazy = True)
    comments = db.relationship('Comment', backref = 'author', lazy = True)
    categories = db.relationship('Category', backref = 'author', lazy = True)


    def like_slide(self, slide):
        if not self.has_liked_slide(slide):
            like = SlideLike(user_id = self.id, slide_id = slide.id)
            db.session.add(like)

    def unlike_slide(self, slide):
        if self.has_liked_slide(slide):
            SlideLike.query.filter_by(
                user_id = self.id, 
                slide_id = slide.id).delete()

    def has_liked_slide(self, slide):
        return SlideLike.query.filter(
            SlideLike.user_id == self.id, 
            SlideLike.slide_id == slide.id).count()>0


    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"


class Slide(db.Model):
    __searchable__  = ['title', 'description']
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(200), nullable = False)
    description = db.Column(db.Text, nullable = False)
    file = db.Column(db.String(1000), nullable = False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    likes = db.relationship('SlideLike', backref = 'slide', lazy = True)
    comments = db.relationship('Comment', backref = 'slide', lazy = True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable = True)


    def __repr__(self):
        return f"Slide('{self.title}', '{self.description}', '{self.file}')"


class SlideLike(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    slide_id = db.Column(db.Integer, db.ForeignKey('slide.id'))

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    comment = db.Column(db.Text, nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    slide_id = db.Column(db.Integer, db.ForeignKey('slide.id'), nullable = False)

    def __repr__(self):
        return f"Comment('self.comment)')"

class Category(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    name = db.Column(db.String(200), nullable = False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable = False)
    slides = db.relationship('Slide', backref = 'cats', lazy = True)

    def __repr__(self):
        return f"Category('{self.name}')"

class Controller(ModelView):
    def is_accessible(self):
        if current_user.is_admin == True:
            return current_user.is_authenticated
        else:
            return 'Not Accessible'

    def not_auth(self):
        return 'Not Accessible'


admin.add_view(Controller(User, db.session, endpoint = 'user'))
admin.add_view(Controller(Category, db.session, endpoint = 'categories'))