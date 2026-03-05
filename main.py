#These are imports from the flask plugin which allow us to create a web server and render html templates and get data from forms
from flask import Flask, render_template, request, session, url_for, redirect
#These are imports from the database handler file which allows us to interact with the database and create tables and add users to the database
from database import DatabaseHandler
from scripts.authorised import authorised
from blueprints.page import pages
from blueprints.authorise import authorise

# Secret key for session encryption
SECRET_KEY = 'supersecretkey'

# Create Flask app instance
app = Flask(__name__)
app.secret_key = SECRET_KEY
# Register blueprints for page routes and authentication routes
app.register_blueprint(pages)
app.register_blueprint(authorise)


# Uncomment these lines to create database tables on startup
# db = DatabaseHandler()
# db.createTables()

# Run the Flask development server
app.run(debug=True)