from flask import render_template, url_for, flash, redirect, request, jsonify, send_file, send_from_directory, g, Blueprint
from medicospdf import db, bcrypt, mail, app
from medicospdf.users.forms import RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm, UpdateUserForm
from medicospdf.models import User, Slide, Comment, Category, followers, Visit
from flask_login import login_user, current_user, logout_user, login_required
import secrets
import os
from PIL import Image
import datetime
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from medicospdf.decorators import check_confirmed

users = Blueprint('users', __name__)


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename) 
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)        #resizing the image before uploading to the site
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender = 'noreply@demo.com', recipients = [user.email])
    msg.body = f'''To reset your password visit the following link
        {url_for('users.reset_token', token=token, _external = True)}
        If you did not make this request then simply igonre this message and no changes will be made.
        '''
    mail.send(msg)

def send_email(to, subject, template):
    msg = Message(subject, recipients = [to], sender = app.config['MAIL_USERNAME'], html = template)
    mail.send(msg)


def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])

def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECURITY_PASSWORD_SALT'],
            max_age=expiration
        )
    except:
        return False
    return email


@users.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username = form.username.data, email = form.email.data, password = hashed_password)
        db.session.add(user)
        db.session.commit()
        token = generate_confirmation_token(user.email)
        confirm_url = url_for('users.confirm_email', token = token, _external = True)
        html = render_template('activate.html', confirm_url = confirm_url)
        subject = "Please confirm your email."
        send_email(user.email, subject, html)
        login_user(user)
        flash('A confirmation mail has been sent via email', 'success')
        # flash(f'Account created for {form.username.data}!', 'success')
        return redirect(url_for('users.unconfirmed'))
    return render_template('register.html', title='Register', form=form)


@users.route('/confirm/<token>')
@login_required
def confirm_email(token):
    try:
        email = confirm_token(token)
    except:
        flash('The Confirmation line is invalid or has expired', 'danger')
    user = User.query.filter_by(email = email).first_or_404()
    if user.confirmed:
        flash('Account already confirmed. Please Login.', 'success')
    else: 
        user.confirmed = True
        user.confirmed_on = datetime.datetime.now()
        db.session.add(user)
        db.session.commit()
        flash('You have confirmed your account. Thanks!', 'success')
    return redirect(url_for('main.home'))

@users.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.confirmed:
        return redirect('home')
    flash('Please confirm your account!', 'warning')
    return render_template('unconfirmed.html')

@users.route('/resend')
@login_required
def resend_confirmation():
    token = generate_confirmation_token(current_user.email)
    confirm_url = url_for('users.confirm_email', token = token, _external = True)
    html = render_template('activate.html', confirm_url=confirm_url)
    subject = 'Please confirm your email.'
    send_email(current_user.email, subject, html)
    flash('A new confirmation email has been sent.', 'success')
    return redirect(url_for('users.unconfirmed'))



@users.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember = form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@users.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@users.route('/account/<int:user_id>')
@login_required
@check_confirmed
def account(user_id):
    page = request.args.get('page', 1, type = int)
    user = User.query.filter_by(id = user_id).first_or_404()
    get_user_prod = Slide.query.filter_by(user_id = user.id).paginate(page = page, per_page = 2)
    if user is None:
        flash('User %s is not found.', username)
        return redirect(url_for('main.home'))
    return render_template('account.html', user = user, slides = get_user_prod, title = 'Account')


@users.route('/follow/<username>')
@login_required
@check_confirmed
def follow(username):
    user = User.query.filter_by(username = username).first()
    # if user in None:
    #     flash('User %s is not found.', username)
    #     return redirect(url_for('home'))
    if user == current_user:
        flash('Your can\'t follow yourself!')
        return redirect(url_for('users.account', user_id = user.id))
    u = current_user.follow(user)
    # if u is None:
    #     flash('Cannot follow' + username + '.')
    #     return redirect(url_for('account', username = user.username))
    db.session.add(u)
    db.session.commit()
    flash('You are following ' + username + '!', 'success')
    return redirect(url_for('users.account', user_id = user.id))

@users.route('/unfollow/<username>')
@login_required
@check_confirmed
def unfollow(username):
    user = User.query.filter_by(username = username).first()
    u = current_user.unfollow(user)
    if u is None:
        flash('Cannot unfollow ' + username + '.')
        return redirect(url_for('users.account', user_id=user.id))
    db.session.add(u)
    db.session.commit()
    flash('You have stopped following ' + username + '.', 'danger')
    return redirect(url_for('users.account', user_id = user.id))


@users.route('/reset_password', methods = ['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.')
        return redirect(url_for('users.login'))
    return render_template('reset_request.html', title = 'Reset Request', form = form)

@users.route('/reset_password/<token>', methods = ['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(f'Your password has been Updated! You are now able to log in', 'success')
        return redirect(url_for('users.login')) 
    return render_template('reset_token.html', title = 'Reset Password', form = form)


@users.route('/update/<int:user_id>', methods = ['GET', 'POST'])
@login_required
def update_user(user_id):
    form = UpdateUserForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('users.account', user_id = current_user.id))
    elif request.method == 'GET':
        form.username.data = current_user.username
    image_file = url_for('static', filename = 'profile_pics/' + current_user.image_file)
    return render_template('update_account.html', title = 'Update Profile', image_file = image_file, form = form)

