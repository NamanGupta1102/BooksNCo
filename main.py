from turtle import title
from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory, Response
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from sqlalchemy.orm import relationship
from wtforms import StringField, SubmitField, SelectField, EmailField, PasswordField, DateField
from wtforms.validators import DataRequired, URL, Length, NumberRange
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.file import FileField, FileAllowed, FileRequired
# from flask_uploads import UploadSet, IMAGES
from flask_sqlalchemy import SQLAlchemy

from apiwork import get_book_info
from datetime import datetime
import smtplib 
import base64
# ---------------------------------- Connections and Configurations --------------------#
app = Flask(__name__)
Bootstrap(app)
ctx = app.app_context()
ctx.push()
# app.secret_key = 'namanshreyadevang'
app.config['SECRET_KEY'] = 'namanshreyadevang'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///BookShareFinal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ------------------------------------ Database Tables -----------------------------#
class User(db.Model):
    name = db.Column(db.String(50))
    password = db.Column(db.String(50))
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50), unique=True)
    post = relationship("Post", back_populates="user")
    address = db.Column(db.String(100), unique=True)
    


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    isbn = db.Column(db.Integer, nullable=True)
    type = db.Column(db.String(50), nullable=True) # rent or sell
    rent_period = db.Column(db.Integer, nullable=True) # per month
    price = db.Column(db.Integer, nullable=True)
    category = db.Column(db.String(50), nullable=True)
    # copies = db.Column(db.Integer,nullable = False)

    img = db.Column(db.Text)  # , nullable = False)
    img_name = db.Column(db.Text)  # , nullable = False)
    mimetype = db.Column(db.Text)  # , nullable = False)

    title = db.Column(
        db.String(50))  # ,nullable    pic = dc.Column(db.LargeBinary)
    # = False)
    author = db.Column(db.String(50))  # ,nullable = False)
    time = db.Column(db.DateTime)  # ,nullable = False)

    sellid = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = relationship("User", back_populates="post")


db.create_all()

# ------------------------------------ WTF Forms -----------------------------------#


class Postform(FlaskForm):
    # isbn = StringField(label="ISBN", validators=[DataRequired(),NumberRange(min=None, max=None, message=None)])
    # type = SelectField(label="Rent or Sell",
    #                    choices=['rent', 'sell'],
    #                    validators=[DataRequired()])  # Sell or rent
    rent_period =  SelectField(label="Rent period (in months)",
                       choices=[1,2,3,4,5,6],default=0) #,
                    #    validators=[DataRequired()])
    price = StringField(label="Price", validators=[DataRequired()])
    category = SelectField(
        label="Category",
        choices=['Fictional', 'Non Fictional', 'Educational'],
        validators=[DataRequired()])
    # copies = db.Column(db.Integer,nullable = False)
    photo = FileField(
        "photo",
        validators=[FileAllowed(['jpg', 'jpeg', 'png']),
                    FileRequired()])
    title = StringField(label="title")
    author = StringField(label="author")
    submit = SubmitField("Submit")
    


class Isbnform(FlaskForm):
    isbn = StringField(label="ISBN", validators=[DataRequired()])
    type = SelectField(label="Rent or Sell",
                       choices=['rent', 'sell'],
                       validators=[DataRequired()])
    submit = SubmitField("Submit")

class Payemnt(FlaskForm):
    name = StringField(label="Name on Card", validators=[DataRequired()])
    valid_till = StringField(label="Valid till",validators=[DataRequired()])
    # valid_till = DateField(label='Valid Till', format = '%m-%y') 
    card_no = StringField(label="Card Number", validators=[DataRequired(), Length(min = 12, max=12)])
    cvv = StringField(label="CVV", validators=[DataRequired(), Length(min = 3, max=3)])
    submit = SubmitField("Submit") 
# ------------------------------------ Routing -------------------------------------#


@app.route('/')
def index():
    return render_template('index.html',
                           logged_in=current_user.is_authenticated)


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == "POST":
        print("post succed")
        if User.query.filter_by(email=request.form.get('email')).first():
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            request.form.get('password'),
            method='pbkdf2:sha256',
            salt_length=8)

        new_user = User(
            email=request.form.get('email'),
            name=request.form.get('username'),
            password=hash_and_salted_password,
            address = request.form.get('address')
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html",
                           logged_in=current_user.is_authenticated)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        # Email doesn't exist or password incorrect.
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            # login_user(user)

            # return redirect(url_for("sell", uid=user.id))
            return redirect(url_for("dashboard", uid=user.id))

    return render_template("login.html",
                           logged_in=current_user.is_authenticated)


@app.route('/temp', methods=['POST', 'GET'])
def temp():
    # t = Post.query.filter_by(id=3).first()
    # x = Response(t.img, mimetype=t.mimetype)

    all_posts = db.session.query(Post).all()
    base64_images = [base64.b64encode(
        i.img).decode("utf-8") for i in all_posts]
    return render_template("temp.html", res=all_posts, images=base64_images)


@app.route('/sell', methods=['POST', 'GET'])
def sell():
    form = Isbnform()
    uid = request.args.get('uid')
    # ISBN conditions
    # cond_isbn = 1
    # user = User.query.get(uid)
    post = Post()
    if form.validate_on_submit():
        print("-------------SOMETHING RANDOM IN VALIDATE ------------")
        post.isbn = int(form.isbn.data.replace("-",""))
        post.sellid = uid
        post.type = form.type.data
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('sell2', post_id=post.id))
    return render_template("sell.html", form=form, uid = uid )


