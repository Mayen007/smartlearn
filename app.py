from flask import Flask, render_template, request, jsonify, session
import os
import logging
from dotenv import load_dotenv
from ai_tutor import get_ai_tutor
from student_session import StudentSession
from quiz_generator import get_quiz_generator
import uuid
from datetime import datetime
import requests
from payment_store import (
    init_payment_db,
    create_payment,
    update_payment_status,
    get_payment,
    list_payments,
    STATUS_COMPLETED,
    STATUS_FAILED,
    STATUS_PENDING
)
import hmac
import hashlib

# Firebase imports with error handling
try:
    from firebase_config import (
        initialize_firebase, require_auth, optional_auth,
        get_user_data, create_user_profile, save_quiz_result,
        save_learning_session, is_firebase_available
    )
    FIREBASE_ENABLED = True
except ImportError:
    FIREBASE_ENABLED = False
    print("⚠️ Firebase not available - running without authentication")

# Load environment variables
load_dotenv()

APP_PHASE = os.getenv('APP_PHASE', 'Phase 5 - Payments & Subscription')
APP_VERSION = os.getenv('APP_VERSION', '0.1.0')

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-123')

# Configure Flask-Session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# ----------------------------------------------------------------------------
# Logging Configuration
# ----------------------------------------------------------------------------
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
)
logger = logging.getLogger('smartlearn')
init_payment_db()

# Initialize Firebase if available
if FIREBASE_ENABLED:
    firebase_initialized = initialize_firebase()
    if firebase_initialized:
        logger.info("Firebase initialized successfully")
    else:
        logger.warning(
            "Firebase initialization failed - running in local mode")
        FIREBASE_ENABLED = False
else:
    logger.info("Running without Firebase authentication")

# In-memory storage for student sessions (in production, use Redis or database)
student_sessions = {}


@app.route('/')
def index():
    """Homepage with navigation and Ask the Tutor section"""
    return render_template('index.html')


@app.route('/ask', methods=['POST'])
def ask_tutor():
    """AI-powered tutor route using OpenAI GPT-4o with session tracking"""
    try:
        data = request.get_json()
        question = data.get('question', '')
        subject = data.get('subject', 'General')

        # Validate input
        if not question.strip():
            return jsonify({'error': 'Please provide a question'}), 400

        # Get or create student session
        student_session = get_or_create_student_session()

        # Generate AI-powered response
        ai_tutor_instance = get_ai_tutor()
        response = ai_tutor_instance.generate_answer(subject, question)

        # Track the question in student session
        student_session.add_question(subject, question, response)

        # Add session data to response
        response['session_id'] = student_session.session_id
        response['learning_tip'] = get_learning_tip(student_session, subject)

        return jsonify(response)

    except Exception as e:
        logger.exception("Error in ask_tutor route")
        # Fallback response
        fallback_response = {
            'answer': f"I'm experiencing some technical difficulties right now. Please try again in a moment. Your question was: '{question}' in {subject}.",
            'quiz_question': "What is the capital of Kenya?",
            'quiz_options': ["Nairobi", "Mombasa", "Kisumu", "Nakuru"],
            'quiz_answer': "Nairobi",
            'subject': subject
        }
        return jsonify(fallback_response)


