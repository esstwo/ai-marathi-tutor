"""Standalone script to test Mitra's Marathi conversation quality."""

import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

SYSTEM_PROMPT = """You are Mitra, a friendly Marathi tutor for kids aged 5-12.

Rules:
• Always respond primarily in Marathi, using Devanagari script.
• If the child speaks in English, acknowledge what they said and gently model the Marathi equivalent: "हो, तुला water हवे आहे ना? मराठीत आपण म्हणतो 'पाणी'"
• Never explicitly say the child made a mistake. Instead, repeat the correct form naturally in the next response.
• Keep sentences short and vocabulary within the child's demonstrated level.
• Introduce one new word per 3–4 exchanges, with context clues.
• If the child seems stuck (long pause or "I don't know"), offer a hint in English and then model the Marathi."""

# Simulated child messages for a 5-turn conversation
CHILD_MESSAGES = [
    "Hi Mitra! I want to learn Marathi",
    "What is cat called in Marathi?",
    "Mala manjar aavadta",
    "I don't know how to say 'my cat is white'",
    "Mazhi manjar pandhari aahe! What about dog?",
]


def main():
    client = Groq()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    print("=" * 60)
    print("MarathiMitra Test Conversation")
    print("=" * 60)

    for i, child_msg in enumerate(CHILD_MESSAGES, 1):
        print(f"\n--- Turn {i} ---")
        print(f"Child: {child_msg}")

        messages.append({"role": "user", "content": child_msg})

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=300,
            messages=messages,
        )

        mitra_reply = response.choices[0].message.content
        print(f"Mitra: {mitra_reply}")

        messages.append({"role": "assistant", "content": mitra_reply})

    print("\n" + "=" * 60)
    print("Test complete — review Marathi quality above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
