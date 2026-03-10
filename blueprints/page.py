# Blueprint for all page routes (signin, signup, dashboards)
import json
import random
from pathlib import Path

from flask import Blueprint, get_flashed_messages, render_template, request, session, url_for, redirect
from scripts.authorised import authorised

pages = Blueprint('pages', __name__)


QUESTION_FILES = [
    'alertness.json',
    'attitude.json',
    'essential_documents.json',
    'hazard_awareness.json',
    'incidents_accidents_emergencies.json',
    'motorway_rules.json',
    'other_types_of_vehicle.json',
    'road_and_traffic_signs.json',
    'rules_of_the_road.json',
    'safety_and_your_vehicle.json',
    'safety_margins.json',
    'vehicle_handling.json',
]

QUESTIONS_DIR = Path(__file__).resolve().parent.parent / 'questions'


def category_display_name(category_slug):
    return category_slug.replace('_', ' ').title()


def load_questions_by_category():
    categories = {}

    for file_name in QUESTION_FILES:
        file_path = QUESTIONS_DIR / file_name
        if not file_path.exists():
            continue

        with file_path.open('r', encoding='utf-8') as file_obj:
            file_questions = json.load(file_obj)

        category_slug = file_path.stem
        question_items = []

        for question_index, question in enumerate(file_questions, start=1):
            question_items.append(
                {
                    'id': f'{category_slug}_q{question_index}',
                    'question': question['question'],
                    'options': question['options'],
                    'answer': question['answer'],
                }
            )

        categories[category_slug] = {
            'name': category_display_name(category_slug),
            'questions': question_items,
        }

    return categories


def build_mock_test_questions(category_map):
    mock_questions = []

    for file_name in QUESTION_FILES:
        category_slug = Path(file_name).stem
        category_data = category_map.get(category_slug)
        if not category_data:
            continue

        for question in category_data['questions']:
            mock_questions.append(
                {
                    'source_id': question['id'],
                    'question': question['question'],
                    'options': question['options'],
                    'answer': question['answer'],
                    'category': category_data['name'],
                }
            )

    for question in mock_questions:
        question['id'] = question['source_id']

    return mock_questions


QUESTION_CATEGORIES = load_questions_by_category()
ALL_MOCK_TEST_QUESTIONS = build_mock_test_questions(QUESTION_CATEGORIES)
MOCK_TEST_QUESTION_LOOKUP = {question['id']: question for question in ALL_MOCK_TEST_QUESTIONS}


def select_random_mock_test_question_ids(test_size=50):
    all_ids = list(MOCK_TEST_QUESTION_LOOKUP.keys())
    if not all_ids:
        return []

    sample_size = min(test_size, len(all_ids))
    return random.sample(all_ids, sample_size)


def get_mock_test_questions_from_ids(question_ids):
    questions = []
    for question_id in question_ids:
        question = MOCK_TEST_QUESTION_LOOKUP.get(question_id)
        if question:
            questions.append(question)
    return questions


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
    if session.get('role') != 'student':
        return redirect(url_for('pages.signin'))
    user = session['user']
    return render_template('studentDashboard.html', user = user)


# Instructor dashboard - only accessible when logged in
@pages.route('/instructorDashboard')
def instructorDashboard():
    # Redirect to signin if not logged in
    if not authorised():
        return redirect(url_for('pages.signin'))
    if session.get('role') != 'instructor':
        return redirect(url_for('pages.signin'))
    user = session['user']
    return render_template('instructorDashboard.html', user = user)


@pages.route('/student/questions')
def student_questions_folder():
    # Only logged-in students can access practice questions.
    if not authorised() or session.get('role') != 'student':
        return redirect(url_for('pages.signin'))

    user = session['user']
    categories = []

    for file_name in QUESTION_FILES:
        category_slug = Path(file_name).stem
        category_data = QUESTION_CATEGORIES.get(category_slug)
        if not category_data:
            continue

        categories.append(
            {
                'slug': category_slug,
                'name': category_data['name'],
                'count': len(category_data['questions']),
            }
        )

    return render_template('studentQuestionsFolder.html', user=user, categories=categories)


@pages.route('/student/questions/all-random')
def student_practice_all_random():
    # Only logged-in students can access practice questions.
    if not authorised() or session.get('role') != 'student':
        return redirect(url_for('pages.signin'))

    user = session['user']
    questions = list(ALL_MOCK_TEST_QUESTIONS)
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