@app.route('/quiz/generate', methods=['POST'])
def generate_quiz():
    """Generate a new AI-powered quiz"""
    try:
        data = request.get_json()
        subject = data.get('subject', 'General')
        topic = data.get('topic', 'General')
        difficulty = data.get('difficulty', 'intermediate')
        quiz_type = data.get('quiz_type', 'concept_check')
        num_questions = data.get('num_questions', 5)

        # Validate inputs
        if not subject or not topic:
            return jsonify({'error': 'Subject and topic are required'}), 400

        if difficulty not in ['beginner', 'intermediate', 'advanced']:
            difficulty = 'intermediate'

        if quiz_type not in ['concept_check', 'problem_solving', 'critical_thinking', 'application']:
            quiz_type = 'concept_check'

        if not isinstance(num_questions, int) or num_questions < 3 or num_questions > 10:
            num_questions = 5

        # Get session (needed for gating)
        student_session = get_or_create_student_session()

        # Enforce free plan quiz generation limit unless premium
        if not student_session.can_generate_quiz():
            remaining = student_session.remaining_free_quizzes()
            return jsonify({
                'success': False,
                'error': 'Quiz generation limit reached for Free plan. Please upgrade to Premium to unlock unlimited quizzes.',
                'plan': 'Free',
                'remaining_free_quizzes': remaining
            }), 402  # Payment Required semantic

        # Generate quiz (allowed)
        quiz_generator_instance = get_quiz_generator()
        quiz_data = quiz_generator_instance.generate_quiz(
            subject, topic, difficulty, quiz_type, num_questions)

        # Get quiz statistics
        quiz_stats = quiz_generator_instance.get_quiz_statistics(quiz_data)
        # Add quiz to student session (increments generation counter)
        student_session.add_generated_quiz(quiz_data)

        return jsonify({
            'success': True,
            'quiz': quiz_data,
            'statistics': quiz_stats,
            'session_id': student_session.session_id
        })

    except Exception as e:
        logger.exception("Error generating quiz")
        return jsonify({'error': 'Failed to generate quiz'}), 500


@app.route('/quiz/<quiz_id>/start', methods=['POST'])
def start_quiz(quiz_id):
    """Start a quiz session"""
    try:
        student_session = get_or_create_student_session()

        # Find the quiz in the session
        quiz_data = student_session.get_quiz(quiz_id)
        if not quiz_data:
            return jsonify({'error': 'Quiz not found'}), 404

        # Start quiz session
        quiz_session = student_session.start_quiz_session(quiz_id, quiz_data)

        return jsonify({
            'success': True,
            'quiz_session': quiz_session,
            'quiz_data': quiz_data
        })

    except Exception as e:
        logger.exception("Error starting quiz")
        return jsonify({'error': 'Failed to start quiz'}), 500


@app.route('/quiz/<quiz_id>/submit', methods=['POST'])
def submit_quiz(quiz_id):
    """Submit completed quiz answers"""
    try:
        data = request.get_json()
        answers = data.get('answers', [])
        time_taken = data.get('time_taken', 0)

        student_session = get_or_create_student_session()

        # Get quiz data
        quiz_data = student_session.get_quiz(quiz_id)
        if not quiz_data:
            return jsonify({'error': 'Quiz not found'}), 404

        # Grade the quiz
        quiz_generator_instance = get_quiz_generator()
        quiz_results = quiz_generator_instance.grade_quiz(quiz_data, answers)
        quiz_results['time_taken'] = time_taken

        # Record quiz attempt in student session
        student_session.add_quiz_attempt(
            quiz_data['subject'],
            quiz_data,
            quiz_results['score_percentage'],
            time_taken
        )

        # Update quiz session
        student_session.complete_quiz_session(quiz_id, quiz_results)

        return jsonify({
            'success': True,
            'results': quiz_results,
            'session_id': student_session.session_id
        })

    except Exception as e:
        logger.exception("Error submitting quiz")
        return jsonify({'error': 'Failed to submit quiz'}), 500


@app.route('/quiz/result', methods=['POST'])
def submit_quiz_result():
    """Submit quiz results and track performance (legacy endpoint)"""
    try:
        data = request.get_json()
        subject = data.get('subject', 'General')
        quiz_data = data.get('quiz_data', {})
        score = data.get('score', 0)
        time_taken = data.get('time_taken', 0)

        # Get student session
        student_session = get_or_create_student_session()

        # Track quiz attempt
        student_session.add_quiz_attempt(subject, quiz_data, score, time_taken)

        return jsonify({
            'success': True,
            'message': 'Quiz result recorded successfully',
            'session_id': student_session.session_id
        })

    except Exception as e:
        logger.exception("Error in submit_quiz_result")
        return jsonify({'error': 'Failed to record quiz result'}), 500


@app.route('/quiz/history')
def get_quiz_history():
    """Get quiz history for the current session"""
    try:
        student_session = get_or_create_student_session()
        quiz_history = student_session.get_quiz_history()

        return jsonify({
            'quiz_history': quiz_history,
            'session_id': student_session.session_id
        })

    except Exception as e:
        logger.exception("Error getting quiz history")
        return jsonify({'error': 'Failed to load quiz history'}), 500


