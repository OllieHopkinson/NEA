from flask import Blueprint, render_template, request, session, url_for, redirect
from scripts.authorised import authorised

pages = Blueprint('pages', __name__)

@pages.route('/signin')
def signin():
    if authorised():
        role = session.get('role')

        if role == 'student':
            return redirect(url_for('pages.studentDashboard'))
        elif role == 'instructor':
            return redirect(url_for('pages.instructorDashboard'))

    return render_template('signin.html')


# Route shows the signup page where new users can register.
@pages.route('/')
def signup():
    return render_template('signup.html')


# Dashboard route shown after successful login or signup.
@pages.route('/studentDashboard')
def studentDashboard():
    if not authorised():
        return redirect(url_for('pages.signin'))
    user = session['user']
    return render_template('studentDashboard.html', user = user)


@pages.route('/instructorDashboard')
def instructorDashboard():
    if not authorised():
        return redirect(url_for('pages.signin'))
    user = session['user']
    return render_template('instructorDashboard.html', user = user)