#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import collections.abc
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort, jsonify
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from config import csrf
from wtforms.csrf.core import CSRF
from flask_migrate import Migrate
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:6969@localhost:5432/fyyur'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app,db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
  __tablename__ = 'venue'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), nullable=False)
  city = db.Column(db.String(120), nullable=False)
  state = db.Column(db.String(120), nullable=False)
  address = db.Column(db.String(120), nullable=False)
  phone = db.Column(db.String(120), nullable=False)
  genres = db.Column(db.String(300), nullable=False)
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  website = db.Column(db.String(120), nullable=False)
  seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
  seeking_description = db.Column(db.String, nullable=True)
  shows = db.relationship('Show', backref='venue', lazy=False)
  
  def __repr__(self):
    return f'<Venue: {self.id}, name: {self.name}, city: {self.city}, state: {self.state}, address: {self.address}, phone: {self.phone}, image_link: {self.image_link}, facebook_link: {self.facebook_link}, genres: {self.genres}, website: {self.website}, shows: {self.shows}>'

  # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
  __tablename__ = 'artist'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(), nullable=False)
  city = db.Column(db.String(120), nullable=False)
  state = db.Column(db.String(120), nullable=False)
  phone = db.Column(db.String(120), nullable=False)
  genres = db.Column(db.String(120), nullable=False)
  image_link = db.Column(db.String(500))
  facebook_link = db.Column(db.String(120))
  website = db.Column(db.String(120))
  seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
  seeking_description = db.Column(db.String, nullable=True)
  shows = db.relationship('Show', backref='artist', lazy=False)

  def __repr__(self):
    return f'<Artist: {self.id}, name: {self.name}, city: {self.city}, state: {self.state}, phone: {self.phone}, genres: {self.genres}, image_link: {self.image_link}, facebook_link: {self.facebook_link}, website: {self.website}, shows: {self.shows}>'

  # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Show(db.Model):
  _tablename__ = 'show'
  
  id = db.Column(db.Integer, primary_key=True)
  date = db.Column(db.DateTime, nullable=False)
  artist_id = db.Column(db.Integer, db.ForeignKey("artist.id"), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey("venue.id"), nullable=False)

  def __repr__(self):
    return f'<Show {self.id}, date: {self.date}, artist_id: {self.artist_id}, venue_id: {self.venue_id}>'

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#
if not hasattr(collections, 'Callable'):
    collections.Callable = collections.abc.Callable 

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  areas = []
  data = Venue.query.order_by('city', 'state', 'name').all()
  for venue in data:
    area_item = {}
    pos_area = -1
    if len(areas) == 0:
      pos_area = 0
      area_item = {
        "city": venue.city,
        "state": venue.state,
        "venues": []
      }
      areas.append(area_item)
    else:
      for i, area in enumerate(areas):
        if area['city'] == venue.city and area['state'] == venue.state:
          pos_area = i
          break
      if pos_area < 0:
        area_item = {
          "city": venue.city,
          "state": venue.state,
          "venues": []
        }
        areas.append(area_item)
        pos_area = len(areas) - 1
      else:
        area_item = areas[pos_area]
    v = {
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": 4
    }
    area_item['venues'].append(v)
    areas[pos_area] = area_item
  return render_template('pages/venues.html', areas=areas)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term')
  search = "%{}%".format(search_term.replace(" ", "\ "))
  data = Venue.query.filter(Venue.name.match(search)).order_by('name').all()
  items = []
  for row in data:
    aux = {
      "id": row.id,
      "name": row.name,
      "num_upcoming_shows": len(row.shows)
    }
    items.append(aux)

  response={
    "count": len(items),
    "data": items
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue = Venue.query.filter(Venue.id == venue_id).first()

  past = db.session.query(Show).filter(Show.venue_id == venue_id).filter(
      Show.date < datetime.now()).join(Artist, Show.artist_id == Artist.id).add_columns(Artist.id, Artist.name,
                                                                                              Artist.image_link,
                                                                                              Show.date).all()

  upcoming = db.session.query(Show).filter(Show.venue_id == venue_id).filter(
      Show.date > datetime.now()).join(Artist, Show.artist_id == Artist.id).add_columns(Artist.id, Artist.name,
                                                                                              Artist.image_link,
                                                                                              Show.date).all()

  upcoming_shows = []

  past_shows = []

  for i in upcoming:
      upcoming_shows.append({
          'artist_id': i[1],
          'artist_name': i[2],
          'image_link': i[3],
          'date': str(i[4])
      })

  for i in past:
      past_shows.append({
          'artist_id': i[1],
          'artist_name': i[2],
          'image_link': i[3],
          'date': str(i[4])
      })

  if venue is None:
      abort(404)

  response = {
      "id": venue.id,
      "name": venue.name,
      "genres": [venue.genres],
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website": venue.website,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
      "image_link": venue.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past),
      "upcoming_shows_count": len(upcoming),
  }
  return render_template('pages/show_venue.html', venue=response)
