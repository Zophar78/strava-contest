from flask import Blueprint, current_app, flash, render_template, redirect, request, url_for
from flask_login import login_required, current_user
from stravalib import Client
from .extensions import db
from .models import Athlete
from .tasks import sync_athlete, compute_athlete_points

strava = Blueprint("strava", __name__)

@strava.route("/authorize")
@login_required
def authorize():
    client = Client()
    # Generate the Strava authorization URL
    url = client.authorization_url(
        client_id=current_app.config["STRAVA_CLIENT_ID"],
        redirect_uri=url_for(".callback", _external=True),
        approval_prompt="auto",
    )
    # Redirect the user to Strava's OAuth page
    return redirect(url, code=302)

@strava.route("/callback")
@login_required
def callback():
    error = request.args.get("error")
    if error:
        # Display error message if Strava returned an error
        flash(f'Error: {error}')
    else:
        code = request.args.get("code")
        client = Client()
        # Exchange the authorization code for an access token
        access_token = client.exchange_code_for_token(
            client_id=current_app.config["STRAVA_CLIENT_ID"],
            client_secret=current_app.config["STRAVA_CLIENT_SECRET"],
            code=code,
        )
        # Retrieve athlete information from Strava
        strava_athlete = client.get_athlete()

        # Create a new Athlete instance with the received data
        new_athlete = Athlete(
            id=strava_athlete.id,
            firstname=strava_athlete.firstname,
            lastname=strava_athlete.lastname,
            country=strava_athlete.country,
            access_token=access_token['access_token'],
            refresh_token=access_token['refresh_token'],
            expires_at=access_token['expires_at']
        )
        athlete = Athlete.query.filter_by(id=strava_athlete.id).first()
        if athlete:
            # Update existing athlete
            db.session.merge(new_athlete)
        else:
            # Add new athlete
            db.session.add(new_athlete)
        db.session.commit()
        # Associate athlete with current user
        current_user.athlete_id = strava_athlete.id
        db.session.commit()
        # Synchronize the athlete's data
        sync_athlete(new_athlete)
        compute_athlete_points(new_athlete)
        # Flash a success message
        flash('Strava account linked successfully!')

    # Render the index page after processing the callback
    return render_template("index.html")
