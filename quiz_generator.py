"""
SmartLearn Quiz Generator Module
Handles AI-generated quiz creation, quiz sessions, and automated grading
"""

import os
import openai
import requests
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import random
import json
from dotenv import load_dotenv

class QuizGenerator:
    def __init__(self):
        """Initialize the quiz generator with OpenAI client"""
        # Load environment variables from .env file
        load_dotenv()
        
        self.client = None
        self.huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY')
        self.use_huggingface = os.getenv(
            'USE_HUGGINGFACE', 'false').lower() == 'true'
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
            if api_key and api_key.startswith('sk-'):
                try:
                    self.client = openai.OpenAI(api_key=api_key)
                    print("✅ Quiz Generator OpenAI client initialized successfully")
                    # Test the connection
                    self._test_openai_connection()
                except Exception as e:
                    print(f"⚠️  Quiz Generator OpenAI SDK init failed, enabling HTTP fallback: {e}")
                    openai.api_key = api_key
                    self.openai_api_key = api_key
                    self.client = True
                    self.openai_via_http = True
                    try:
                        self._test_openai_connection()
                    except Exception:
                        pass
            else:
                print("⚠️  Quiz Generator: OPENAI_API_KEY not found or invalid in environment variables")
                self.client = None
        except Exception as e:
            print(f"❌ Quiz Generator: Error initializing OpenAI client: {str(e)}")
            self.client = None

    def _test_openai_connection(self):
        """Test OpenAI connection with a simple request"""
        try:
            if self.client:
                resp = self._call_openai_chat(messages=[{"role": "user", "content": "Hello"}], model="gpt-3.5-turbo", max_tokens=10, temperature=0.0, timeout=10)
                text = self._get_response_text(resp)
                if text is not None:
                    print("✅ Quiz Generator OpenAI connection test successful")
        except Exception as e:
            print(f"⚠️  Quiz Generator OpenAI connection test failed: {str(e)}")
    
    def generate_quiz(self, subject: str, topic: str, difficulty: str = 'intermediate', 
                     quiz_type: str = 'concept_check', num_questions: int = 5) -> Dict:
        """Generate a complete quiz using AI with improved error handling"""
        
        print(f"🔍 generate_quiz called for subject: {subject}, topic: {topic}")
        print(f"🔍 OpenAI client status: {self.client is not None}")
        print(f"� Hugging Face enabled: {self.use_huggingface}")
        
        # Try OpenAI first
        if self.client:
            try:
                print("🚀 Attempting OpenAI API call...")
                return self._generate_openai_quiz(subject, topic, difficulty, quiz_type, num_questions)
            except Exception as e:
                print(f"❌ OpenAI failed: {str(e)}")

        # Fallback to Hugging Face if enabled
        if self.use_huggingface and self.huggingface_api_key:
            try:
                print("🚀 Attempting Hugging Face API call...")
                return self._generate_huggingface_quiz(subject, topic, difficulty, quiz_type, num_questions)
            except Exception as e:
                print(f"❌ Hugging Face failed: {str(e)}")

        # Final fallback to generic quiz
        print("⚠️  All AI services failed, using fallback quiz")
        return self._generate_fallback_quiz(subject, topic, difficulty, num_questions)

    def _generate_openai_quiz(self, subject: str, topic: str, difficulty: str, 
                             quiz_type: str, num_questions: int) -> Dict:
        """Generate quiz using OpenAI with improved error handling"""
        try:
            # Generate quiz prompt
            prompt = self._create_quiz_prompt(subject, topic, difficulty, quiz_type, num_questions)
            print(f"📝 Generated quiz prompt length: {len(prompt)} characters")
            
            # Call OpenAI API with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are SmartLearn, an expert quiz creator for African high school students. Create engaging, curriculum-aligned multiple-choice questions."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=2000,
                        temperature=0.7,
                        timeout=30  # Add timeout
                    )
                    break  # Success, exit retry loop
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e  # Last attempt failed
                    print(f"⚠️  Quiz Generator attempt {attempt + 1} failed, retrying...")
                    import time
                    time.sleep(1)  # Wait before retry
            
            print("✅ Quiz Generator OpenAI API call successful!")
            # Extract the response content
            ai_response = response.choices[0].message.content
            print(f"📄 AI quiz response length: {len(ai_response)} characters")
            
            # Validate response
            if not ai_response or len(ai_response.strip()) < 100:
                raise Exception("AI quiz response too short or empty")
            
            # Parse the quiz from AI response
            quiz_data = self._parse_quiz_response(ai_response, subject, topic, difficulty, quiz_type)
            
            # Validate quiz data
            if not self._validate_quiz(quiz_data, num_questions):
                print("⚠️  Quiz validation failed, using fallback")
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
                'time_limit': self._calculate_time_limit(difficulty, num_questions),
                'ai_provider': 'openai'
            }
            
            return quiz_data
            
        except Exception as e:
            print(f"❌ OpenAI quiz generation failed: {str(e)}")
            raise e

    def _generate_huggingface_quiz(self, subject: str, topic: str, difficulty: str, 
                                  quiz_type: str, num_questions: int) -> Dict:
        """Generate quiz using Hugging Face Inference API with better error handling"""
        try:
            print("🔄 Using Hugging Face Inference API for quiz generation")

            # Create a structured prompt for quiz generation
            prompt = f"""Create a {difficulty} level quiz for {subject} about {topic}.

Generate {num_questions} multiple-choice questions with 4 options each (A, B, C, D).

Format:
QUESTION 1: [Question]
A) [Option A]
B) [Option B] 
C) [Option C]
D) [Option D]
CORRECT: [A/B/C/D]
EXPLANATION: [Brief explanation]

Make questions educational for African high school students."""

            headers = {"Authorization": f"Bearer {self.huggingface_api_key}"}

            # Try reliable models for quiz generation
            models_to_try = [
                "microsoft/DialoGPT-medium",
                "gpt2",
                "distilgpt2"
            ]

            ai_response = ""
            for model in models_to_try:
                try:
                    payload = {
                        "inputs": prompt,
                        "parameters": {
                            "max_length": 500,
                            "temperature": 0.7,
                            "do_sample": True
                        }
                    }

                    response = requests.post(
                        f"https://api-inference.huggingface.co/models/{model}",
                        headers=headers,
                        json=payload,
                        timeout=25
                    )

                    print(f"📊 Quiz Model {model} - Status: {response.status_code}")

                    if response.status_code == 200:
                        result = response.json()
                        print(f"📊 Raw quiz response: {result}")

                        if isinstance(result, list) and len(result) > 0:
                            generated = result[0].get('generated_text', '')
                            if generated and len(generated) > len(prompt):
                                ai_response = generated.replace(prompt, "").strip()
                                if len(ai_response) > 50:
                                    print(f"✅ Quiz Model {model} successful!")
                                    break

                except Exception as e:
                    print(f"⚠️  Quiz Model {model} failed: {str(e)}")
                    continue

            # Validate response
            if not ai_response or len(ai_response.strip()) < 50:
                raise Exception("No valid quiz response from any Hugging Face model")

            print(f"📄 Final AI quiz response: {ai_response[:300]}...")

            # Parse the quiz from AI response
            quiz_data = self._parse_quiz_response(ai_response, subject, topic, difficulty, quiz_type)

            # Validate quiz data
            if not self._validate_quiz(quiz_data, num_questions):
                print("⚠️  Hugging Face quiz validation failed, using fallback")
                quiz_data = self._generate_fallback_quiz(subject, topic, difficulty, num_questions)

            # Add metadata
            quiz_data['metadata'] = {
                'subject': subject,
                'topic': topic,
                'difficulty': difficulty,
                'quiz_type': quiz_type,
                'num_questions': len(quiz_data['questions']),
                'generated_at': datetime.now().isoformat(),
                'time_limit': self._calculate_time_limit(difficulty, num_questions),
                'ai_provider': 'huggingface'
            }

            return quiz_data

        except Exception as e:
            print(f"❌ Hugging Face quiz generation error: {str(e)}")
            raise e
    
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

    def _call_openai_chat(self, **kwargs):
        """Adapter to call OpenAI chat/completions across SDK versions for quiz_generator."""
        if not self.client:
            raise Exception("OpenAI client not initialized")

        try:
            if hasattr(self.client, 'chat') and hasattr(self.client.chat, 'completions'):
                return self.client.chat.completions.create(**kwargs)
        except Exception:
            pass

        try:
            return openai.ChatCompletion.create(**kwargs)
        except Exception as e:
            try:
                return openai.Completion.create(**kwargs)
            except Exception:
                raise e

    def _get_response_text(self, resp) -> Optional[str]:
        """Normalize different OpenAI response shapes to a text string for quiz_generator."""
        if resp is None:
            return None

        try:
            if hasattr(resp, 'choices'):
                choice = resp.choices[0]
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    return choice.message.content
                if isinstance(choice, dict) and 'message' in choice and 'content' in choice['message']:
                    return choice['message']['content']
                if 'text' in choice:
                    return choice['text']
        except Exception:
            pass

        try:
            if isinstance(resp, dict):
                if 'choices' in resp and len(resp['choices']) > 0:
                    ch = resp['choices'][0]
                    if isinstance(ch, dict):
                        if 'message' in ch and 'content' in ch['message']:
                            return ch['message']['content']
                        if 'text' in ch:
                            return ch['text']
                if 'generated_text' in resp:
                    return resp['generated_text']
        except Exception:
            pass

        try:
            return str(resp)
        except Exception:
            return None
