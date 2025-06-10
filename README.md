# Strava Contest Dashboard

Welcome to the Activity Leaderboard Dashboard — a dynamic platform designed to motivate and promote physical activity within small communities, whether it’s among friends, clubs, or workplaces.

Users simply register and link their Strava accounts, and from there, the dashboard takes over — seamlessly fetching activities, calculating points based on customizable rules, and presenting live leaderboards to spark friendly competition and foster healthier habits.

Turn your group’s fitness journey into an engaging challenge — track, compete, and stay inspired!

---

## Features

- OAuth2 authentication with Strava
- Activity import and synchronization
- Points and leaderboard system (customizable rules)
- Weekly, monthly and yearly dashboards
- User profile with Strava account linking
- Admin and user-friendly interface (Bootstrap 5)
- SQLite support (easy to run locally)

---

## Prerequisites

- Python 3.10+
- A valid Strava account
- Strava API credentials (client_id and client_secret)

---

## Strava API Access

To use this application, you must create a Strava API application to obtain your `client_id` and `client_secret`.
You can do this by logging into your Strava account and visiting:
https://www.strava.com/settings/api

For more details, see the [official Strava API documentation](https://developers.strava.com/docs/getting-started/).

**Tip:**
If you're building this for a club, create a dedicated Strava account for the club. This keeps API credentials and activity data clearly associated with the club, and avoids issues if personal access is revoked.

---

## Database

This project uses [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/) as the ORM layer.

The SQLite database file is automatically created at runtime if it does not already exist.
Make sure the database URI is properly configured through your environment variables or configuration files, depending on your deployment context.

By default, the application expects a URI like:
```bash
sqlite:///app.db
```

Example with environment variable:
You can customize this by setting the SQLALCHEMY_DATABASE_URI and DATABASE_FILE variable to match your desired setup.
```bash
export DATABASE_FILE="db.sqlite" #(Default value)
```

Explore the schema with [sqlite-web](https://github.com/coleifer/sqlite-web):

```console
docker run -it --rm \
    -p 8080:8080 \
    -v "$(pwd)":/data \
    -e SQLITE_DATABASE=/data/db.sqlite \
    coleifer/sqlite-web
```

---

## Running the Application

Set your Strava API credentials as environment variables:

```console
STRAVA_CLIENT_ID=[your_client_id] STRAVA_CLIENT_SECRET=[your_client_secret] python app.py
```

---

### From Docker compose

A docker compose is provided for your convenience

First of all, configure the file "webapp.env".

```console
docker compose  up --build
```
This makes the application available on 8080


### From VSCode
When running the project using VSCode's built-in debugger, the WERKZEUG_RUN_MAIN environment variable may not be set, which means the scheduler will not start as expected. To fix this add the following environment variable to your configuration:
```json
"env": {
  "FLASK_MAIN_PROCESS": "true"
}
```

### Example VSCode Debug Configuration (`.vscode/launch.json`)

To run and debug the Flask app in VSCode with the scheduler properly started, use the following launch configuration:

```json
{
  "configurations": [
    {
      "name": "Flask (.env)",
      "type": "debugpy",
      "request": "launch",
      "module": "flask",
      "args": ["run"],
      "envFile": "${workspaceFolder}/.env",
      "env": {
        "FLASK_MAIN_PROCESS": "true"
      },
    }
  ]
}
```

### Recommended VSCode Workspace Settings (`.vscode/settings.json`)

```json
{
  "python.defaultInterpreterPath": "~/.venv/bin/python",
  "python.envFile": "${workspaceFolder}/.env"
}
```

## Rules

Current contest rules:

- The minimum time for an eligible/valid activity is **30 minutes** (configurable)
- **Standard:** 1 point per activity (minimum 30 min, maximum one per day)
- **Regularity A:** 2 bonus points for the first activity of the week following a week with at least one activity. The first week of the month considers the last week of the previous month.
- **Regularity B:** 2 points for the 3rd activity in the week (i.e., more than 2 activities)
- **Healthy life:** 1 point if total activity time in a week is more than 120 minutes (configurable)

---

## Calendar

- Dashboard points are displayed per week, month and year.
- ISO calendar is used as a reference.
- Some rules are evaluated per week (like regularity bonus).
- A week is considered to be 7 days. For monthly dashboards, weeks may include days from the previous or next month.
- A week is considered part of the current month if it contains at least 4 days in that month.
- Example (August 2025):
```plaintext
    August 2025
Mo Tu We Th Fr Sa Su
             1  2  3
 4  5  6  7  8  9 10
11 12 13 14 15 16 17
18 19 20 21 22 23 24
25 26 27 28 29 30 31
```
  The first week has only 3 days in August, so contest points for August start on Monday 4th. The last week of July ends on August 3rd.

---

## Strava API

- [Strava API documentation](https://developers.strava.com/)

---

## Development & Contribution

- Fork and clone the repository
- Create a virtual environment and install dependencies
- Run the app and contribute!

---

## License

MIT License

---

## Acknowledgements

- [Flask](https://flask.palletsprojects.com/)
- [Bootstrap](https://getbootstrap.com/)
- [stravalib](https://github.com/stravalib/stravalib)
