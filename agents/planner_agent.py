"""
INDECLOW by AxeroAI
📋 Planner Agent — Converts requirements into step-by-step execution plans
"""

import json
from typing import List, Dict, Optional
from utils.ollama_client import ollama
from utils.logger import logger


class PlanStep:
    def __init__(self, step_id: int, title: str, description: str,
                 agent: str, files: List[str] = None, depends_on: List[int] = None):
        self.step_id = step_id
        self.title = title
        self.description = description
        self.agent = agent
        self.files = files or []
        self.depends_on = depends_on or []
        self.status = "pending"  # pending | in_progress | done | failed

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "title": self.title,
            "description": self.description,
            "agent": self.agent,
            "files": self.files,
            "depends_on": self.depends_on,
            "status": self.status,
        }


class PlannerAgent:
    """
    📋 Planner Agent
    Takes a completed requirement document and generates
    a structured, ordered execution plan with agent assignments.
    """

    SYSTEM_PROMPT = """You are a software project planner for INDECLOW by AxeroAI.
Given a requirement document, you produce a detailed, step-by-step build plan.

Return ONLY valid JSON with this exact structure:
{
  "project_name": "slug-name",
  "project_title": "Human Readable Title",
  "tech_stack": ["html", "css", "js"],
  "estimated_files": ["index.html", "style.css", "script.js"],
  "steps": [
    {
      "step_id": 1,
      "title": "Step Title",
      "description": "Detailed description of what to do",
      "agent": "developer",
      "files": ["index.html"],
      "depends_on": []
    }
  ]
}

Agent types: developer, terminal, debug, deployment
Always include a final "deployment" step.
Generate complete, logical steps that cover the full build.
"""

    def create_plan(self, requirement_document: str, session: dict) -> Optional[dict]:
        prompt = f"""
Requirement Document:
{requirement_document}

Project Type: {session.get('project_type', 'general')}

Create a complete execution plan for this project.
"""
        logger.info("Planner Agent generating execution plan...")
        response = ollama.generate(prompt, system=self.SYSTEM_PROMPT, temperature=0.3)

        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end > start:
                plan_data = json.loads(response[start:end])
                logger.info(
                    f"Plan created: {len(plan_data.get('steps', []))} steps, "
                    f"stack: {plan_data.get('tech_stack')}"
                )
                return plan_data
        except Exception as e:
            logger.error(f"Plan parsing failed: {e}")

        # Fallback plan
        return self._fallback_plan(session)

    def _fallback_plan(self, session: dict) -> dict:
        ptype = session.get("project_type", "general")
        name = session.get("answers", {}).get(
            next(iter(session.get("answers", {})), ""), "my-project"
        )

        base_steps = [
            {
                "step_id": 1,
                "title": "Create project structure",
                "description": "Set up folder structure and base files",
                "agent": "terminal",
                "files": [],
                "depends_on": [],
            },
            {
                "step_id": 2,
                "title": "Build HTML structure",
                "description": "Create main index.html with semantic markup",
                "agent": "developer",
                "files": ["index.html"],
                "depends_on": [1],
            },
            {
                "step_id": 3,
                "title": "Add CSS styling",
                "description": "Create responsive stylesheet",
                "agent": "developer",
                "files": ["style.css"],
                "depends_on": [2],
            },
            {
                "step_id": 4,
                "title": "Add JavaScript",
                "description": "Add interactivity and functionality",
                "agent": "developer",
                "files": ["script.js"],
                "depends_on": [3],
            },
            {
                "step_id": 5,
                "title": "Debug and validate",
                "description": "Check for errors and validate all code",
                "agent": "debug",
                "files": [],
                "depends_on": [4],
            },
            {
                "step_id": 6,
                "title": "Deploy and generate preview",
                "description": "Start server and generate live preview URL",
                "agent": "deployment",
                "files": [],
                "depends_on": [5],
            },
        ]

        return {
            "project_name": "indeclow-project",
            "project_title": f"INDECLOW — {ptype.title()} Project",
            "tech_stack": ["html", "css", "js"],
            "estimated_files": ["index.html", "style.css", "script.js"],
            "steps": base_steps,
        }

    def format_plan_message(self, plan: dict) -> str:
        lines = [
            f"📋 **Build Plan: {plan.get('project_title', 'Project')}**\n",
            f"🛠️ Stack: {', '.join(plan.get('tech_stack', []))}",
            f"📁 Files: {', '.join(plan.get('estimated_files', []))}",
            f"📌 Steps: {len(plan.get('steps', []))}\n",
        ]
        for step in plan.get("steps", []):
            agent_icons = {
                "developer": "🎨", "terminal": "💻",
                "debug": "🐞", "deployment": "🌐",
            }
            icon = agent_icons.get(step.get("agent", ""), "⚙️")
            lines.append(
                f"{icon} **Step {step['step_id']}**: {step['title']}"
            )
        return "\n".join(lines)
