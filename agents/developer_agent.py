"""
INDECLOW by AxeroAI
🎨 Developer Agent — Generates complete, production-grade code
"""

from pathlib import Path
from typing import Dict, Optional
from utils.ollama_client import ollama
from utils.file_utils import save_file, extract_code_blocks, save_project_manifest
from utils.logger import logger


class DeveloperAgent:
    """
    🎨 Developer Agent
    Generates complete, production-grade HTML/CSS/JS (and more)
    based on the project plan and requirements.
    """

    SYSTEM_PROMPT = """You are INDECLOW, an expert frontend and backend developer by AxeroAI.

Generate COMPLETE, production-grade, visually stunning code.

RULES:
- Write the FULL code. Never truncate. Never use placeholder comments.
- For HTML: include <!DOCTYPE html>, meta tags, linked CSS and JS
- For CSS: use CSS variables, flexbox/grid, smooth transitions, responsive media queries
- For JS: use modern ES6+, clean functions, proper event listeners
- Create visually stunning designs — avoid generic/boring layouts
- Use Google Fonts (via CDN) for beautiful typography
- Every page must be fully mobile responsive
- Include smooth animations and hover effects
- Code must work immediately when opened in a browser

FILE FORMAT (use exactly this format for each file):
## File: `filename.ext`
```html
// filename.ext
<full code here>
```

Generate ALL files needed. Do not skip any file from the plan.
"""

    def generate_project(
        self,
        plan: dict,
        requirements: dict,
        project_dir: Path,
        progress_callback=None,
    ) -> Dict[str, Path]:
        generated_files = {}
        req_doc = requirements.get("requirement_document", "")
        answers = requirements.get("answers", {})
        ptype = requirements.get("project_type", "general")

        prompt = self._build_generation_prompt(plan, req_doc, answers, ptype)

        if progress_callback:
            progress_callback("🎨 Developer Agent generating code...")

        logger.info("Developer Agent generating project code...")
        response = ollama.generate(prompt, system=self.SYSTEM_PROMPT, temperature=0.6)

        code_blocks = extract_code_blocks(response)

        if not code_blocks:
            logger.warning("No code blocks found, using fallback generator")
            code_blocks = self._fallback_generate(plan, answers, ptype)

        for filename, code in code_blocks.items():
            file_path = project_dir / filename
            if save_file(file_path, code):
                generated_files[filename] = file_path
                if progress_callback:
                    progress_callback(f"✅ Generated: `{filename}`")

        save_project_manifest(project_dir, {
            "project_name": plan.get("project_name", "indeclow-project"),
            "project_title": plan.get("project_title", "Project"),
            "tech_stack": plan.get("tech_stack", []),
            "files_generated": list(generated_files.keys()),
            "requirements": answers,
        })

        logger.info(f"Generated {len(generated_files)} files in {project_dir}")
        return generated_files

    def _build_generation_prompt(self, plan: dict, req_doc: str,
                                  answers: dict, ptype: str) -> str:
        files_needed = ", ".join(plan.get("estimated_files", ["index.html", "style.css", "script.js"]))
        steps_desc = "\n".join(
            f"- Step {s['step_id']}: {s['title']} — {s['description']}"
            for s in plan.get("steps", [])
            if s.get("agent") == "developer"
        )

        answers_formatted = "\n".join(
            f"  {q}: {a}" for q, a in answers.items()
        )

        return f"""
Build a complete {ptype} project with these requirements:

{req_doc}

User's Answers:
{answers_formatted}

Files to generate: {files_needed}

Build steps:
{steps_desc}

Generate ALL files listed above as complete, production-ready code.
Make it visually impressive, modern, and fully functional.
"""

    def _fallback_generate(self, plan: dict, answers: dict, ptype: str) -> Dict[str, str]:
        """Emergency fallback: generate a basic but working project."""
        name = next(iter(answers.values()), "Project") if answers else "Project"
        color = "#6c63ff"
        for q, a in answers.items():
            if "color" in q.lower():
                color = a if a.startswith("#") else color

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name}</title>
    <link rel="stylesheet" href="style.css">
    <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <nav class="navbar">
        <div class="nav-logo">{name}</div>
        <ul class="nav-links">
            <li><a href="#about">About</a></li>
            <li><a href="#work">Work</a></li>
            <li><a href="#contact">Contact</a></li>
        </ul>
    </nav>
    <section class="hero" id="home">
        <div class="hero-content">
            <h1>Hello, I'm <span class="highlight">{name}</span></h1>
            <p>Building things that matter.</p>
            <a href="#contact" class="btn">Get in Touch</a>
        </div>
    </section>
    <section class="about" id="about">
        <div class="container">
            <h2>About Me</h2>
            <p>I'm a passionate creator dedicated to crafting exceptional digital experiences.</p>
        </div>
    </section>
    <section class="contact" id="contact">
        <div class="container">
            <h2>Contact</h2>
            <form class="contact-form">
                <input type="text" placeholder="Your Name" required>
                <input type="email" placeholder="Your Email" required>
                <textarea placeholder="Your Message" rows="5" required></textarea>
                <button type="submit" class="btn">Send Message</button>
            </form>
        </div>
    </section>
    <footer>
        <p>Built with ❤️ by INDECLOW — AxeroAI</p>
    </footer>
    <script src="script.js"></script>