#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  # app = Flask(__name__)
  # csrf.init_app(app)
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  if request.content_type != 'application/x-www-form-urlencoded':
    return jsonify({"error": "Request must be JSON"}), 400
  try:
      venue = Venue(
          name=request.form['name'],
          city=request.form['city'],
          state=request.form['state'],
          address=request.form['address'],
          phone=request.form['phone'],
          genres=request.form.getlist('genres'),
          image_link=request.form['image_link'],
          facebook_link=request.form['facebook_link'],
          website=request.form['website_link'],
          seeking_talent = request.form.get('seeking_talent', 'false').lower() in ['y'],
          seeking_description=request.form['seeking_description']
      )
      print(venue)
      db.session.add(venue)
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully added!')
  except Exception as e:
      print(e)
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be added')
      db.session.rollback()
  finally:
      db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = Artist.query.order_by('name').all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term')
  search = "%{}%".format(search_term.replace(" ", "\ "))
  data = Artist.query.filter(Artist.name.match(search)).order_by('name').all()
  items = []
  for row in data:
    aux = {
      "id": row.id,
      "name": row.name,
      "num_upcoming_shows": len(row.shows)
    }
    items.append(aux)
  response={
    "count": len(items),
    "data": items
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.filter(Artist.id == artist_id).first()

  past = db.session.query(Show).filter(Show.venue_id == artist_id).filter(
      Show.date < datetime.now()).join(Artist, Show.artist_id == Artist.id).add_columns(Artist.id, Artist.name,
                                                                                              Artist.image_link,
                                                                                              Show.date).all()

  upcoming = db.session.query(Show).filter(Show.venue_id == artist_id).filter(
      Show.date > datetime.now()).join(Artist, Show.artist_id == Artist.id).add_columns(Artist.id, Artist.name,
                                                                                              Artist.image_link,
                                                                                              Show.date).all()

  upcoming_shows = []

  past_shows = []

  for i in upcoming:
      upcoming_shows.append({
          'artist_id': i[1],
          'artist_name': i[2],
          'image_link': i[3],
          'date': str(i[4])
      })

  for i in past:
      past_shows.append({
          'artist_id': i[1],
          'artist_name': i[2],
          'image_link': i[3],
          'date': str(i[4])
      })

  if artist is None:
      abort(404)

  response = {
      "id": artist.id,
      "name": artist.name,
      "genres": [artist.genres],
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "website": artist.website,
      "facebook_link": artist.facebook_link,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past),
      "upcoming_shows_count": len(upcoming),
  }
  return render_template('pages/show_artist.html', artist=response)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  print("Form fields:", form._fields) 
  artist = Artist.query.filter_by(id=artist_id).first()

  form.name.data = artist.name
  form.city.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.facebook_link.data = artist.facebook_link
  form.website_link.data = artist.website
  form.image_link.data = artist.image_link
  form.genres.data = artist.genres
  form.seeking_description.data=artist.seeking_description
  form.seeking_venue.data = artist.seeking_venue
  
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  if request.content_type != 'application/x-www-form-urlencoded':
    return jsonify({"error": "Request must be JSON"}), 400
  try:
    # Query the existing artist
    artist = Artist.query.get(artist_id)
      
    if not artist:
      flash(f'Artist with ID {artist_id} does not exist.')
      return redirect(url_for('show_artist', artist_id=artist_id))
    
    artist.name=request.form['name']
    artist.city=request.form['city']
    artist.state=request.form['state']
    artist.phone=request.form['phone']
    artist.genres=request.form.getlist('genres')
    artist.image_link=request.form['image_link']
    artist.facebook_link=request.form['facebook_link']
    artist.website=request.form['website_link']
    artist.seeking_description=request.form['seeking_description']
    seeking_venue_str = request.form.get('seeking_venue', 'false').lower()
    seeking_venue = seeking_venue_str in ['y']
    artist.seeking_venue = seeking_venue
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully edited!')
  except Exception as e:
      print(e)
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be edited')
      db.session.rollback()
  finally:
      db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  print("Form fields:", form._fields) 
  venue = Venue.query.filter_by(id=venue_id).first()

  form.name.data = venue.name
  form.city.data = venue.city
  form.state.data = venue.state
  form.phone.data = venue.phone
  form.address.data = venue.address
  form.facebook_link.data = venue.facebook_link
  form.website_link.data = venue.website
  form.image_link.data = venue.image_link
  form.genres.data = venue.genres
  form.seeking_description.data=venue.seeking_description
  form.seeking_talent.data = venue.seeking_talent
  
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  if request.content_type != 'application/x-www-form-urlencoded':
    return jsonify({"error": "Request must be JSON"}), 400
  try:
    # Query the existing venue
    venue = Venue.query.get(venue_id)
      
    if not venue:
      flash(f'Venue with ID {venue_id} does not exist.')
      return redirect(url_for('show_venue', venue_id=venue_id))
    
    venue.name=request.form['name']
    venue.city=request.form['city']
    venue.state=request.form['state']
    venue.address=request.form['address']
    venue.phone=request.form['phone']
    venue.genres=request.form.getlist('genres')
    venue.image_link=request.form['image_link']
    venue.facebook_link=request.form['facebook_link']
    venue.website=request.form['website_link']
    venue.seeking_description=request.form['seeking_description']
    seeking_talent_str = request.form.get('seeking_talent', 'false').lower()
    seeking_talent = seeking_talent_str in ['y']
    venue.seeking_talent = seeking_talent
    
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully edited!')
  except Exception as e:
      print(e)
      flash('An error occurred. Venue ' + request.form['name'] + ' could not be edited')
      db.session.rollback()
  finally:
      db.session.close()
  return render_template('pages/home.html')

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  if request.content_type != 'application/x-www-form-urlencoded':
    return jsonify({"error": "Request must be JSON"}), 400
  try:
      artist = Artist(
          name=request.form['name'],
          city=request.form['city'],
          state=request.form['state'],
          phone=request.form['phone'],
          genres=request.form.getlist('genres'),
          image_link=request.form['image_link'],
          facebook_link=request.form['facebook_link'],
          website=request.form['website_link'],
          seeking_venue=request.form.get('seeking_venue', 'false').lower() in ['y'],
          seeking_description=request.form['seeking_description']
      )
      print(artist)
      db.session.add(artist)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully added!')
  except Exception as e:
      print(e)
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be added')
      db.session.rollback()
  finally:
      db.session.close()
  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  rows = db.session.query(Show, Artist, Venue).join(Artist).join(Venue).filter(Show.date > datetime.now()).order_by('date').all()
  data = []
  for row in rows:
    item = {
      'venue_id': row.Venue.id,
      'artist_id': row.Artist.id,
      'venue_name': row.Venue.name,
      'artist_name': row.Artist.name,
      'artist_image_link': row.Artist.image_link,
      'start_time': row.Show.date.strftime('%Y-%m-%d %H:%M')
    }
    data.append(item)
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  if request.content_type != 'application/x-www-form-urlencoded':
    return jsonify({"error": "Request must be JSON"}), 400
  try:
      show = Show(
          artist_id=request.form['artist_id'],
          venue_id=request.form['venue_id'],
          date=request.form['start_time'],
      )
      print(show)
      db.session.add(show)
      db.session.commit()
      flash('Show ' + request.form['artist_id'] + ' was successfully added!')
  except Exception as e:
      print(e)
      flash('An error occurred. Show ' + request.form['name'] + ' could not be added')
      db.session.rollback()
  finally:
      db.session.close()
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
