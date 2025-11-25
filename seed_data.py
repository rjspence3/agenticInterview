"""
Seed data script for the Agentic Interview System.

This script populates the database with sample data for development and testing:
- Organizations
- People (candidates/interviewees)
- Interview templates with questions
- Sample completed sessions (optional)

Usage:
    python seed_data.py
"""

from database import get_db_session, init_db
from db_models import (
    Organization, Person, PersonStatus,
    InterviewTemplate, TemplateQuestion,
    InterviewSession, SessionStatus, EvaluatorType,
    Lens
)
from datetime import datetime, timedelta


def seed_all():
    """
    Seed all sample data into the database.
    """
    print("=" * 60)
    print("Seeding Agentic Interview System Database")
    print("=" * 60)

    # Initialize database (create tables if they don't exist)
    print("\n1. Initializing database...")
    init_db()
    print("   ✓ Database initialized")

    with get_db_session() as db:
        # Create organization
        print("\n2. Creating organization...")
        org = create_organization(db)
        print(f"   ✓ Created organization: {org.name}")

        # Create people
        print("\n3. Creating people...")
        people = create_people(db, org.id)
        print(f"   ✓ Created {len(people)} people")

        # Create templates
        print("\n4. Creating interview templates...")
        templates = create_templates(db, org.id)
        print(f"   ✓ Created {len(templates)} templates")

        # Create lenses (Phase 7)
        print("\n5. Creating analysis lenses...")
        lenses = create_lenses(db, org.id)
        print(f"   ✓ Created {len(lenses)} lenses")

        print("\n" + "=" * 60)
        print("Seed data creation complete!")
        print("=" * 60)
        print("\nSummary:")
        print(f"  - Organizations: 1")
        print(f"  - People: {len(people)}")
        print(f"  - Templates: {len(templates)}")
        print(f"  - Total questions: {sum(len(t.questions) for t in templates)}")
        print(f"  - Lenses: {len(lenses)}")
        print("\nYou can now run the app with: streamlit run app.py")


def create_organization(db) -> Organization:
    """Create a sample organization."""
    org = Organization(
        name="TechCorp",
        settings={"timezone": "UTC", "language": "en"}
    )
    db.add(org)
    db.flush()
    return org


def create_people(db, org_id: int) -> list[Person]:
    """Create sample people (candidates/interviewees)."""
    people = [
        Person(
            organization_id=org_id,
            name="Alice Johnson",
            email="alice.johnson@example.com",
            role="Software Engineer",
            department="Engineering",
            tags=["python", "backend", "senior"],
            status=PersonStatus.ACTIVE
        ),
        Person(
            organization_id=org_id,
            name="Bob Smith",
            email="bob.smith@example.com",
            role="Frontend Developer",
            department="Engineering",
            tags=["javascript", "react", "mid-level"],
            status=PersonStatus.ACTIVE
        ),
        Person(
            organization_id=org_id,
            name="Carol Williams",
            email="carol.williams@example.com",
            role="Product Manager",
            department="Product",
            tags=["product", "strategy", "senior"],
            status=PersonStatus.ACTIVE
        ),
        Person(
            organization_id=org_id,
            name="David Brown",
            email="david.brown@example.com",
            role="Data Scientist",
            department="Data",
            tags=["python", "ml", "junior"],
            status=PersonStatus.ACTIVE
        ),
        Person(
            organization_id=org_id,
            name="Eve Davis",
            email="eve.davis@example.com",
            role="DevOps Engineer",
            department="Engineering",
            tags=["kubernetes", "aws", "mid-level"],
            status=PersonStatus.ACTIVE
        ),
    ]

    for person in people:
        db.add(person)

    db.flush()
    return people


