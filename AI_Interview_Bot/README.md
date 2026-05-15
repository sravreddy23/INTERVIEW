# InterviewAI

InterviewAI is a modern AI-powered interview practice chatbot built with Streamlit and Python. It simulates realistic interview sessions, scores answers, gives feedback, and stores progress locally for dashboard analytics.

## Features

- Dark, hackathon-ready UI with a chat-style experience
- Interview modes for HR, Python, DBMS, DSA, OS, Networks, Aptitude, and Behavioral
- Company-style interview mode for Google, Amazon, Microsoft, Infosys, TCS, and Meta
- One-question-at-a-time AI interviewer with follow-up logic and dynamic difficulty
- Answer analysis with score, strengths, weaknesses, sample answer, and complexity feedback
- Resume PDF upload with skill extraction and personalized question generation
- Session memory, dashboard analytics, and simple authentication
- Deployment-ready for Streamlit Cloud, Render, and Replit
- Optional voice AI hooks and MongoDB environment placeholders

## Folder Structure

```text
InterviewAI/
├── app.py
├── README.md
├── requirements.txt
├── .env.example
├── .streamlit/
│   └── config.toml
├── assets/
├── data/
└── utils/
    ├── analysis.py
    ├── auth.py
    ├── config.py
    ├── interview_engine.py
    ├── resume.py
    ├── storage.py
    ├── ui.py
    └── voice.py
```

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and add your Google AI API key.
4. Run the app:

```bash
streamlit run app.py
```

## Environment Variables

- `GOOGLE_API_KEY`: your Google AI / Gemini API key
- `GOOGLE_MODEL`: default model, such as `gemini-1.5-flash`
- `APP_SECRET_KEY`: optional app secret used for local deployments
- `USE_MONGODB`: set to `true` only if you wire in MongoDB later
- `MONGODB_URI`: MongoDB connection string (Atlas or local)
- `MONGODB_DB_NAME`: database name to use for app collections

If `GOOGLE_API_KEY` is missing, the app automatically falls back to a local demo mode so the UI still works.

## Deployment

### Streamlit Cloud

1. Push the project to GitHub.
2. Create a new Streamlit Cloud app.
3. Set the main file path to `app.py`.
4. Add `GOOGLE_API_KEY` and any other environment variables in the Streamlit Cloud secrets panel.

### Render

1. Create a new Web Service.
2. Connect your GitHub repo.
3. Use the command `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`.
4. Add environment variables in the Render dashboard.

### Replit

1. Import the GitHub repo into Replit.
2. Install dependencies from `requirements.txt`.
3. Set the run command to `streamlit run app.py --server.address 0.0.0.0 --server.port 8501`.
4. Store secrets in Replit's Secrets panel.

## Google AI Integration Example

The core app uses the modern Google Gemini Python SDK:

```python
from google import genai

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
response = client.models.generate_content(
    model="gemini-1.5-flash",
    contents="You are a professional interviewer. Ask me one question.",
)
```

## Notes

- Authentication is local and SQLite-backed by default.
- Resume storage and performance analytics are saved locally in `data/interviewai.db`.
- MongoDB settings are optional placeholders unless you implement a Mongo storage adapter.
- Voice AI is optional and only enabled if you install the extra libraries.
