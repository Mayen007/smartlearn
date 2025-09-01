"""SmartLearn Student Session Manager
Handles session-based student tracking, question history, learning analytics, and quiz management."""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import random
import uuid


class StudentSession:
    def __init__(self, session_id: str):
        """Initialize a new student session."""
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_activity = datetime.now()

        # Learning data
        self.questions_asked: List[Dict] = []
        self.quiz_attempts: List[Dict] = []
        self.subjects_explored = set()
        self.learning_strengths = defaultdict(int)
        self.learning_gaps = defaultdict(int)

        # Quiz management (Phase 4)
        self.generated_quizzes: Dict[str, Dict] = {}
        self.quiz_sessions: Dict[str, Dict] = {}
        self.quiz_history: List[Dict] = []

        # Subscription / payments (Phase 6)
        self.is_premium: bool = False  # upgraded after successful payment
        self.quiz_generations: int = 0  # number of quizzes generated this session
        self.free_quiz_limit: int = 3  # free tier limit

        # Session preferences
        self.preferred_subjects: List[str] = []
        self.difficulty_level: str = "intermediate"
        self.learning_style: str = "visual"  # visual, auditory, kinesthetic

    def add_question(self, subject: str, question: str, ai_response: Dict):
        """Record a new question and AI response."""
        question_data = {
            'id': len(self.questions_asked) + 1,
            'timestamp': datetime.now().isoformat(),
            'subject': subject,
            'question': question,
            'ai_response': ai_response,
            'topic': self._extract_topic(question, subject),
            'difficulty': self._assess_difficulty(question, subject)
        }
        self.questions_asked.append(question_data)
        self.subjects_explored.add(subject)
        self.last_activity = datetime.now()
        self._update_learning_analytics(question_data)

    def add_quiz_attempt(self, subject: str, quiz_data: Dict, score: int, time_taken: int):
        """Record a quiz attempt."""
        quiz_attempt = {
            'id': len(self.quiz_attempts) + 1,
            'timestamp': datetime.now().isoformat(),
            'subject': subject,
            'quiz_data': quiz_data,
            'score': score,
            'time_taken': time_taken,
            'topic': quiz_data.get('topic', 'General')
        }
        self.quiz_attempts.append(quiz_attempt)
        self.last_activity = datetime.now()
        self._update_performance_analytics(quiz_attempt)

    def add_generated_quiz(self, quiz_data: Dict) -> str:
        """Add a generated quiz to the session and return quiz ID."""
        quiz_id = str(uuid.uuid4())
        quiz_record = {
            'id': quiz_id,
            'timestamp': datetime.now().isoformat(),
            'quiz_data': quiz_data,
            'status': 'generated',
            'started_at': None,
            'completed_at': None,
            'results': None
        }
        self.generated_quizzes[quiz_id] = quiz_record
        self.last_activity = datetime.now()
        self.quiz_generations += 1
        return quiz_id

    def get_quiz(self, quiz_id: str) -> Optional[Dict]:
        """Get quiz data by ID"""
        if quiz_id in self.generated_quizzes:
            return self.generated_quizzes[quiz_id]['quiz_data']
        return None

    def start_quiz_session(self, quiz_id: str, quiz_data: Dict) -> Dict:
        """Start a quiz session"""
        if quiz_id not in self.generated_quizzes:
            raise ValueError("Quiz not found")

        quiz_record = self.generated_quizzes[quiz_id]
        quiz_record['status'] = 'started'
        quiz_record['started_at'] = datetime.now().isoformat()

        # Create quiz session
        quiz_session = {
            'quiz_id': quiz_id,
            'started_at': quiz_record['started_at'],
            'time_limit': quiz_data.get('metadata', {}).get('time_limit', 600),
            'current_question': 0,
            'answers': [],
            'start_time': datetime.now()
        }

        self.quiz_sessions[quiz_id] = quiz_session
        self.last_activity = datetime.now()

        return quiz_session

    def complete_quiz_session(self, quiz_id: str, results: Dict):
        """Complete a quiz session with results"""
        if quiz_id not in self.generated_quizzes:
            raise ValueError("Quiz not found")

        quiz_record = self.generated_quizzes[quiz_id]
        quiz_record['status'] = 'completed'
        quiz_record['completed_at'] = datetime.now().isoformat()
        quiz_record['results'] = results

        # Remove from active sessions
        if quiz_id in self.quiz_sessions:
            del self.quiz_sessions[quiz_id]

        # Add to quiz history
        history_entry = {
            'quiz_id': quiz_id,
            'timestamp': quiz_record['completed_at'],
            'subject': quiz_record['quiz_data'].get('subject', 'Unknown'),
            'topic': quiz_record['quiz_data'].get('topic', 'Unknown'),
            'difficulty': quiz_record['quiz_data'].get('difficulty', 'intermediate'),
            'score': results.get('score_percentage', 0),
            'time_taken': results.get('time_taken', 0),
            'total_questions': results.get('total_questions', 0),
            'correct_answers': results.get('correct_answers', 0)
        }

        self.quiz_history.append(history_entry)
        self.last_activity = datetime.now()

        # Update learning analytics based on quiz performance
        self._update_quiz_analytics(history_entry)

    def get_quiz_history(self) -> List[Dict]:
        """Get quiz history for the session"""
        return sorted(self.quiz_history, key=lambda x: x['timestamp'], reverse=True)

    def get_active_quizzes(self) -> List[Dict]:
        """Get all active (generated but not completed) quizzes"""
        active_quizzes = []
        for quiz_id, quiz_record in self.generated_quizzes.items():
            if quiz_record['status'] in ['generated', 'started']:
                active_quizzes.append({
                    'quiz_id': quiz_id,
                    'quiz_data': quiz_record['quiz_data'],
                    'status': quiz_record['status'],
                    'generated_at': quiz_record['timestamp']
                })
        return active_quizzes

    def get_learning_history(self, limit: int = 10) -> List[Dict]:
        """Get recent learning history including quizzes"""
        recent_questions = self.questions_asked[-limit:
                                                ] if self.questions_asked else []
        recent_quizzes = self.quiz_attempts[-limit:] if self.quiz_attempts else []

        # Combine and sort by timestamp
        all_activities = []
        for q in recent_questions:
            all_activities.append({
                'type': 'question',
                'data': q,
                'timestamp': q['timestamp']
            })

        for q in recent_quizzes:
            all_activities.append({
                'type': 'quiz',
                'data': q,
                'timestamp': q['timestamp']
            })

        # Sort by timestamp (newest first)
        all_activities.sort(key=lambda x: x['timestamp'], reverse=True)
        return all_activities[:limit]

    def get_subject_analytics(self) -> Dict:
        """Get analytics by subject including quiz performance"""
        analytics = {}

        for subject in self.subjects_explored:
            subject_questions = [
                q for q in self.questions_asked if q['subject'] == subject]
            subject_quizzes = [
                q for q in self.quiz_attempts if q['subject'] == subject]

            # Get quiz performance for this subject
            quiz_scores = [q['score'] for q in subject_quizzes]
            avg_quiz_score = sum(quiz_scores) / \
                len(quiz_scores) if quiz_scores else 0

            analytics[subject] = {
                'questions_asked': len(subject_questions),
                'quiz_attempts': len(subject_quizzes),
                'average_quiz_score': avg_quiz_score,
                'topics_covered': list(set(q['topic'] for q in subject_questions)),
                'last_activity': max([q['timestamp'] for q in subject_questions + subject_quizzes]) if subject_questions or subject_quizzes else None,
                'quiz_performance': {
                    'total_quizzes': len(subject_quizzes),
                    'high_scores': len([s for s in quiz_scores if s >= 80]),
                    'improvement_needed': len([s for s in quiz_scores if s < 60])
                }
            }

        return analytics

    def get_learning_recommendations(self) -> List[Dict]:
        """Generate personalized learning recommendations including quiz suggestions"""
        recommendations = []

        # Analyze learning patterns
        weak_subjects = self._identify_weak_subjects()
        unexplored_topics = self._identify_unexplored_topics()
        learning_gaps = self._identify_learning_gaps()
        quiz_performance = self._analyze_quiz_performance()

        # Generate recommendations
        if weak_subjects:
            recommendations.append({
                'type': 'subject_focus',
                'priority': 'high',
                'title': f'Focus on {weak_subjects[0]}',
                'description': f'You\'ve shown some challenges in {weak_subjects[0]}. Consider reviewing fundamental concepts.',
                'action': f'Take a beginner quiz on {weak_subjects[0]} basics',
                'subject': weak_subjects[0]
            })

        if unexplored_topics:
            recommendations.append({
                'type': 'topic_exploration',
                'priority': 'medium',
                'title': f'Explore {unexplored_topics[0]}',
                'description': f'You haven\'t covered {unexplored_topics[0]} yet. This could expand your knowledge.',
                'action': f'Generate a quiz on {unexplored_topics[0]}',
                'subject': 'General'
            })

        if learning_gaps:
            recommendations.append({
                'type': 'gap_filling',
                'priority': 'high',
                'title': 'Fill Knowledge Gaps',
                'description': f'Review {learning_gaps[0]} to strengthen your foundation.',
                'action': f'Practice {learning_gaps[0]} concepts with targeted quizzes',
                'subject': 'General'
            })

        # Quiz-specific recommendations
        if quiz_performance['low_performance_areas']:
            weak_topic = quiz_performance['low_performance_areas'][0]
            recommendations.append({
                'type': 'quiz_practice',
                'priority': 'high',
                'title': f'Practice {weak_topic}',
                'description': f'Your quiz performance in {weak_topic} suggests you need more practice.',
                'action': f'Take more quizzes on {weak_topic}',
                'subject': 'General'
            })

        if quiz_performance['strength_areas']:
            strong_topic = quiz_performance['strength_areas'][0]
            recommendations.append({
                'type': 'quiz_advancement',
                'priority': 'medium',
                'title': f'Advance in {strong_topic}',
                'description': f'You\'re doing well in {strong_topic}. Try more challenging questions.',
                'action': f'Take an advanced quiz on {strong_topic}',
                'subject': 'General'
            })

        # Add general learning recommendations
        if len(self.questions_asked) < 5:
            recommendations.append({
                'type': 'engagement',
                'priority': 'medium',
                'title': 'Build Learning Momentum',
                'description': 'Start with simple questions to build confidence.',
                'action': 'Ask any question that comes to mind',
                'subject': 'General'
            })

        # Sort by priority
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        recommendations.sort(key=lambda x: priority_order.get(
            x['priority'], 0), reverse=True)

        return recommendations[:5]  # Return top 5 recommendations

    def get_progress_summary(self) -> Dict:
        """Return aggregate session progress summary."""
        total_questions = len(self.questions_asked)
        total_quizzes = len(self.quiz_attempts)
        quiz_scores = [q['score'] for q in self.quiz_attempts]
        average_quiz_score = sum(quiz_scores) / len(quiz_scores) if quiz_scores else 0
        # Calculate session duration
        session_duration_minutes = int((datetime.now() - self.created_at).total_seconds() / 60)
        # Determine most active subject
        subject_counts = defaultdict(int)
        for q in self.questions_asked:
            subject_counts[q['subject']] += 1
        most_active_subject = None
        if subject_counts:
            most_active_subject = max(subject_counts.items(), key=lambda x: x[1])[0]
        progress = {
            'total_questions': total_questions,
            'total_quizzes': total_quizzes,
            'average_quiz_score': round(average_quiz_score, 2),
            'subjects_explored': list(self.subjects_explored),
            'plan': 'Premium' if self.is_premium else 'Free',
            'quiz_generations': self.quiz_generations,
            'free_quiz_limit': self.free_quiz_limit,
            'session_duration_minutes': session_duration_minutes,
            'most_active_subject': most_active_subject,
        }
        # Quiz performance extras
        progress['quiz_performance'] = {
            'quizzes_generated': len(self.generated_quizzes),
            'best_performing_subject': self._get_best_performing_subject()
        }
        return progress

    # ---------------- Subscription helpers (Phase 6) -----------------
    def can_generate_quiz(self) -> bool:
        """Return True if user can generate another quiz under current plan."""
        if self.is_premium:
            return True
        return self.quiz_generations < self.free_quiz_limit

    def remaining_free_quizzes(self) -> int:
        if self.is_premium:
            return -1  # unlimited
        return max(self.free_quiz_limit - self.quiz_generations, 0)

    def upgrade_to_premium(self):
        self.is_premium = True

    def _extract_topic(self, question: str, subject: str) -> str:
        """Extract topic from question (simplified)"""
        # This is a simplified topic extraction
        # In production, you might use NLP or AI to extract topics
        question_lower = question.lower()

        topic_keywords = {
            'Mathematics': ['algebra', 'geometry', 'calculus', 'trigonometry', 'statistics'],
            'Physics': ['mechanics', 'electricity', 'waves', 'optics', 'thermodynamics'],
            'Biology': ['cell', 'genetics', 'ecology', 'evolution', 'anatomy'],
            'Chemistry': ['organic', 'inorganic', 'physical', 'analytical', 'biochemistry'],
            'History': ['ancient', 'medieval', 'modern', 'african', 'world'],
            'Geography': ['physical', 'human', 'economic', 'political', 'climate']
        }

        subject_keywords = topic_keywords.get(subject, [])
        for keyword in subject_keywords:
            if keyword in question_lower:
                return keyword.title()

        return 'General'

    def _assess_difficulty(self, question: str, subject: str) -> str:
        """Assess question difficulty (simplified)"""
        # Simple difficulty assessment based on question length and keywords
        question_lower = question.lower()

        # Advanced keywords that suggest higher difficulty
        advanced_keywords = ['prove', 'derive', 'calculate',
                             'solve', 'analyze', 'compare', 'explain why']

        if any(keyword in question_lower for keyword in advanced_keywords):
            return 'advanced'
        elif len(question.split()) > 15:
            return 'intermediate'
        else:
            return 'basic'

    def _update_learning_analytics(self, question_data: Dict):
        """Update learning analytics based on question data"""
        topic = question_data['topic']
        difficulty = question_data['difficulty']

        # Update learning strengths (topics with many questions)
        self.learning_strengths[topic] += 1

        # Update learning gaps (difficult topics)
        if difficulty == 'advanced':
            self.learning_gaps[topic] += 1

    def _update_performance_analytics(self, quiz_attempt: Dict):
        """Update performance analytics based on quiz results"""
        score = quiz_attempt['score']
        topic = quiz_attempt['topic']

        if score >= 80:
            self.learning_strengths[topic] += 2
        elif score < 60:
            self.learning_gaps[topic] += 2

    def _update_quiz_analytics(self, quiz_history_entry: Dict):
        """Update analytics based on quiz performance"""
        score = quiz_history_entry['score']
        topic = quiz_history_entry['topic']

        if score >= 80:
            self.learning_strengths[topic] += 3
        elif score < 60:
            self.learning_gaps[topic] += 3

    def _identify_weak_subjects(self) -> List[str]:
        """Identify subjects where student needs improvement"""
        subject_scores = defaultdict(list)

        for quiz in self.quiz_attempts:
            subject_scores[quiz['subject']].append(quiz['score'])

        weak_subjects = []
        for subject, scores in subject_scores.items():
            if len(scores) >= 2 and sum(scores) / len(scores) < 70:
                weak_subjects.append(subject)

        return weak_subjects

    def _identify_unexplored_topics(self) -> List[str]:
        """Identify topics the student hasn't explored yet"""
        explored_topics = set()
        for q in self.questions_asked:
            explored_topics.add(q['topic'])

        # Define common topics for each subject
        common_topics = {
            'Mathematics': ['Algebra', 'Geometry', 'Calculus', 'Trigonometry', 'Statistics'],
            'Physics': ['Mechanics', 'Electricity', 'Waves', 'Optics', 'Thermodynamics'],
            'Biology': ['Cell Biology', 'Genetics', 'Ecology', 'Evolution', 'Human Biology'],
            'Chemistry': ['Organic Chemistry', 'Inorganic Chemistry', 'Physical Chemistry', 'Analytical Chemistry'],
            'History': ['Ancient History', 'Medieval History', 'Modern History', 'African History', 'World History'],
            'Geography': ['Physical Geography', 'Human Geography', 'Economic Geography', 'Political Geography', 'Climate']
        }

        unexplored = []
        for subject in self.subjects_explored:
            subject_topics = common_topics.get(subject, [])
            for topic in subject_topics:
                if topic not in explored_topics:
                    unexplored.append(topic)

        return unexplored[:3]  # Return top 3 unexplored topics

    def _identify_learning_gaps(self) -> List[str]:
        """Identify specific learning gaps"""
        return [topic for topic, count in self.learning_gaps.items() if count >= 2]

    def _analyze_quiz_performance(self) -> Dict:
        """Analyze quiz performance to identify strengths and weaknesses"""
        if not self.quiz_history:
            return {
                'low_performance_areas': [],
                'strength_areas': [],
                'overall_trend': 'stable'
            }

        # Group by topic
        topic_scores = defaultdict(list)
        for quiz in self.quiz_history:
            topic_scores[quiz['topic']].append(quiz['score'])

        # Calculate average scores per topic
        topic_averages = {}
        for topic, scores in topic_scores.items():
            topic_averages[topic] = sum(scores) / len(scores)

        # Identify low performance areas (score < 60)
        low_performance = [topic for topic,
                           avg in topic_averages.items() if avg < 60]

        # Identify strength areas (score >= 80)
        strength_areas = [topic for topic,
                          avg in topic_averages.items() if avg >= 80]

        return {
            'low_performance_areas': low_performance,
            'strength_areas': strength_areas,
            'topic_averages': topic_averages
        }

    def _get_best_performing_subject(self) -> Optional[str]:
        """Get the subject with the best quiz performance"""
        subject_scores = defaultdict(list)

        for quiz in self.quiz_history:
            subject_scores[quiz['subject']].append(quiz['score'])

        if not subject_scores:
            return None

        best_subject = None
        best_average = 0

        for subject, scores in subject_scores.items():
            average = sum(scores) / len(scores)
            if average > best_average:
                best_average = average
                best_subject = subject

        return best_subject

    def _get_improvement_areas(self) -> List[str]:
        """Get areas that need improvement based on quiz performance"""
        if not self.quiz_history:
            return []

        # Find topics with consistently low scores
        topic_scores = defaultdict(list)
        for quiz in self.quiz_history:
            topic_scores[quiz['topic']].append(quiz['score'])

        improvement_areas = []
        for topic, scores in topic_scores.items():
            if len(scores) >= 2 and sum(scores) / len(scores) < 60:
                improvement_areas.append(topic)

        return improvement_areas[:3]  # Return top 3 areas

    def _calculate_average_score(self, quizzes: List[Dict]) -> float:
        """Calculate average score for a list of quizzes"""
        if not quizzes:
            return 0.0
        return sum(q['score'] for q in quizzes) / len(quizzes)

    def _calculate_overall_average_score(self) -> float:
        """Calculate overall average quiz score"""
        return self._calculate_average_score(self.quiz_attempts)

    def to_dict(self) -> Dict:
        """Convert session to dictionary for storage"""
        return {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'questions_asked': self.questions_asked,
            'quiz_attempts': self.quiz_attempts,
            'subjects_explored': list(self.subjects_explored),
            'learning_strengths': dict(self.learning_strengths),
            'learning_gaps': dict(self.learning_gaps),
            'generated_quizzes': self.generated_quizzes,
            'quiz_sessions': self.quiz_sessions,
            'quiz_history': self.quiz_history,
            'preferred_subjects': self.preferred_subjects,
            'difficulty_level': self.difficulty_level,
            'learning_style': self.learning_style
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'StudentSession':
        """Create session from dictionary"""
        session = cls(data['session_id'])
        session.created_at = datetime.fromisoformat(data['created_at'])
        session.last_activity = datetime.fromisoformat(data['last_activity'])
        session.questions_asked = data['questions_asked']
        session.quiz_attempts = data['quiz_attempts']
        session.subjects_explored = set(data['subjects_explored'])
        session.learning_strengths = defaultdict(
            int, data['learning_strengths'])
        session.learning_gaps = defaultdict(int, data['learning_gaps'])
        session.generated_quizzes = data.get('generated_quizzes', {})
        session.quiz_sessions = data.get('quiz_sessions', {})
        session.quiz_history = data.get('quiz_history', [])
        session.preferred_subjects = data['preferred_subjects']
        session.difficulty_level = data['difficulty_level']
        session.learning_style = data['learning_style']
        return session
