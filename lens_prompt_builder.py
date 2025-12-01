"""
Lens Prompt Builder - Constructs LLM prompts for lens analysis.

This module builds structured prompts that instruct the LLM to analyze
interview transcripts according to specific lens criteria.
"""

from typing import List, Dict, Any
from db_models import Lens, InterviewSession, TranscriptEntry, SpeakerType


def build_lens_prompt(
    lens: Lens,
    session: InterviewSession,
    transcript: List[TranscriptEntry]
) -> str:
    """
    Build a structured prompt for lens analysis.

    Args:
        lens: The Lens configuration with criteria and scoring scales
        session: The InterviewSession being analyzed
        transcript: List of TranscriptEntry objects (ordered conversation)

    Returns:
        Formatted prompt string ready for LLM
    """
    # Extract lens configuration
    config = lens.config
    criteria = config.get("criteria", [])
    scoring_scale = config.get("scoring_scale", "0-5")

    # Build transcript section
    transcript_text = _format_transcript(transcript)

    # Build criteria section
    criteria_text = _format_criteria(criteria, scoring_scale)

    # Build output schema
    output_schema = _format_output_schema(scoring_scale)

    # Build few-shot examples if provided
    examples_text = _format_examples(config.get("examples", []))

    # Assemble complete prompt
    prompt = f"""You are an expert technical interviewer analyzing an interview transcript to assess: {lens.name}

DESCRIPTION:
{lens.description or 'No description provided'}

TRANSCRIPT:
{transcript_text}

ASSESSMENT CRITERIA:
{criteria_text}

TASK:
For each criterion listed above, carefully analyze the transcript and output:
1. **score**: A numeric score on the {scoring_scale} scale
2. **flags**: A list of boolean observations or patterns identified (e.g., ["clear_explanation", "missing_edge_cases"])
3. **extracted_items**: A list of specific behaviors, concepts, or processes identified (e.g., ["tested with examples", "considered performance"])
4. **supporting_quotes**: Specific text excerpts from the transcript that support your assessment (include speaker and approximate text)
5. **notes**: A brief 1-2 sentence explanation of your assessment

Be objective and evidence-based. Every score and flag should be supported by specific quotes from the transcript.

OUTPUT FORMAT (strict JSON):
{output_schema}

{examples_text}

Now analyze the transcript above and provide your assessment in the exact JSON format specified."""

    return prompt


def _format_transcript(transcript: List[TranscriptEntry]) -> str:
    """Format transcript entries into a readable conversation."""
    lines = []
    # Provide clear labels for all known speaker types while keeping
    # sensible defaults for any future roles that may be added.
    speaker_labels = {speaker: speaker.value.upper() for speaker in SpeakerType}
    speaker_labels.update(
        {
            SpeakerType.SYSTEM: "INTERVIEWER",
            SpeakerType.PARTICIPANT: "CANDIDATE",
        }
    )
    for entry in transcript:
        if isinstance(entry.speaker, SpeakerType):
            speaker_label = speaker_labels.get(entry.speaker, entry.speaker.value.upper())
        elif hasattr(entry.speaker, "value"):
            speaker_label = str(entry.speaker.value).upper()
        else:
            speaker_label = str(entry.speaker).upper()
        lines.append(f"[{speaker_label}]: {entry.text}")

    return "\n\n".join(lines)


def _format_criteria(criteria: List[Dict[str, Any]], scale: str) -> str:
    """Format criteria definitions for the prompt."""
    if not criteria:
        return "No specific criteria defined."

    lines = []
    for i, criterion in enumerate(criteria, 1):
        name = criterion.get("name", f"criterion_{i}")
        definition = criterion.get("definition", "No definition provided")
        examples = criterion.get("examples", [])

        lines.append(f"{i}. **{name}** (scale: {scale})")
        lines.append(f"   Definition: {definition}")

        if examples:
            lines.append(f"   What to look for: {', '.join(examples)}")

        lines.append("")  # Blank line between criteria

    return "\n".join(lines)


