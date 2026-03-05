# Blueprint for all authentication routes (login, logout, create account)
from flask import Blueprint, flash, request, redirect, url_for, session

from database import DatabaseHandler


authorise = Blueprint('authorise', __name__, url_prefix='/auth')


#These lists are used to see if the user name or passwords have any special characters or numbers in
special_characters = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '_', '=', '+',]
numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']


# Handle student login - verifies credentials and creates session
@authorise.route('/authoriseStudent', methods=['POST'])
def authorise_student():
    # Get login form data
    formDetails = request.form
    username = formDetails.get('username')
    password = formDetails.get('password')
    email = formDetails.get('email')

    db = DatabaseHandler()
    success = db.authoriseUserType(username, password, email, 'student')

    if success:
        # double-check not necessary, but kept for logic consistency
        session['user'] = username # Store username in session for later use
        session['role'] = 'student'
        # Redirect to student dashboard on success
        return redirect(url_for('pages.studentDashboard'))        
    else:
        # Show error message and return to signin
        flash('Invalid credentials or user type. Please try again.')
        return redirect(url_for('pages.signin'))
    
    
# Handle instructor login - verifies credentials and creates session
# This function is called when the user submits the login form. It checks the credentials against the database and redirects to the appropriate dashboard if successful, or back to signin if not for instructors.
@authorise.route('/authoriseInstructor', methods=['POST'])
def authorise_instructor():
    # Get login form data
    formDetails = request.form
    username = formDetails.get('username')
    password = formDetails.get('password')
    email = formDetails.get('email')

    db = DatabaseHandler()
    success = db.authoriseUserType(username, password, email, 'instructor')

    if success:
        session['user'] = username # Store username in session for later use
        session['role'] = 'instructor'
        # Redirect to instructor dashboard on success
        return redirect(url_for('pages.instructorDashboard'))
    else:
        # Show error message and return to signin
        flash('Invalid credentials or user type. Please try again.')
        return redirect(url_for('pages.signin'))
        

# Route to appropriate login function based on user type
@authorise.route('/authorise_user', methods=['POST'])
def authorise_user_generic():
    # dispatch based on the user_type field and log details
    formDetails = request.form
    user_type = formDetails.get('user_type')
    # Call student or instructor login function
    if user_type == 'student':
        return authorise_student()
    elif user_type == 'instructor':
        return authorise_instructor()
    else:
        return redirect(url_for('pages.signin'))


# Handle user registration with validation
@authorise.route('/create_user', methods=['POST'])
def create_user():
    #This function gets all the data from the sign up form and stores it to be checked against the requirements
    formDetails = request.form
    username = formDetails.get('username')
    password = formDetails.get('password')
    confirm_password = formDetails.get('confirm_password')
    email = formDetails.get('email')
    user_type = formDetails.get('user_type')

    # This does server side checks and validates that anything inputted is in the right format and meets the requirements
    # server side validation with detailed error messages
    # Collect all validation errors
    errors = []

    # username length and characters
    # Validate username is 3-10 characters with no special characters
    if not (3 <= len(username) <= 10):
        errors.append('Username must be between 3 and 10 characters long.')
    if any(char in special_characters for char in username):
        errors.append('Username may not contain special characters.')

    # password requirements
    # Validate password has minimum length, number, and special character
    if len(password) < 4:
        errors.append('Password must be at least 4 characters long.')
    if password != confirm_password:
        errors.append('Passwords do not match.')
    if not any(char in numbers for char in password):
        errors.append('Password must contain at least one number.')
    if not any(char in special_characters for char in password):
        errors.append('Password must contain at least one special character.')

    
    # Ensure user selected student or instructor
    if user_type not in ['student', 'instructor']:
        errors.append('You must select either student or instructor.')

    # proceed only if no validation errors
    # If validation passed, check email availability and create account
    if not errors:
        db = DatabaseHandler()

        # verify that email is not already taken (usernames may be shared)
        with db.connect() as con:
            cur = con.cursor()
            table = 'students' if user_type == 'student' else 'instructors'
            cur.execute(f"SELECT 1 FROM {table} WHERE email = ?", (email,))
            if cur.fetchone():
                errors.append('Email already in use.')

        if not errors:
            # Create student or instructor account
            if user_type == 'student':
                success = db.createStudent(username, password, email)
            else:
                success = db.createInstructor(username, password, email)

            if success:
                # redirect to the appropriate dashboard after signup
                if user_type == 'student':
                    return redirect(url_for('pages.studentDashboard'))
                else:
                    return redirect(url_for('pages.instructorDashboard'))
            else:
                # underlying database error
                errors.append('An internal error occurred; please try again.')

    # flash each error and redirect back to signup page
    for msg in errors:
        flash(msg)
    return redirect(url_for('pages.signup'))


# Clear session and log out user
@authorise.route('/logout')
def logout():
    session.clear()  # Clear all session data
    return redirect(url_for('pages.signin'))  # Redirect to the signin page after logout