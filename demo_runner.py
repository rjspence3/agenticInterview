"""
Narrated Demo Runner for Agentic Interview System.

This script orchestrates a complete demo with voice narration.
It generates narration audio and provides step-by-step instructions
for running with Chrome DevTools MCP.

Usage:
    # Generate all audio first (one-time):
    python demo_runner.py generate

    # Run the narrated demo:
    python demo_runner.py run

    # Run a specific section:
    python demo_runner.py section admin
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from typing import Callable, Optional

from demo_narration import DemoNarrator, DEMO_SEGMENTS


class NarratedDemo:
    """Orchestrates demo with narration and MCP command guidance."""

    def __init__(self):
        self.narrator = DemoNarrator(voice="nova", model="tts-1-hd")
        self.screenshots_dir = Path("demo_screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
        self.step_count = 0

    def narrate(self, segment: str, wait: bool = True) -> None:
        """Play a narration segment."""
        print(f"\n🎙️  Narrating: {segment}")
        self.narrator.say_segment(segment, wait=wait)

    def narrate_text(self, text: str, wait: bool = True) -> None:
        """Narrate custom text."""
        print(f"\n🎙️  Speaking: {text[:50]}...")
        self.narrator.say(text, wait=wait)

    def step(self, description: str) -> None:
        """Display a step for the demo operator."""
        self.step_count += 1
        print(f"\n{'='*60}")
        print(f"📌 STEP {self.step_count}: {description}")
        print(f"{'='*60}")

    def mcp_instruction(self, instruction: str) -> None:
        """Display MCP command instruction."""
        print(f"\n🔧 MCP Command:")
        print(f"   {instruction}")
        print()

    def pause(self, message: str = "Press Enter to continue...") -> None:
        """Pause for operator input."""
        input(f"\n⏸️  {message}")

    def wait(self, seconds: float) -> None:
        """Wait for specified duration."""
        print(f"⏳ Waiting {seconds}s...")
        time.sleep(seconds)

    # =========================================================================
    # Demo Sections
    # =========================================================================

    def run_intro(self) -> None:
        """Run the introduction section."""
        self.step("Introduction")
        self.narrate("intro")

        self.mcp_instruction(
            "Navigate to http://localhost:8501 and take a screenshot"
        )
        self.pause()

    def run_admin_section(self) -> None:
        """Run the Admin Dashboard section."""
        # Admin Overview
        self.step("Admin Dashboard Overview")
        self.narrate("admin_intro")

        self.mcp_instruction(
            'Click on "Admin" in the sidebar. Take a screenshot showing all 4 tabs.'
        )
        self.pause()

        # People Management
        self.step("People Management")
        self.narrate("admin_people")

        self.mcp_instruction("""
In the People Management tab:
1. Fill Name: "Demo Candidate"
2. Fill Email: "demo@example.com"
3. Fill Role: "Software Engineer"
4. Fill Department: "Engineering"
5. Click "Add Person"
6. Take a screenshot
        """)
        self.pause()

        # Template Management
        self.step("Template Management")
        self.narrate("admin_templates")

        self.mcp_instruction(
            'Click "Template Management" tab. Expand a template to show questions. Screenshot.'
        )
        self.pause()

        # Lens Management
        self.step("Lens Management")
        self.narrate("admin_lenses")

        self.mcp_instruction(
            'Click "Lens Management" tab. Expand a lens to show criteria. Screenshot.'
        )
        self.pause()

        # Live Sessions
        self.step("Live Sessions")
        self.narrate("admin_live")

        self.mcp_instruction(
            'Click "Live Sessions" tab. Screenshot (may be empty initially).'
        )
        self.pause()

    def run_interviewer_section(self) -> None:
        """Run the Interviewer View section."""
        self.step("Interviewer View")
        self.narrate("interviewer_intro")

        self.mcp_instruction(
            'Click "Interviewer View" in sidebar. Screenshot the question bank.'
        )
        self.pause()

        self.step("Create New Question")
        self.narrate("interviewer_create")

        self.mcp_instruction("""
In the Add Question form:
1. Question: "Explain the difference between lists and tuples in Python"
2. Competency: "Python"
3. Difficulty: "Easy"
4. Keypoints: "mutable, immutable, brackets, parentheses"
5. Click "Add Question"
6. Screenshot
        """)
        self.pause()

    def run_interview_section(self) -> None:
        """Run the Interview (Chat mode) section."""
        self.step("Start Chat Interview")
        self.narrate("interview_setup")

        self.mcp_instruction("""
1. Click "Interviewee View"
2. Select any Person
3. Select "Python Developer L2" template
4. Select "Chat Interview" mode
5. Click "Start Interview"
6. Screenshot the chat interface
        """)
        self.pause()

        self.step("Chat Interface")
        self.narrate("chat_intro")
        self.wait(2)

        self.step("Answer a Question")
        self.mcp_instruction("""
