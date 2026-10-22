import requests
import json


def generate_quiz_questions(topic, difficulty, num_questions):

    prompt = f"""
Generate {num_questions} multiple choice questions about {topic}.
Difficulty: {difficulty}

Return JSON only.

Format example:
{{
  "questions": [
    {{
      "question": "Question text",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": "Exact correct option text"
    }}
  ]
}}
"""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "phi",
                "prompt": prompt,
                "stream": False,
                "temperature": 0.2,
                "format": "json"
            },
            timeout=60
        )

        result = response.json()
        print("FULL RESPONSE:", result)

        raw_text = result.get("response", "").strip()

        # Convert JSON string to Python object
        data = json.loads(raw_text)

        # If model returns {"questions": [...]}
        if isinstance(data, dict) and "questions" in data:
            return data["questions"]

        # If model directly returns [...]
        if isinstance(data, list):
            return data

        return []

    except Exception as e:
        print("Ollama Error:", str(e))
        return []