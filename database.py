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
                        email TEXT NOT NULL UNIQUE);''')
            
            con.execute('''CREATE TABLE IF NOT EXISTS instructors(
                        instructorId INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        password TEXT NOT NULL,
                        email TEXT NOT NULL UNIQUE);''')
            
    #Here is where the functions are to create a student or instructor they take in the username password and email and add them to the database
    def createStudent(self, username, password, email):
        try:
            with self.connect() as con:
                con.execute('''INSERT INTO students(username, password, email) VALUES (?, ?, ?)''', (username, password, email))
            return True
        except:
            return False
            
    def createInstructor(self, username, password, email):
        try:
            with self.connect() as con:
                con.execute('''INSERT INTO instructors(username, password, email) VALUES (?, ?, ?)''', (username, password, email))
            return True
        except:
            return False