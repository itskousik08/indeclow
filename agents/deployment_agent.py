"""
INDECLOW by AxeroAI
🌐 Deployment Agent — Live preview via ngrok + Python HTTP server
"""

import time
import threading
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from config import NGROK_AUTH_TOKEN
from utils.logger import logger


class DeploymentAgent:
    """
    🌐 Deployment Agent
    Starts a local HTTP server for the project and creates
    a public URL using ngrok for live preview.
    """

    def __init__(self):
        self.active_servers: dict = {}
        self.active_tunnels: dict = {}
        self._port_counter = 8100

    def _next_port(self) -> int:
        self._port_counter += 1
        return self._port_counter

    def start_server(self, project_dir: Path, port: Optional[int] = None) -> Tuple[bool, int, Optional[subprocess.Popen]]:
        if port is None:
            port = self._next_port()

        try:
            process = subprocess.Popen(
                ["python3", "-m", "http.server", str(port)],
                cwd=str(project_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            time.sleep(1.5)  # Let server start

            if process.poll() is None:
                self.active_servers[port] = process
                logger.info(f"HTTP server started on port {port} for {project_dir}")
                return True, port, process
            else:
                return False, port, None

        except Exception as e:
            logger.error(f"Failed to start HTTP server: {e}")
            return False, port, None

    def create_ngrok_tunnel(self, port: int) -> Optional[str]:
        """Create ngrok tunnel and return public URL."""
        if not NGROK_AUTH_TOKEN:
            logger.warning("NGROK_AUTH_TOKEN not set — using local URL only")
            return None

        try:
            from pyngrok import ngrok, conf

            conf.get_default().auth_token = NGROK_AUTH_TOKEN
            tunnel = ngrok.connect(port, "http")
            public_url = tunnel.public_url

            if public_url.startswith("http://"):
                public_url = public_url.replace("http://", "https://")

            self.active_tunnels[port] = tunnel
            logger.info(f"ngrok tunnel created: {public_url}")
            return public_url

        except ImportError:
            logger.warning("pyngrok not installed — run: pip install pyngrok")
            return None
        except Exception as e:
            logger.error(f"ngrok tunnel failed: {e}")
            return None

    def deploy(self, project_dir: Path, progress_callback=None) -> dict:
        """Full deployment: start server + create tunnel."""
        result = {
            "success": False,
            "local_url": None,
            "public_url": None,
            "port": None,
            "error": None,
        }

        if progress_callback:
            progress_callback("🌐 Starting HTTP server...")

        ok, port, proc = self.start_server(project_dir)
        if not ok:
            result["error"] = "Failed to start HTTP server"
            return result

        result["port"] = port
        result["local_url"] = f"http://localhost:{port}"

        if progress_callback:
            progress_callback(f"✅ Server running on port {port}")
            progress_callback("🔗 Creating public URL via ngrok...")

        public_url = self.create_ngrok_tunnel(port)

        if public_url:
            result["public_url"] = public_url
            result["success"] = True
            if progress_callback:
                progress_callback(f"🌍 Public URL: {public_url}")
        else:
            result["public_url"] = result["local_url"]
            result["success"] = True
            if progress_callback:
                progress_callback(f"📡 Local preview: {result['local_url']}")
                progress_callback("⚠️ Set NGROK_AUTH_TOKEN in .env for a public URL")

        return result

    def stop_server(self, port: int) -> bool:
        proc = self.active_servers.get(port)
        if proc:
            proc.terminate()
            del self.active_servers[port]
            logger.info(f"Stopped server on port {port}")

        tunnel = self.active_tunnels.get(port)
        if tunnel:
            try:
                from pyngrok import ngrok
                ngrok.disconnect(tunnel.public_url)
            except Exception:
                pass
            del self.active_tunnels[port]

        return True

    def stop_all(self) -> None:
        for port in list(self.active_servers.keys()):
            self.stop_server(port)
        try:
            from pyngrok import ngrok
            ngrok.kill()
        except Exception:
            pass
        logger.info("All deployment servers stopped")

    def format_deploy_message(self, result: dict, project_name: str = "Project") -> str:
        if not result["success"]:
            return f"❌ Deployment failed: {result.get('error', 'Unknown error')}"

        lines = [
            f"🎉 **{project_name} is LIVE!**\n",
            f"🌐 **Preview URL:** {result['public_url']}",
            f"💻 **Local URL:** {result['local_url']}",
            f"📡 **Port:** {result['port']}",
            "\n_Powered by INDECLOW — AxeroAI_",
        ]
        return "\n".join(lines)
