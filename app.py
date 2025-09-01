from flask import Flask, render_template, request, jsonify, session
import os
from dotenv import load_dotenv
from ai_tutor import get_ai_tutor
from student_session import StudentSession
from quiz_generator import get_quiz_generator
import uuid
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-123')

# Configure Flask-Session
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

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
        print(f"Error in ask_tutor route: {str(e)}")
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

        # Generate quiz
        quiz_generator_instance = get_quiz_generator()
        quiz_data = quiz_generator_instance.generate_quiz(
            subject, topic, difficulty, quiz_type, num_questions)

        # Get quiz statistics
        quiz_stats = quiz_generator_instance.get_quiz_statistics(quiz_data)

        # Add quiz to student session
        student_session = get_or_create_student_session()
        student_session.add_generated_quiz(quiz_data)

        return jsonify({
            'success': True,
            'quiz': quiz_data,
            'statistics': quiz_stats,
            'session_id': student_session.session_id
        })

    except Exception as e:
        print(f"Error generating quiz: {str(e)}")
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
        print(f"Error starting quiz: {str(e)}")
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
        print(f"Error submitting quiz: {str(e)}")
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
        print(f"Error in submit_quiz_result: {str(e)}")
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
        print(f"Error getting quiz history: {str(e)}")
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
        print(f"Error getting available quizzes: {str(e)}")
        return jsonify({'error': 'Failed to load available quizzes'}), 500


@app.route('/learning/dashboard')
def get_learning_dashboard():
    """Get personalized learning dashboard data"""
    try:
        student_session = get_or_create_student_session()

        dashboard_data = {
            'progress_summary': student_session.get_progress_summary(),
            'subject_analytics': student_session.get_subject_analytics(),
            'learning_recommendations': student_session.get_learning_recommendations(),
            'recent_activity': student_session.get_learning_history(5),
            'quiz_history': student_session.get_quiz_history(),
            'session_id': student_session.session_id
        }

        return jsonify(dashboard_data)

    except Exception as e:
        print(f"Error in get_learning_dashboard: {str(e)}")
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
        print(f"Error in get_learning_history: {str(e)}")
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
        print(f"Error in get_learning_recommendations: {str(e)}")
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
        print(f"Error in reset_session: {str(e)}")
        return jsonify({'error': 'Failed to reset session'}), 500


@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': 'SmartLearn AI Tutor',
        'phase': 'Phase 4 - Quiz Generator',
        'active_sessions': len(student_sessions)
    })


def get_or_create_student_session():
    """Get existing student session or create a new one"""
    session_id = session.get('student_session_id')

    if not session_id or session_id not in student_sessions:
        # Create new session
        session_id = str(uuid.uuid4())
        session['student_session_id'] = session_id
        student_sessions[session_id] = StudentSession(session_id)

    return student_sessions[session_id]


def get_learning_tip(student_session, subject):
    """Generate a contextual learning tip based on student's progress"""
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


if __name__ == '__main__':
    # Check if OpenAI API key is configured
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  WARNING: OPENAI_API_KEY not found in environment variables!")
        print("   The AI tutor will use fallback responses.")
        print("   To enable AI features, add your OpenAI API key to .env file")

    print("🚀 SmartLearn Phase 4 - Quiz Generator")
    print("   Features: AI quiz generation, Interactive quiz interface, Automated grading")

    app.run(debug=True, host='0.0.0.0', port=5000)
