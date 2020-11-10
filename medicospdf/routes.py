from flask import render_template, url_for, flash, redirect, request
from medicospdf import app, db, bcrypt
from medicospdf.forms import RegistrationForm, LoginForm, SlideForm
from medicospdf.models import User, Post, Slide
from flask_login import login_user, current_user, logout_user, login_required
import secrets
import os


posts = [
    {
        'author': 'Pitambar Mahato',
        'title': 'Blog Post 1',
        'content': 'First post content',
        'date_posted': 'April 20, 2018'
    },
    {
        'author': 'Jane Doe',
        'title': 'Blog Post 2',
        'content': 'Second post content',
        'date_posted': 'April 21, 2018'
    }
]

def convert_file(file_fn, random_hex):
    file_name = 'http://0.0.0.0:80/static/slide_files/' + file_fn
    print(file_name)
    converted_folder = 'medicospdf/static/slide_files'
    output_path = os.path.join(os.getcwd() + '/') + converted_folder + '/' + file_fn
    print(output_path)
    r = os.system('unoconv -f pdf --output = '+ output_path + ' ' + file_name)
    if r == 0:
        return random_hex + '.pdf'
    else: 
        msg = 'Document Not Converted'
        return msg

def save_file(form_file):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_file.filename)
    file_fn = random_hex + f_ext
    file_path = os.path.join(app.root_path, 'static/slide_files', file_fn)
    print(file_path)
    form_file.save(file_path)
    file_conv = convert_file(file_fn, random_hex)
    return file_conv, random_hex



@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', posts=posts)


@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username = form.username.data, email = form.email.data, password = hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember = form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/slide/new', methods = ['GET', 'POST'])
def new_slide():
    form = SlideForm()
    if form.validate_on_submit():
        if form.file.data:
            uploaded_file, random_hex = save_file(form.file.data)
        if uploaded_file == random_hex + '.pdf':
            slide = Slide(title = form.title.data, 
                category = form.category.data, description = form.description.data, 
                file = uploaded_file, author = current_user)
            db.session.add(slide)
            db.session.commit()
            flash('Your Slide has been created!!!', 'success')
            return redirect(url_for('new_slide'))
        else:
            flash('Your Slide is not Created!!!', 'danger')
            return redirect(url_for('new_slide'))
    return render_template('create_slide.html', title = 'Add New Slide', form = form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/account')
@login_required
def account():
    return render_template('account.html', title = 'Account')