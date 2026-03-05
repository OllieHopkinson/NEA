# Check if a user is currently logged in
from flask import session

# Returns True if user is in session, False otherwise
def authorised():
    return 'user' in session