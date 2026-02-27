#These are imports from the flask plugin which allow us to create a web server and render html templates and get data from forms
from flask import Flask, render_template, request
#These are imports from the database handler file which allows us to interact with the database and create tables and add users to the database
from database import DatabaseHandler

app = Flask(__name__)

#These lists are used to see if the user name or passwords have any special characters or numbers in
special_characters = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '_', '=', '+',]
numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
# Route for the signin page. Displays form for existing users to log in.
@app.route('/signin')
def signin():
    return render_template('signin.html')

# Route shows the signup page where new users can register.
@app.route('/')
def signup():
    return render_template('signup.html')

# Dashboard route shown after successful login or signup.
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/auth/create_user', methods=['POST'])
def create_user():
    #This function gets all the data from the sing in/up form and stores it to be checked against the requirements
    formDetails = request.form
    username = formDetails.get('username')
    password = formDetails.get('password')
    confirm_password = formDetails.get('confirm_password')
    email = formDetails.get('email')
    user_type = formDetails.get('user_type')

    # This does server side checks and validates that anything inputed is in the right format and meets the requirements
    if (len(username) >= 3 and len(username) <= 10 
        and len(password) >= 4 
        and len(confirm_password) >= 4
        and password == confirm_password
        and user_type in ['student', 'instructor']
        and not any(char in special_characters for char in username)
        and any(char in numbers for char in password)
        and any(char in special_characters for char in password)):
            #This add the users data to the database if all checks are passed
            db = DatabaseHandler()
            if user_type == 'student':
                success = db.createStudent(username, password, email)
            else:
                success = db.createInstructor(username, password, email)

            if success:
                return render_template('dashboard.html')
            
        
    return 'failed to create user'

# db = DatabaseHandler()
# db.createTables()

app.run(debug=True)