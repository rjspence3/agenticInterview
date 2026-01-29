"""
Demo Narration System using OpenAI TTS.

This module provides text-to-speech narration for the Agentic Interview System demo.
Uses OpenAI's TTS API to generate high-quality voice narration.

Usage:
    from demo_narration import DemoNarrator

    narrator = DemoNarrator()
    narrator.say("Welcome to the demo!")

    # Or generate all audio files upfront:
    narrator.generate_all_demo_audio()
"""

import os
import time
import subprocess
from pathlib import Path
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


# Demo narration segments
DEMO_SEGMENTS = {
    # Introduction
    "intro": """
        Welcome to the Agentic Interview System demo.
        This system enables organizations to conduct structured technical interviews
        with automated evaluation and real-time admin supervision.
        Let's explore all the features.
    """,

    # Admin Dashboard
    "admin_intro": """
        First, let's look at the Admin Dashboard.
        This is where administrators manage the system configuration.
        There are four main tabs: People Management, Template Management,
        Lens Management, and Live Sessions.
    """,

    "admin_people": """
        In People Management, you can add and manage interviewees.
        Each person has a name, email, role, department, and optional tags.
        Let's create a new test candidate.
    """,

    "admin_templates": """
        Template Management is where you create interview blueprints.
        Each template contains a set of questions with competencies,
        difficulty levels, and ground-truth keypoints for evaluation.
    """,

    "admin_lenses": """
        Lens Management lets you configure analytical frameworks.
        Lenses are applied after interviews to extract structured insights,
        like assessing debugging skills or communication abilities.
    """,

    "admin_live": """
        The Live Sessions tab shows all interviews currently in progress.
        Admins can see when interviewees raise their hand for help,
        and can join sessions to provide real-time assistance.
    """,

    # Interviewer View
    "interviewer_intro": """
        Now let's look at the Interviewer View.
        This is where question authors manage the question bank.
        You can create questions with specific competencies, difficulties,
        and keypoints that define the expected answer.
    """,

    "interviewer_create": """
        Let's create a new interview question.
        We'll specify the question text, select a competency area,
        set the difficulty level, and define the keypoints.
    """,

    # Interview Flow
    "interview_setup": """
        Now for the main event - conducting an interview.
        The Interviewee View supports two modes:
        Classic step-by-step interviews, and a conversational Chat mode.
        Let's start with the Chat Interview experience.
    """,

    "chat_intro": """
        The Chat Interview provides a conversational interface.
        Questions appear as system messages, and candidates respond naturally.
        After each answer, the system provides immediate evaluation feedback
        with scores, mastery levels, and constructive feedback.
    """,

    "chat_answer": """
        Notice the real-time loading indicator while the answer is being evaluated.
        The system analyzes the response against the ground-truth keypoints
        and provides both a numerical score and qualitative feedback.
    """,

    # Raise Hand Feature
    "raise_hand_intro": """
        One of our key features is the Raise Hand system.
        If a candidate needs help during an interview,
        they can raise their hand to request admin assistance.
    """,

    "raise_hand_admin": """
        When an admin joins a session, the interview automatically pauses.
        The admin can see the full transcript, send messages to the candidate,
        skip questions, or end the interview early.
        All admin messages are saved in the transcript for audit purposes.
    """,

    "raise_hand_resume": """
        When the admin clicks Resume and Leave,
        the interview continues where it left off.
        The candidate sees a notification that the interview has resumed.
    """,

    # Reports
    "reports_intro": """
        Finally, let's look at the Reports and Analytics section.
        Here you can review completed interviews,
        view score distributions, and export data for further analysis.
    """,

    "reports_detail": """
        The session detail view shows the complete interview transcript,
        question-by-question evaluations, and any lens analysis results.
        You can export individual sessions as JSON
        or the full session list as CSV.
    """,

    # Conclusion
    "conclusion": """
        That concludes our demo of the Agentic Interview System.
        We've seen the admin dashboard, question management,
        both interview modes, real-time admin assistance,
        and comprehensive reporting.
        Thank you for watching!
    """,
}


