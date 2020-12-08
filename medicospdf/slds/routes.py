from flask import render_template, url_for, flash, redirect, request, jsonify, send_file, send_from_directory, g, Blueprint
from flask_login import login_user, current_user, logout_user, login_required
from medicospdf.decorators import check_confirmed
from medicospdf.slds.forms import SlideForm, CommentForm
from medicospdf.models import User, Slide, Comment, Category, followers, Visit
import secrets
import os
from medicospdf import app, db, bcrypt
from PIL import Image
import datetime
from flask_mail import Message
from medicospdf.decorators import check_confirmed


slds = Blueprint('slds', __name__)



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


@slds.route('/slide/<int:slide_id>', methods= ['GET', 'POST'])
@login_required
@check_confirmed
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
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(comment = form.comment.data, author = current_user, slide_id = slide.id)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been posted.', 'success')
        return redirect(url_for('slds.slide', slide_id = slide.id))
    page = request.args.get('page', 1, type = int)
    comments = Comment.query.filter_by(slide_id = slide.id).paginate(page, per_page = 2)
    return render_template('slide.html', title = slide.title, 
                        slide = slide, comments = comments, 
                        form = form, legend = Slide, categories = cat, visitors = v)


@slds.route('/like', methods = ['GET'])
@login_required
@check_confirmed
def like_action():
    if request.args['action'] == 'like':
        slide = Slide.query.filter_by(id=request.args['slide_id']).first_or_404()
        if current_user.has_liked_slide(slide):
            current_user.unlike_slide(slide)
            db.session.commit()
            like = len(slide.likes)
            return jsonify({'status':'unlike', 'like':like, 'text':'Like'})
        else:
            current_user.like_slide(slide)
            db.session.commit()
            like = len(slide.likes)
            return jsonify({"status": 'liked', 'like':like, 'text':'Liked'})

@slds.route('/slide/new', methods = ['GET', 'POST'])
@login_required
@check_confirmed
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
            return redirect(url_for('slds.new_slide'))
        else:
            flash('Your Slide is not Created!!!', 'danger')
            return redirect(url_for('slds.new_slide'))
    return render_template('create_slide.html', title = 'Add New Slide', form = form, categories = cat)

@slds.route('/download/<name>')
@login_required
@check_confirmed
def download(name):
    path = 'static/slide_files/' + name
    return send_file(path, as_attachment = True)


@slds.route('/delete/<int:slide_id>', methods = ['GET', 'POST'])
@login_required
def delete_slide(slide_id):
    slide = Slide.query.get_or_404(slide_id)
    if slide.author != current_user: #if the user is trying to delete the post of other user then it will be aborted.s
        abort(403)
    db.session.delete(slide)
    db.session.commit()
    flash('Your slide has been deleted!', 'danger')
    return redirect(url_for('account', user_id = slide.author.id))

@slds.route('/category/<int:cat_id>')
@login_required
@check_confirmed
def category(cat_id):
    page = request.args.get('page', 1, type = int)
    cats = Category.query.all()
    cat = Category.query.filter_by(id = cat_id).first_or_404()
    get_cat_prod = Slide.query.filter_by(category_id = cat.id).paginate(page= page, per_page = 2)
    return render_template('category.html', posts = get_cat_prod, categories = cats, cat = cat)
