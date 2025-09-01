You are an expert software architect and developer.
Help me build "SmartLearn" — an AI-powered personalized tutor and learning companion
for high school students in Africa. The goal is to demonstrate prompt engineering,
Flask backend integration, and AI tutoring features in a hackathon project.

We will build this system in PHASES.
At the end of each phase, provide working code snippets, clear instructions, and
explain dependencies/configuration.

====================================================================
PHASE 1: PROJECT SETUP

- Initialize a Flask app with clean structure (app.py, templates/, static/).
- Create a simple homepage (index.html) with navigation.
- Add a placeholder section “Ask the Tutor” where students can input a question.
- Ensure app runs locally with Flask dev server.

====================================================================
PHASE 2: AI TUTOR (Prompt Engineering + GPT-4o Integration)

- Integrate OpenAI GPT-4o API into Flask backend.
- Create a function `generate_answer(subject, question)`
  → Uses structured prompt engineering to:
  - Understand the subject (Math, Physics, History, etc.)
  - Generate clear, step-by-step explanation.
  - Provide a quiz question related to the topic.
- Add a route `/ask` that accepts student questions and returns AI answers.
- Ensure answers are curriculum-friendly (e.g., KCSE/WAEC style).
- Example: If a student asks about “Photosynthesis”,
  AI should explain it in simple terms and generate a practice quiz question.

====================================================================
PHASE 3: PERSONALIZED LEARNING FLOW

- Track student interactions in session (no login yet).
- Store last 3 questions + answers in memory.
- Display history on dashboard.
- Add feature: “Suggest what to learn next” → AI recommends a follow-up topic
  using prompt engineering.

====================================================================
PHASE 4: QUIZ GENERATOR

- Add a “Generate Quiz” button per subject.
- Flask route `/quiz/<subject>` → AI generates 5 multiple-choice questions.
- Display quiz in HTML form (radio buttons).
- On submit → grade answers (AI + simple key).
- Show score and explanation.

====================================================================
PHASE 5: PAYMENTS INTEGRATION

- Integrate IntaSend API for subscription/payment.
- Add “Upgrade to Premium” button on homepage.
- Flask backend handles checkout session and redirects to IntaSend payment flow.
- On successful payment → unlock more quiz attempts + premium tutoring.

====================================================================
PHASE 6: POLISH & DEPLOYMENT

- Add TailwindCSS styling for clean UI.
- Add animations (progress bars, quiz completion).
- Deploy to Replit / Railway / Render for demo.
- Ensure live demo works with AI API + IntaSend test keys.

====================================================================
RULES FOR YOU (the AI assistant):

1. Always provide code that is directly runnable.
2. Clearly state dependencies (e.g., Flask, OpenAI, IntaSend SDK).
3. Use simple and hackathon-friendly solutions (no over-engineering).
4. At the end of each phase, suggest "Next Step".
