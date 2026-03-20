import json
from pathlib import Path


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


def build_all_practice_questions(category_map):
    questions = []

    for file_name in QUESTION_FILES:
        category_slug = Path(file_name).stem
        category_data = category_map.get(category_slug)
        if not category_data:
            continue

        for question in category_data['questions']:
            questions.append(
                {
                    'id': question['id'],
                    'question': question['question'],
                    'options': question['options'],
                    'answer': question['answer'],
                    'category_slug': category_slug,
                    'category': category_data['name'],
                }
            )

    return questions


def build_question_folder_categories(category_map):
    categories = []

    for file_name in QUESTION_FILES:
        category_slug = Path(file_name).stem
        category_data = category_map.get(category_slug)
        if not category_data:
            continue

        categories.append(
            {
                'slug': category_slug,
                'name': category_data['name'],
                'count': len(category_data['questions']),
            }
        )

    return categories


QUESTION_CATEGORIES = load_questions_by_category()
ALL_PRACTICE_QUESTIONS = build_all_practice_questions(QUESTION_CATEGORIES)
PRACTICE_QUESTION_LOOKUP = {question['id']: question for question in ALL_PRACTICE_QUESTIONS}
