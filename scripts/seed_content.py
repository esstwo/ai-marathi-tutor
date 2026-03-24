"""
Seed the lessons table in Supabase from content/level1_lessons.json.
Usage: python -m scripts.seed_content
"""

import json
from backend.db.supabase_client import supabase_admin


def load_lessons(file_path: str, level: int):
    with open(file_path) as f:
        lessons = json.load(f)

    rows = []
    for lesson in lessons:
        # Transform quiz: convert correct_answer to correct_index
        quiz_questions = []
        for q in lesson["quiz"]:
            correct_index = q["options"].index(q["correct_answer"])
            quiz_questions.append({
                "question": q["question"],
                "options": q["options"],
                "correct_index": correct_index,
            })

        # Transform vocabulary: rename romanized -> pronunciation
        vocabulary = [
            {
                "marathi": v["marathi"],
                "english": v["english"],
                "pronunciation": v["romanized"],
            }
            for v in lesson["vocabulary"]
        ]

        title = f"{lesson['title']['marathi']} — {lesson['title']['english']}"

        rows.append({
            "level": level,
            "sequence": lesson["lesson_id"],
            "title": title,
            "theme": lesson["theme"],
            "vocabulary": vocabulary,
            "quiz_questions": quiz_questions,
        })

    return rows


def seed():
    rows = load_lessons("content/level1_lessons.json", level=1)

    result = supabase_admin.table("lessons").insert(rows).execute()
    print(f"Inserted {len(result.data)} lessons.")
    for row in result.data:
        print(f"  - {row['title']}")


if __name__ == "__main__":
    seed()
