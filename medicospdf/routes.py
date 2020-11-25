from flask import render_template, url_for, flash, redirect, request, send_file, send_from_directory, g
from medicospdf import app, db, bcrypt, mail
from medicospdf.forms import RegistrationForm, LoginForm, SlideForm, CommentForm, SearchForm, RequestResetForm, ResetPasswordForm
from medicospdf.models import User, Post, Slide, Comment, Category, followers, Visit
from flask_login import login_user, current_user, logout_user, login_required
import secrets
import os
from flask_mail import Message

def convert_file(file_fn, random_hex):
    file_name = 'http://127.0.0.1:5000/static/slide_files/' + file_fn
    converted_folder = 'medicospdf/static/slide_files'
    output_path = os.path.join(os.getcwd() + '/') + converted_folder + '/' + file_fn
    print(output_path)
    r = os.system('unoconv -f pdf --output='+ output_path + ' ' + file_name)
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
    print(file_conv)
    return file_conv, random_hex

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender = 'noreply@demo.com', recipients = [user.email])
    msg.body = f'''To reset your password visit the following link
        {url_for('reset_token', token=token, _external = True)}

        If you did not make this request then simply igonre this message and no changes will be made.
        '''
    mail.send(msg)



@app.route("/", methods = ['GET', 'POST'])
@app.route("/home", methods = ['GET', 'POST'])
@login_required
def home():
    cat = Category.query.all()
    page = request.args.get('page', 1, type = int)
    # slides = Slide.query.order_by(Slide.date_posted.desc()).paginate(page = page, per_page = 6)
    # slides = Slide.query.join(followers, (followers.c.followed_id == Slide.user_id)).filter(followers.c.follower_id == self.id).order_by(Slide.date_posted.desc()).paginate(page = page, per_page = 6)
    slides = current_user.followed_posts().paginate(page = page, per_page = 2)
    if request.method == 'POST' and 'tag' in request.form:
        tag = request.form['tag']
        search = '%{}%'.format(tag)
        slides = Slide.query.filter(Slide.title.like(search))
        return render_template('search.html', posts = slides, categories = cat)

    return render_template('home.html', posts=slides, categories = cat)

@app.route('/slide/<int:slide_id>', methods= ['GET', 'POST'])
def slide(slide_id):
    cat = Category.query.all()
    slide = Slide.query.get_or_404(slide_id)
    v = Visit.query.filter_by(id = slide_id).first()
    if not v:
        v = Visit()
        v.count += 1
        db.session.add(v)
    v.count += 1
    db.session.commit()
    print(v.count)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(comment = form.comment.data, author = current_user, slide_id = slide.id)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been posted.', 'success')
        return redirect(url_for('slide', slide_id = slide.id))
    page = request.args.get('page', 1, type = int)
    comments = Comment.query.filter_by(slide_id = slide.id).paginate(page, per_page = 2)
    return render_template('slide.html', title = slide.title, 
                        slide = slide, comments = comments, 
                        form = form, legend = Slide, categories = cat, visitors = v)


@app.route('/like/<int:slide_id>/<action>', methods = ['GET'])
@login_required
def like_action(slide_id, action):
    slide = Slide.query.filter_by(id=slide_id).first_or_404()
    if action == 'like':
        current_user.like_slide(slide)
        db.session.commit()
    if action == 'unlike':
        current_user.unlike_slide(slide)
        db.session.commit()
    return redirect(url_for('slide', slide_id = slide.id))


@app.route("/about")
def about():
    cat = Category.query.all()
    return render_template('about.html', title='About', categories = cat)


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
@login_required
def new_slide():
    form = SlideForm()
    cat = Category.query.all()
    if form.validate_on_submit():
        if form.file.data:
            uploaded_file, random_hex = save_file(form.file.data)
            print(uploaded_file)
        if uploaded_file == random_hex + '.pdf':
            slide = Slide(title = form.title.data, 
                category_id = form.category.data, description = form.description.data, 
                file = uploaded_file, author = current_user)
            db.session.add(slide)
            db.session.commit()
            flash('Your Slide has been created!!!', 'success')
            return redirect(url_for('new_slide'))
        else:
            flash('Your Slide is not Created!!!', 'danger')
            return redirect(url_for('new_slide'))
    return render_template('create_slide.html', title = 'Add New Slide', form = form, categories = cat)

@app.route('/download/<name>')
def download(name):
    path = 'static/slide_files/' + name
    return send_file(path, as_attachment = True)



@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/account/<username>')
@login_required
def account(username):
    user = User.query.filter_by(username = username).first()
    if user is None:
        flash('User %s is not found.', username)
        return redirect(url_for('home'))
    slides = user.slides
    return render_template('account.html', user = user, slides = slides, title = 'Account')

@app.route('/explore')
def explore():
    page = request.args.get('page', 1, type = int)
    slides = Slide.query.order_by(Slide.date_posted.desc()).paginate(page = page, per_page = 10)
    return render_template('explore.html', slides = slides)

@app.route('/category/<name>')
def category(name):
    cats = Category.query.all()
    cat = Category.query.filter_by(name = name).first_or_404()
    return render_template('category.html', name = name, posts = cat.slides, categories = cats)


@app.route('/follow/<username>')
def follow(username):
    user = User.query.filter_by(username = username).first()
    # if user in None:
    #     flash('User %s is not found.', username)
    #     return redirect(url_for('home'))
    if user == current_user:
        flash('Your can\'t follow yourself!')
        return redirect(url_for('account', username = user.username))
    u = current_user.follow(user)
    # if u is None:
    #     flash('Cannot follow' + username + '.')
    #     return redirect(url_for('account', username = user.username))
    db.session.add(u)
    db.session.commit()
    flash('You are following ' + username + '!', 'success')
    return redirect(url_for('account', username = user.username))

@app.route('/unfollow/<username>')
def unfollow(username):
    user = User.query.filter_by(username = username).first()
    u = current_user.unfollow(user)
    if u is None:
        flash('Cannot unfollow ' + username + '.')
        return redirect(url_for('account', username=user.username))
    db.session.add(u)
    db.session.commit()
    flash('You have stopped following ' + username + '.', 'danger')
    return redirect(url_for('account', username = user.username))


@app.route('/reset_password', methods = ['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title = 'Reset Request', form = form)

@app.route('/reset_password/<token>', methods = ['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(f'Your password has been Updated! You are now able to log in', 'success')
        return redirect(url_for('login')) 
    return render_template('reset_token.html', title = 'Reset Password', form = form)
