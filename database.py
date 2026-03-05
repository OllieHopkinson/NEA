import sqlite3 as sql


class DatabaseHandler:
    def __init__(self, dbName = 'app.db'):
        self.dbName = dbName


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
            
            con.execute('''CREATE TABLE IF NOT EXISTS instructors(
                        instructorId INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL CHECK(LENGTH(username) > 2),
                        password TEXT NOT NULL CHECK(LENGTH(password) > 4),
                        email TEXT UNIQUE NOT NULL);''')
            
            
    def authoriseUser(self, username, password, email):
        """Check both tables; returns True if any match."""
        try:
            with self.connect() as con:
                cur = con.cursor()
                cur.execute('''SELECT * FROM students WHERE username = ? AND password = ? AND email = ?''', (username, password, email))
                student = cur.fetchone()
                if student:
                    return True
                
                cur.execute('''SELECT * FROM instructors WHERE username = ? AND password = ? AND email = ?''', (username, password, email))
                instructor = cur.fetchone()
                if instructor:
                    return True
                
            return False
        except Exception as e:
            print(e)
            return False

    def authoriseUserType(self, username, password, email, user_type):
        """Check only the specified user_type table."""
        if user_type not in ("student", "instructor"):
            return False
        table = "students" if user_type == "student" else "instructors"
        try:
            with self.connect() as con:
                cur = con.cursor()
                cur.execute(f'''SELECT * FROM {table} WHERE username = ? AND password = ? AND email = ?''',
                            (username, password, email))
                return cur.fetchone() is not None
        except Exception as e:
            print(e)
            return False
        
            
    #Here is where the functions are to create a student or instructor they take in the username password and email and add them to the database
    def createStudent(self, username, password, email):
        try:
            with self.connect() as con:
                con.execute('''INSERT INTO students(username, password, email) VALUES (?, ?, ?)''', (username, password, email))
            return True
        except Exception as e:
            print(e)
            return False
        
            
    def createInstructor(self, username, password, email):
        try:
            with self.connect() as con:
                con.execute('''INSERT INTO instructors(username, password, email) VALUES (?, ?, ?)''', (username, password, email))
            return True
        except Exception as e:
            print(e)
            return False