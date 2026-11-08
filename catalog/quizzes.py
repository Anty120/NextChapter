"""Small editorial comprehension quizzes; answers are graded only on the server."""
import json
from pathlib import Path


def book_quiz(slug):
    bank = json.loads((Path(__file__).parent / 'demo_library' / 'quizzes.json').read_text(encoding='utf-8'))
    return bank.get(slug, [])


def public_questions(questions, submitted=None):
    rows = []
    for index, question in enumerate(questions):
        value = submitted.get(f'q{index}', '') if submitted is not None else ''
        row = {'prompt': question['prompt'], 'name': f'q{index}', 'choices': [
            {'value': str(i), 'label': label, 'selected': value == str(i)}
            for i, label in enumerate(question['choices'])]}
        if submitted is not None:
            row.update(correct=value == str(question['answer']), explanation=question['explanation'],
                       answer=question['choices'][question['answer']])
        rows.append(row)
    return rows
