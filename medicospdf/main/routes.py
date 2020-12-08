from flask import render_template, request, Blueprint
from medicospdf.models import Slide, Category
from flask_login import login_user, current_user, logout_user, login_required
from medicospdf.decorators import check_confirmed


main = Blueprint('main', __name__)


@main.route("/", methods = ['GET', 'POST'])
@main.route("/home", methods = ['GET', 'POST'])
@login_required
@check_confirmed
def home():
    cat = Category.query.all()
    page = request.args.get('page', 1, type = int)
    silds = Slide.query.order_by(Slide.date_posted.desc()).paginate(page = page, per_page = 2)
    slides = current_user.followed_posts().paginate(page = page, per_page = 2)
    if request.method == 'POST' and 'tag' in request.form:
        tag = request.form['tag']
        search = '%{}%'.format(tag)
        slides = Slide.query.filter(Slide.title.like(search))
        return render_template('search.html', posts = slides, categories = cat)

    return render_template('home.html', posts=slides, categories = cat, silds = silds)

@main.route('/explore')
@login_required
@check_confirmed
def explore():
    page = request.args.get('page', 1, type = int)
    cats = Category.query.all()
    slides = Slide.query.order_by(Slide.date_posted.desc()).paginate(page = page, per_page = 2)
    return render_template('explore.html', posts = slides, categories = cats)


@main.route("/about")
@login_required
@check_confirmed
def about():
    cat = Category.query.all()
    return render_template('about.html', title='About', categories = cat)

