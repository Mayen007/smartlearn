/**
 * Firebase Authentication Client-Side Configuration
 * Using CDN version for easier setup
 */

// Firebase Configuration - Replace with your actual config
const firebaseConfig = {
  apiKey: "AIzaSyBwl2LF9BB1bfJ3-QUf06YQY7C2Pr8b1A4",
  authDomain: "smartlearn-ai-90942.firebaseapp.com",
  projectId: "smartlearn-ai-90942",
  storageBucket: "smartlearn-ai-90942.firebasestorage.app",
  messagingSenderId: "208797441928",
  appId: "1:208797441928:web:a56c647a6532dc531c643d",
  measurementId: "G-B5TJ5CD0H8"
};

// Global variables
let firebaseApp = null;
let auth = null;
let currentUser = null;
let userToken = null;

// Initialize Firebase when DOM is loaded
document.addEventListener('DOMContentLoaded', function () {
  initializeFirebase();
});

function initializeFirebase() {
  console.log('🔍 initializeFirebase called');

  try {
    // Check if Firebase is loaded
    console.log('🔍 Checking Firebase availability...');
    console.log('🔍 typeof firebase:', typeof firebase);

    if (typeof firebase === 'undefined') {
      console.warn('❌ Firebase SDK not loaded from CDN');
      return;
    }

    console.log('🔍 Firebase SDK loaded, initializing...');
    console.log('🔍 Firebase config:', firebaseConfig);

    // Initialize Firebase
    firebaseApp = firebase.initializeApp(firebaseConfig);
    auth = firebase.auth();

    console.log('✅ Firebase initialized');
    console.log('🔍 Firebase app:', firebaseApp);
    console.log('🔍 Auth instance:', auth);

    // Check for redirect result first
    auth.getRedirectResult().then((result) => {
      if (result.user) {
        console.log('✅ Google Sign-In redirect successful:', result.user.email);
      } else {
        console.log('🔍 No redirect result');
      }
    }).catch((error) => {
      console.error('❌ Redirect result error:', error);
      if (error.code !== 'auth/no-redirect-operation') {
        showError('Sign-in failed: ' + error.message);
      }
    });

    // Set up auth state listener
    auth.onAuthStateChanged(handleAuthStateChange);

  } catch (error) {
    console.error('❌ Firebase initialization failed:', error);
  }
}

function handleAuthStateChange(user) {
  if (user) {
    currentUser = user;
    user.getIdToken().then(token => {
      userToken = token;
      updateUIForAuthenticatedUser(user);

      // Create user profile if it doesn't exist
      createUserProfileIfNeeded(user);
    });
  } else {
    currentUser = null;
    userToken = null;
    updateUIForUnauthenticatedUser();
  }
}

async function createUserProfileIfNeeded(user) {
  try {
    const response = await makeAuthenticatedRequest('/api/user-profile', {
      method: 'GET'
    });

    if (!response.ok) {
      // User profile doesn't exist, create it
      await makeAuthenticatedRequest('/api/create-user', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          uid: user.uid,
          email: user.email,
          name: user.displayName || user.email.split('@')[0]
        })
      });
    }
  } catch (error) {
    console.error('Error handling user profile:', error);
  }
}

