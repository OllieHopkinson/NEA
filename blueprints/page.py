# Blueprint for all page routes (signin, signup, dashboards)
import random

from flask import Blueprint, flash, get_flashed_messages, jsonify, render_template, request, session, url_for, redirect
from database import DatabaseHandler
from scripts.authorised import authorised

from blueprints.mock_test import (
    MOCK_TEST_QUESTION_LOOKUP,
    get_mock_test_questions_from_ids,
    select_random_mock_test_question_ids,
)
from blueprints.practice_questions import (
    ALL_PRACTICE_QUESTIONS,
    PRACTICE_QUESTION_LOOKUP,
    QUESTION_CATEGORIES,
    build_question_folder_categories,
)

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
    # Redirect to dashboard if user is already logged in
    if authorised():
        role = session.get('role')

        if role == 'student':
            return redirect(url_for('pages.studentDashboard'))
        elif role == 'instructor':
            return redirect(url_for('pages.instructorDashboard'))

    messages = get_flashed_messages()
    return render_template('signup.html', messages = messages)


# Student dashboard - only accessible when logged in
# Dashboard route shown after successful login or signup.
@pages.route('/studentDashboard')
def studentDashboard():
    # Redirect to signin if not logged in
    if not authorised():
        return redirect(url_for('pages.signin'))
    if session.get('role') != 'student':
        return redirect(url_for('pages.signin'))
    user = session['user']

    db = DatabaseHandler()
    mock_stats = db.getMockPassRateForStudent(user)
    practice_stats = db.getPracticeStatsForStudent(user, total_available_questions=len(ALL_PRACTICE_QUESTIONS))

    return render_template(
        'studentDashboard.html',
        user=user,
        mock_stats=mock_stats,
        practice_stats=practice_stats,
    )


# Instructor dashboard - only accessible when logged in
@pages.route('/instructorDashboard')
def instructorDashboard():
    # Redirect to signin if not logged in
    if not authorised():
        return redirect(url_for('pages.signin'))
    if session.get('role') != 'instructor':
        return redirect(url_for('pages.signin'))

    user = session['user']
    instructor_email = session.get('email')

    if not instructor_email:
        flash('Please sign in again to access instructor student management.')
        return redirect(url_for('pages.signin'))

    messages = get_flashed_messages()
    searched_email = request.args.get('searched_email', '').strip()

    db = DatabaseHandler()
    searched_student = db.findStudentByEmail(searched_email) if searched_email else None
    student_stats = db.getInstructorStudentsWithSummary(
        instructor_email,
        total_available_questions=len(ALL_PRACTICE_QUESTIONS),
    )

    return render_template(
        'instructorDashboard.html',
        user=user,
        student_stats=student_stats,
        searched_email=searched_email,
        searched_student=searched_student,
        messages=messages,
    )


@pages.route('/instructor/students/search', methods=['POST'])
def instructor_search_student():
    # Only logged-in instructors can search for students.
    if not authorised() or session.get('role') != 'instructor':
        return redirect(url_for('pages.signin'))

    student_email = request.form.get('student_email', '').strip()
    if not student_email:
        flash('Enter a student email to search.')
        return redirect(url_for('pages.instructorDashboard'))

    db = DatabaseHandler()
    student = db.findStudentByEmail(student_email)

    if not student:
        flash('No student account found with that email.')
        return redirect(url_for('pages.instructorDashboard'))

    return redirect(url_for('pages.instructorDashboard', searched_email=student['email']))


@pages.route('/instructor/students/add', methods=['POST'])
def instructor_add_student():
    # Only logged-in instructors can add students.
    if not authorised() or session.get('role') != 'instructor':
        return redirect(url_for('pages.signin'))

    instructor_email = session.get('email')
    if not instructor_email:
        flash('Please sign in again to add students.')
        return redirect(url_for('pages.signin'))

    student_email = request.form.get('student_email', '').strip()
    if not student_email:
        flash('Student email is required.')
        return redirect(url_for('pages.instructorDashboard'))

    db = DatabaseHandler()
    success, result = db.addStudentToInstructor(instructor_email, student_email)

    if not success and result == 'student_not_found':
        flash('No student account found with that email.')
    elif not success and result == 'already_added':
        flash('That student is already on your roster.')
    elif success:
        flash('Student added to your roster.')
    else:
        flash('Unable to add student right now. Please try again.')

    return redirect(url_for('pages.instructorDashboard'))


@pages.route('/instructor/students/<path:student_email>/stats')
def instructor_student_stats(student_email):
    # Only logged-in instructors can view student stats.
    if not authorised() or session.get('role') != 'instructor':
        return redirect(url_for('pages.signin'))

    instructor_email = session.get('email')
    if not instructor_email:
        flash('Please sign in again to view student stats.')
        return redirect(url_for('pages.signin'))

    db = DatabaseHandler()
    student = db.getInstructorStudentPerformance(
        instructor_email,
        student_email,
        total_available_questions=len(ALL_PRACTICE_QUESTIONS),
    )

    if not student:
        flash('Student not found on your roster.')
        return redirect(url_for('pages.instructorDashboard'))

    return render_template('instructorStudentStats.html', user=session['user'], student=student)