@app.route('/sell2', methods=['POST', 'GET'])
def sell2():
    post_id = request.args.get('post_id')
    post = Post.query.filter_by(id=post_id).first()
    info = get_book_info(int(post.isbn))
    post.title = info['title']
    post.author = info['author']
    if post.title == 'NA':
        post.title = " "
    if post.author == 'NA':
        post.author = " "

    form = Postform(title=post.title, author=post.author, rent_period = 1)
    # uid = request.args.get('uid')
    # post_id = Post.query.get('id')

    # ISBN conditions
    # user = User.query.get(uid)
    # print("---------------- UID = ",uid)
    print("-------------------Post id = ", post_id)
    if form.validate_on_submit():
        cond_isbn = 0
        print("works database ")
        post = Post.query.filter_by(id=post_id).first()
        # post.isbn = int(form.isbn.data)
        # post.type = form.type.data
        
        post.rent_period = int(form.rent_period.data)
        
        post.price = float(form.price.data)
        post.category = form.category.data
        post.img_name = form.photo.data.filename
        post.img = form.photo.data.read()
        post.mimetype = form.photo.data.mimetype

        info = get_book_info(int(post.isbn))
        post.title = form.title.data
        post.author = form.author.data
        post.time = datetime.now()
        # post.sellid = uid
        # isbn_details = Post.query.get(form.isbn.data)
        db.session.commit()
        return redirect(url_for("dashboard", uid=post.sellid))
    return render_template("sell2.html", post = post,form=form, postisbn=post.isbn)


# @app.route('/posts', methods=['POST', 'GET'])
# def posts():
    form = Postform()
    uid = request.args.get('uid')
    user = User.query.get(uid)
    if form.validate_on_submit():
        post = Post()
        post.isbn = int(form.isbn.data)
        post.type = form.type.data
        post.price = float(form.price.data)
        post.category = form.category.data
        post.img_name = form.photo.data.filename
        post.img = form.photo.data.read()
        post.mimetype = form.photo.data.mimetype
        # print(form.photo.data.mimetype)
        # api
        # if api not null :
        #     api.title = api.name
        #     autht
        # else:
        info = get_book_info(int(form.isbn.data))
        post.title = info['title']
        post.author = info['author']
        post.time = datetime.now()

        # post.
        # user_details = User.query.get(form.)
        # print(form.photo.data)
        # print(form.photo.data['FileStorage:'])
        # t = form.photo.data
        # print("This is the ouput ",form.photo.data.read())
        post.sellid = uid
        db.session.add(post)
        db.session.commit()
        return f"osirs"

    return render_template('post.html', form=form)

@app.route('/postinfo', methods=['POST', 'GET'])
def postinfo():
    post_id = request.args.get('post_id')
    uid = request.args.get('uid')
    post = Post.query.filter_by(id=post_id).first()
    sell = User.query.filter_by(id=post.sellid).first()
    picture = base64.b64encode(post.img).decode("utf-8")
    buy = "Rent"
    if post.type=='sell':
        buy = "Buy"
    return render_template("shop-details.html",post_id = post_id, uid=uid, post=post,sell = sell,picture=picture,buy=buy)


@app.route('/dashboard', methods=['POST', 'GET'])
def dashboard():
    no_data=0
    try: 
        delete_post = request.args.get('delete_post')
        print(delete_post)
        Post.query.filter_by(id =delete_post).delete()
        db.session.commit()
    except: pass
    print("==========Post to delete = ", delete_post)
    uid = request.args.get('uid')
    all_posts = db.session.query(Post).all()
    base64_images = [base64.b64encode(
        i.img).decode("utf-8") for i in all_posts]
    # for i in all_posts:
    #     print(i.sellid == uid,type(i.sellid),type(uid))
    if request.method == "POST":
        search_name = request.form.get('search').lower()
        # User.query.filter_by(email=email).first()
        print(f"------- dta received{search_name}")
        all_posts = db.session.query(Post).all()
        ans = []
        for i in all_posts:
            if search_name in i.title.lower():
                ans.append(i)
            
        if len(ans) ==0: 
            no_data =1

        print(f"------- dta received{ans}")
        base64_images = [base64.b64encode(
        i.img).decode("utf-8") for i in ans]
        # print(f"------- img received{base64_images}")
        # user = User.query.filter_by(email=email).first()
        return render_template('dashboard.html', res=ans, images=base64_images, uid=uid,no_data=no_data)
    return render_template("dashboard.html", res=all_posts, images=base64_images, uid=uid,no_data=no_data)

    # return render_template('dashboard.html',oranges = 'oranges')

@app.route('/payment', methods=['POST', 'GET'])
def payment():
    uid = request.args.get('uid')
    post_id = request.args.get('post_id')
    form = Payemnt()
    if form.validate_on_submit():
        # delete_post = request.args.get('delete_post')
        # print(delete_post)
        post = Post.query.filter_by(id =post_id).first()
        user = User.query.filter_by(id =uid).first()
        seller = User.query.filter_by(id =post.sellid).first()



        Post.query.filter_by(id =post_id).delete()
        db.session.commit()
        return render_template('thankyou.html',post =post,user=user)
    return render_template('payment.html',form=form)

@app.route('/contact', methods=['POST', 'GET'])
def contact():
    # uid = request.args.get('uid')
    uid = request.args.get('uid')
    print(uid,"  ______________________uid ")
    return render_template('contact.html',uid = uid)
# x="rwsfd erfdx"
# print(x.title())
app.run(host='0.0.0.0', debug=False)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=False)