In the chat input, type:
"Lists are mutable sequences using square brackets. Tuples are immutable using parentheses.
Lists can be modified after creation while tuples cannot. Tuples are more memory efficient."

Press Enter and wait for evaluation. Screenshot the result.
        """)
        self.pause()

        self.narrate("chat_answer")

    def run_raise_hand_section(self) -> None:
        """Run the Raise Hand feature section."""
        self.step("Raise Hand Feature")
        self.narrate("raise_hand_intro")

        self.mcp_instruction(
            'In the active chat interview, click the "🙋 Raise Hand" button. Screenshot.'
        )
        self.pause()

        self.step("Admin Sees Raised Hand")
        self.narrate("raise_hand_admin")

        self.mcp_instruction("""
In a new tab or window:
1. Go to Admin > Live Sessions
2. See the session with "HAND" indicator
3. Click "Join"
4. Screenshot the admin session view
5. Type a message: "Hi! How can I help?"
6. Click Send
7. Screenshot
        """)
        self.pause()

        self.step("Resume Interview")
        self.narrate("raise_hand_resume")

        self.mcp_instruction(
            'Click "Resume & Leave". Check the interviewee view shows resumed status.'
        )
        self.pause()

    def run_reports_section(self) -> None:
        """Run the Reports section."""
        self.step("Reports Dashboard")
        self.narrate("reports_intro")

        self.mcp_instruction(
            'Click "Reports" in sidebar. Screenshot showing session list and analytics.'
        )
        self.pause()

        self.step("Session Detail")
        self.narrate("reports_detail")

        self.mcp_instruction(
            'Click on any completed session. Screenshot showing transcript and evaluations.'
        )
        self.pause()

    def run_conclusion(self) -> None:
        """Run the conclusion."""
        self.step("Conclusion")
        self.narrate("conclusion")
        print("\n✅ Demo complete!")

    # =========================================================================
    # Main Entry Points
    # =========================================================================

    def run_full_demo(self) -> None:
        """Run the complete narrated demo."""
        print("=" * 60)
        print("🎬 AGENTIC INTERVIEW SYSTEM - NARRATED DEMO")
        print("=" * 60)
        print("\nThis demo will guide you through all features with voice narration.")
        print("Make sure you have:")
        print("  ✅ App running: streamlit run app.py --server.port 8501")
        print("  ✅ Chrome with MCP: --remote-debugging-port=9222")
        print("  ✅ Audio enabled")
        print()
        self.pause("Press Enter to begin the demo...")

        try:
            self.run_intro()
            self.run_admin_section()
            self.run_interviewer_section()
            self.run_interview_section()
            self.run_raise_hand_section()
            self.run_reports_section()
            self.run_conclusion()
        except KeyboardInterrupt:
            print("\n\n⏹️  Demo interrupted.")

    def run_section(self, section: str) -> None:
        """Run a specific demo section."""
        sections = {
            "intro": self.run_intro,
            "admin": self.run_admin_section,
            "interviewer": self.run_interviewer_section,
            "interview": self.run_interview_section,
            "raisehand": self.run_raise_hand_section,
            "reports": self.run_reports_section,
            "conclusion": self.run_conclusion,
        }

        if section not in sections:
            print(f"Unknown section: {section}")
            print(f"Available: {', '.join(sections.keys())}")
            return

        sections[section]()

    def generate_audio(self) -> None:
        """Generate all narration audio files."""
        print("Generating demo narration audio...")
        print("This uses OpenAI TTS and may take a minute.\n")
        self.narrator.generate_all_demo_audio()
        print("\n✅ Audio generation complete!")
        print("You can now run: python demo_runner.py run")


def main():
    """Main entry point."""
    demo = NarratedDemo()

    if len(sys.argv) < 2:
        print("Narrated Demo Runner")
        print("-" * 40)
        print("Usage:")
        print("  python demo_runner.py generate  - Generate audio files")
        print("  python demo_runner.py run       - Run full demo")
        print("  python demo_runner.py section <name>  - Run specific section")
        print()
        print("Sections: intro, admin, interviewer, interview, raisehand, reports, conclusion")
        return

    command = sys.argv[1]

    if command == "generate":
        demo.generate_audio()
    elif command == "run":
        demo.run_full_demo()
    elif command == "section":
        if len(sys.argv) < 3:
            print("Please specify a section name")
        else:
            demo.run_section(sys.argv[2])
    elif command == "test":
        # Quick test of narration
        demo.narrate_text("This is a test of the demo narration system. Audio is working correctly.")
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