@app.route('/quiz/available')
def get_available_quizzes():
    """Get available quiz topics and subjects"""
    try:
        # Define available quiz topics
        available_quizzes = {
            'Mathematics': ['Algebra', 'Geometry', 'Trigonometry', 'Calculus', 'Statistics'],
            'Physics': ['Mechanics', 'Electricity', 'Waves', 'Optics', 'Modern Physics'],
            'Biology': ['Cell Biology', 'Genetics', 'Ecology', 'Evolution', 'Human Biology'],
            'Chemistry': ['Organic Chemistry', 'Inorganic Chemistry', 'Physical Chemistry', 'Analytical Chemistry'],
            'History': ['Ancient History', 'Medieval History', 'Modern History', 'African History', 'World History'],
            'Geography': ['Physical Geography', 'Human Geography', 'Economic Geography', 'Political Geography', 'Climate']
        }

        return jsonify({
            'available_quizzes': available_quizzes,
            'difficulty_levels': ['beginner', 'intermediate', 'advanced'],
            'quiz_types': ['concept_check', 'problem_solving', 'critical_thinking', 'application']
        })

    except Exception as e:
        logger.exception("Error getting available quizzes")
        return jsonify({'error': 'Failed to load available quizzes'}), 500


@app.route('/learning/dashboard')
def get_learning_dashboard():
    """Get personalized learning dashboard data (student view)."""
    try:
        student_session = get_or_create_student_session()

        progress_summary = student_session.get_progress_summary()
        subject_analytics = student_session.get_subject_analytics()
        recent_activity = student_session.get_learning_history(5)
        quiz_history = student_session.get_quiz_history()
        learning_recommendations = student_session.get_learning_recommendations()

        # Base payload
        dashboard_data = {
            'session_id': student_session.session_id,
            'progress_summary': progress_summary,
            'subject_analytics': subject_analytics,
            'learning_recommendations': learning_recommendations,
            'recent_activity': recent_activity,
            'quiz_history': quiz_history,
            'subscription': {
                'plan': 'Premium' if student_session.is_premium else 'Free',
                'quiz_generations': student_session.quiz_generations,
                'free_quiz_limit': student_session.free_quiz_limit,
                'remaining_free_quizzes': student_session.remaining_free_quizzes()
            }
        }

        return jsonify(dashboard_data)

    except Exception as e:
        logger.exception("Error in get_learning_dashboard")
        return jsonify({'error': 'Failed to load dashboard data'}), 500


@app.route('/learning/history')
def get_learning_history():
    """Get learning history for the current session"""
    try:
        student_session = get_or_create_student_session()
        limit = request.args.get('limit', 10, type=int)

        history = student_session.get_learning_history(limit)

        return jsonify({
            'history': history,
            'session_id': student_session.session_id
        })

    except Exception as e:
        logger.exception("Error in get_learning_history")
        return jsonify({'error': 'Failed to load learning history'}), 500


@app.route('/learning/recommendations')
def get_learning_recommendations():
    """Get personalized learning recommendations"""
    try:
        student_session = get_or_create_student_session()
        recommendations = student_session.get_learning_recommendations()

        return jsonify({
            'recommendations': recommendations,
            'session_id': student_session.session_id
        })

    except Exception as e:
        logger.exception("Error in get_learning_recommendations")
        return jsonify({'error': 'Failed to load recommendations'}), 500


@app.route('/session/reset', methods=['POST'])
def reset_session():
    """Reset the current student session"""
    try:
        session_id = session.get('student_session_id')
        if session_id and session_id in student_sessions:
            del student_sessions[session_id]

        # Clear session
        session.pop('student_session_id', None)

        return jsonify({
            'success': True,
            'message': 'Session reset successfully'
        })

    except Exception as e:
        logger.exception("Error in reset_session")
        return jsonify({'error': 'Failed to reset session'}), 500