def _format_output_schema(scale: str) -> str:
    """Generate the expected JSON output schema."""
    return """{
  "criteria_results": [
    {
      "criterion": "criterion_name_here",
      "score": <number on """ + scale + """ scale>,
      "flags": ["flag1", "flag2"],
      "extracted_items": ["item1", "item2"],
      "supporting_quotes": [
        {
          "speaker": "candidate" or "interviewer",
          "text": "exact quote from transcript"
        }
      ],
      "notes": "Brief explanation of assessment"
    }
  ]
}"""


def _format_examples(examples: List[Dict[str, Any]]) -> str:
    """Format few-shot examples if provided."""
    if not examples:
        return ""

    lines = ["EXAMPLES (for reference):\n"]

    for i, example in enumerate(examples, 1):
        lines.append(f"Example {i}:")
        lines.append(f"Context: {example.get('context', 'N/A')}")
        lines.append(f"Expected Assessment: {example.get('assessment', 'N/A')}")
        lines.append("")

    return "\n".join(lines)


def validate_lens_config(config: Dict[str, Any]) -> tuple[bool, str]:
    """
    Validate that a lens configuration is well-formed.

    Performs strict validation including:
    - Required fields presence
    - Type checking
    - String length limits
    - Character validation (to prevent prompt injection)
    - Scoring scale format

    Args:
        config: The lens configuration dictionary

    Returns:
        Tuple of (is_valid, error_message)
    """
    import re
    from constants import (
        MAX_CRITERION_NAME_LENGTH,
        MAX_CRITERION_DEFINITION_LENGTH,
        MAX_CRITERIA_COUNT
    )

    # Check config is a dictionary
    if not isinstance(config, dict):
        return False, "Config must be a dictionary"

    # Check required fields
    if "criteria" not in config:
        return False, "Missing required field: criteria"

    if not isinstance(config["criteria"], list):
        return False, "criteria must be a list"

    if len(config["criteria"]) == 0:
        return False, "At least one criterion is required"

    if len(config["criteria"]) > MAX_CRITERIA_COUNT:
        return False, f"Too many criteria (max {MAX_CRITERIA_COUNT})"

    # Valid name pattern: alphanumeric, underscores, spaces only
    # This prevents prompt injection via special characters
    valid_name_pattern = re.compile(r'^[\w\s\-]+$')

    # Validate each criterion
    for i, criterion in enumerate(config["criteria"]):
        if not isinstance(criterion, dict):
            return False, f"Criterion {i} must be a dictionary"

        # Check required fields
        if "name" not in criterion:
            return False, f"Criterion {i} missing required field: name"

        if "definition" not in criterion:
            return False, f"Criterion {i} missing required field: definition"

        # Validate name
        name = criterion["name"]
        if not isinstance(name, str):
            return False, f"Criterion {i}: name must be a string"
        if len(name) == 0:
            return False, f"Criterion {i}: name cannot be empty"
        if len(name) > MAX_CRITERION_NAME_LENGTH:
            return False, f"Criterion {i}: name too long (max {MAX_CRITERION_NAME_LENGTH} chars)"
        if not valid_name_pattern.match(name):
            return False, f"Criterion {i}: name contains invalid characters (use only letters, numbers, spaces, hyphens, underscores)"

        # Validate definition
        definition = criterion["definition"]
        if not isinstance(definition, str):
            return False, f"Criterion {i}: definition must be a string"
        if len(definition) == 0:
            return False, f"Criterion {i}: definition cannot be empty"
        if len(definition) > MAX_CRITERION_DEFINITION_LENGTH:
            return False, f"Criterion {i}: definition too long (max {MAX_CRITERION_DEFINITION_LENGTH} chars)"

        # Validate optional examples field
        if "examples" in criterion:
            examples = criterion["examples"]
            if not isinstance(examples, list):
                return False, f"Criterion {i}: examples must be a list"
            for j, example in enumerate(examples):
                if not isinstance(example, str):
                    return False, f"Criterion {i}, example {j}: must be a string"
                if len(example) > 200:
                    return False, f"Criterion {i}, example {j}: too long (max 200 chars)"

    # Check scoring scale format
    scale = config.get("scoring_scale", "0-5")
    if not isinstance(scale, str):
        return False, "scoring_scale must be a string"
    if "-" not in scale:
        return False, "scoring_scale must be in format 'min-max' (e.g., '0-5')"

    # Validate scale values are numeric
    try:
        parts = scale.split("-")
        if len(parts) != 2:
            return False, "scoring_scale must have exactly two values separated by '-'"
        min_val = float(parts[0])
        max_val = float(parts[1])
        if min_val >= max_val:
            return False, "scoring_scale min must be less than max"
    except ValueError:
        return False, "scoring_scale values must be numeric"

    return True, ""


