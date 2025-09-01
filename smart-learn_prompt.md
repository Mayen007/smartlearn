# Phase 1: Firebase setup

You are an expert Firebase + AI developer.  
Set up a Firebase project called "SmartLearn AI".

1. Enable Firebase Authentication (Email/Google login).
2. Create Firestore collections:

   - users {uid, name, email, role, subscriptionStatus, createdAt}
   - plans {userId, planId, aiResponse, createdAt}
   - sessions {userId, sessionId, query, aiAnswer, createdAt}

3. Setup Firebase Hosting to serve a web frontend.
4. Write config files for Firebase SDK (firebase.js).

# Phase 2: Frontend (Dashboard + Auth Flow)

Build a responsive web frontend (HTML/CSS/JS or React).

- Landing Page: brief intro + "Sign In with Google/Email".
- Dashboard: user profile, study goals form, "Get Smart Plan" button.
- Display AI-generated plans in a styled card format.
- Store results in Firestore (plans collection).
  Use Tailwind CSS for styling.

# Phase 3: AI Integration

Implement Firebase Cloud Function `generateStudyPlan`.

- Input: subject, available hours, exam date, learning style.
- Process: send structured prompt to AI API (e.g., OpenAI GPT or Gemini).
- Output: JSON {topics, schedule, tips, resources}.
- Save output to Firestore under `plans`.
- Return response to frontend.

# Phase 4: Monetization with IntaSend

Integrate InstaSend payments:

- Premium feature = "AI Practice Tests" + "Detailed Feedback".
- Free users: get basic study plans.
- Premium users: access detailed practice + advanced feedback.

Workflow:

1. User clicks "Upgrade to Premium".
2. Firebase Function calls InstaSend API for checkout.
3. On success, update `users.subscriptionStatus = premium`.
4. Lock premium features unless subscriptionStatus == "premium".

# Phase 5: Security and Testing

- Secure Firestore rules (only allow users to read/write their data).
- Ensure API keys for AI & InstaSend are stored in Firebase Functions, not frontend.
- Write simple Jest tests for Firebase Functions.
- Test authentication, AI responses, and payment flow.