@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': 'SmartLearn AI Tutor',
        'phase': APP_PHASE,
        'version': APP_VERSION,
        'active_sessions': len(student_sessions)
    })


def get_or_create_student_session() -> StudentSession:
    """Get existing student session or create a new one.

    Returns:
        StudentSession: The active (existing or newly created) session object.
    """
    session_id = session.get('student_session_id')

    if not session_id or session_id not in student_sessions:
        # Create new session
        session_id = str(uuid.uuid4())
        session['student_session_id'] = session_id
        student_sessions[session_id] = StudentSession(session_id)

    return student_sessions[session_id]


def get_learning_tip(student_session: StudentSession, subject: str) -> str:
    """Generate a contextual learning tip based on student's progress.

    Args:
        student_session: The current student session instance.
        subject: Subject/topic string provided by the user.

    Returns:
        str: A short learning tip.
    """
    progress = student_session.get_progress_summary()

    if progress['total_questions'] == 0:
        return f"Welcome to SmartLearn! Start by asking questions about {subject} to build your learning profile."

    if progress['total_questions'] < 3:
        return f"Great start! Keep asking questions about {subject} to unlock personalized recommendations."

    # Get subject-specific analytics
    subject_analytics = student_session.get_subject_analytics()
    if subject in subject_analytics:
        avg_score = subject_analytics[subject]['average_quiz_score']
        if avg_score > 0:
            if avg_score >= 80:
                return f"Excellent work in {subject}! You're mastering the concepts. Try more challenging questions."
            elif avg_score >= 60:
                return f"Good progress in {subject}! Focus on areas where you scored lower to improve."
            else:
                return f"Keep practicing {subject}! Review the basics and ask for clarification on difficult concepts."

    return f"Keep exploring {subject}! Every question helps us understand your learning needs better."


# ====================================================================
# FIREBASE AUTHENTICATION ROUTES (Only available if Firebase is enabled)
# ====================================================================

if FIREBASE_ENABLED:

    @app.route('/api/create-user', methods=['POST'])
    @require_auth
    def create_user_api():
        """Create user profile in Firestore"""
        try:
            data = request.get_json()
            uid = data.get('uid') or request.user['uid']
            email = data.get('email') or request.user['email']
            name = data.get('name') or request.user.get(
                'name', email.split('@')[0])

            # Create user profile
            user_profile = create_user_profile(uid, email, name)

            if user_profile:
                return jsonify({
                    'success': True,
                    'message': 'User profile created successfully',
                    'user': user_profile
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to create user profile'
                }), 500

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error creating user profile: {str(e)}'
            }), 500

    @app.route('/api/user-profile', methods=['GET'])
    @require_auth
    def get_user_profile_api():
        """Get user profile data"""
        try:
            uid = request.user['uid']
            user_data = get_user_data(uid)

            if user_data:
                return jsonify({
                    'success': True,
                    'user': user_data
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'User profile not found'
                }), 404

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error getting user profile: {str(e)}'
            }), 500

    @app.route('/api/save-quiz-result', methods=['POST'])
    @require_auth
    def save_quiz_result_api():
        """Save quiz result for authenticated user"""
        try:
            uid = request.user['uid']
            data = request.get_json()

            quiz_data = {
                'subject': data.get('subject'),
                'score': data.get('score'),
                'totalQuestions': data.get('totalQuestions'),
                'timeTaken': data.get('timeTaken'),
                'difficulty': data.get('difficulty', 'medium'),
                'questions': data.get('questions', [])
            }

            success = save_quiz_result(uid, quiz_data)

            if success:
                return jsonify({
                    'success': True,
                    'message': 'Quiz result saved successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to save quiz result'
                }), 500

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error saving quiz result: {str(e)}'
            }), 500

    @app.route('/api/save-learning-session', methods=['POST'])
    @require_auth
    def save_learning_session_api():
        """Save learning session for authenticated user"""
        try:
            uid = request.user['uid']
            data = request.get_json()

            session_data = {
                'question': data.get('question'),
                'subject': data.get('subject'),
                'aiResponse': data.get('aiResponse'),
                'sessionType': data.get('sessionType', 'question')
            }

            success = save_learning_session(uid, session_data)

            if success:
                return jsonify({
                    'success': True,
                    'message': 'Learning session saved successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Failed to save learning session'
                }), 500

        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error saving learning session: {str(e)}'
            }), 500

    @app.route('/api/firebase-status', methods=['GET'])
    def firebase_status():
        """Check Firebase status"""
        return jsonify({
            'firebase_enabled': FIREBASE_ENABLED,
            'firebase_initialized': is_firebase_available()
        })