def create_templates(db, org_id: int) -> list[InterviewTemplate]:
    """Create sample interview templates with questions."""

    # Template 1: Python Developer Interview
    python_template = InterviewTemplate(
        organization_id=org_id,
        name="Python Developer - L2",
        description="Technical interview for mid-level Python developers covering fundamentals, OOP, and problem-solving.",
        version=1,
        active=True
    )
    db.add(python_template)
    db.flush()

    python_questions = [
        TemplateQuestion(
            template_id=python_template.id,
            order_index=0,
            question_text="What is the difference between a list and a tuple in Python?",
            competency="Python Fundamentals",
            difficulty="Easy",
            keypoints=["mutable vs immutable", "syntax differences", "use cases", "performance"]
        ),
        TemplateQuestion(
            template_id=python_template.id,
            order_index=1,
            question_text="Explain how decorators work in Python. Provide an example.",
            competency="Python Advanced",
            difficulty="Medium",
            keypoints=["function wrapping", "@ syntax", "use cases", "example code"]
        ),
        TemplateQuestion(
            template_id=python_template.id,
            order_index=2,
            question_text="What is the GIL (Global Interpreter Lock) and how does it affect multithreading in Python?",
            competency="Python Concurrency",
            difficulty="Hard",
            keypoints=["GIL definition", "thread safety", "performance impact", "alternatives like multiprocessing"]
        ),
        TemplateQuestion(
            template_id=python_template.id,
            order_index=3,
            question_text="Describe a situation where you would use a generator instead of a list. What are the benefits?",
            competency="Python Performance",
            difficulty="Medium",
            keypoints=["lazy evaluation", "memory efficiency", "yield keyword", "use cases"]
        ),
    ]

    for q in python_questions:
        db.add(q)

    # Template 2: System Design Interview
    system_design_template = InterviewTemplate(
        organization_id=org_id,
        name="System Design - Senior",
        description="System design interview for senior engineers covering scalability, architecture, and trade-offs.",
        version=1,
        active=True
    )
    db.add(system_design_template)
    db.flush()

    system_design_questions = [
        TemplateQuestion(
            template_id=system_design_template.id,
            order_index=0,
            question_text="Design a URL shortening service like bit.ly. How would you handle millions of requests per day?",
            competency="System Design",
            difficulty="Hard",
            keypoints=["URL hashing", "database design", "caching strategy", "scalability", "API design"]
        ),
        TemplateQuestion(
            template_id=system_design_template.id,
            order_index=1,
            question_text="How would you design a rate limiter for an API?",
            competency="System Design",
            difficulty="Medium",
            keypoints=["rate limiting algorithms", "token bucket", "sliding window", "distributed systems", "Redis"]
        ),
        TemplateQuestion(
            template_id=system_design_template.id,
            order_index=2,
            question_text="Explain the CAP theorem and provide a real-world example where you'd choose AP over CP.",
            competency="Distributed Systems",
            difficulty="Hard",
            keypoints=["CAP theorem definition", "consistency", "availability", "partition tolerance", "trade-offs", "example"]
        ),
    ]

    for q in system_design_questions:
        db.add(q)

    # Template 3: Behavioral Interview
    behavioral_template = InterviewTemplate(
        organization_id=org_id,
        name="Behavioral - Leadership",
        description="Behavioral interview focused on leadership, teamwork, and problem-solving.",
        version=1,
        active=True
    )
    db.add(behavioral_template)
    db.flush()

    behavioral_questions = [
        TemplateQuestion(
            template_id=behavioral_template.id,
            order_index=0,
            question_text="Tell me about a time when you had to work with a difficult team member. How did you handle it?",
            competency="Teamwork",
            difficulty="Medium",
            keypoints=["specific example", "actions taken", "communication", "outcome", "reflection"]
        ),
        TemplateQuestion(
            template_id=behavioral_template.id,
            order_index=1,
            question_text="Describe a project where you had to meet a tight deadline. What was your approach?",
            competency="Time Management",
            difficulty="Medium",
            keypoints=["prioritization", "planning", "execution", "obstacles overcome", "result"]
        ),
        TemplateQuestion(
            template_id=behavioral_template.id,
            order_index=2,
            question_text="Give me an example of when you took initiative on a project without being asked.",
            competency="Leadership",
            difficulty="Medium",
            keypoints=["initiative shown", "motivation", "impact", "team response", "outcome"]
        ),
    ]

    for q in behavioral_questions:
        db.add(q)

    db.flush()
    return [python_template, system_design_template, behavioral_template]


