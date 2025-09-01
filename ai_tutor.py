"""
SmartLearn AI Tutor Module
Handles AI-powered tutoring using OpenAI GPT-4o with curriculum alignment
"""

import os
import openai
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime
import random


class SmartLearnTutor:
    def __init__(self):
        """Initialize the AI tutor with OpenAI client"""
        self.client = None
        self.huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY')
        self.use_huggingface = os.getenv(
            'USE_HUGGINGFACE', 'false').lower() == 'true'

        # Try OpenAI first, then fallback to Hugging Face
        self._initialize_client()

        # Subject-specific teaching styles
        self.teaching_styles = {
            'Mathematics': 'step-by-step problem solving with clear explanations',
            'Physics': 'conceptual understanding with real-world examples',
            'Chemistry': 'molecular visualization with practical applications',
            'Biology': 'life science connections with African context',
            'History': 'narrative storytelling with critical analysis',
            'Geography': 'spatial thinking with local and global perspectives',
            'English': 'language development with cultural context',
            'General': 'interactive learning with practical examples'
        }

        # Curriculum frameworks
        self.curriculum_frameworks = {
            'KCSE': 'Kenya Certificate of Secondary Education',
            'WAEC': 'West African Examinations Council',
            'IGCSE': 'International General Certificate of Secondary Education'
        }

    def _initialize_client(self):
        """Initialize OpenAI client with error handling"""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.client = openai.OpenAI(api_key=api_key)
                print("✅ OpenAI client initialized successfully")
            else:
                print("⚠️  OPENAI_API_KEY not found in environment variables")
                self.client = None
        except Exception as e:
            print(f"❌ Error initializing OpenAI client: {str(e)}")
            self.client = None

    def generate_answer(self, subject: str, question: str) -> Dict:
        """Generate AI-powered answer with curriculum alignment"""

        print(
            f"🔍 generate_answer called for subject: {subject}, question: {question}")
        print(f"🔍 OpenAI client status: {self.client is not None}")
        print(f"🔍 Hugging Face enabled: {self.use_huggingface}")

        # Try OpenAI first
        if self.client:
            try:
                print("🚀 Attempting OpenAI API call...")
                return self._generate_openai_response(subject, question)
            except Exception as e:
                print(f"❌ OpenAI failed: {str(e)}")

        # Fallback to Hugging Face if enabled
        if self.use_huggingface and self.huggingface_api_key:
            try:
                print("🚀 Attempting Hugging Face API call...")
                return self._generate_huggingface_response(subject, question)
            except Exception as e:
                print(f"❌ Hugging Face failed: {str(e)}")

        # Final fallback to generic response
        print("⚠️  All AI services failed, using fallback response")
        return self._generate_fallback_response(subject, question)

    def _generate_openai_response(self, subject: str, question: str) -> Dict:
        """Generate response using OpenAI"""
        # Create structured prompt
        prompt = self._create_teaching_prompt(subject, question)
        print(f"📝 Generated prompt length: {len(prompt)} characters")

        # Call OpenAI API
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are SmartLearn, an expert tutor for African high school students. Provide clear, engaging explanations aligned with KCSE/WAEC curricula."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.7
        )

        print("✅ OpenAI API call successful!")
        # Extract the response content
        ai_response = response.choices[0].message.content
        print(f"📄 AI response length: {len(ai_response)} characters")

        # Parse and structure the response
        structured_response = self._parse_ai_response(ai_response, subject)

        # Generate practice question
        practice_question = self._generate_practice_question(subject, question)

        return {
            'answer': structured_response,
            'quiz_question': practice_question['question'],
            'quiz_options': practice_question['options'],
            'quiz_answer': practice_question['correct_answer'],
            'subject': subject,
            'timestamp': datetime.now().isoformat(),
            'ai_provider': 'openai'
        }

    def _generate_huggingface_response(self, subject: str, question: str) -> Dict:
        """Generate response using Hugging Face Inference API"""
        # Use the most basic, reliable approach
        print("🔄 Using Hugging Face Inference API")

        # Create a simple prompt
        prompt = f"""You are SmartLearn, an expert {subject} tutor for African high school students.

Student Question: {question}

Please provide a clear, detailed explanation of this concept including:
1. Key points about the topic
2. Step-by-step explanation
3. Real-world examples
4. Common mistakes to avoid

Make your response educational and informative:"""

        try:
            # Use the basic text generation endpoint
            headers = {"Authorization": f"Bearer {self.huggingface_api_key}"}
            payload = {
                "inputs": prompt
            }

            # Try the basic text generation endpoint
            response = requests.post(
                "https://api-inference.huggingface.co/models/gpt2",
                headers=headers,
                json=payload,
                timeout=30
            )

            print(f"📊 Response status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"📊 Raw API response: {result}")

                # Extract the generated text
                ai_response = ""
                if isinstance(result, list) and len(result) > 0:
                    ai_response = result[0].get('generated_text', '')

                # Clean up the response (remove the input prompt)
                if prompt in ai_response:
                    ai_response = ai_response.replace(prompt, "").strip()

                # Ensure we have a meaningful response
                if len(ai_response.strip()) < 20:
                    print(f"⚠️  Response too short, using fallback")
                    raise Exception("Response too short")

                print("✅ Hugging Face API call successful!")
                print(f"📄 AI response length: {len(ai_response)} characters")
                print(f"📄 AI response: {ai_response[:200]}...")

                # Parse and structure the response
                structured_response = self._parse_ai_response(
                    ai_response, subject)

                # Generate practice question
                practice_question = self._generate_practice_question(
                    subject, question)

                return {
                    'answer': structured_response,
                    'quiz_question': practice_question['question'],
                    'quiz_options': practice_question['options'],
                    'quiz_answer': practice_question['correct_answer'],
                    'subject': subject,
                    'timestamp': datetime.now().isoformat(),
                    'ai_provider': 'huggingface'
                }
            else:
                print(f"⚠️  API failed with status {response.status_code}")
                print(f"⚠️  Response text: {response.text}")
                raise Exception(
                    f"API call failed with status {response.status_code}")

        except Exception as e:
            print(f"❌ Hugging Face API error: {str(e)}")
            raise e

    def _create_teaching_prompt(self, subject: str, question: str) -> str:
        """Create a structured prompt for AI teaching"""

        teaching_style = self.teaching_styles.get(
            subject, self.teaching_styles['General'])
        curriculum = self.curriculum_frameworks.get(
            'KCSE', 'African high school curriculum')

        prompt = f"""You are SmartLearn, an expert {subject} tutor for African high school students.

STUDENT QUESTION: {question}

IMPORTANT: You MUST provide a COMPLETE and DETAILED explanation of the concept asked about. Do NOT give generic responses or acknowledgments. Actually TEACH the student about the topic.

TEACHING REQUIREMENTS:
- Subject: {subject}
- Teaching Style: {teaching_style}
- Curriculum: {curriculum}
- Target Audience: African high school students (ages 14-18)

RESPONSE STRUCTURE:
You MUST structure your response exactly as follows:

Key Points:
- [List 3-4 main concepts related to the question]

Step-by-Step Explanation:
[Provide a COMPLETE explanation of the concept. Break it down in simple, clear terms that a high school student can understand. Use examples and analogies.]

Real-world Example:
[Give a specific, practical example relevant to African context or daily life]

Common Mistakes:
[Highlight 2-3 common errors students make when learning this concept and how to avoid them]

Additional Tips:
[Provide 1-2 helpful study tips or memory aids for this topic]

CRITICAL: Your response must be EDUCATIONAL and INFORMATIVE. Do not just acknowledge the question - actually explain the concept in detail. The student should learn something new from your response."""

        return prompt

    def _parse_ai_response(self, ai_response: str, subject: str) -> str:
        """Parse and clean the AI response"""

        # Basic cleaning
        cleaned_response = ai_response.strip()

        # Ensure proper formatting
        if not cleaned_response.startswith('Key Points:'):
            # Add structure if missing
            cleaned_response = f"Key Points:\n- Understanding {subject} concepts\n\n{cleaned_response}"

        return cleaned_response

    def _generate_practice_question(self, subject: str, topic: str) -> Dict:
        """Generate a practice question related to the topic"""

        # Subject-specific practice questions
        practice_questions = {
            'Mathematics': {
                'question': 'What is the value of x in the equation 2x + 5 = 13?',
                'options': ['x = 3', 'x = 4', 'x = 5', 'x = 6'],
                'correct_answer': 'x = 4'
            },
            'Physics': {
                'question': 'What is the SI unit of force?',
                'options': ['Newton (N)', 'Joule (J)', 'Watt (W)', 'Pascal (Pa)'],
                'correct_answer': 'Newton (N)'
            },
            'Biology': {
                'question': 'What is the powerhouse of the cell?',
                'options': ['Mitochondria', 'Nucleus', 'Golgi apparatus', 'Endoplasmic reticulum'],
                'correct_answer': 'Mitochondria'
            },
            'Chemistry': {
                'question': 'What is the chemical symbol for gold?',
                'options': ['Ag', 'Au', 'Fe', 'Cu'],
                'correct_answer': 'Au'
            },
            'History': {
                'question': 'What is the capital of Kenya?',
                'options': ['Nairobi', 'Mombasa', 'Kisumu', 'Nakuru'],
                'correct_answer': 'Nairobi'
            },
            'Geography': {
                'question': 'What is the largest desert in Africa?',
                'options': ['Sahara', 'Kalahari', 'Namib', 'Libyan'],
                'correct_answer': 'Sahara'
            },
            'English': {
                'question': 'Which of these is a proper noun?',
                'options': ['city', 'London', 'river', 'mountain'],
                'correct_answer': 'London'
            }
        }

        # Get question for the subject, or use general if not found
        question_data = practice_questions.get(
            subject, practice_questions['Mathematics'])

        return question_data

    def _generate_fallback_response(self, subject: str, question: str) -> Dict:
        """Generate fallback response when AI is unavailable"""

        # Generate a more educational fallback response
        fallback_responses = {
            'Mathematics': f"Let me help you understand {subject}! '{question}' is an important mathematical concept. Here's a basic explanation: Mathematics is the study of numbers, quantities, shapes, and patterns. When you ask about mathematical concepts, you're exploring how to solve problems using logical thinking and systematic approaches. I recommend starting with the fundamentals and building up to more complex topics.",
            'Physics': f"Great question about {subject}! '{question}' touches on fundamental physics principles. Physics is the study of matter, energy, and their interactions. It helps us understand how the universe works, from tiny particles to massive galaxies. When learning physics, focus on understanding the underlying principles rather than just memorizing formulas.",
            'Biology': f"Excellent {subject} question: '{question}'. Biology is the study of living organisms and life processes. It helps us understand how living things work, grow, and interact with their environment. When studying biology, try to connect concepts to real-world examples you can observe around you.",
            'Chemistry': f"Interesting {subject} question: '{question}'. Chemistry is the study of matter, its properties, and how it changes. It's all around us - in the air we breathe, the food we eat, and the materials we use. Understanding chemistry helps explain many everyday phenomena.",
            'History': f"Fascinating {subject} question: '{question}'. History is the study of past events and how they shape our present and future. It helps us understand human behavior, societies, and the consequences of decisions. When studying history, look for patterns and connections between different events.",
            'Geography': f"Great {subject} question: '{question}'. Geography is the study of Earth's physical features, climate, and human populations. It helps us understand how people interact with their environment and how different regions are connected. Geography combines physical science with social studies.",
            'English': f"Excellent {subject} question: '{question}'. English language study helps develop communication skills, critical thinking, and cultural understanding. It's about more than just grammar - it's about expressing ideas clearly and understanding different perspectives through literature and language.",
            'General': f"Interesting question: '{question}'. This is a great topic to explore! Learning is about asking questions and seeking understanding. When you encounter new concepts, try to break them down into smaller parts and connect them to things you already know."
        }

        response = fallback_responses.get(
            subject, fallback_responses['General'])

        # Generate a simple practice question
        practice_question = self._generate_practice_question(subject, question)

        return {
            'answer': response,
            'quiz_question': practice_question['question'],
            'quiz_options': practice_question['options'],
            'quiz_answer': practice_question['correct_answer'],
            'subject': subject,
            'timestamp': datetime.now().isoformat(),
            'fallback': True
        }


# Global instance - will be initialized when needed
ai_tutor = None


def get_ai_tutor():
    """Get or create AI tutor instance"""
    global ai_tutor
    if ai_tutor is None:
        ai_tutor = SmartLearnTutor()
    return ai_tutor