</body>
</html>"""

        css = f""":root {{
    --primary: {color};
    --dark: #0f0f0f;
    --light: #f9f9f9;
    --text: #333;
    --radius: 12px;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{ font-family: 'Space Grotesk', sans-serif; color: var(--text); background: var(--light); }}
.navbar {{ position: fixed; top: 0; width: 100%; display: flex; justify-content: space-between; align-items: center; padding: 1.2rem 5%; background: rgba(255,255,255,0.95); backdrop-filter: blur(12px); z-index: 999; box-shadow: 0 2px 20px rgba(0,0,0,0.08); }}
.nav-logo {{ font-size: 1.4rem; font-weight: 700; color: var(--primary); }}
.nav-links {{ list-style: none; display: flex; gap: 2rem; }}
.nav-links a {{ text-decoration: none; color: var(--text); font-weight: 500; transition: color 0.3s; }}
.nav-links a:hover {{ color: var(--primary); }}
.hero {{ min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, var(--dark) 0%, #1a1a2e 100%); color: white; text-align: center; padding: 2rem; }}
.hero-content {{ max-width: 700px; }}
.hero h1 {{ font-size: clamp(2.5rem, 6vw, 5rem); font-weight: 700; line-height: 1.1; margin-bottom: 1.5rem; }}
.highlight {{ color: var(--primary); }}
.hero p {{ font-size: 1.3rem; opacity: 0.8; margin-bottom: 2.5rem; }}
.btn {{ display: inline-block; padding: 1rem 2.5rem; background: var(--primary); color: white; border-radius: 50px; text-decoration: none; font-weight: 600; border: none; cursor: pointer; font-size: 1rem; transition: transform 0.3s, box-shadow 0.3s; }}
.btn:hover {{ transform: translateY(-3px); box-shadow: 0 10px 30px rgba(108,99,255,0.4); }}
.container {{ max-width: 900px; margin: 0 auto; padding: 5rem 2rem; }}
.about h2, .contact h2 {{ font-size: 2.5rem; font-weight: 700; margin-bottom: 1.5rem; color: var(--dark); }}
.contact-form {{ display: flex; flex-direction: column; gap: 1rem; max-width: 500px; }}
.contact-form input, .contact-form textarea {{ padding: 1rem; border: 2px solid #e0e0e0; border-radius: var(--radius); font-family: inherit; font-size: 1rem; transition: border-color 0.3s; }}
.contact-form input:focus, .contact-form textarea:focus {{ outline: none; border-color: var(--primary); }}
footer {{ background: var(--dark); color: rgba(255,255,255,0.6); text-align: center; padding: 2rem; }}
@media (max-width: 768px) {{ .nav-links {{ display: none; }} .hero h1 {{ font-size: 2.5rem; }} }}"""

        js = """document.addEventListener('DOMContentLoaded', () => {
    // Smooth reveal on scroll
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('section').forEach(s => {
        s.style.opacity = '0';
        s.style.transform = 'translateY(30px)';
        s.style.transition = 'opacity 0.7s ease, transform 0.7s ease';
        observer.observe(s);
    });

    // Contact form
    const form = document.querySelector('.contact-form');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            alert('Message sent! Thank you.');
            form.reset();
        });
    }
});"""

        return {
            "index.html": html,
            "style.css": css,
            "script.js": js,
        }

    def generate_single_file(
        self, filename: str, description: str, context: str = ""
    ) -> str:
        prompt = f"""
Generate a complete {filename} file.
Purpose: {description}
Context: {context}

Return ONLY the complete file contents, no explanation.
"""
        return ollama.generate(prompt, system=self.SYSTEM_PROMPT, temperature=0.6)
