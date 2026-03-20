import random

from blueprints.practice_questions import ALL_PRACTICE_QUESTIONS


ALL_MOCK_TEST_QUESTIONS = list(ALL_PRACTICE_QUESTIONS)
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