@pages.route('/student/questions')
def student_questions_folder():
    # Only logged-in students can access practice questions.
    if not authorised() or session.get('role') != 'student':
        return redirect(url_for('pages.signin'))

    user = session['user']
    categories = build_question_folder_categories(QUESTION_CATEGORIES)

    db = DatabaseHandler()
    category_correct_counts = db.getPracticeCorrectCountsByCategory(user)

    for category in categories:
        total_questions = category['count']
        correct_questions = category_correct_counts.get(category['slug'], 0)
        category['correct_count'] = correct_questions
        category['correct_percentage'] = round((correct_questions / total_questions) * 100, 1) if total_questions else 0.0

    return render_template('studentQuestionsFolder.html', user=user, categories=categories)


@pages.route('/student/questions/record', methods=['POST'])
def record_student_practice_answer():
    # Only logged-in students can record question progress.
    if not authorised() or session.get('role') != 'student':
        return jsonify({'ok': False, 'error': 'unauthorised'}), 401

    payload = request.get_json(silent=True) or {}
    question_id = payload.get('question_id')
    selected_answer = payload.get('selected_answer', '')

    question = PRACTICE_QUESTION_LOOKUP.get(question_id)
    if not question:
        return jsonify({'ok': False, 'error': 'unknown_question'}), 400

    is_correct = selected_answer == question['answer']

    db = DatabaseHandler()
    db.recordPracticeQuestionAttempt(
        student_username=session['user'],
        question_id=question_id,
        category_slug=question['category_slug'],
        is_correct=is_correct,
    )

    return jsonify({'ok': True, 'is_correct': is_correct})


@pages.route('/student/questions/all-random')
def student_practice_all_random():
    # Only logged-in students can access practice questions.
    if not authorised() or session.get('role') != 'student':
        return redirect(url_for('pages.signin'))

    user = session['user']
    questions = list(ALL_PRACTICE_QUESTIONS)
    random.shuffle(questions)

    return render_template(
        'studentPracticeQuestions.html',
        user=user,
        category_name='All Topics (Random Order)',
        questions=questions,
    )


@pages.route('/student/questions/<category_slug>')
def student_practice_category(category_slug):
    # Only logged-in students can access practice questions.
    if not authorised() or session.get('role') != 'student':
        return redirect(url_for('pages.signin'))

    category_data = QUESTION_CATEGORIES.get(category_slug)
    if not category_data:
        return redirect(url_for('pages.student_questions_folder'))

    user = session['user']
    return render_template(
        'studentPracticeQuestions.html',
        user=user,
        category_name=category_data['name'],
        questions=category_data['questions'],
    )


@pages.route('/student/mock-test/start')
def start_student_mock_test():
    # Only logged-in students can initiate the mock test.
    if not authorised() or session.get('role') != 'student':
        return redirect(url_for('pages.signin'))

    # Gate access so the test page can only be opened from the dashboard flow.
    session['can_start_mock_test'] = True
    return redirect(url_for('pages.student_mock_test'))


@pages.route('/student/mock-test', methods=['GET', 'POST'])
def student_mock_test():
    # Only logged-in students can access this test.
    if not authorised() or session.get('role') != 'student':
        return redirect(url_for('pages.signin'))

    user = session['user']
    duration_seconds = 60 * 60
    result = None

    if request.method == 'GET':
        can_start_from_dashboard = session.pop('can_start_mock_test', False)
        active_question_ids = session.get('active_mock_test_question_ids', [])

        if can_start_from_dashboard:
            # Start a new mock test with a random set/order of 50 questions.
            question_ids = select_random_mock_test_question_ids(test_size=50)
            session['active_mock_test_question_ids'] = question_ids
            questions = get_mock_test_questions_from_ids(question_ids)
        elif active_question_ids:
            # Allow refresh/re-entry of an in-progress test.
            questions = get_mock_test_questions_from_ids(active_question_ids)
        else:
            # Block direct URL access unless started from dashboard flow.
            return redirect(url_for('pages.studentDashboard'))

        return render_template(
            'studentMockTest.html',
            user=user,
            questions=questions,
            duration_seconds=duration_seconds,
            submitted_answers={},
            result=result,
        )

    if request.method == 'POST':
        question_ids = session.get('active_mock_test_question_ids', [])
        if not question_ids:
            # Fallback if session state is missing, using submitted question IDs.
            question_ids = [key for key in request.form.keys() if key in MOCK_TEST_QUESTION_LOOKUP]

        questions = get_mock_test_questions_from_ids(question_ids)
        total_questions = len(questions)
        pass_mark = 43 if total_questions >= 50 else max(1, round(total_questions * 0.86))
        score = 0
        submitted_answers = {}

        for question in questions:
            selected = request.form.get(question['id'], '')
            submitted_answers[question['id']] = selected
            if selected == question['answer']:
                score += 1

        result = {
            'score': score,
            'total': total_questions,
            'passed': score >= pass_mark,
            'pass_mark': pass_mark,
        }

        db = DatabaseHandler()
        db.recordMockTestAttempt(
            student_username=user,
            score=score,
            total_questions=total_questions,
            passed=result['passed'],
        )

        # Clear active test so the next visit starts a new random test.
        session.pop('active_mock_test_question_ids', None)

        return render_template(
            'studentMockTest.html',
            user = user,
            questions = questions,
            duration_seconds = duration_seconds,
            submitted_answers = submitted_answers,
            result = result,
        )