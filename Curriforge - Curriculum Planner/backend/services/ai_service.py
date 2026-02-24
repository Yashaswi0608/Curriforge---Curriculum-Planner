import json
from groq import Groq
from config import settings

# Configure Groq
client = Groq(api_key=settings.GROQ_API_KEY)
MODEL = "llama-3.3-70b-versatile"


def _chat(prompt: str, *, max_tokens: int = 8192, temperature: float = 0.7) -> str:
    """Send a single-turn chat completion to Groq and return the text."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()


def _parse_json(text: str) -> dict:
    """Extract and parse JSON from an LLM response."""
    # Strip markdown fences
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try extracting the first JSON object
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])


async def generate_curriculum(
    subject: str,
    level: str,
    reason: str,
    duration_weeks: int,
    daily_hours: float,
    user_profile: dict,
) -> dict:
    """Generate a full personalized curriculum using Groq AI."""

    prompt = f"""You are an expert curriculum designer. Create a detailed, personalized curriculum for the following:

**Subject:** {subject}
**Level:** {level}
**Duration:** {duration_weeks} weeks, {daily_hours} hours/day
**Reason for learning:** {reason or 'General interest'}

**Student Profile:**
- Age: {user_profile.get('age', 'Not specified')}
- Educational Qualification: {user_profile.get('educational_qualification', 'Not specified')}
- Educational Interests: {user_profile.get('educational_interests', 'Not specified')}
- Hobbies: {user_profile.get('hobbies', 'Not specified')}
- Habits: {user_profile.get('habits', 'Not specified')}
- Daily Routine: {user_profile.get('daily_routine', 'Not specified')}
- Ongoing Courses: {user_profile.get('ongoing_courses', 'None')}

Generate a comprehensive JSON response with this EXACT structure:
{{
    "title": "Course Title",
    "description": "Brief course description (2-3 sentences)",
    "curriculum": {{
        "overview": "Course overview paragraph",
        "learning_outcomes": ["outcome1", "outcome2", "outcome3", "outcome4", "outcome5"],
        "prerequisites": ["prereq1", "prereq2"]
    }},
    "topics": [
        {{
            "week": 1,
            "day": 1,
            "title": "Topic Title",
            "description": "What will be covered",
            "duration_minutes": 60,
            "resources": [
                {{"name": "Resource Name", "url": "https://www.youtube.com/results?search_query=TOPIC+tutorial", "type": "free", "platform": "YouTube"}}
            ]
        }}
    ],
    "roadmap": {{
        "phases": [
            {{
                "name": "Phase name",
                "weeks": "1-2",
                "focus": "What to focus on",
                "milestones": ["milestone1", "milestone2"]
            }}
        ]
    }},
    "schedule": {{
        "daily_plan": "Description of ideal daily learning schedule considering the student's routine",
        "weekly_structure": "How weeks are organized",
        "tips": ["study tip 1", "study tip 2"]
    }},
    "resources": {{
        "free": [
            {{"name": "Resource name", "url": "https://www.youtube.com/results?search_query=TOPIC+tutorial", "platform": "YouTube", "description": "Brief desc"}},
            {{"name": "Resource name", "url": "https://www.freecodecamp.org/news/search/?query=TOPIC", "platform": "freeCodeCamp", "description": "Brief desc"}}
        ],
        "paid": []
    }}
}}

IMPORTANT - RESOURCE URL RULES (follow strictly):
- Create at least {duration_weeks * 5} individual topics spread across the weeks
- Consider the student's educational background and adjust complexity
- Consider their hobbies and daily routine when suggesting study times
- Make topics progressive - build on previous knowledge
- Return ONLY valid JSON, no markdown code blocks or extra text
- ALL resources must be FREE and accessible WITHOUT any login or account
- NEVER invent or guess a specific article/course URL - they may not exist
- ONLY use these approved URL patterns (replace TOPIC with url-encoded topic keywords):
  * YouTube search: https://www.youtube.com/results?search_query=TOPIC+tutorial
  * freeCodeCamp search: https://www.freecodecamp.org/news/search/?query=TOPIC
  * W3Schools (for web/programming): https://www.w3schools.com/LANGUAGE/ (e.g. /python/, /js/, /sql/)
  * MDN Web Docs: https://developer.mozilla.org/en-US/search?q=TOPIC
  * MIT OpenCourseWare: https://ocw.mit.edu/search/?q=TOPIC
  * GeeksforGeeks: https://www.geeksforgeeks.org/TOPIC/ (use main topic page only)
  * Wikipedia: https://en.wikipedia.org/wiki/TOPIC
  * GitHub search: https://github.com/search?q=TOPIC+tutorial
  * The Odin Project: https://www.theodinproject.com/ (homepage only)
  * CS50 Harvard: https://cs50.harvard.edu/ (homepage only)
  * Khan Academy: https://www.khanacademy.org/search?page_search_query=TOPIC
