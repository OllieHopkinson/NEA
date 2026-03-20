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

            # Track each submitted mock test so pass rates can be calculated.
            con.execute('''CREATE TABLE IF NOT EXISTS mock_test_attempts(
                        attemptId INTEGER PRIMARY KEY AUTOINCREMENT,
                        studentUsername TEXT NOT NULL,
                        score INTEGER NOT NULL,
                        totalQuestions INTEGER NOT NULL,
                        passed INTEGER NOT NULL CHECK(passed IN (0, 1)),
                        takenAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP);''')

            # Track one row per student/question; once correct, it remains correct.
            con.execute('''CREATE TABLE IF NOT EXISTS practice_question_progress(
                        studentUsername TEXT NOT NULL,
                        questionId TEXT NOT NULL,
                        categorySlug TEXT NOT NULL,
                        isCorrect INTEGER NOT NULL CHECK(isCorrect IN (0, 1)),
                        lastAnsweredAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(studentUsername, questionId));''')

            # Map instructors to the students they have added to their roster.
            con.execute('''CREATE TABLE IF NOT EXISTS instructor_students(
                        instructorEmail TEXT NOT NULL,
                        studentEmail TEXT NOT NULL,
                        addedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY(instructorEmail, studentEmail));''')
            
            
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
                if storedHash and check_password_hash(storedHash[0], password):
                    return True
            return False
        except Exception as e:
            print(e)
            return False
        
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

    # Save a completed mock test attempt for one student.
    def recordMockTestAttempt(self, student_username, score, total_questions, passed):
        with self.connect() as con:
            con.execute(
                '''INSERT INTO mock_test_attempts(studentUsername, score, totalQuestions, passed)
                   VALUES (?, ?, ?, ?)''',
                (student_username, score, total_questions, int(bool(passed)))
            )

    # Return attempts, passes and pass-rate percentage for one student.
    def getMockPassRateForStudent(self, student_username):
        with self.connect() as con:
            cur = con.cursor()
            cur.execute(
                '''SELECT COUNT(*), COALESCE(SUM(passed), 0)
                   FROM mock_test_attempts
                   WHERE studentUsername = ?''',
                (student_username,)
            )
            attempts, passes = cur.fetchone()

        pass_rate = round((passes / attempts) * 100, 1) if attempts else None
        return {
            'attempts': attempts,
            'passes': passes,
            'pass_rate_percentage': pass_rate,
        }

    # Save/update practice progress for one question.
    def recordPracticeQuestionAttempt(self, student_username, question_id, category_slug, is_correct):
        with self.connect() as con:
            con.execute(
                '''INSERT INTO practice_question_progress(studentUsername, questionId, categorySlug, isCorrect)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(studentUsername, questionId) DO UPDATE SET
                       categorySlug = excluded.categorySlug,
                       isCorrect = CASE
                           WHEN practice_question_progress.isCorrect = 1 OR excluded.isCorrect = 1 THEN 1
                           ELSE 0
                       END,
                       lastAnsweredAt = CURRENT_TIMESTAMP''',
                (student_username, question_id, category_slug, int(bool(is_correct)))
            )

    # Return aggregate practice stats for one student.
    def getPracticeStatsForStudent(self, student_username, total_available_questions=0):
        with self.connect() as con:
            cur = con.cursor()
            cur.execute(
                '''SELECT COUNT(*), COALESCE(SUM(isCorrect), 0)
                   FROM practice_question_progress
                   WHERE studentUsername = ?''',
                (student_username,)
            )
            answered, correct = cur.fetchone()

        accuracy = round((correct / answered) * 100, 1) if answered else None
        completion = round((correct / total_available_questions) * 100, 1) if total_available_questions else 0.0

        return {
            'answered': answered,
            'correct': correct,
            'accuracy_percentage': accuracy,
            'completion_percentage': completion,
        }

    # Return a per-category map of correctly answered practice questions.
    def getPracticeCorrectCountsByCategory(self, student_username):
        with self.connect() as con:
            cur = con.cursor()
            cur.execute(
                '''SELECT categorySlug, COALESCE(SUM(isCorrect), 0)
                   FROM practice_question_progress
                   WHERE studentUsername = ?
                   GROUP BY categorySlug''',
                (student_username,)
            )
            rows = cur.fetchall()

        return {slug: count for slug, count in rows}

    # Return mock/practice performance summary for each student.
    def getStudentPerformanceSummary(self, total_available_questions=0):
        with self.connect() as con:
            cur = con.cursor()
            cur.execute(
                '''SELECT s.username,
                          COALESCE(m.mock_attempts, 0),
                          COALESCE(m.mock_passes, 0),
                          COALESCE(p.practice_answered, 0),
                          COALESCE(p.practice_correct, 0)
                   FROM students s
                   LEFT JOIN (
                       SELECT studentUsername,
                              COUNT(*) AS mock_attempts,
                              COALESCE(SUM(passed), 0) AS mock_passes
                       FROM mock_test_attempts
                       GROUP BY studentUsername
                   ) m ON m.studentUsername = s.username
                   LEFT JOIN (
                       SELECT studentUsername,
                              COUNT(*) AS practice_answered,
                              COALESCE(SUM(isCorrect), 0) AS practice_correct
                       FROM practice_question_progress
                       GROUP BY studentUsername
                   ) p ON p.studentUsername = s.username
                   ORDER BY s.username'''
            )
            rows = cur.fetchall()

        summary = []
        for username, mock_attempts, mock_passes, practice_answered, practice_correct in rows:
            mock_pass_rate = round((mock_passes / mock_attempts) * 100, 1) if mock_attempts else None
            practice_accuracy = round((practice_correct / practice_answered) * 100, 1) if practice_answered else None
            practice_completion = round((practice_correct / total_available_questions) * 100, 1) if total_available_questions else 0.0

            summary.append(
                {
                    'username': username,
                    'mock_attempts': mock_attempts,
                    'mock_passes': mock_passes,
                    'mock_pass_rate_percentage': mock_pass_rate,
                    'practice_answered': practice_answered,
                    'practice_correct': practice_correct,
                    'practice_accuracy_percentage': practice_accuracy,
                    'practice_completion_percentage': practice_completion,
                }
            )

        return summary

    # Find one student account by email.
    def findStudentByEmail(self, student_email):
        with self.connect() as con:
            cur = con.cursor()
            cur.execute(
                '''SELECT username, email
                   FROM students
                   WHERE LOWER(email) = LOWER(?)''',
                (student_email,)
            )
            row = cur.fetchone()

        if not row:
            return None

        return {
            'username': row[0],
            'email': row[1],
        }

    # Add a student to one instructor's roster by student email.
    def addStudentToInstructor(self, instructor_email, student_email):
        student = self.findStudentByEmail(student_email)
        if not student:
            return False, 'student_not_found'

        canonical_student_email = student['email']

        with self.connect() as con:
            cur = con.cursor()
            cur.execute(
                '''SELECT 1
                   FROM instructor_students
                   WHERE LOWER(instructorEmail) = LOWER(?)
                     AND LOWER(studentEmail) = LOWER(?)''',
                (instructor_email, canonical_student_email)
            )
            if cur.fetchone():
                return False, 'already_added'

            cur.execute(
                '''INSERT INTO instructor_students(instructorEmail, studentEmail)
                   VALUES (?, ?)''',
                (instructor_email, canonical_student_email)
            )

        return True, 'added'

    # Return stats for all students on one instructor's roster.
    def getInstructorStudentsWithSummary(self, instructor_email, total_available_questions=0):
        with self.connect() as con:
            cur = con.cursor()
            cur.execute(
                '''SELECT s.username, s.email
                   FROM instructor_students i
                   JOIN students s ON LOWER(s.email) = LOWER(i.studentEmail)
                   WHERE LOWER(i.instructorEmail) = LOWER(?)
                   ORDER BY s.username''',
                (instructor_email,)
            )
            rows = cur.fetchall()

        summary = []
        for username, email in rows:
            mock_stats = self.getMockPassRateForStudent(username)
            practice_stats = self.getPracticeStatsForStudent(
                username,
                total_available_questions=total_available_questions,
            )

            summary.append(
                {
                    'username': username,
                    'email': email,
                    'mock_attempts': mock_stats['attempts'],
                    'mock_passes': mock_stats['passes'],
                    'mock_pass_rate_percentage': mock_stats['pass_rate_percentage'],
                    'practice_answered': practice_stats['answered'],
                    'practice_correct': practice_stats['correct'],
                    'practice_accuracy_percentage': practice_stats['accuracy_percentage'],
                    'practice_completion_percentage': practice_stats['completion_percentage'],
                }
            )

        return summary

    # Return one instructor-scoped student performance record.
    def getInstructorStudentPerformance(self, instructor_email, student_email, total_available_questions=0):
        with self.connect() as con:
            cur = con.cursor()
            cur.execute(
                '''SELECT s.username, s.email
                   FROM instructor_students i
                   JOIN students s ON LOWER(s.email) = LOWER(i.studentEmail)
                   WHERE LOWER(i.instructorEmail) = LOWER(?)
                     AND LOWER(s.email) = LOWER(?)''',
                (instructor_email, student_email)
            )
            row = cur.fetchone()

        if not row:
            return None

        username, email = row
        mock_stats = self.getMockPassRateForStudent(username)
        practice_stats = self.getPracticeStatsForStudent(
            username,
            total_available_questions=total_available_questions,
        )

        return {
            'username': username,
            'email': email,
            'mock_attempts': mock_stats['attempts'],
            'mock_passes': mock_stats['passes'],
            'mock_pass_rate_percentage': mock_stats['pass_rate_percentage'],
            'practice_answered': practice_stats['answered'],
            'practice_correct': practice_stats['correct'],
            'practice_accuracy_percentage': practice_stats['accuracy_percentage'],
            'practice_completion_percentage': practice_stats['completion_percentage'],
        }