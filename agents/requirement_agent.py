"""
INDECLOW by AxeroAI
🧠 Requirement Agent — Gathers all requirements before building
"""

import json
from typing import Dict, List, Optional, Tuple
from utils.ollama_client import ollama
from utils.logger import logger


PROJECT_TEMPLATES = {
    "portfolio": {
        "questions": [
            "What is your full name?",
            "What is your profession/title? (e.g. Full-Stack Developer, Designer)",
            "What sections do you want? (e.g. About, Projects, Skills, Contact)",
            "What color theme do you prefer? (e.g. dark, light, blue/white, minimal)",
            "Do you want animations and smooth scroll effects? (yes/no)",
            "Do you want a contact form? (yes/no)",
            "Any reference website URL for style inspiration?",
            "Do you want it responsive for mobile? (yes/no)",
        ],
        "keywords": ["portfolio", "personal site", "resume", "cv", "my website"],
    },
    "ecommerce": {
        "questions": [
            "What is the name of your store?",
            "What products will you sell? (brief description)",
            "Do you need a shopping cart and checkout flow?",
            "Do you need user login/registration?",
            "What payment methods? (Stripe, PayPal, COD, etc.)",
            "Do you need an admin dashboard?",
            "What technology stack? (React, plain HTML, etc.)",
            "Any color/branding preferences?",
        ],
        "keywords": ["ecommerce", "shop", "store", "sell", "products", "cart"],
    },
    "landing": {
        "questions": [
            "What is the product/service name?",
            "What is the main goal of the page? (signups, sales, awareness)",
            "What sections do you need? (Hero, Features, Pricing, Testimonials, CTA)",
            "What is your brand color palette?",
            "Do you want a countdown timer or special offer section?",
            "Do you need an email signup form?",
            "Any specific fonts or style vibe? (modern, corporate, playful)",
        ],
        "keywords": ["landing", "launch", "product page", "promo", "coming soon"],
    },
    "dashboard": {
        "questions": [
            "What is the dashboard for? (analytics, admin, monitoring, etc.)",
            "What data/metrics will be displayed?",
            "Do you need charts and graphs? What types?",
            "Do you need authentication/login?",
            "What is the tech stack? (React, plain HTML+JS, Vue)",
            "Light or dark theme?",
            "Will there be real data or mock/static data for now?",
        ],
        "keywords": ["dashboard", "admin", "panel", "analytics", "monitor", "metrics"],
    },
    "api": {
        "questions": [
            "What does this API do?",
            "What endpoints/routes do you need?",
            "What data models/schemas are required?",
            "Do you need authentication? (JWT, API key, OAuth)",
            "What database? (SQLite, PostgreSQL, MongoDB, in-memory)",
            "What framework? (FastAPI, Flask, Express, etc.)",
            "Do you need CORS support?",
            "Do you need API documentation auto-generation?",
        ],
        "keywords": ["api", "rest", "backend", "server", "endpoint", "fastapi", "flask"],
    },
    "general": {
        "questions": [
            "Can you describe exactly what you want to build?",
            "What is the main purpose/goal of this project?",
            "Who is the target user?",
            "What technology stack do you prefer? (or should I choose?)",
            "Any specific design style or color preferences?",
            "Are there any existing systems this needs to integrate with?",
            "What is the timeline/urgency?",
        ],
        "keywords": [],
    },
}


class RequirementAgent:
    """
    🧠 Requirement Agent
    Detects project type, asks all necessary questions,
    and returns a structured requirement document.
    """

    def __init__(self):
        self.sessions: Dict[str, dict] = {}

    def detect_project_type(self, user_message: str) -> str:
        msg = user_message.lower()
        for ptype, data in PROJECT_TEMPLATES.items():
            if ptype == "general":
                continue
            for kw in data["keywords"]:
                if kw in msg:
                    return ptype
        return "general"

    def start_session(self, chat_id: str, user_message: str) -> dict:
        ptype = self.detect_project_type(user_message)
        template = PROJECT_TEMPLATES[ptype]

        session = {
            "chat_id": chat_id,
            "project_type": ptype,
            "original_request": user_message,
            "questions": list(template["questions"]),
            "answers": {},
            "current_q_index": 0,
            "status": "gathering",
            "extra_questions": [],
        }

        # Ask Ollama to generate 2-3 additional context-specific questions
        try:
            extra = self._generate_extra_questions(user_message, ptype)
            session["extra_questions"] = extra
            session["questions"].extend(extra)
        except Exception as e:
            logger.warning(f"Extra questions generation failed: {e}")

        self.sessions[chat_id] = session
        logger.info(f"Started requirement session for {chat_id}: type={ptype}")
        return session

    def _generate_extra_questions(self, request: str, ptype: str) -> List[str]:
        prompt = f"""
A user wants to build a {ptype} project. Their request: "{request}"

Generate exactly 2 additional clarifying questions specific to their request that aren't covered by generic template questions.
Return ONLY a JSON array of question strings, nothing else.
Example: ["Question 1?", "Question 2?"]
"""
        response = ollama.generate(prompt, temperature=0.5)
        try:
            start = response.find("[")
            end = response.rfind("]") + 1
            if start != -1 and end > start:
                return json.loads(response[start:end])
        except Exception:
            pass
        return []

    def get_next_question(self, chat_id: str) -> Optional[Tuple[str, int, int]]:
        session = self.sessions.get(chat_id)
        if not session:
            return None
        idx = session["current_q_index"]
        questions = session["questions"]
        if idx >= len(questions):
            return None
        return questions[idx], idx + 1, len(questions)

    def record_answer(self, chat_id: str, answer: str) -> bool:
        session = self.sessions.get(chat_id)
        if not session:
            return False
        idx = session["current_q_index"]
        q = session["questions"][idx]
        session["answers"][q] = answer
        session["current_q_index"] += 1
        logger.info(f"Recorded answer {idx+1}/{len(session['questions'])} for {chat_id}")
        return True

    def is_complete(self, chat_id: str) -> bool:
        session = self.sessions.get(chat_id)
        if not session:
            return False
        return session["current_q_index"] >= len(session["questions"])

    def finalize(self, chat_id: str) -> Optional[dict]:
        session = self.sessions.get(chat_id)
        if not session:
            return None
        session["status"] = "complete"
        doc = self.build_requirement_document(session)
        session["requirement_document"] = doc
        logger.info(f"Requirements finalized for {chat_id}")
        return session

    def build_requirement_document(self, session: dict) -> str:
        lines = [
            "# 📋 INDECLOW Requirement Document",
            f"\n**Original Request:** {session['original_request']}",
            f"**Project Type:** {session['project_type'].title()}",
            "\n## Requirements\n",
        ]
        for q, a in session["answers"].items():
            lines.append(f"**{q}**\n→ {a}\n")
        return "\n".join(lines)

    def get_session(self, chat_id: str) -> Optional[dict]:
        return self.sessions.get(chat_id)

    def clear_session(self, chat_id: str) -> None:
        self.sessions.pop(chat_id, None)