def create_lenses(db, org_id: int) -> list[Lens]:
    """Create sample analysis lenses with criteria."""

    # Lens 1: Debugging Process Assessment
    debugging_lens = Lens(
        organization_id=org_id,
        name="Debugging Process Assessment",
        description="Evaluates the candidate's systematic approach to identifying and resolving technical issues",
        config={
            "criteria": [
                {
                    "name": "systematic_approach",
                    "definition": "Follows a structured, methodical process to identify and resolve issues",
                    "examples": [
                        "reproduces the problem",
                        "forms hypotheses before testing",
                        "tests incrementally",
                        "isolates variables systematically"
                    ]
                },
                {
                    "name": "tool_usage",
                    "definition": "Effectively uses debugging tools and techniques",
                    "examples": [
                        "mentions debuggers (gdb, pdb, etc.)",
                        "discusses logging strategies",
                        "uses print statements strategically",
                        "references profilers or monitoring tools"
                    ]
                },
                {
                    "name": "root_cause_analysis",
                    "definition": "Digs deep to find underlying causes, not just symptoms",
                    "examples": [
                        "asks 'why' multiple times",
                        "distinguishes symptom from cause",
                        "considers multiple root cause possibilities",
                        "traces through code execution"
                    ]
                }
            ],
            "scoring_scale": "0-5",
            "examples": [
                {
                    "context": "Candidate describes reproducing bug, checking logs, forming hypothesis, testing fix",
                    "assessment": "systematic_approach: 4/5 (good process), tool_usage: 3/5 (basic tools mentioned), root_cause_analysis: 4/5 (traced to underlying issue)"
                }
            ]
        },
        active=True,
        version=1
    )
    db.add(debugging_lens)

    # Lens 2: Communication Clarity
    communication_lens = Lens(
        organization_id=org_id,
        name="Communication Clarity",
        description="Assesses how clearly and effectively the candidate explains technical concepts",
        config={
            "criteria": [
                {
                    "name": "clarity",
                    "definition": "Explains concepts clearly and concisely without excessive jargon",
                    "examples": [
                        "uses simple, accessible language",
                        "provides concrete examples",
                        "checks for understanding",
                        "avoids unnecessary complexity"
                    ]
                },
                {
                    "name": "structure",
                    "definition": "Organizes thoughts logically with clear progression",
                    "examples": [
                        "uses frameworks (e.g., 'First, Second, Third')",
                        "provides roadmap before diving into details",
                        "follows logical flow",
                        "connects ideas explicitly"
                    ]
                },
                {
                    "name": "adaptability",
                    "definition": "Adjusts communication style based on context and feedback",
                    "examples": [
                        "simplifies when asked",
                        "provides more detail when needed",
                        "responds to confusion signals",
                        "tailors examples to audience"
                    ]
                }
            ],
            "scoring_scale": "0-5"
        },
        active=True,
        version=1
    )
    db.add(communication_lens)

    # Lens 3: Problem-Solving Approach
    problem_solving_lens = Lens(
        organization_id=org_id,
        name="Problem-Solving Approach",
        description="Evaluates the candidate's general problem-solving methodology and critical thinking",
        config={
            "criteria": [
                {
                    "name": "problem_decomposition",
                    "definition": "Breaks complex problems into manageable sub-problems",
                    "examples": [
                        "identifies distinct components",
                        "tackles one piece at a time",
                        "prioritizes sub-problems",
                        "recognizes dependencies"
                    ]
                },
                {
                    "name": "edge_case_consideration",
                    "definition": "Thinks about boundary conditions and edge cases",
                    "examples": [
                        "mentions null/empty cases",
                        "considers error conditions",
                        "thinks about scale limits",
                        "discusses invalid inputs"
                    ]
                },
                {
                    "name": "solution_validation",
                    "definition": "Verifies solutions work correctly",
                    "examples": [
                        "walks through examples",
                        "tests with sample data",
                        "considers counterexamples",
                        "checks assumptions"
                    ]
                }
            ],
            "scoring_scale": "0-5"
        },
        active=True,
        version=1
    )
    db.add(problem_solving_lens)

    db.flush()
    return [debugging_lens, communication_lens, problem_solving_lens]


if __name__ == "__main__":
    try:
        seed_all()
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        raise
