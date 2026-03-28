"""
INDECLOW by AxeroAI
🧩 Agent Manager — Central registry and dispatcher
"""

from agents.requirement_agent import RequirementAgent
from agents.planner_agent import PlannerAgent
from agents.developer_agent import DeveloperAgent
from agents.terminal_agent import TerminalAgent
from agents.debug_agent import DebugAgent
from agents.deployment_agent import DeploymentAgent
from agents.communication_agent import CommunicationAgent
from agents.skill_agent import SkillAgent
from agents.update_agent import UpdateAgent
from utils.logger import logger


class AgentManager:
    """
    Central registry that instantiates and provides access to all INDECLOW agents.
    All agents are singletons shared across the entire session.
    """

    def __init__(self):
        logger.info("🧩 Initializing Agent Manager...")

        self.requirement  = RequirementAgent()
        self.planner      = PlannerAgent()
        self.developer    = DeveloperAgent()
        self.terminal     = TerminalAgent()
        self.debug        = DebugAgent()
        self.deployment   = DeploymentAgent()
        self.communication = CommunicationAgent()
        self.skill        = SkillAgent()
        self.update       = UpdateAgent()

        self._registry = {
            "requirement":    self.requirement,
            "planner":        self.planner,
            "developer":      self.developer,
            "terminal":       self.terminal,
            "debug":          self.debug,
            "deployment":     self.deployment,
            "communication":  self.communication,
            "skill":          self.skill,
            "update":         self.update,
        }

        logger.info(f"✅ {len(self._registry)} agents ready")

    def get(self, name: str):
        agent = self._registry.get(name)
        if not agent:
            raise KeyError(f"Unknown agent: '{name}'")
        return agent

    def set_bot(self, bot) -> None:
        """Inject the Telegram bot instance into the Communication Agent."""
        self.communication.set_bot(bot)

    def shutdown(self) -> None:
        """Graceful shutdown — stop all deployment servers."""
        try:
            self.deployment.stop_all()
        except Exception as e:
            logger.error(f"Shutdown error: {e}")
        logger.info("Agent Manager shut down.")