else:
    # Firebase disabled routes
    @app.route('/api/firebase-status', methods=['GET'])
    def firebase_status():
        """Check Firebase status"""
        return jsonify({
            'firebase_enabled': False,
            'firebase_initialized': False,
            'message': 'Firebase is not available'
        })


INTASEND_PUBLIC_KEY = os.getenv('INTASEND_PUBLIC_KEY')  # publishable key
INTASEND_SECRET_KEY = os.getenv('INTASEND_SECRET_KEY')  # secret key for server
# separate webhook signing secret (recommended)
INTASEND_WEBHOOK_SECRET = os.getenv('INTASEND_WEBHOOK_SECRET')
# Auto-detect environment based on key prefix
if INTASEND_SECRET_KEY and INTASEND_SECRET_KEY.startswith('ISSecretKey_live_'):
    INTASEND_BASE_URL = os.getenv(
        'INTASEND_BASE_URL', 'https://payment.intasend.com/api/v1')
else:
    INTASEND_BASE_URL = os.getenv(
        'INTASEND_BASE_URL', 'https://sandbox.intasend.com/api/v1')


def create_intasend_checkout(amount: float, email: str, reference: str):
    """Create an IntaSend checkout session.

    Returns a dict with keys:
      success (bool), checkout_url (str|None), provider_data (dict|None), error (str|None)
    """
    if not INTASEND_SECRET_KEY:
        return {'success': False, 'error': 'INTASEND_SECRET_KEY not configured', 'checkout_url': None, 'provider_data': None}

    headers = {
        'Authorization': f'Bearer {INTASEND_SECRET_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {
        'amount': amount,
        'currency': os.getenv('INTASEND_CURRENCY', 'KES'),
        'email': email or 'anonymous@example.com',
        'comment': 'SmartLearn Premium Upgrade',
        'reference': reference,
        'redirect_url': os.getenv('INTASEND_REDIRECT_URL', 'http://localhost:5000/payment/complete')
    }
    if INTASEND_PUBLIC_KEY:
        # Some IntaSend endpoints accept / require public key (harmless if ignored)
        payload['public_key'] = INTASEND_PUBLIC_KEY

    try:
        logger.info('Creating IntaSend checkout: ref=%s amount=%.2f base=%s',
                    reference, amount, INTASEND_BASE_URL)
        resp = requests.post(f'{INTASEND_BASE_URL}/checkout/',
                             json=payload, headers=headers, timeout=20)
        logger.info('IntaSend response status: %d', resp.status_code)
        if resp.status_code not in (200, 201):
            snippet = resp.text[:500]
            logger.error('IntaSend error creating checkout ref=%s status=%s body=%s',
                         reference, resp.status_code, snippet)
            return {'success': False, 'error': f'Provider error {resp.status_code}', 'checkout_url': None, 'provider_data': None}
        data = resp.json()
        checkout_url = data.get('url') or data.get(
            'checkout_url') or data.get('hosted_url')
        if not checkout_url:
            logger.error(
                'IntaSend response missing checkout URL ref=%s body=%s', reference, data)
            return {'success': False, 'error': 'Missing checkout URL in provider response', 'checkout_url': None, 'provider_data': data}
        logger.info('IntaSend checkout created ref=%s url=%s',
                    reference, checkout_url)
        return {'success': True, 'checkout_url': checkout_url, 'provider_data': data, 'error': None}
    except Exception as e:
        logger.exception(
            'Exception creating IntaSend checkout ref=%s', reference)
        return {'success': False, 'error': str(e), 'checkout_url': None, 'provider_data': None}


