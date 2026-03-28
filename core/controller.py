"""
INDECLOW by AxeroAI
🎛️ Controller — Orchestrates the full multi-agent build pipeline
"""

import asyncio
from pathlib import Path
from typing import Optional, Callable

from core.agent_manager import AgentManager
from utils.file_utils import create_project_dir, zip_project, list_project_files
from utils.logger import logger


class BuildSession:
    """Tracks state for one user's active build."""

    def __init__(self, chat_id: str):
        self.chat_id = chat_id
        self.state = "idle"          # idle | gathering | planning | building | done
        self.requirement_session: Optional[dict] = None
        self.plan: Optional[dict] = None
        self.project_dir: Optional[Path] = None
        self.generated_files: dict = {}
        self.deploy_result: Optional[dict] = None
        self.last_error: Optional[str] = None


class Controller:
    """
    🎛️ Main Controller
    Coordinates all agents through the full pipeline:
      Requirement → Plan → Build → Debug → Deploy → Deliver
    """

    def __init__(self, agents: AgentManager):
        self.agents = agents
        self.sessions: dict[str, BuildSession] = {}

    # ── Session helpers ──────────────────────────────────────────────────────

    def get_session(self, chat_id: str) -> BuildSession:
        if chat_id not in self.sessions:
            self.sessions[chat_id] = BuildSession(chat_id)
        return self.sessions[chat_id]

    def clear_session(self, chat_id: str) -> None:
        self.sessions.pop(chat_id, None)
        self.agents.requirement.clear_session(chat_id)

    # ── Async progress helper ────────────────────────────────────────────────

    def _make_progress(self, chat_id: str) -> Callable[[str], None]:
        """Returns a sync callback that schedules a Telegram message."""
        comm = self.agents.communication

        def callback(msg: str):
            asyncio.create_task(comm.send_message(chat_id, msg))

        return callback

    # ── Phase 1: Requirement gathering ───────────────────────────────────────

    async def handle_new_request(self, chat_id: str, user_message: str) -> None:
        session = self.get_session(chat_id)
        comm = self.agents.communication

        session.state = "gathering"
        req_session = self.agents.requirement.start_session(chat_id, user_message)
        session.requirement_session = req_session

        await comm.send_message(
            chat_id,
            (
                "🧠 *Requirement Agent activated!*\n\n"
                f"I detected you want to build a *{req_session['project_type'].title()}* project.\n"
                "Before I start building, I need to ask you a few questions.\n"
                f"Total questions: *{len(req_session['questions'])}*\n\n"
                "_Please answer each question — your answers shape the final product._"
            ),
        )
        await asyncio.sleep(0.5)
        await self._send_next_question(chat_id)

    async def _send_next_question(self, chat_id: str) -> None:
        comm = self.agents.communication
        result = self.agents.requirement.get_next_question(chat_id)
        if result:
            question, q_num, total = result
            await comm.send_question(chat_id, question, q_num, total)
        else:
            await self._finalize_requirements(chat_id)

    async def handle_answer(self, chat_id: str, answer: str) -> None:
        session = self.get_session(chat_id)
        if session.state != "gathering":
            return

        recorded = self.agents.requirement.record_answer(chat_id, answer)
        if not recorded:
            return

        if self.agents.requirement.is_complete(chat_id):
            await self._finalize_requirements(chat_id)
        else:
            await self._send_next_question(chat_id)

    async def _finalize_requirements(self, chat_id: str) -> None:
        comm = self.agents.communication
        req_data = self.agents.requirement.finalize(chat_id)
        session = self.get_session(chat_id)
        session.requirement_session = req_data

        await comm.send_message(
            chat_id,
            "✅ *All requirements collected!*\n\n📋 Creating your build plan...",
        )
        await self._run_build_pipeline(chat_id)

    # ── Phase 2–6: Full build pipeline ───────────────────────────────────────

    async def _run_build_pipeline(self, chat_id: str) -> None:
        session = self.get_session(chat_id)
        comm = self.agents.communication
        req_data = session.requirement_session

        if not req_data:
            await comm.send_error(chat_id, "Requirement data missing. Please /start again.")
            return

        # ── Phase 2: Planning ────────────────────────────────────────────────
        session.state = "planning"
        await comm.send_progress(chat_id, "planning", "Planner Agent designing execution plan...")

        plan = self.agents.planner.create_plan(
            req_data.get("requirement_document", ""),
            req_data,
        )
        session.plan = plan
        plan_msg = self.agents.planner.format_plan_message(plan)
        await comm.send_plan(chat_id, plan_msg)
        await asyncio.sleep(1)

        # ── Phase 3: Build ───────────────────────────────────────────────────
        session.state = "building"
        project_title = plan.get("project_title", "INDECLOW Project")
        await comm.send_build_started(chat_id)

        project_dir = create_project_dir(plan.get("project_name", "indeclow-project"))
        session.project_dir = project_dir

        progress = self._make_progress(chat_id)

        # Inject active skill instructions into developer context
        skill_context = self.agents.skill.get_active_instructions()
        if skill_context:
            req_data["skill_context"] = skill_context

        generated_files = self.agents.developer.generate_project(
            plan=plan,
            requirements=req_data,
            project_dir=project_dir,
            progress_callback=progress,
        )
        session.generated_files = generated_files

        await comm.send_message(
            chat_id,
            f"🏗️ *Code generation complete!*\n📁 {len(generated_files)} files created.",
        )

        # ── Phase 4: Debug ───────────────────────────────────────────────────
        await comm.send_progress(chat_id, "debug", "Debug Agent scanning for issues...")

        debug_results = self.agents.debug.debug_project(project_dir, progress_callback=progress)
        debug_report = self.agents.debug.format_debug_report(debug_results)
        await comm.send_message(chat_id, debug_report)

        # ── Phase 5: Deploy ──────────────────────────────────────────────────
        await comm.send_progress(chat_id, "deploy", "Deployment Agent starting live preview...")

        deploy_result = self.agents.deployment.deploy(project_dir, progress_callback=progress)
        session.deploy_result = deploy_result
        preview_url = deploy_result.get("public_url") or deploy_result.get("local_url", "N/A")

        # ── Phase 6: Deliver ─────────────────────────────────────────────────
        await comm.send_build_complete(
            chat_id,
            project_name=project_title,
            preview_url=preview_url,
            files_count=len(generated_files),
        )

        # Send ZIP
        await comm.send_progress(chat_id, "zip", "Packaging project as ZIP...")
        zip_path = zip_project(project_dir)
        if zip_path:
            await comm.send_document(
                chat_id,
                str(zip_path),
                caption=f"📦 {project_title} — Generated by INDECLOW by AxeroAI",
            )
        else:
            await comm.send_message(chat_id, "⚠️ Could not create ZIP. Files are saved on server.")

        # Send file tree
        file_tree = "\n".join(f"  📄 {f}" for f in list_project_files(project_dir))
        await comm.send_message(
            chat_id,
            f"📁 *Project Files:*\n```\n{file_tree}\n```\n\n"
            f"_Use /update to modify anything. Use /skill to add new capabilities._",
        )

        session.state = "done"
        logger.info(f"Build pipeline complete for {chat_id}: {project_dir}")

    # ── Update request ────────────────────────────────────────────────────────

    async def handle_update(self, chat_id: str, update_request: str) -> None:
        session = self.get_session(chat_id)
        comm = self.agents.communication

        if not session.project_dir or not session.project_dir.exists():
            await comm.send_error(
                chat_id,
                "No active project found. Please build a project first with /start.",
            )
            return

        await comm.send_message(
            chat_id,
            f"🔄 *Update Agent activated*\nApplying: _{update_request}_",
        )

        progress = self._make_progress(chat_id)
        result = self.agents.update.apply_update(
            session.project_dir, update_request, progress_callback=progress
        )

        if result["success"]:
            await comm.send_message(
                chat_id,
                f"✅ *Update applied!*\nModified: `{result['file']}`\n\n"
                "_Use /deploy to refresh your live preview._",
            )
        else:
            await comm.send_error(
                chat_id, result.get("error", "Update failed."), recoverable=True
            )

    # ── Skill install ─────────────────────────────────────────────────────────

    async def handle_skill_install(self, chat_id: str, repo_url: str) -> None:
        comm = self.agents.communication

        await comm.send_message(
            chat_id,
            f"🧩 *Skill Agent activated*\nInstalling from: `{repo_url}`",
        )

        progress = self._make_progress(chat_id)
        skill = self.agents.skill.install(repo_url, progress_callback=progress)

        if skill:
            await comm.send_message(
                chat_id,
                f"🎉 *Skill Installed!*\n\n"
                f"🧩 Name: `{skill.name}`\n"
                f"📝 {skill.description}\n\n"
                "_This skill is now active for all future builds._",
            )
        else:
            await comm.send_error(
                chat_id,
                "Skill installation failed. Check the GitHub URL and try again.",
                recoverable=True,
            )

    # ── Re-deploy ─────────────────────────────────────────────────────────────

    async def handle_redeploy(self, chat_id: str) -> None:
        session = self.get_session(chat_id)
        comm = self.agents.communication

        if not session.project_dir:
            await comm.send_error(chat_id, "No project to deploy. Build one first with /start.")
            return

        await comm.send_progress(chat_id, "deploy", "Re-deploying project...")
        progress = self._make_progress(chat_id)
        result = self.agents.deployment.deploy(session.project_dir, progress_callback=progress)
        session.deploy_result = result
        msg = self.agents.deployment.format_deploy_message(
            result, session.plan.get("project_title", "Project") if session.plan else "Project"
        )
        await comm.send_message(chat_id, msg)

    # ── Status ────────────────────────────────────────────────────────────────

    async def handle_status(self, chat_id: str) -> None:
        session = self.get_session(chat_id)
        comm = self.agents.communication

        state_icons = {
            "idle": "💤", "gathering": "🧠", "planning": "📋",
            "building": "🏗️", "done": "✅",
        }
        icon = state_icons.get(session.state, "❓")

        lines = [f"{icon} *Status: {session.state.upper()}*\n"]

        if session.plan:
            lines.append(f"📦 Project: {session.plan.get('project_title', 'N/A')}")
        if session.project_dir:
            file_count = len(list(session.project_dir.rglob("*")))
            lines.append(f"📁 Files: {file_count}")
        if session.deploy_result:
            url = session.deploy_result.get("public_url") or session.deploy_result.get("local_url")
            if url:
                lines.append(f"🌐 Preview: {url}")

        skills = self.agents.skill.list_skills()
        if skills:
            active = [s["name"] for s in skills if s["active"]]
            lines.append(f"🧩 Active Skills: {', '.join(active) or 'none'}")

        await comm.send_message(chat_id, "\n".join(lines))

    # ── Logs ──────────────────────────────────────────────────────────────────

    async def handle_logs(self, chat_id: str) -> None:
        comm = self.agents.communication
        log = self.agents.terminal.get_log()
        if not log:
            await comm.send_message(chat_id, "📄 No terminal commands executed yet.")
            return
        lines = ["📋 *Terminal Log (last 10)*\n"]
        for entry in log[-10:]:
            rc = "✅" if entry["returncode"] == 0 else "❌"
            lines.append(f"{rc} `{entry['command'][:60]}`")
            if entry.get("stderr"):
                lines.append(f"   ↳ {entry['stderr'][:100]}")
        await comm.send_message(chat_id, "\n".join(lines))
