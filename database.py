# Handles all database operations including user authentication and account creation
import sqlite3 as sql
from werkzeug.security import generate_password_hash, check_password_hash

class DatabaseHandler:
    # Initialize database with a name (default: app.db)
    def __init__(self, dbName = 'app.db'):
        self.dbName = dbName

    # Returns a connection to the SQLite database
    def connect(self):
        return sql.connect(self.dbName)
        

    def createTables(self):
        with self.connect() as con:
            #This is where we create the tables for the student and instructors
            con.execute('''CREATE TABLE IF NOT EXISTS students(
                        studentId INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        password TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL);''')
            
            # Create instructors table with validation constraints
            con.execute('''CREATE TABLE IF NOT EXISTS instructors(
                        instructorId INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL CHECK(LENGTH(username) > 2),
                        password TEXT NOT NULL CHECK(LENGTH(password) > 4),
                        email TEXT UNIQUE NOT NULL);''')
            
            
    # Verify user credentials in both students and instructors tables
    def authoriseUser(self, username, password, email):
        """Check both tables; returns True if any match."""
        try:
            with self.connect() as con:
                cur = con.cursor()
                # Check students table first
                cur.execute('''SELECT password FROM students WHERE username = ? AND email = ?''', (username, email))
                storedHashStudent = cur.fetchone()
                if storedHashStudent:
                    # Verify password hash matches
                    if check_password_hash(storedHashStudent[0], password):
                        return True
                
                # Check instructors table if not found in students
                cur.execute('''SELECT password FROM instructors WHERE username = ? AND email = ?''', (username, email))
                storedHashInstructor = cur.fetchone()
                if storedHashInstructor:
                    if check_password_hash(storedHashInstructor[0], password):
                        return True
                
            return False
        except Exception as e:
            print(e)
            return False
        
    # Verify credentials for a specific user type (student or instructor only)
    def authoriseUserType(self, username, password, email, user_type):
        """Check only the specified user_type table."""
        # Validate user type is either student or instructor
        if user_type not in ("student", "instructor"):
            return False
        # Select the correct table based on user type
        table = "students" if user_type == "student" else "instructors"
        try:
            with self.connect() as con:
                cur = con.cursor()
                # Get stored password hash for the user
                cur.execute(f'''SELECT password FROM {table} WHERE username = ? AND email = ?''',
                            (username, email))
                storedHash = cur.fetchone()
                # Verify the password matches the stored hash
                if storedHash and check_password_hash(storedHash[0], password):
                    return True
                return False
        except Exception as e:
            print(e)
            return False
        
    # Add a new student to the database with hashed password        
    #Here is where the functions are to create a student or instructor they take in the username password and email and add them to the database
    def createStudent(self, username, password, email):
        try:
            # Hash the password before storing
            hashed_password = generate_password_hash(password)
            with self.connect() as con:
                con.execute('''INSERT INTO students(username, password, email) VALUES (?, ?, ?)''', (username, hashed_password, email))
            return True, None
        except sql.IntegrityError as e:
            print(e)
            return False, 'integrity_error'
        except Exception as e:
            print(e)
            return False, 'unknown_error'

    # Add a new instructor to the database with hashed password
    def createInstructor(self, username, password, email):
        try:
            # Hash the password before storing
            hashed_password = generate_password_hash(password)
            with self.connect() as con:
                con.execute('''INSERT INTO instructors(username, password, email) VALUES (?, ?, ?)''', (username, hashed_password, email))
            return True, None
        except sql.IntegrityError as e:
            print(e)
            return False, 'integrity_error'
        except Exception as e:
            print(e)
            return False, 'unknown_error'