@app.route('/payment/upgrade', methods=['POST'])
def start_upgrade():
    """Initiate a Premium upgrade checkout and return payment URL."""
    try:
        student_session = get_or_create_student_session()
        if student_session.is_premium:
            return jsonify({'success': True, 'message': 'Already Premium', 'already_premium': True})

        data = request.get_json() or {}
        email = data.get('email') or 'student@example.com'

        amount = float(os.getenv('PREMIUM_PRICE', '100'))  # KES 100 default
        reference = f'PREMIUM-{student_session.session_id[:8]}'

        # Check IntaSend configuration
        if not INTASEND_SECRET_KEY:
            logger.error(
                'IntaSend not configured - missing INTASEND_SECRET_KEY')
            return jsonify({'success': False, 'error': 'Payment system not configured. Please contact support.'}), 500

        result = create_intasend_checkout(amount, email, reference)
        if not result.get('success'):
            return jsonify({'success': False, 'error': result.get('error') or 'Payment provider temporarily unavailable.'}), 502

        # Persist payment intent (only if checkout created)
        create_payment(reference, email, amount, student_session.session_id)

        return jsonify({'success': True, 'checkout_url': result['checkout_url'], 'reference': reference})
    except Exception as e:
        logger.exception('Error starting upgrade')
        return jsonify({'success': False, 'error': f'Upgrade failed: {str(e)}'}), 500


@app.route('/payment/complete')
def payment_complete():
    """Landing page / redirect after payment (simplified).
    In a real app you'd verify transaction via IntaSend API before upgrading.
    """
    student_session = get_or_create_student_session()
    # DO NOT auto-upgrade here; rely on webhook or manual verification
    return render_template('index.html')


@app.route('/payment/status')
def payment_status():
    """Return current subscription status."""
    student_session = get_or_create_student_session()
    reference = request.args.get('reference')
    payment_info = get_payment(reference) if reference else None
    return jsonify({
        'plan': 'Premium' if student_session.is_premium else 'Free',
        'quiz_generations': student_session.quiz_generations,
        'free_quiz_limit': student_session.free_quiz_limit,
        'remaining_free_quizzes': student_session.remaining_free_quizzes(),
        'payment': payment_info
    })


@app.route('/payment/verify/<reference>', methods=['POST'])
def payment_verify(reference):
    """Manually verify payment status with IntaSend (fallback if webhook delayed).

    NOTE: Endpoint shape guessed; adjust to match IntaSend's transaction/invoice lookup.
    """
    try:
        if not INTASEND_SECRET_KEY:
            return jsonify({'success': False, 'error': 'Not configured'}), 500
        # Basic lookup only if currently pending
        local = get_payment(reference)
        if not local:
            return jsonify({'success': False, 'error': 'Unknown reference'}), 404
        if local['status'] == STATUS_COMPLETED:
            return jsonify({'success': True, 'status': local['status'], 'already_completed': True})
        headers = {
            'Authorization': f'Bearer {INTASEND_SECRET_KEY}'
        }
        # Attempt a generic GET - adjust path according to real API (placeholder)
        verify_url = f"{INTASEND_BASE_URL}/checkout/{reference}/"
        resp = requests.get(verify_url, headers=headers, timeout=15)
        logger.info('Verify call ref=%s status=%s',
                    reference, resp.status_code)
        if resp.status_code == 404:
            return jsonify({'success': False, 'error': 'Provider reference not found'}), 404
        if resp.status_code >= 400:
            return jsonify({'success': False, 'error': f'Provider error {resp.status_code}'}), 502
        data = {}
        try:
            data = resp.json()
        except Exception:
            pass
        # Heuristics for status keys
        provider_status = (data.get('status') or data.get(
            'payment_status') or '').lower()
        if provider_status in ('paid', 'completed', 'success'):
            update_payment_status(reference, STATUS_COMPLETED, data.get(
                'transaction_id') or data.get('id'), data)
            # Upgrade session if possible
            refreshed = get_payment(reference)
            sid = refreshed.get('session_id') if refreshed else None
            if sid and sid in student_sessions:
                student_sessions[sid].upgrade_to_premium()
        elif provider_status in ('failed', 'cancelled', 'canceled', 'error'):
            update_payment_status(reference, STATUS_FAILED, data.get(
                'transaction_id') or data.get('id'), data)
        return jsonify({'success': True, 'provider_status': provider_status, 'local_status': get_payment(reference)['status'], 'provider_raw': data})
    except Exception:
        logger.exception('Manual verify failed ref=%s', reference)
        return jsonify({'success': False, 'error': 'Verification failed'}), 500


