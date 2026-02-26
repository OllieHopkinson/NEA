from flask import Flask, render_template, request

app = Flask(__name__)

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
    formDetails = request.form
    username = formDetails.get('username')
    password = formDetails.get('password')
    confirm_password = formDetails.get('confirm_password')
    email = formDetails.get('email')

    if (len(username) >= 3 and len(username) <= 10 
        and len(password) >= 4 
        and len(confirm_password) >= 4 
        and password == confirm_password
        and not any(char in special_characters for char in username)
        and any(char in numbers for char in password)
        and any(char in special_characters for char in password)):
        return render_template('dashboard.html')
        
    return 'failed to create user'

app.run(debug=True)