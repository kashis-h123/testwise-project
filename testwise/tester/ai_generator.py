from google import genai
from dotenv import load_dotenv
import os
import traceback
import json

# ---------------------------
# LOAD ENV VARIABLES
# ---------------------------
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found. Check your .env file")

# Initialize client
client = genai.Client(api_key=api_key)


# ---------------------------
# AI TEST CASE FUNCTION
# ---------------------------
def generate_ai_test_cases(dom_report, title):

    prompt = f"""
    Generate 2 structured website test cases in STRICT JSON format.

    Page Title: {title}
    Forms: {dom_report['forms']}
    Buttons: {dom_report['buttons']}
    Links: {dom_report['links']}
    Missing Alt Images: {len(dom_report['images_without_alt'])}

    Output ONLY JSON like this:

    [
      {{
        "title": "Test case title",
        "steps": [
          "Step 1",
          "Step 2",
          "Step 3"
        ],
        "expected": "Expected result description"
      }}
    ]

    Rules:
    - steps MUST NOT be empty
    - expected MUST NOT be empty
    - Do NOT return text outside JSON
    """

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )

        text = getattr(response, "text", "").strip()

        if not text:
            return []

        # ---------------------------
        # CLEAN RESPONSE (handles ```json issues)
        # ---------------------------
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()

        # ---------------------------
        # PARSE JSON
        # ---------------------------
        test_cases = json.loads(text)

        # ---------------------------
        # VALIDATE DATA
        # ---------------------------
        valid_cases = []
        for tc in test_cases:
            if (
                isinstance(tc, dict)
                and tc.get("steps")
                and tc.get("expected")
                and len(tc.get("steps")) > 0
            ):
                valid_cases.append(tc)

        return valid_cases

    except json.JSONDecodeError:
        print("❌ JSON PARSE ERROR")
        print(text)
        return []

    except Exception as e:
        print("❌ AI ERROR:")
        print(traceback.format_exc())
        return []


# ---------------------------
# MAIN (TEST RUN)
# ---------------------------
if __name__ == "__main__":

    dom_report = {
        "forms": 2,
        "buttons": 4,
        "links": 10,
        "images_without_alt": ["img1.jpg", "img2.jpg"]
    }

    title = "Sample Website Page"

    print("\n Generating AI Test Cases...\n")

    test_cases = generate_ai_test_cases(dom_report, title)

    for i, tc in enumerate(test_cases, 1):
        print(f"\n🧪 Test Case {i}: {tc['title']}")
        print("📝 Steps:")
        for step in tc["steps"]:
            print(f" - {step}")
        print(f"Expected: {tc['expected']}")