@app.route('/payment/webhook', methods=['POST'])
def payment_webhook():
    """Handle IntaSend webhook (simplified – add signature verification in prod)."""
    try:
        raw_body = request.get_data()  # bytes
        sig_header = request.headers.get(
            'X-IntaSend-Signature') or request.headers.get('X-INTASEND-SIGNATURE')
        # Optional signature verification if secret configured
        if INTASEND_WEBHOOK_SECRET:
            if not sig_header:
                logger.warning('Webhook rejected: missing signature header')
                return jsonify({'success': False, 'error': 'Missing signature'}), 400
            try:
                expected = hmac.new(INTASEND_WEBHOOK_SECRET.encode(
                    'utf-8'), raw_body, hashlib.sha256).hexdigest()
                if not hmac.compare_digest(expected, sig_header.strip()):
                    logger.warning(
                        'Webhook signature mismatch expected=%s got=%s', expected, sig_header)
                    return jsonify({'success': False, 'error': 'Invalid signature'}), 400
            except Exception:
                logger.exception('Error verifying webhook signature')
                return jsonify({'success': False, 'error': 'Signature verification error'}), 400
        payload = request.get_json(silent=True) or {}
        reference = payload.get('reference') or payload.get('invoice')
        status = payload.get('status')
        transaction_id = payload.get('transaction_id') or payload.get('id')
        if not reference:
            return jsonify({'success': False, 'error': 'Missing reference'}), 400
        normalized_status = STATUS_PENDING
        if status and isinstance(status, str):
            status_l = status.lower()
            if status_l in ('paid', 'completed', 'success'):
                normalized_status = STATUS_COMPLETED
            elif status_l in ('failed', 'cancelled', 'canceled', 'error'):
                normalized_status = STATUS_FAILED
        update_payment_status(reference, normalized_status,
                              transaction_id, payload)
        # Auto-upgrade associated session if completed
        if normalized_status == STATUS_COMPLETED:
            payment_record = get_payment(reference)
            if payment_record:
                sid = payment_record.get('session_id')
                if sid and sid in student_sessions:
                    student_sessions[sid].upgrade_to_premium()
        return jsonify({'success': True})
    except Exception:
        logger.exception('Webhook processing failed')
        return jsonify({'success': False, 'error': 'Webhook processing failed'}), 500


@app.route('/admin/payments')
def admin_list_payments():
    payments = list_payments(100)
    return jsonify({'payments': payments})


@app.route('/debug/config')
def debug_config():
    """Debug endpoint to check IntaSend configuration."""
    return jsonify({
        'intasend_secret_key_configured': bool(INTASEND_SECRET_KEY),
        'intasend_secret_key_prefix': INTASEND_SECRET_KEY[:20] + '...' if INTASEND_SECRET_KEY else None,
        'intasend_base_url': INTASEND_BASE_URL,
        'premium_price': os.getenv('PREMIUM_PRICE', '100'),
        'is_live_mode': INTASEND_SECRET_KEY.startswith('ISSecretKey_live_') if INTASEND_SECRET_KEY else False,
        'public_key_configured': bool(INTASEND_PUBLIC_KEY),
        'webhook_signature_enforced': bool(INTASEND_WEBHOOK_SECRET)
    })


if __name__ == '__main__':
    if not os.getenv('OPENAI_API_KEY'):
        logger.warning(
            'OPENAI_API_KEY not found – AI tutor will use fallback responses.')
        logger.info(
            'Add your OpenAI key to the .env file to enable full AI features.')

    logger.info('🚀 Starting SmartLearn (%s | %s)', APP_PHASE, APP_VERSION)
    app.run(debug=True, host='0.0.0.0', port=5000)