// Authentication functions
const AuthManager = {
  async signUp(email, password, displayName) {
    try {
      if (!auth) throw new Error('Firebase not initialized');

      const userCredential = await auth.createUserWithEmailAndPassword(email, password);
      const user = userCredential.user;

      // Update profile with display name
      if (displayName) {
        await user.updateProfile({ displayName });
      }

      return { success: true, user };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  async signIn(email, password) {
    try {
      if (!auth) throw new Error('Firebase not initialized');

      const userCredential = await auth.signInWithEmailAndPassword(email, password);
      return { success: true, user: userCredential.user };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  async signInWithGoogle() {
    try {
      if (!auth) throw new Error('Firebase not initialized');

      console.log('🔍 Starting Google Sign-In...');

      const provider = new firebase.auth.GoogleAuthProvider();

      // Add additional scopes if needed
      provider.addScope('email');
      provider.addScope('profile');

      // Set custom parameters
      provider.setCustomParameters({
        prompt: 'select_account'
      });

      console.log('🔍 Opening Google popup...');
      const result = await auth.signInWithPopup(provider);

      console.log('✅ Google Sign-In successful:', result.user.email);
      return { success: true, user: result.user };
    } catch (error) {
      console.error('❌ Google Sign-In error:', error);

      // Handle specific error cases
      if (error.code === 'auth/popup-blocked') {
        console.log('🔄 Popup blocked, trying redirect...');
        try {
          await auth.signInWithRedirect(provider);
          return { success: true, user: null }; // Will be handled by redirect result
        } catch (redirectError) {
          return { success: false, error: 'Sign-in popup was blocked. Please allow popups for this site and try again.' };
        }
      } else if (error.code === 'auth/popup-closed-by-user') {
        return { success: false, error: 'Sign-in was cancelled.' };
      } else if (error.code === 'auth/cancelled-popup-request') {
        return { success: false, error: 'Another sign-in process is already in progress.' };
      }

      return { success: false, error: error.message || 'Failed to sign in with Google.' };
    }
  },

  async signOut() {
    try {
      if (!auth) throw new Error('Firebase not initialized');

      await auth.signOut();
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  },

  getCurrentUser() {
    return currentUser;
  },

  async getUserToken() {
    if (currentUser) {
      try {
        return await currentUser.getIdToken();
      } catch (error) {
        console.error('Error getting user token:', error);
        return null;
      }
    }
    return null;
  }
};

// UI Update functions
function updateUIForAuthenticatedUser(user) {
  // Hide auth section
  const authSection = document.getElementById('auth-section');
  if (authSection) {
    authSection.style.display = 'none';
  }

  // Show user section
  const userSection = document.getElementById('user-section');
  if (userSection) {
    userSection.style.display = 'block';
    userSection.innerHTML = `
            <div class="user-info">
                <span>Welcome, ${user.displayName || user.email}!</span>
                <button onclick="handleSignOut()" class="btn btn-secondary">Sign Out</button>
            </div>
        `;
  }

  // Show main app content
  const appContent = document.getElementById('app-content');
  if (appContent) {
    appContent.style.display = 'block';
  }

  console.log('✅ UI updated for authenticated user');
}

function updateUIForUnauthenticatedUser() {
  // Show auth section
  const authSection = document.getElementById('auth-section');
  if (authSection) {
    authSection.style.display = 'flex';
  }

  // Hide user section
  const userSection = document.getElementById('user-section');
  if (userSection) {
    userSection.style.display = 'none';
  }

  // Hide main app content
  const appContent = document.getElementById('app-content');
  if (appContent) {
    appContent.style.display = 'none';
  }

  console.log('ℹ️ UI updated for unauthenticated user');
}

// Global functions for HTML onclick handlers
window.handleSignIn = async function (email, password) {
  const result = await AuthManager.signIn(email, password);
  if (!result.success) {
    showError(result.error);
  }
};

window.handleSignUp = async function (email, password, displayName) {
  const result = await AuthManager.signUp(email, password, displayName);
  if (!result.success) {
    showError(result.error);
  }
};

window.handleGoogleSignIn = async function (event) {
  console.log('🔍 Google Sign-In clicked');
  console.log('🔍 Event:', event);
  console.log('🔍 Firebase available:', typeof firebase !== 'undefined');
  console.log('🔍 Auth available:', auth !== null);

  if (event) {
    event.preventDefault();
  }

  try {
    // Add loading state
    const button = event ? event.target : document.getElementById('google-signin-btn-1') || document.getElementById('google-signin-btn-2');
    console.log('🔍 Button found:', button);

    if (button) {
      const originalText = button.textContent;
      button.textContent = 'Signing in...';
      button.disabled = true;

      console.log('🔍 Button state updated, calling AuthManager.signInWithGoogle()');
      const result = await AuthManager.signInWithGoogle();
      console.log('🔍 AuthManager result:', result);

      // Reset button state
      button.textContent = originalText;
      button.disabled = false;

      if (!result.success) {
        console.error('❌ Google Sign-In failed:', result.error);
        showError(result.error);
      } else {
        console.log('✅ Google Sign-In successful');
      }
    } else {
      console.error('❌ Could not find button element');
      // Try without button state management
      console.log('🔍 Trying without button management...');
      const result = await AuthManager.signInWithGoogle();
      console.log('🔍 AuthManager result (no button):', result);

      if (!result.success) {
        console.error('❌ Google Sign-In failed:', result.error);
        showError(result.error);
      } else {
        console.log('✅ Google Sign-In successful');
      }
    }
  } catch (error) {
    console.error('❌ Google Sign-In error:', error);
    showError('Failed to sign in with Google. Please try again.');

    // Reset button state
    const button = event ? event.target : document.getElementById('google-signin-btn-1') || document.getElementById('google-signin-btn-2');
    if (button) {
      button.textContent = 'Continue with Google';
      button.disabled = false;
    }
  }
};

window.handleSignOut = async function () {
  const result = await AuthManager.signOut();
  if (result.success) {
    // Optionally redirect to home page
    window.location.reload();
  }
};

// Helper functions
async function makeAuthenticatedRequest(url, options = {}) {
  const token = await AuthManager.getUserToken();

  const authOptions = {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  };

  return fetch(url, authOptions);
}

function showError(message) {
  // Create a better error display
  console.error('Auth Error:', message);

  // Remove any existing error messages
  const existingError = document.querySelector('.auth-error-message');
  if (existingError) {
    existingError.remove();
  }

  // Create new error message element
  const errorDiv = document.createElement('div');
  errorDiv.className = 'auth-error-message';
  errorDiv.style.cssText = `
    background-color: #fee2e2;
    border: 1px solid #fecaca;
    color: #dc2626;
    padding: 12px;
    border-radius: 6px;
    margin: 10px 0;
    font-size: 14px;
  `;
  errorDiv.textContent = message;

  // Insert error message into the modal
  const authModal = document.querySelector('.auth-modal-content');
  if (authModal) {
    const firstForm = authModal.querySelector('.auth-form');
    if (firstForm) {
      firstForm.parentNode.insertBefore(errorDiv, firstForm);
    }
  }

  // Auto-remove error after 10 seconds
  setTimeout(() => {
    if (errorDiv && errorDiv.parentNode) {
      errorDiv.remove();
    }
  }, 10000);
}

function showAuthSection() {
  const authSection = document.getElementById('auth-section');
  if (authSection) {
    authSection.style.display = 'flex';
  }
}

function hideAuthSection() {
  const authSection = document.getElementById('auth-section');
  if (authSection) {
    authSection.style.display = 'none';
  }
}

// Tab switching functions
function showSignIn() {
  document.getElementById('signin-form').style.display = 'block';
  document.getElementById('signup-form').style.display = 'none';

  document.querySelectorAll('.auth-tab').forEach(tab => tab.classList.remove('active'));
  document.querySelector('.auth-tab[onclick="showSignIn()"]').classList.add('active');
}

function showSignUp() {
  document.getElementById('signin-form').style.display = 'none';
  document.getElementById('signup-form').style.display = 'block';

  document.querySelectorAll('.auth-tab').forEach(tab => tab.classList.remove('active'));
  document.querySelector('.auth-tab[onclick="showSignUp()"]').classList.add('active');
}

// Form handlers
function handleSignInForm(event) {
  event.preventDefault();
  const email = document.getElementById('signin-email').value;
  const password = document.getElementById('signin-password').value;
  handleSignIn(email, password);
}

function handleSignUpForm(event) {
  event.preventDefault();
  const name = document.getElementById('signup-name').value;
  const email = document.getElementById('signup-email').value;
  const password = document.getElementById('signup-password').value;
  handleSignUp(email, password, name);
}

// Export for other modules
window.FirebaseAuth = {
  AuthManager,
  makeAuthenticatedRequest,
  getCurrentUser: () => currentUser,
  getUserToken: () => AuthManager.getUserToken(),
  isAuthenticated: () => !!currentUser
};