class DemoNarrator:
    """Handles text-to-speech narration for demos."""

    def __init__(
        self,
        voice: str = "nova",  # Options: alloy, echo, fable, onyx, nova, shimmer
        model: str = "tts-1",  # tts-1 or tts-1-hd
        speed: float = 1.0,
        audio_dir: str = "demo_audio"
    ):
        """
        Initialize the narrator.

        Args:
            voice: OpenAI TTS voice to use
            model: TTS model (tts-1 for speed, tts-1-hd for quality)
            speed: Playback speed (0.25 to 4.0)
            audio_dir: Directory to save audio files
        """
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.voice = voice
        self.model = model
        self.speed = speed
        self.audio_dir = Path(audio_dir)
        self.audio_dir.mkdir(exist_ok=True)

    def _clean_text(self, text: str) -> str:
        """Clean up text for better TTS output."""
        # Remove extra whitespace
        lines = [line.strip() for line in text.strip().split('\n')]
        return ' '.join(line for line in lines if line)

    def generate_audio(self, text: str, filename: str) -> Path:
        """
        Generate audio file from text.

        Args:
            text: Text to convert to speech
            filename: Output filename (without extension)

        Returns:
            Path to the generated audio file
        """
        output_path = self.audio_dir / f"{filename}.mp3"

        # Skip if already generated
        if output_path.exists():
            print(f"Audio already exists: {output_path}")
            return output_path

        clean_text = self._clean_text(text)
        print(f"Generating audio for: {filename}...")

        response = self.client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=clean_text,
            speed=self.speed
        )

        # Write response content to file
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"Saved: {output_path}")
        return output_path

    def play_audio(self, filepath: Path) -> None:
        """Play an audio file using system player."""
        if not filepath.exists():
            print(f"Audio file not found: {filepath}")
            return

        # Use afplay on macOS
        subprocess.run(["afplay", str(filepath)], check=True)

    def say(self, text: str, wait: bool = True) -> None:
        """
        Generate and immediately play text as speech.

        Args:
            text: Text to speak
            wait: If True, wait for audio to finish before returning
        """
        # Generate temp file
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        filepath = self.generate_audio(text, f"temp_{text_hash}")

        if wait:
            self.play_audio(filepath)
        else:
            subprocess.Popen(["afplay", str(filepath)])

    def say_segment(self, segment_name: str, wait: bool = True) -> None:
        """
        Play a predefined demo segment.

        Args:
            segment_name: Key from DEMO_SEGMENTS
            wait: If True, wait for audio to finish
        """
        if segment_name not in DEMO_SEGMENTS:
            print(f"Unknown segment: {segment_name}")
            return

        filepath = self.audio_dir / f"{segment_name}.mp3"

        if not filepath.exists():
            self.generate_audio(DEMO_SEGMENTS[segment_name], segment_name)

        if wait:
            self.play_audio(filepath)
        else:
            subprocess.Popen(["afplay", str(filepath)])

    def generate_all_demo_audio(self) -> None:
        """Pre-generate all demo narration audio files."""
        print(f"Generating {len(DEMO_SEGMENTS)} audio segments...")
        print(f"Voice: {self.voice}, Model: {self.model}")
        print("-" * 40)

        for name, text in DEMO_SEGMENTS.items():
            self.generate_audio(text, name)

        print("-" * 40)
        print(f"All audio files saved to: {self.audio_dir}/")

    def list_segments(self) -> list[str]:
        """List all available demo segments."""
        return list(DEMO_SEGMENTS.keys())

    def get_segment_text(self, segment_name: str) -> Optional[str]:
        """Get the text for a segment."""
        return DEMO_SEGMENTS.get(segment_name)


def preview_all_segments():
    """Preview all segment texts without generating audio."""
    print("=" * 60)
    print("DEMO NARRATION SEGMENTS")
    print("=" * 60)

    for name, text in DEMO_SEGMENTS.items():
        clean = ' '.join(line.strip() for line in text.strip().split('\n') if line.strip())
        print(f"\n[{name}]")
        print(f"  {clean[:100]}..." if len(clean) > 100 else f"  {clean}")

    print("\n" + "=" * 60)
    print(f"Total segments: {len(DEMO_SEGMENTS)}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "preview":
            preview_all_segments()
        elif sys.argv[1] == "generate":
            narrator = DemoNarrator()
            narrator.generate_all_demo_audio()
        elif sys.argv[1] == "test":
            narrator = DemoNarrator()
            narrator.say("Hello! This is a test of the demo narration system.")
        elif sys.argv[1] == "play":
            if len(sys.argv) > 2:
                narrator = DemoNarrator()
                narrator.say_segment(sys.argv[2])
            else:
                print("Usage: python demo_narration.py play <segment_name>")
        else:
            print("Usage: python demo_narration.py [preview|generate|test|play <segment>]")
    else:
        print("Demo Narration System")
        print("-" * 40)
        print("Commands:")
        print("  preview  - Show all segment texts")
        print("  generate - Generate all audio files")
        print("  test     - Test audio playback")
        print("  play <segment> - Play specific segment")
        print("")
        print("Available segments:")
        for name in DEMO_SEGMENTS.keys():
            print(f"  - {name}")
