"""
Seed the lessons table in Supabase from content JSON files.
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
    """Insert all lessons (levels 1-4). Fails if rows already exist."""
    lesson_files = [
        ("content/level1_lessons.json", 1),
        ("content/level2_lessons.json", 2),
        ("content/level3_lessons.json", 3),
        ("content/level4_lessons.json", 4),
    ]

    for file_path, level in lesson_files:
        rows = load_lessons(file_path, level)
        result = supabase_admin.table("lessons").insert(rows).execute()
        print(f"Inserted {len(result.data)} Level {level} lessons.")
        for row in result.data:
            print(f"  - {row['title']}")


def reseed():
    """Delete all existing lessons and re-insert from JSON files."""
    print("Deleting all existing lessons...")
    supabase_admin.table("lessons").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    print("Deleted. Re-seeding...")
    seed()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--reseed":
        reseed()
    else:
        seed()
