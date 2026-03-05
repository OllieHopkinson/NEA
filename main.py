#These are imports from the flask plugin which allow us to create a web server and render html templates and get data from forms
from flask import Flask, render_template, request, session, url_for, redirect
#These are imports from the database handler file which allows us to interact with the database and create tables and add users to the database
from database import DatabaseHandler
from scripts.authorised import authorised
from blueprints.page import pages
from blueprints.authorise import authorise

SECRET_KEY = 'supersecretkey'

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.register_blueprint(pages)
app.register_blueprint(authorise)


db = DatabaseHandler()
db.createTables()

app.run(debug=True)