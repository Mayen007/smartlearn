"""
SmartLearn Quiz Generator Module
Handles AI-generated quiz creation, quiz sessions, and automated grading
"""

import os
import openai
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import random
import json

class QuizGenerator:
    def __init__(self):
        """Initialize the quiz generator with OpenAI client"""
        self.client = None
        self._initialize_client()
        
        # Quiz difficulty levels
        self.difficulty_levels = {
            'beginner': {'min_score': 0, 'max_score': 60, 'complexity': 'basic'},
            'intermediate': {'min_score': 60, 'max_score': 80, 'complexity': 'moderate'},
            'advanced': {'min_score': 80, 'max_score': 100, 'complexity': 'challenging'}
        }
        
        # Quiz types and their characteristics
        self.quiz_types = {
            'concept_check': 'Test understanding of fundamental concepts',
            'problem_solving': 'Apply knowledge to solve problems',
            'critical_thinking': 'Analyze and evaluate information',
            'application': 'Use knowledge in real-world scenarios'
        }
    
    def _initialize_client(self):
        """Initialize OpenAI client with error handling"""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.client = openai.OpenAI(api_key=api_key)
                print("✅ Quiz Generator OpenAI client initialized successfully")
            else:
                print("⚠️  Quiz Generator: OPENAI_API_KEY not found in environment variables")
                self.client = None
        except Exception as e:
            print(f"❌ Quiz Generator: Error initializing OpenAI client: {str(e)}")
            self.client = None
    
    def generate_quiz(self, subject: str, topic: str, difficulty: str = 'intermediate', 
                     quiz_type: str = 'concept_check', num_questions: int = 5) -> Dict:
        """Generate a complete quiz using AI"""
        
        if not self.client:
            print("⚠️  Quiz Generator: Using fallback quiz (OpenAI not available)")
            return self._generate_fallback_quiz(subject, topic, difficulty, num_questions)
        
        try:
            # Generate quiz prompt
            prompt = self._create_quiz_prompt(subject, topic, difficulty, quiz_type, num_questions)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are SmartLearn, an expert quiz creator for African high school students. Create engaging, curriculum-aligned multiple-choice questions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            # Extract the response content
            ai_response = response.choices[0].message.content
            
            # Parse the quiz from AI response
            quiz_data = self._parse_quiz_response(ai_response, subject, topic, difficulty, quiz_type)
            
            # Validate quiz data
            if not self._validate_quiz(quiz_data, num_questions):
                # Generate fallback quiz if AI parsing fails
                quiz_data = self._generate_fallback_quiz(subject, topic, difficulty, num_questions)
            
            # Add metadata
            quiz_data['metadata'] = {
                'subject': subject,
                'topic': topic,
                'difficulty': difficulty,
                'quiz_type': quiz_type,
                'num_questions': len(quiz_data['questions']),
                'generated_at': datetime.now().isoformat(),
                'time_limit': self._calculate_time_limit(difficulty, num_questions)
            }
            
            return quiz_data
            
        except Exception as e:
            print(f"Error generating quiz: {str(e)}")
            # Return fallback quiz
            return self._generate_fallback_quiz(subject, topic, difficulty, num_questions)
    
    def _create_quiz_prompt(self, subject: str, topic: str, difficulty: str, 
                           quiz_type: str, num_questions: int) -> str:
        """Create a structured prompt for quiz generation"""
        
        difficulty_info = self.difficulty_levels.get(difficulty, self.difficulty_levels['intermediate'])
        quiz_type_info = self.quiz_types.get(quiz_type, self.quiz_types['concept_check'])
        
        prompt = f"""Create a {difficulty} level quiz for {subject} focusing on {topic}.

QUIZ REQUIREMENTS:
- Number of questions: {num_questions}
- Quiz type: {quiz_type} ({quiz_type_info})
- Difficulty: {difficulty} (suitable for {difficulty_info['complexity']} understanding)
- Format: Multiple choice with 4 options (A, B, C, D)
- Target audience: African high school students (KCSE/WAEC level)

QUESTION GUIDELINES:
1. Questions should be clear and unambiguous
2. All options should be plausible but only one correct
3. Include explanations for correct answers
4. Vary question types and cognitive levels
5. Use real-world examples relevant to African context when possible

RESPONSE FORMAT:
Please structure your response exactly as follows:

QUIZ TITLE: [Engaging quiz title]

QUESTION 1:
[Question text]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
CORRECT ANSWER: [A/B/C/D]
EXPLANATION: [Brief explanation of why this is correct]

QUESTION 2:
[Question text]
A) [Option A]
B) [Option B]
C) [Option C]
D) [Option D]
CORRECT ANSWER: [A/B/C/D]
EXPLANATION: [Brief explanation of why this is correct]

[Continue for all {num_questions} questions]

Remember: Make questions engaging, educational, and appropriate for {difficulty} level students."""

        return prompt
    
    def _parse_quiz_response(self, ai_response: str, subject: str, topic: str, 
                           difficulty: str, quiz_type: str) -> Dict:
        """Parse the AI response to extract quiz data"""
        
        lines = ai_response.split('\n')
        quiz_data = {
            'title': '',
            'questions': [],
            'subject': subject,
            'topic': topic,
            'difficulty': difficulty,
            'quiz_type': quiz_type
        }
        
        current_question = None
        current_options = []
        current_correct = ''
        current_explanation = ''
        
        for line in lines:
            line = line.strip()
            
            # Extract quiz title
            if line.startswith('QUIZ TITLE:'):
                quiz_data['title'] = line.replace('QUIZ TITLE:', '').strip()
                continue
            
            # Start of new question
            if line.startswith('QUESTION') and ':' in line:
                # Save previous question if exists
                if current_question:
                    quiz_data['questions'].append({
                        'question': current_question,
                        'options': current_options,
                        'correct_answer': current_correct,
                        'explanation': current_explanation
                    })
                
                # Reset for new question
                current_question = ''
                current_options = []
                current_correct = ''
                current_explanation = ''
                continue
            
            # Extract question text
            if current_question == '' and line and not line.startswith(('A)', 'B)', 'C)', 'D)', 'CORRECT ANSWER:', 'EXPLANATION:')):
                current_question = line
                continue
            
            # Extract options
            if line.startswith(('A)', 'B)', 'C)', 'D)')):
                option_text = line[2:].strip()
                current_options.append(option_text)
                continue
            
            # Extract correct answer
            if line.startswith('CORRECT ANSWER:'):
                current_correct = line.replace('CORRECT ANSWER:', '').strip()
                continue
            
            # Extract explanation
            if line.startswith('EXPLANATION:'):
                current_explanation = line.replace('EXPLANATION:', '').strip()
                continue
        
        # Add the last question
        if current_question:
            quiz_data['questions'].append({
                'question': current_question,
                'options': current_options,
                'correct_answer': current_correct,
                'explanation': current_explanation
            })
        
        return quiz_data
    
    def _validate_quiz(self, quiz_data: Dict, expected_questions: int) -> bool:
        """Validate that the quiz data is complete and correct"""
        
        if not quiz_data.get('title'):
            return False
        
        if len(quiz_data.get('questions', [])) != expected_questions:
            return False
        
        for question in quiz_data['questions']:
            if not question.get('question'):
                return False
            if len(question.get('options', [])) != 4:
                return False
            if not question.get('correct_answer'):
                return False
            if not question.get('explanation'):
                return False
        
        return True
    
    def _generate_fallback_quiz(self, subject: str, topic: str, difficulty: str, 
                               num_questions: int) -> Dict:
        """Generate a fallback quiz when AI generation fails"""
        
        fallback_quizzes = {
            'Mathematics': {
                'Algebra': [
                    {
                        'question': 'What is the value of x in the equation 2x + 5 = 13?',
                        'options': ['x = 3', 'x = 4', 'x = 5', 'x = 6'],
                        'correct_answer': 'x = 4',
                        'explanation': 'Subtract 5 from both sides: 2x = 8, then divide by 2: x = 4'
                    },
                    {
                        'question': 'Which of the following is a quadratic equation?',
                        'options': ['2x + 3 = 7', 'x² + 2x + 1 = 0', '3x - 5 = 10', 'x + 2 = 5'],
                        'correct_answer': 'x² + 2x + 1 = 0',
                        'explanation': 'A quadratic equation has the highest power of x as 2 (x²)'
                    }
                ],
                'Geometry': [
                    {
                        'question': 'What is the area of a circle with radius 5 units?',
                        'options': ['25π', '50π', '75π', '100π'],
                        'correct_answer': '25π',
                        'explanation': 'Area = πr² = π × 5² = 25π square units'
                    }
                ]
            },
            'Physics': {
                'Mechanics': [
                    {
                        'question': 'What is the SI unit of force?',
                        'options': ['Newton (N)', 'Joule (J)', 'Watt (W)', 'Pascal (Pa)'],
                        'correct_answer': 'Newton (N)',
                        'explanation': 'Force is measured in Newtons (N) in the SI system'
                    }
                ]
            },
            'Biology': {
                'Cell Biology': [
                    {
                        'question': 'What is the powerhouse of the cell?',
                        'options': ['Mitochondria', 'Nucleus', 'Golgi apparatus', 'Endoplasmic reticulum'],
                        'correct_answer': 'Mitochondria',
                        'explanation': 'Mitochondria produce energy through cellular respiration'
                    }
                ]
            }
        }
        
        # Get available questions for the subject and topic
        subject_questions = fallback_quizzes.get(subject, {})
        topic_questions = subject_questions.get(topic, [])
        
        # If no specific topic questions, use general subject questions
        if not topic_questions:
            for topic_questions in subject_questions.values():
                if topic_questions:
                    break
        
        # If still no questions, create generic ones
        if not topic_questions:
            topic_questions = [
                {
                    'question': f'What is the main focus of {topic} in {subject}?',
                    'options': ['Basic concepts', 'Advanced theories', 'Practical applications', 'Historical development'],
                    'correct_answer': 'Basic concepts',
                    'explanation': f'{topic} covers fundamental concepts in {subject}'
                }
            ]
        
        # Select questions (repeat if needed to reach num_questions)
        selected_questions = []
        while len(selected_questions) < num_questions:
            selected_questions.extend(topic_questions)
        
        selected_questions = selected_questions[:num_questions]
        
        return {
            'title': f'{subject} - {topic} Quiz ({difficulty.capitalize()})',
            'questions': selected_questions,
            'subject': subject,
            'topic': topic,
            'difficulty': difficulty,
            'quiz_type': 'concept_check',
            'metadata': {
                'subject': subject,
                'topic': topic,
                'difficulty': difficulty,
                'quiz_type': 'concept_check',
                'num_questions': len(selected_questions),
                'generated_at': datetime.now().isoformat(),
                'time_limit': self._calculate_time_limit(difficulty, num_questions),
                'fallback': True
            }
        }
    
    def _calculate_time_limit(self, difficulty: str, num_questions: int) -> int:
        """Calculate appropriate time limit for quiz based on difficulty and questions"""
        
        base_time_per_question = {
            'beginner': 90,      # 1.5 minutes per question
            'intermediate': 75,  # 1.25 minutes per question
            'advanced': 60       # 1 minute per question
        }
        
        time_per_question = base_time_per_question.get(difficulty, 75)
        total_time = num_questions * time_per_question
        
        # Add buffer time
        buffer_time = 300  # 5 minutes
        return total_time + buffer_time
    
    def grade_quiz(self, quiz_data: Dict, student_answers: List[str]) -> Dict:
        """Grade a completed quiz and return detailed results"""
        
        if not quiz_data.get('questions'):
            return {'error': 'Invalid quiz data'}
        
        if len(student_answers) != len(quiz_data['questions']):
            return {'error': 'Number of answers does not match number of questions'}
        
        results = {
            'total_questions': len(quiz_data['questions']),
            'correct_answers': 0,
            'incorrect_answers': 0,
            'score_percentage': 0,
            'question_results': [],
            'feedback': [],
            'time_taken': 0,  # Will be set by caller
            'difficulty_level': quiz_data.get('difficulty', 'intermediate'),
            'subject': quiz_data.get('subject', 'Unknown'),
            'topic': quiz_data.get('topic', 'Unknown')
        }
        
        for i, (question, student_answer) in enumerate(zip(quiz_data['questions'], student_answers)):
            correct_answer = question['correct_answer']
            is_correct = student_answer == correct_answer
            
            if is_correct:
                results['correct_answers'] += 1
            else:
                results['incorrect_answers'] += 1
            
            question_result = {
                'question_number': i + 1,
                'question': question['question'],
                'student_answer': student_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
                'explanation': question['explanation'],
                'options': question['options']
            }
            
            results['question_results'].append(question_result)
        
        # Calculate score
        results['score_percentage'] = (results['correct_answers'] / results['total_questions']) * 100
        
        # Generate feedback based on performance
        results['feedback'] = self._generate_performance_feedback(results)
        
        return results
    
    def _generate_performance_feedback(self, results: Dict) -> List[str]:
        """Generate personalized feedback based on quiz performance"""
        
        feedback = []
        score = results['score_percentage']
        
        if score >= 90:
            feedback.append("🎉 Excellent work! You've mastered this topic.")
            feedback.append("💡 Consider exploring more advanced concepts in this subject.")
        elif score >= 80:
            feedback.append("👍 Great job! You have a solid understanding of this topic.")
            feedback.append("🔍 Review the incorrect answers to strengthen your knowledge.")
        elif score >= 70:
            feedback.append("✅ Good effort! You're on the right track.")
            feedback.append("📚 Focus on the areas where you made mistakes.")
        elif score >= 60:
            feedback.append("⚠️ You're making progress, but there's room for improvement.")
            feedback.append("🎯 Review the fundamental concepts before moving forward.")
        else:
            feedback.append("📖 This topic needs more attention.")
            feedback.append("🔄 Consider reviewing the basics and asking the AI tutor for help.")
        
        # Subject-specific feedback
        if results['subject'] == 'Mathematics':
            feedback.append("🧮 Practice more problems to improve your mathematical thinking.")
        elif results['subject'] == 'Physics':
            feedback.append("⚡ Focus on understanding the underlying principles.")
        elif results['subject'] == 'Biology':
            feedback.append("🔬 Try to connect concepts to real-world examples.")
        
        return feedback
    
    def get_quiz_statistics(self, quiz_data: Dict) -> Dict:
        """Generate statistics about a quiz"""
        
        if not quiz_data.get('questions'):
            return {}
        
        total_questions = len(quiz_data['questions'])
        
        # Analyze question types and difficulty
        question_types = []
        for question in quiz_data['questions']:
            question_text = question['question'].lower()
            
            if any(word in question_text for word in ['calculate', 'solve', 'find']):
                question_types.append('problem_solving')
            elif any(word in question_text for word in ['explain', 'why', 'how']):
                question_types.append('conceptual')
            elif any(word in question_text for word in ['compare', 'analyze', 'evaluate']):
                question_types.append('critical_thinking')
            else:
                question_types.append('recall')
        
        # Count question types
        type_counts = {}
        for q_type in question_types:
            type_counts[q_type] = type_counts.get(q_type, 0) + 1
        
        return {
            'total_questions': total_questions,
            'question_types': type_counts,
            'difficulty': quiz_data.get('difficulty', 'intermediate'),
            'estimated_time': quiz_data.get('metadata', {}).get('time_limit', 0),
            'subject': quiz_data.get('subject', 'Unknown'),
            'topic': quiz_data.get('topic', 'Unknown')
        }

# Global instance - will be initialized when needed
quiz_generator = None

def get_quiz_generator():
    """Get or create quiz generator instance"""
    global quiz_generator
    if quiz_generator is None:
        quiz_generator = QuizGenerator()
    return quiz_generator
