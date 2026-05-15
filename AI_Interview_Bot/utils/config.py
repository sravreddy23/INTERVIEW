"""Central configuration and prompt constants for InterviewAI."""

from pathlib import Path

APP_NAME = "InterviewAI"
APP_SUBTITLE = "AI interview practice for students and job seekers"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "interviewai.db"
ASSETS_DIR = BASE_DIR / "assets"

INTERVIEW_MODES = [
    "HR Interview",
    "Python",
    "DBMS",
    "DSA",
    "Operating Systems",
    "Computer Networks",
    "Aptitude",
    "Behavioral Interview",
]

COMPANY_OPTIONS = [
    "Neutral / Standard",
    "Google",
    "Amazon",
    "Microsoft",
    "Infosys",
    "TCS",
    "Meta",
]

CODING_MODES = {"Python", "DBMS", "DSA", "Operating Systems", "Computer Networks"}

MODE_TOPIC_HINTS = {
    "HR Interview": "communication, motivation, teamwork, conflict resolution, self-awareness",
    "Python": "syntax, data structures, OOP, modules, error handling, testing",
    "DBMS": "normalization, SQL, joins, indexing, transactions, ACID, optimization",
    "DSA": "arrays, strings, recursion, trees, graphs, sorting, greedy, DP, complexity",
    "Operating Systems": "processes, threads, scheduling, synchronization, memory, deadlocks",
    "Computer Networks": "OSI model, TCP/IP, routing, DNS, HTTP, security, congestion",
    "Aptitude": "logic, numbers, percentages, ratios, probability, speed and time",
    "Behavioral Interview": "ownership, leadership, adaptability, teamwork, results, reflection",
}

COMPANY_STYLE_HINTS = {
    "Neutral / Standard": "professional and supportive",
    "Google": "structured, analytical, evidence-driven, and problem-solving focused",
    "Amazon": "ownership-heavy, customer-obsessed, and leadership-principle oriented",
    "Microsoft": "collaborative, growth-minded, and technical with product awareness",
    "Infosys": "fundamentals-focused, clear, and communication-oriented",
    "TCS": "practical, process-aware, and client-focused",
    "Meta": "impact-driven, product-aware, scalable, and direct",
}

DEFAULT_MODEL = "gemini-1.5-flash"
DEFAULT_MAX_TURNS = 10
DEFAULT_TIMER_SECONDS = 180

SKILL_KEYWORDS = {
    "python": ["python", "pandas", "numpy", "django", "flask", "fastapi", "pytest", "oop"],
    "data structures": ["array", "linked list", "stack", "queue", "tree", "graph", "heap", "trie"],
    "dbms": ["sql", "mysql", "postgres", "oracle", "index", "normalization", "transaction", "acid"],
    "cloud": ["aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "devops"],
    "java": ["java", "spring", "hibernate", "maven", "gradle"],
    "javascript": ["javascript", "react", "node", "express", "typescript"],
    "communication": ["communication", "presentation", "stakeholder", "teamwork", "leadership"],
    "testing": ["unit test", "integration test", "selenium", "cypress", "jest", "mock"],
    "machine learning": ["machine learning", "ml", "pytorch", "tensorflow", "scikit"],
}

LLM_RESPONSE_KEYS = [
    "question",
    "difficulty",
    "is_follow_up",
    "focus_area",
    "reason",
    "expected_answer_signals",
]

ANALYSIS_RESPONSE_KEYS = [
    "score",
    "confidence",
    "technical_correctness",
    "communication_quality",
    "strengths",
    "weaknesses",
    "improvements",
    "sample_answer",
    "time_complexity",
    "space_complexity",
    "overall_feedback",
]
