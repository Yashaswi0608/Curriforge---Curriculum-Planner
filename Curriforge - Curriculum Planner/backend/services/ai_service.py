import json
import google.generativeai as genai
from config import settings

# Configure Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


async def generate_curriculum(
    subject: str,
    level: str,
    reason: str,
    duration_weeks: int,
    daily_hours: float,
    user_profile: dict,
) -> dict:
    """Generate a full personalized curriculum using Gemini AI."""

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
                {{"name": "Resource Name", "url": "https://...", "type": "free/paid", "platform": "YouTube/Coursera/etc"}}
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
            {{"name": "Resource", "url": "https://...", "platform": "Platform name", "description": "Brief desc"}}
        ],
        "paid": [
            {{"name": "Resource", "url": "https://...", "platform": "Platform name", "price": "$XX", "description": "Brief desc"}}
        ]
    }}
}}

IMPORTANT:
- Create at least {duration_weeks * 5} individual topics spread across the weeks
- Each topic should have at least 1-2 real resource links
- Consider the student's educational background and adjust complexity
- Consider their hobbies and daily routine when suggesting study times
- Include links to real free resources (YouTube, freeCodeCamp, Khan Academy, MIT OCW, Coursera, etc.)
- Make topics progressive - build on previous knowledge
- Return ONLY valid JSON, no markdown code blocks or extra text
"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()

        # Clean up response - remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        result = json.loads(text)
        return result
    except json.JSONDecodeError as e:
        # If JSON parsing fails, try to extract JSON from the response
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            result = json.loads(text[start:end])
            return result
        except:
            return {
                "error": f"Failed to parse AI response: {str(e)}",
                "raw_response": text[:500]
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
        response = model.generate_content(prompt)
        text = response.text.strip()

        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        result = json.loads(text)
        return result
    except json.JSONDecodeError:
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            result = json.loads(text[start:end])
            return result
        except:
            return {"error": "Failed to parse practice questions", "questions": []}
    except Exception as e:
        return {"error": f"AI service error: {str(e)}", "questions": []}


async def evaluate_answers(
    questions: list,
    user_answers: list,
) -> dict:
    """Evaluate user's answers using Gemini AI."""

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
        response = model.generate_content(prompt)
        text = response.text.strip()

        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        result = json.loads(text)
        return result
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
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"I'm sorry, I encountered an error: {str(e)}. Please try again."
