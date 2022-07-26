#!/usr/bin/env python3

from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import config
import requests

MOVIE_DATABASE_API_KEY = config.key['mdb_key']
MOVIE_DATABASE_SEARCH_API = "https://api.themoviedb.org/3/search/movie"
MOVIE_DATABASE_INFO_API = "https://api.themoviedb.org/3/movie"
MOVIE_DATABASE_IMAGE_API = "https://image.tmdb.org/t/p/w500"

app = Flask(__name__)
app.config['SECRET_KEY'] = config.key['app_key']
Bootstrap(app)

# CREATE DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///top-movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class UpdateForm(FlaskForm):
    your_rating = StringField(label="Your rating out of 10 e.g 7.5", validators=[DataRequired()])
    your_review = StringField(label="Your review", validators=[DataRequired()])
    done = SubmitField(label="Done")


class AddForm(FlaskForm):
    movie_title = StringField(label="Movie Title", validators=[DataRequired()])
    add_movie = SubmitField(label="Add Movie")


# CREATE TABLE
class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(1000), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    image_url = db.Column(db.String(250), nullable=True)


db.create_all()


@app.route("/")
def home():
    # This line creates a list of all the movies sorted by rating
    all_movies = Movie.query.order_by(Movie.rating).all()

    # This line loops through all the movies
    for i in range(len(all_movies)):
        # This line gives each movie a new ranking reversed from their order in all_movies
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movie=all_movies)


@app.route("/edit", methods=["GET", "POST"])
def edit():
    form = UpdateForm()
    movie_id = request.args.get("id")
    movie = Movie.query.get(movie_id)
    if form.validate_on_submit():
        movie.rating = float(form.your_rating.data)
        movie.review = form.your_review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movies=movie, form=form)


@app.route("/delete")
def delete():
    movie_id = request.args.get('id')
    movie_selected = Movie.query.get(movie_id)
    db.session.delete(movie_selected)
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add", methods=["GET", "POST"])
def add():
    add_form = AddForm()
    parameters = {
        "api_key": MOVIE_DATABASE_API_KEY,
        "query": add_form.movie_title.data
    }
    if add_form.validate_on_submit():
        response = requests.get(MOVIE_DATABASE_SEARCH_API, params=parameters)
        data = response.json()['results']
        return render_template('select.html', data=data)
    return render_template('add.html', form=add_form)


@app.route('/find', methods=["GET", "POST"])
def find():
    movie_id = request.args.get('id')
    print(movie_id)
    if movie_id:
        response = requests.get(f"{MOVIE_DATABASE_INFO_API}/{movie_id}",
                                params={"api_key": MOVIE_DATABASE_API_KEY, "language": "en-US"})
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            # The data in release_date includes month and day, we will want to get rid of.
            year=data["release_date"].split("-")[0],
            image_url=f"{MOVIE_DATABASE_IMAGE_API}{data['poster_path']}",
            description=data["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit", id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
