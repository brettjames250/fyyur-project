import json
import dateutil.parser
import babel
import sys
from models import db, Artist, Venue, Show
from flask import (
    Flask,
    render_template,
    request,
    Response,
    flash,
    redirect,
    url_for,
    jsonify,
    abort,
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db.init_app(app)
migrate = Migrate(app, db)

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(value)
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale="en")


app.jinja_env.filters["datetime"] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    return render_template("pages/home.html")


#  Venues
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():
    data = []
    now = datetime.now()
    venues = Venue.query.all()

    locations = db.session.query(Venue.city, Venue.state).distinct(
        Venue.city, Venue.state
    )

    for location in locations:
        data.append({"city": location[0], "state": location[1], "venues": []})

    for venue in venues:
        upcoming_shows = 0
        shows = Show.query.filter_by(venue_id=venue.id).all()

        for show in shows:
            if show.start_time > now:
                upcoming_shows += 1

        for venue_location in data:
            if (
                venue.state == venue_location["state"]
                and venue.city == venue_location["city"]
            ):
                venue_location["venues"].append(
                    {
                        "id": venue.id,
                        "name": venue.name,
                        "num_upcoming_shows": upcoming_shows,
                    }
                )
    return render_template("pages/venues.html", areas=data)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    # 'ilike' is case-sensitive equivalent of 'like'
    user_input = request.form.get("search_term", None)
    matching_venues = Venue.query.filter(Venue.name.ilike(f"%{user_input}%"))
    venue_count = matching_venues.count()

    response = {"count": venue_count, "data": matching_venues}

    return render_template(
        "pages/search_venues.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    shows_at_venue = Show.query.filter_by(venue_id=venue_id).all()

    past_shows = []
    upcoming_shows = []
    current_time = datetime.now()

    if len(shows_at_venue) > 0:
        for show in shows_at_venue:
            data = {
                "artist_id": show.artist_id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                "start_time": format_datetime(str(show.start_time)),
            }
        if show.start_time > current_time:
            upcoming_shows.append(data)
        else:
            past_shows.append(data)

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
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
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    return render_template("pages/show_venue.html", venue=data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    form = VenueForm(request.form, meta={"csrf": False})

    try:
        name = form.name.data.strip()
        city = form.city.data.strip()
        state = form.state.data.strip()
        address = form.address.data.strip()
        phone = form.phone.data.strip()
        genres = request.form.getlist("genres")
        image_link = form.image_link.data.strip()
        facebook_link = form.facebook_link.data.strip()
        website_link = form.website_link.data.strip()
        seeking_talent = True if form.seeking_talent.data == True else False
        seeking_description = form.seeking_description.data.strip()

        new_venue = Venue(
            name=name,
            city=city,
            state=state,
            address=address,
            phone=phone,
            genres=genres,
            image_link=image_link,
            facebook_link=facebook_link,
            website=website_link,
            seeking_talent=seeking_talent,
            seeking_description=seeking_description,
        )

        db.session.add(new_venue)
        db.session.commit()
        flash("Venue created.")
    except Exception as e:
        db.session.rollback()
        print(e)
        flash("Error - Venue could not be created")
    finally:
        db.session.close()
    return redirect(url_for("index"))


@app.route("/venues/<venue_id>", methods=["DELETE"])
def delete_venue(venue_id):

    venue = Venue.query.get_or_404(venue_id)

    try:
        db.session.delete(venue)
        db.session.commit()
        flash("Venue was deleted")
    except Exception as e:
        db.session.rollback()
        print(e)
        flash("Error - Venue was not deleted")
    finally:
        db.session.close
    return redirect(url_for("index"))

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    artists = Artist.query.all()
    return render_template("pages/artists.html", artists=artists)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    # 'ilike' is case-sensitive equivalent of 'like'
    user_input = request.form.get("search_term", None)
    matching_artists = Artist.query.filter(Artist.name.ilike(f"%{user_input}%"))
    artist_count = matching_artists.count()

    response = {
        "count": artist_count,
        "data": matching_artists,
    }
    return render_template(
        "pages/search_artists.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)
    return render_template("pages/show_artist.html", artist=artist)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)

    form = ArtistForm(
        id=artist.id,
        name=artist.name,
        genres=artist.genres,
        city=artist.city,
        state=artist.state,
        phone=artist.phone,
        website_link=artist.website,
        facebook_link=artist.facebook_link,
        seeking_venue=artist.seeking_venue,
        seeking_description=artist.seeking_description,
        image_link=artist.image_link,
    )

    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    artist = Artist.query.get(artist_id)
    form = ArtistForm(request.form, meta={"csrf": False})

    try:
        artist.name = form.name.data.strip()
        artist.city = form.city.data.strip()
        artist.state = form.state.data.strip()
        artist.phone = form.phone.data.strip()
        artist.genres = request.form.getlist("genres")
        artist.image_link = form.image_link.data.strip()
        artist.facebook_link = form.facebook_link.data.strip()
        artist.website = form.website_link.data.strip()
        artist.seeking_venue = True if form.seeking_venue.data == True else False
        artist.seeking_description = form.seeking_description.data.strip()

        db.session.commit()
        flash("Artist details updated.")
    except Exception as e:
        db.session.rollback()
        print(e)
        flash("Error - Unable to update artist")
    finally:
        db.session.close()
    return redirect(url_for("show_artist", artist_id=artist_id))


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)

    form = VenueForm(
        id=venue.id,
        name=venue.name,
        genres=venue.genres,
        address=venue.address,
        city=venue.city,
        state=venue.state,
        phone=venue.phone,
        website_link=venue.website,
        facebook_link=venue.facebook_link,
        seeking_talent=venue.seeking_talent,
        seeking_description=venue.seeking_description,
        image_link=venue.image_link,
    )

    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    venue = Venue.query.get(venue_id)
    form = VenueForm(request.form, meta={"csrf": False})

    try:
        venue.name = form.name.data.strip()
        venue.city = form.city.data.strip()
        venue.state = form.state.data.strip()
        venue.address = form.address.data.strip()
        venue.phone = form.phone.data.strip()
        venue.genres = request.form.getlist("genres")
        venue.image_link = form.image_link.data.strip()
        venue.facebook_link = form.facebook_link.data.strip()
        venue.website_link = form.website_link.data.strip()
        venue.seeking_talent = True if form.seeking_talent.data == True else False
        venue.seeking_description = form.seeking_description.data.strip()

        db.session.commit()
        flash("Venue details updated.")
    except Exception as e:
        db.session.rollback()
        print(e)
        flash("Error - Unable to update venue")
    finally:
        db.session.close()

    return redirect(url_for("show_venue", venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    form = ArtistForm(request.form, meta={"csrf": False})

    try:
        name = form.name.data.strip()
        city = form.city.data.strip()
        state = form.state.data.strip()
        phone = form.phone.data.strip()
        genres = request.form.getlist("genres")
        seeking_venue = True if form.seeking_venue.data == True else False
        seeking_description = form.seeking_description.data.strip()
        facebook_link = form.facebook_link.data.strip()
        image_link = form.image_link.data.strip()
        website_link = form.website_link.data.strip()

        new_artist = Artist(
            name=name,
            city=city,
            state=state,
            phone=phone,
            genres=genres,
            facebook_link=facebook_link,
            image_link=image_link,
            website=website_link,
            seeking_venue=seeking_venue,
            seeking_description=seeking_description,
        )

        db.session.add(new_artist)
        db.session.commit()
        flash("Artist created.")
    except Exception as e:
        db.session.rollback()
        print(e)
        flash("Error - Artist could not be created")
    finally:
        db.session.close()
    return redirect(url_for("index"))


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    all_shows = Show.query.all()
    response_data = []

    for show in all_shows:
        show_details = {
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": str(show.start_time),
        }

        response_data.append(show_details)

    return render_template("pages/shows.html", shows=response_data)


@app.route("/shows/create")
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    form = ShowForm(request.form, meta={"csrf": False})

    try:
        show = Show(
            artist_id=form.artist_id.data.strip(),
            venue_id=form.venue_id.data.strip(),
            start_time=form.start_time.data,
        )
        db.session.add(show)
        db.session.commit()
        flash("Show created")
    except Exception as e:
        db.session.rollback()
        print(e)
        flash("Error - Show could not be created.")
    finally:
        db.session.close()

    return render_template("pages/home.html")


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