- Do NOT include any paid platforms (Udemy, Coursera, DataCamp, Pluralsight, LinkedIn Learning)
- Each topic should have 1-2 resource links using the above patterns
"""

    try:
        text = _chat(prompt, max_tokens=8192, temperature=0.7)
        return _parse_json(text)
    except json.JSONDecodeError as e:
        return {
            "error": f"Failed to parse AI response: {str(e)}",
            "raw_response": text[:500] if 'text' in dir() else "",
        }
    except Exception as e:
        return {"error": f"AI service error: {str(e)}"}


async def generate_practice_questions(
    subject: str,
    topic_title: str,
    level: str,
    course_context: str = "",
) -> dict:
    """Generate 10 practice questions for a specific topic."""

    prompt = f"""You are an expert educator. Generate exactly 10 practice questions for the following:

**Subject:** {subject}
**Topic:** {topic_title}
**Level:** {level}
**Course Context:** {course_context or 'General'}

Generate a JSON response with this EXACT structure:
{{
    "questions": [
        {{
            "id": 1,
            "question": "The question text",
            "type": "mcq",
            "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
            "correct_answer": "A) Option 1",
            "explanation": "Brief explanation of why this is correct"
        }}
    ]
}}

RULES:
- Generate exactly 10 questions
- Mix of MCQ (8 questions) and short answer (2 questions)
- For short answer questions, set type to "short_answer" and options to empty array []
- Questions should test understanding, not just memorization
- Progress from easy to hard
- Return ONLY valid JSON, no markdown code blocks or extra text
"""

    try:
        text = _chat(prompt, max_tokens=4096, temperature=0.7)
        return _parse_json(text)
    except Exception as e:
        return {"error": f"AI service error: {str(e)}", "questions": []}


async def evaluate_answers(
    questions: list,
    user_answers: list,
) -> dict:
    """Evaluate user's answers using Groq AI."""

    prompt = f"""You are an expert educator evaluating student answers. 

Here are the questions and the student's answers:

{json.dumps([{
    "question": q.get("question", ""),
    "correct_answer": q.get("correct_answer", ""),
    "student_answer": user_answers[i] if i < len(user_answers) else "",
    "type": q.get("type", "mcq")
} for i, q in enumerate(questions)], indent=2)}

Evaluate each answer and return a JSON response:
{{
    "results": [
        {{
            "question_id": 1,
            "is_correct": true,
            "feedback": "Brief feedback"
        }}
    ],
    "total_correct": 7,
    "score": 70.0,
    "overall_feedback": "Overall performance feedback and suggestions"
}}

For MCQ: Compare exact option match
For short answers: Use semantic understanding, be lenient with minor variations
Return ONLY valid JSON, no markdown code blocks
"""

    try:
        text = _chat(prompt, max_tokens=4096, temperature=0.3)
        return _parse_json(text)
    except:
        # Fallback: simple matching
        correct = 0
        results = []
        for i, q in enumerate(questions):
            ans = user_answers[i] if i < len(user_answers) else ""
            is_correct = ans.strip().lower() == q.get("correct_answer", "").strip().lower()
            if is_correct:
                correct += 1
            results.append({
                "question_id": i + 1,
                "is_correct": is_correct,
                "feedback": "Correct!" if is_correct else f"Incorrect. The correct answer is: {q.get('correct_answer', '')}"
            })
        return {
            "results": results,
            "total_correct": correct,
            "score": (correct / len(questions)) * 100 if questions else 0,
            "overall_feedback": f"You got {correct}/{len(questions)} correct."
        }


async def ai_chat(
    message: str,
    user_profile: dict,
    course_context: str = "",
) -> str:
    """General AI chat for course-related queries."""

    prompt = f"""You are CurriForge AI, an intelligent learning assistant. You help students with their learning journey.

**Student Profile:**
- Name: {user_profile.get('name', 'Student')}
- Educational Background: {user_profile.get('educational_qualification', 'Not specified')}
- Interests: {user_profile.get('educational_interests', 'Not specified')}

**Course Context:** {course_context or 'General query - no specific course selected'}

**Student's Question:** {message}

Provide a helpful, encouraging, and detailed response. If the student asks about their planner, give specific actionable advice. If they ask about a course topic, explain it clearly. Keep the response concise but thorough. Use markdown formatting for readability.

If the student seems to be asking about enrolling in a new course, suggest they use the "Enroll New Course" feature and mention what information would help create the best curriculum for them.
"""

    try:
        return _chat(prompt, max_tokens=2048, temperature=0.7)
    except Exception as e:
        return f"I'm sorry, I encountered an error: {str(e)}. Please try again."
