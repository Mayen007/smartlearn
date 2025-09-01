# 🔥 Firebase Setup Guide for SmartLearn

## ✅ What's Been Done

Your SmartLearn platform now has Firebase Authentication integration with:

- **Robust Firebase Config** - Handles multiple initialization methods with fallbacks
- **Client-side Auth** - Email/password and Google sign-in using Firebase CDN
- **Secure Backend** - Token verification and protected API routes
- **Simple UI** - Clean auth modal that doesn't interfere with your existing design
- **Error Handling** - Graceful fallbacks if Firebase isn't configured
- **User Data Storage** - Quiz scores and learning sessions saved to Firestore

## 🚀 Setup Instructions

### Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click **"Create a project"**
3. Project name: `SmartLearn AI`
4. Accept terms and create project

### Step 2: Enable Authentication

1. In Firebase Console, go to **Authentication** → **Sign-in method**
2. Enable these providers:
   - ✅ **Email/Password** (click Enable)
   - ✅ **Google** (click Enable, set up OAuth consent)

### Step 3: Create Web App

1. Go to **Project Settings** (⚙️ gear icon)
2. Click **"Add app"** → Web icon (`</>`)
3. App nickname: `SmartLearn Web`
4. ✅ Also set up Firebase Hosting (optional)
5. **COPY THE CONFIG** - you'll need this!

```javascript
// Your Firebase config will look like this:
const firebaseConfig = {
  apiKey: "AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  authDomain: "smartlearn-ai-xxxx.firebaseapp.com",
  projectId: "smartlearn-ai-xxxx",
  storageBucket: "smartlearn-ai-xxxx.appspot.com",
  messagingSenderId: "123456789012",
  appId: "1:123456789012:web:abcdefghijklmnop",
};
```

### Step 4: Enable Firestore Database

1. Go to **Firestore Database**
2. Click **"Create database"**
3. Choose **"Start in test mode"** (for development)
4. Select your preferred location (choose closest to your users)

### Step 5: Configure Your App

#### Update Firebase Config

Edit `static/js/firebase-auth.js` line 8:

```javascript
// Replace this section:
const firebaseConfig = {
  apiKey: "your-api-key-here",
  authDomain: "your-project.firebaseapp.com",
  projectId: "your-project-id",
  storageBucket: "your-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "your-app-id",
};

// With your actual config from Step 3
```

### Step 6: Set Up Service Account (For Backend)

1. Go to **Project Settings** → **Service accounts**
2. Click **"Generate new private key"**
3. Download the JSON file
4. Save it as `serviceAccountKey.json` in your project root

**OR** use environment variables (recommended for production):

Create `.env` file:

```env
# Firebase Service Account
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYour-Private-Key-Here\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id

# Your existing keys
OPENAI_API_KEY=your-openai-key
SECRET_KEY=your-secret-key
```

### Step 7: Test the Setup

1. **Start your Flask app:**

   ```bash
   python app.py
   ```

2. **Visit:** `http://localhost:5000`

3. **Test Firebase Status:**

   - Visit: `http://localhost:5000/api/firebase-status`
   - Should return: `{"firebase_enabled": true, "firebase_initialized": true}`

4. **Test Authentication:**

   - Click "Sign In" button in navigation
   - Try creating an account with email/password
   - Try Google sign-in
   - Check that the button changes to show your name

5. **Test Data Storage:**
   - Ask the AI tutor a question
   - Generate and complete a quiz
   - Check Firebase Console → Firestore to see your data

## 🔧 Firestore Security Rules

Go to **Firestore** → **Rules** and update:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can only access their own data
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

## 📊 Expected Firestore Structure

After users start using your app:

```
users/
  {user-id}/
    uid: "firebase-user-id"
    email: "user@example.com"
    name: "User Name"
    createdAt: timestamp
    quizScores: [
      {
        subject: "Math",
        score: 4,
        totalQuestions: 5,
        timeTaken: 120,
        timestamp: timestamp
      }
    ]
    learningHistory: [
      {
        question: "What is photosynthesis?",
        subject: "Biology",
        aiResponse: "...",
        timestamp: timestamp
      }
    ]
    subscriptionStatus: "free"
    totalQuizzes: 3
    averageScore: 85.5
```

## 🛠️ Troubleshooting

### Firebase not working?

1. Check browser console for errors
2. Verify your config in `firebase-auth.js`
3. Check `/api/firebase-status` endpoint
4. Ensure you enabled Email/Password in Firebase Console

### Backend errors?

1. Make sure `firebase-admin` package is installed
2. Check your service account key path
3. Verify environment variables in `.env`
4. Check Flask terminal for error messages

### Authentication not persisting?

1. Check that your domain is authorized in Firebase Console
2. Verify Firebase config `authDomain` matches your project
3. Clear browser cache and cookies

## ✨ What You Get

- **User Accounts** - Students can sign up and sign in
- **Persistent Data** - Quiz scores and learning history saved
- **Google Sign-In** - Easy registration with Google accounts
- **Progress Tracking** - Individual student progress analytics
- **Secure API** - Protected endpoints with Firebase tokens
- **Scalable** - Ready for multiple users and production deployment

## 🎯 Next Steps

Now that you have Firebase authentication:

1. ✅ **Test everything works** with a few user accounts
2. 🔄 **Next**: Payment integration with user subscriptions
3. 🔄 **Then**: Production deployment with Firebase Hosting

Your SmartLearn platform is now enterprise-ready with user authentication! 🚀

---

**Need help?** Check the browser console and Flask terminal for specific error messages.
