from flask import Blueprint, request, redirect, url_for, session

from database import DatabaseHandler


authorise = Blueprint('authorise', __name__, url_prefix='/auth')


#These lists are used to see if the user name or passwords have any special characters or numbers in
special_characters = ['!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '_', '=', '+',]
numbers = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']


@authorise.route('/authoriseStudent', methods=['POST'])
def authorise_student():
    formDetails = request.form
    username = formDetails.get('username')
    password = formDetails.get('password')
    email = formDetails.get('email')

    db = DatabaseHandler()
    success = db.authoriseUserType(username, password, email, 'student')

    if success:
        if success:
            session['user'] = username # Store username in session for later use
            session['role'] = 'student'   
            return redirect(url_for('pages.studentDashboard'))        
    else:
        return redirect(url_for('pages.signin'))
    
    
# This function is called when the user submits the login form. It checks the credentials against the database and redirects to the appropriate dashboard if successful, or back to signin if not for instructors.
@authorise.route('/authoriseInstructor', methods=['POST'])
def authorise_instructor():
    formDetails = request.form
    username = formDetails.get('username')
    password = formDetails.get('password')
    email = formDetails.get('email')

    db = DatabaseHandler()
    success = db.authoriseUserType(username, password, email, 'instructor')

    if success:
        session['user'] = username # Store username in session for later use
        session['role'] = 'instructor' 
        return redirect(url_for('pages.instructorDashboard'))
    else:
        return redirect(url_for('pages.signin'))
        

@authorise.route('/authorise_user', methods=['POST'])
def authorise_user_generic():
    # dispatch based on the user_type field and log details
    formDetails = request.form
    user_type = formDetails.get('user_type')
    if user_type == 'student':
        return authorise_student()
    elif user_type == 'instructor':
        return authorise_instructor()
    else:
        return redirect(url_for('pages.signin'))


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
    if (len(username) >= 3 and len(username) <= 10 
        and len(password) >= 4 
        and password == confirm_password
        and user_type in ['student', 'instructor']
        and not any(char in special_characters for char in username)
        and any(char in numbers for char in password)
        and any(char in special_characters for char in password)):
            # This adds the user's data to the database if all checks are passed
            db = DatabaseHandler()
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
    
    # any failure falls back to showing the signup page again
    return redirect(url_for('pages.signup'))


@authorise.route('/logout')
def logout():
    session.clear()  # Clear all session data
    return redirect(url_for('pages.signin'))  # Redirect to the signin page after logout