def get_example_lens_config(lens_type: str = "debugging") -> Dict[str, Any]:
    """
    Get an example lens configuration for reference.

    Args:
        lens_type: Type of lens ("debugging", "communication", "system_design")

    Returns:
        Example lens configuration dictionary
    """
    configs = {
        "debugging": {
            "criteria": [
                {
                    "name": "systematic_approach",
                    "definition": "Follows a structured process to identify and resolve issues",
                    "examples": [
                        "reproduces the problem",
                        "forms hypotheses",
                        "tests incrementally",
                        "isolates variables"
                    ]
                },
                {
                    "name": "tool_usage",
                    "definition": "Effectively uses debugging tools and techniques",
                    "examples": [
                        "mentions debuggers",
                        "discusses logging",
                        "uses print statements strategically",
                        "references profilers"
                    ]
                },
                {
                    "name": "root_cause_analysis",
                    "definition": "Digs deep to find underlying causes, not just symptoms",
                    "examples": [
                        "asks why multiple times",
                        "distinguishes symptom from cause",
                        "considers multiple possibilities"
                    ]
                }
            ],
            "scoring_scale": "0-5",
            "examples": [
                {
                    "context": "Candidate describes reproducing bug, checking logs, forming hypothesis",
                    "assessment": "systematic_approach: 4/5, tool_usage: 3/5"
                }
            ]
        },
        "communication": {
            "criteria": [
                {
                    "name": "clarity",
                    "definition": "Explains concepts clearly and concisely",
                    "examples": [
                        "uses simple language",
                        "provides examples",
                        "checks for understanding"
                    ]
                },
                {
                    "name": "structure",
                    "definition": "Organizes thoughts logically",
                    "examples": [
                        "uses frameworks",
                        "provides roadmap",
                        "follows logical flow"
                    ]
                }
            ],
            "scoring_scale": "0-5"
        },
        "system_design": {
            "criteria": [
                {
                    "name": "requirements_gathering",
                    "definition": "Asks clarifying questions before diving into design",
                    "examples": [
                        "asks about scale",
                        "clarifies constraints",
                        "identifies use cases"
                    ]
                },
                {
                    "name": "trade_off_analysis",
                    "definition": "Considers multiple approaches and discusses pros/cons",
                    "examples": [
                        "compares options",
                        "discusses limitations",
                        "considers edge cases"
                    ]
                },
                {
                    "name": "scalability_thinking",
                    "definition": "Considers how system will handle growth",
                    "examples": [
                        "mentions caching",
                        "discusses sharding",
                        "considers bottlenecks"
                    ]
                }
            ],
            "scoring_scale": "0-10"
        }
    }

    return configs.get(lens_type, configs["debugging"])


# ==============================================================================
# Public API
# ==============================================================================

__all__ = [
    "build_lens_prompt",
    "validate_lens_config",
    "get_example_lens_config",
]
