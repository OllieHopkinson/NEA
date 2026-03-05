from flask import session

def authorised():
    return 'user' in session