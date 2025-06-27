from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from flask_bootstrap import Bootstrap5
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, PasswordField
from wtforms.validators import DataRequired, URL, Email, Length
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
Bootstrap5(app)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

# Database Models
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    reviews = db.relationship("Review", back_populates="author")

class Cafe(db.Model):
    __tablename__ = "cafes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    location = db.Column(db.String(500), nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    open_time = db.Column(db.String(250), nullable=False)
    close_time = db.Column(db.String(250), nullable=False)
    coffee_rating = db.Column(db.String(250), nullable=False)
    wifi_rating = db.Column(db.String(250), nullable=False)
    power_rating = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250))
    can_take_calls = db.Column(db.Boolean, default=False)
    restroom = db.Column(db.Boolean, default=False)
    reviews = db.relationship("Review", back_populates="cafe")
    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    cafe_id = db.Column(db.Integer, db.ForeignKey("cafes.id"))
    author = db.relationship("User", back_populates="reviews")
    cafe = db.relationship("Cafe", back_populates="reviews")

# Forms
class CafeForm(FlaskForm):
    name = StringField('Cafe name', validators=[DataRequired()])
    location = StringField("Location (Address)", validators=[DataRequired()])
    map_url = StringField("Google Maps URL", validators=[DataRequired(), URL()])
    open_time = StringField("Opening Time (e.g. 9AM)", validators=[DataRequired()])
    close_time = StringField("Closing Time (e.g. 5:30PM)", validators=[DataRequired()])
    coffee_rating = SelectField("Coffee Rating", choices=['☕️','☕️☕️','☕️☕️☕️','☕️☕️☕️☕️','☕️☕️☕️☕️☕️'], validators=[DataRequired()])
    wifi_rating = SelectField("Wifi Rating", choices=['✘','💪','💪💪','💪💪💪','💪💪💪💪','💪💪💪💪💪'], validators=[DataRequired()])
    power_rating = SelectField("Power Rating", choices=['✘','🔌','🔌🔌','🔌🔌🔌','🔌🔌🔌🔌'], validators=[DataRequired()])
    seats = StringField("Number of Seats")
    can_take_calls = SelectField("Can Take Calls?", choices=[(True, 'Yes'), (False, 'No')], coerce=bool)
    restroom = SelectField("Has Restroom?", choices=[(True, 'Yes'), (False, 'No')], coerce=bool)
    submit = SubmitField('Submit')

class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Up")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")

class ReviewForm(FlaskForm):
    text = StringField("Your Review", validators=[DataRequired()])
    rating = SelectField("Rating", choices=[(1, "1 Star"), (2, "2 Stars"), (3, "3 Stars"), (4, "4 Stars"), (5, "5 Stars")], coerce=int)
    submit = SubmitField("Submit Review")

# Flask-Login Config
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route("/")
def home():
    return render_template("index.html", logged_in=current_user.is_authenticated)

@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        
        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("cafes"))
    
    return render_template("register.html", form=form, logged_in=current_user.is_authenticated)

@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('cafes'))
            
    return render_template("login.html", form=form, logged_in=current_user.is_authenticated)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/add', methods=['GET', 'POST'])
def add_cafe():
    if not current_user.is_authenticated:
        flash("You need to login or register to add a cafe.")
        return redirect(url_for('login'))
    
    form = CafeForm()
    if form.validate_on_submit():
        new_cafe = Cafe(
            name=form.name.data,
            location=form.location.data,
            map_url=form.map_url.data,
            open_time=form.open_time.data,
            close_time=form.close_time.data,
            coffee_rating=form.coffee_rating.data,
            wifi_rating=form.wifi_rating.data,
            power_rating=form.power_rating.data,
            seats=form.seats.data,
            can_take_calls=form.can_take_calls.data,
            restroom=form.restroom.data
        )
        db.session.add(new_cafe)
        db.session.commit()
        return redirect(url_for('cafes'))
    return render_template('add.html', form=form, logged_in=current_user.is_authenticated)

@app.route('/cafes')
def cafes():
    all_cafes = Cafe.query.all()
    return render_template('cafes.html', cafes=all_cafes, logged_in=current_user.is_authenticated)

@app.route('/cafe/<int:cafe_id>', methods=['GET', 'POST'])
def show_cafe(cafe_id):
    cafe = Cafe.query.get_or_404(cafe_id)
    form = ReviewForm()
    
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login to leave a review.")
            return redirect(url_for('login'))
        
        new_review = Review(
            text=form.text.data,
            rating=form.rating.data,
            author=current_user,
            cafe=cafe
        )
        db.session.add(new_review)
        db.session.commit()
        return redirect(url_for('show_cafe', cafe_id=cafe.id))
    
    return render_template('cafe.html', cafe=cafe, form=form, logged_in=current_user.is_authenticated)

# API Endpoints
@app.route('/api/cafes')
def get_all_cafes():
    cafes = Cafe.query.all()
    return jsonify(cafes=[cafe.to_dict() for cafe in cafes])

@app.route('/api/cafe/<int:cafe_id>')
def get_cafe(cafe_id):
    cafe = Cafe.query.get_or_404(cafe_id)
    return jsonify(cafe=cafe.to_dict())




# At the end of main.py
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run()  # Local development only