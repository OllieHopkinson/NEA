# Blueprint for all page routes (signin, signup, dashboards)
from flask import Blueprint, get_flashed_messages, render_template, request, session, url_for, redirect
from scripts.authorised import authorised

pages = Blueprint('pages', __name__)

# Display sign in page or redirect if already logged in
@pages.route('/signin')
def signin():
    # Redirect to dashboard if user is already logged in
    if authorised():
        role = session.get('role')

        if role == 'student':
            return redirect(url_for('pages.studentDashboard'))
        elif role == 'instructor':
            return redirect(url_for('pages.instructorDashboard'))

    messages = get_flashed_messages()
    return render_template('signin.html', messages=messages)


# Home page - displays the signup form for new users
# Route shows the signup page where new users can register.
@pages.route('/')
def signup():
    messages = get_flashed_messages()
    return render_template('signup.html', messages = messages)


# Student dashboard - only accessible when logged in
# Dashboard route shown after successful login or signup.
@pages.route('/studentDashboard')
def studentDashboard():
    # Redirect to signin if not logged in
    if not authorised():
        return redirect(url_for('pages.signin'))
    user = session['user']
    return render_template('studentDashboard.html', user = user)


# Instructor dashboard - only accessible when logged in
@pages.route('/instructorDashboard')
def instructorDashboard():
    # Redirect to signin if not logged in
    if not authorised():
        return redirect(url_for('pages.signin'))
    user = session['user']
    return render_template('instructorDashboard.html', user = user)