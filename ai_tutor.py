"""
SmartLearn AI Tutor Module
Handles AI-powered tutoring using OpenAI GPT-4o with curriculum alignment
"""

import os
import openai
import requests
import json
import re
from typing import Dict, List, Optional
from datetime import datetime
import random
from dotenv import load_dotenv


class SmartLearnTutor:
    def __init__(self):
        """Initialize providers, teaching styles, and curriculum frameworks (clean)."""
        load_dotenv()

        # Provider / state
        self.client = None
        self.huggingface_api_key = os.getenv('HUGGINGFACE_API_KEY')
        self.use_huggingface = os.getenv('USE_HUGGINGFACE', 'false').lower() == 'true'
        self._openai_disabled_until = None

        # Initialize OpenAI first
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
            if api_key and api_key.startswith('sk-'):
                try:
                    self.client = openai.OpenAI(api_key=api_key)
                    print("✅ OpenAI client initialized successfully")
                    # Test the connection
                    self._test_openai_connection()
                except Exception as e:
                    # Fallback: avoid relying on SDK internals. Use HTTP fallback.
                    print(f"⚠️  OpenAI SDK init failed, enabling HTTP fallback: {e}")
                    openai.api_key = api_key
                    self.openai_api_key = api_key
                    # Keep client truthy so code prefers OpenAI path, but mark HTTP usage
                    self.client = True
                    self.openai_via_http = True
                    # Do not call SDK-specific test that may fail; use HTTP test via adapter
                    try:
                        self._test_openai_connection()
                    except Exception:
                        pass
            else:
                print("⚠️  OPENAI_API_KEY not found or invalid in environment variables")
                self.client = None
        except Exception as e:
            print(f"❌ Error initializing OpenAI client: {str(e)}")
            self.client = None

    def _test_openai_connection(self):
        """Test OpenAI connection with a simple request"""
        try:
            if self.client:
                # Use adapter to call OpenAI in a compatible way for multiple SDK versions
                resp = self._call_openai_chat(messages=[{"role": "user", "content": "Hello"}], model="gpt-3.5-turbo", max_tokens=10, temperature=0.0, timeout=10)
                text = self._get_response_text(resp)
                if text is not None:
                    print("✅ OpenAI connection test successful")
        except Exception as e:
            print(f"⚠️  OpenAI connection test failed: {str(e)}")

    def generate_answer(self, subject: str, question: str) -> Dict:
        """Generate AI-powered answer with curriculum alignment"""

        print(
            f"🔍 generate_answer called for subject: {subject}, question: {question}")
        print(f"🔍 OpenAI client status: {self.client is not None}")
        print(f"🔍 Hugging Face enabled: {self.use_huggingface}")

        # Try OpenAI first (even if self.client is just the HTTP fallback flag)
        from time import time
        if self.client and not self._is_openai_temporarily_disabled():
            try:
                print("🚀 Attempting OpenAI API call...")
                return self._generate_openai_response(subject, question)
            except Exception as e:
                print(f"❌ OpenAI failed: {type(e).__name__}: {e}")
                # Capture reason in diagnostic field for front-end visibility
                error_reason = str(e)
                # Classify & potentially disable provider for cooldown
                self._maybe_disable_openai(error_reason)
        else:
            if self._is_openai_temporarily_disabled():
                error_reason = "OpenAI temporarily disabled after repeated errors"
            else:
                error_reason = "OpenAI client not initialized"

        # Fallback to Hugging Face if enabled
        if self.use_huggingface and self.huggingface_api_key:
            try:
                print("🚀 Attempting Hugging Face API call...")
                return self._generate_huggingface_response(subject, question)
            except Exception as e:
                print(f"❌ Hugging Face failed: {str(e)}")

        # Final fallback to generic response
        print("⚠️  All AI services failed, using fallback response")
        fallback = self._generate_fallback_response(subject, question)
        # Surface diagnostic info (non-sensitive) if available
        if 'error_reason' not in fallback:
            fallback['error_reason'] = error_reason if 'error_reason' in locals() else 'unknown'
        return fallback

    def _generate_openai_response(self, subject: str, question: str) -> Dict:
        """Generate response using OpenAI with improved error handling"""
        try:
            # Create structured prompt
            prompt = self._create_teaching_prompt(subject, question)
            print(f"📝 Generated prompt length: {len(prompt)} characters")

            # Dynamically select an available model (legacy SDK friendliness)
            model = self._select_openai_model()
            print(f"🔧 Using OpenAI model: {model}")

            # Call OpenAI API with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self._call_openai_chat(
                        model=model,
                        messages=[
                            {"role": "system", "content": (
                                "You are SmartLearn, an expert tutor for African high school students. Provide clear, deep, engaging explanations aligned with KCSE/WAEC curricula. "
                                "ALWAYS output a detailed explanation. First output a JSON object ONLY with the schema: {\\n"
                                "  'key_points': string[], 'step_by_step': string, 'real_world_example': string, 'common_mistakes': string[], 'additional_tips': string[]\\n} "
                                "No markdown, no prose outside JSON. After the JSON, add a markdown version starting with '---\nMARKDOWN:' for display." )},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=1500,
                        temperature=0.7,
                        timeout=30
                    )
                    break  # Success, exit retry loop
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e  # Last attempt failed
                    print(
                        f"⚠️  OpenAI attempt {attempt + 1} failed, retrying...")
                    import time
                    time.sleep(1)  # Wait before retry

            print("✅ OpenAI API call successful!")

            # Extract the response content
            ai_response = self._get_response_text(response) or ""
            print(f"📄 AI response length: {len(ai_response)} characters")

            # Validate response
            if not ai_response or len(ai_response.strip()) < 50:
                raise Exception("AI response too short or empty")

            # Phase 1: attempt to grab JSON block (first pass)
            structured_obj = self._attempt_parse_with_repair(ai_response, subject, question)

            if structured_obj is None:
                # Final fallback to legacy parsing (string markdown)
                answer_markdown = self._parse_ai_response(ai_response, subject)
                answer_structured = None
            else:
                answer_structured = structured_obj
                answer_markdown = self._structured_to_markdown(structured_obj)

            # Generate practice question
            practice_question = self._generate_practice_question(subject, question)

            return {
                'answer': answer_markdown,                 # markdown version (backward compatibility)
                'answer_markdown': answer_markdown,        # explicit markdown
                'answer_structured': answer_structured,    # dict or None
                'quiz_question': practice_question['question'],
                'quiz_options': practice_question['options'],
                'quiz_answer': practice_question['correct_answer'],
                'subject': subject,
                'timestamp': datetime.now().isoformat(),
                'ai_provider': 'openai',
                'fallback': False if answer_structured or answer_markdown else True
            }

        except Exception as e:
            print(f"❌ OpenAI response generation failed: {str(e)}")
            raise e

    def _generate_huggingface_response(self, subject: str, question: str) -> Dict:
        """Generate response using Hugging Face Inference API with better error handling"""
        try:
            print("🔄 Using Hugging Face Inference API")

            # Create a more structured prompt
            prompt = f"""You are SmartLearn, an expert {subject} tutor for African high school students.

Question: {question}

Provide a clear explanation with:
1. Key concepts
2. Simple explanation
3. One example
4. Study tip

Answer:"""

            headers = {"Authorization": f"Bearer {self.huggingface_api_key}"}

            # Try a more reliable model
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
                            "max_length": 200,
                            "temperature": 0.7,
                            "do_sample": True
                        }
                    }

                    response = requests.post(
                        f"https://api-inference.huggingface.co/models/{model}",
                        headers=headers,
                        json=payload,
                        timeout=20
                    )

                    print(f"📊 Model {model} - Status: {response.status_code}")

                    if response.status_code == 200:
                        result = response.json()
                        print(f"📊 Raw response: {result}")

                        if isinstance(result, list) and len(result) > 0:
                            generated = result[0].get('generated_text', '')
                            if generated and len(generated) > len(prompt):
                                ai_response = generated.replace(
                                    prompt, "").strip()
                                if len(ai_response) > 20:
                                    print(f"✅ Model {model} successful!")
                                    break

                except Exception as e:
                    print(f"⚠️  Model {model} failed: {str(e)}")
                    continue

            # Validate response
            if not ai_response or len(ai_response.strip()) < 20:
                raise Exception(
                    "No valid response from any Hugging Face model")

            print(f"📄 Final AI response: {ai_response[:200]}...")

            # Parse and structure the response
            structured_response = self._parse_ai_response(ai_response, subject)

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
        """Parse and clean the AI response with better formatting"""

        if not ai_response or len(ai_response.strip()) < 20:
            return f"I'm sorry, I couldn't generate a proper response for your {subject} question. Please try rephrasing your question or ask about a different topic."

        # Basic cleaning
        cleaned_response = ai_response.strip()

        # Ensure proper structure
        if not any(keyword in cleaned_response.lower() for keyword in ['key points', 'explanation', 'example']):
            # Add basic structure if missing
            cleaned_response = f"""**Key Points:**
• Understanding {subject} concepts
• Applying knowledge to solve problems

**Explanation:**
{cleaned_response}

**Additional Tips:**
• Practice regularly with similar problems
• Ask questions when you don't understand something"""

        # Format markdown-style headers
        cleaned_response = cleaned_response.replace(
            '**Key Points:**', '### Key Points:')
        cleaned_response = cleaned_response.replace(
            '**Explanation:**', '### Step-by-Step Explanation:')
        cleaned_response = cleaned_response.replace(
            '**Real-world Example:**', '### Real-world Example:')
        cleaned_response = cleaned_response.replace(
            '**Common Mistakes:**', '### Common Mistakes:')
        cleaned_response = cleaned_response.replace(
            '**Additional Tips:**', '### Additional Tips:')

        return cleaned_response

    def _extract_json_from_text(self, text: str) -> Optional[dict]:
        """Attempt to extract a JSON object from noisy model output."""
        if not text or not text.strip():
            return None

        # Try direct parse first
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return data
        except Exception:
            pass

        # Find first {...} block using regex (naive but effective for many cases)
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            candidate = match.group(0)
            try:
                data = json.loads(candidate)
                if isinstance(data, dict):
                    return data
            except Exception:
                # Try to clean up common issues: trailing commas
                cleaned = re.sub(r",\s*\}", "}", candidate)
                cleaned = re.sub(r",\s*\]", "]", cleaned)
                try:
                    data = json.loads(cleaned)
                    if isinstance(data, dict):
                        return data
                except Exception:
                    return None

        return None

    def _validate_ai_answer_schema(self, obj: Optional[dict]) -> bool:
        """Validate that the AI answer JSON matches expected schema."""
        if not obj or not isinstance(obj, dict):
            return False

        # Required keys and their types
        schema = {
            'key_points': list,
            'step_by_step': str,
            'real_world_example': str,
            'common_mistakes': list,
            'additional_tips': list
        }

        for key, typ in schema.items():
            if key not in obj:
                print(f"⚠️  Missing key in AI JSON: {key}")
                return False
            if not isinstance(obj[key], typ):
                print(f"⚠️  Key {key} has incorrect type: expected {typ}, got {type(obj[key])}")
                return False

        return True

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

    def _call_openai_chat(self, **kwargs):
        """Adapter to call OpenAI chat/completions across SDK versions.

        Accepts model, messages, max_tokens, temperature, timeout.
        Returns the raw response object.
        """
        # Prefer calling through the client if it's a proper SDK client
        try:
            if self.client and hasattr(self.client, 'chat') and hasattr(self.client.chat, 'completions'):
                return self.client.chat.completions.create(**kwargs)
        except Exception:
            pass

        # Try top-level SDK calls if available
        try:
            if hasattr(openai, 'ChatCompletion'):
                return openai.ChatCompletion.create(**kwargs)
        except Exception:
            pass

        # As a robust fallback, call the OpenAI REST API directly
        api_key = getattr(self, 'openai_api_key', None) or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise Exception('OPENAI_API_KEY not set for HTTP fallback')

        url = 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': kwargs.get('model'),
            'messages': kwargs.get('messages'),
            'max_tokens': kwargs.get('max_tokens'),
            'temperature': kwargs.get('temperature', 0.7)
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=kwargs.get('timeout', 30))
            if resp.status_code == 200:
                return resp.json()
            else:
                snippet = resp.text[:300]
                raise Exception(f'HTTP {resp.status_code}: {snippet}')
        except requests.RequestException as e:
            raise Exception(f'Network error calling OpenAI: {e}')

    def _get_response_text(self, resp) -> Optional[str]:
        """Normalize different OpenAI response shapes to a text string."""
        if resp is None:
            return None

        # New SDK response: resp.choices[0].message.content
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

        # If resp is a dict (requests-like)
        try:
            if isinstance(resp, dict):
                # Common key paths
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

        # As a last resort, try stringifying the object
        try:
            return str(resp)
        except Exception:
            return None

    def _select_openai_model(self) -> str:
        """Select an OpenAI model name based on environment / legacy usage."""
        # Prefer environment override
        env_model = os.getenv('OPENAI_MODEL')
        if env_model:
            return env_model
        # Fallback priority list (older API first for compatibility)
        return 'gpt-3.5-turbo'

    def _attempt_parse_with_repair(self, raw: str, subject: str, question: str) -> Optional[dict]:
        """Try to parse JSON (first block) and repair simple issues (quotes, trailing commas)."""
        if not raw:
            return None
        candidate = self._extract_json_from_text(raw)
        if candidate and self._validate_ai_answer_schema(candidate):
            return candidate
        # Attempt mild repair: replace single quotes around keys with double quotes
        try:
            # Only operate on extracted candidate if present
            if candidate is None:
                # naive brace extraction
                m = re.search(r"\{[\s\S]*?\}", raw)
                if not m:
                    return None
                text_block = m.group(0)
            else:
                text_block = json.dumps(candidate)
            repaired = re.sub(r"'(\w+)':", r'"\1":', text_block)
            repaired = re.sub(r"'([^']*)'", lambda m: '"'+m.group(1)+'"', repaired)
            repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
            parsed = json.loads(repaired)
            if self._validate_ai_answer_schema(parsed):
                return parsed
        except Exception:
            return None
        return None

    def _structured_to_markdown(self, data: dict) -> str:
        """Convert structured dict schema to markdown display."""
        if not data or not isinstance(data, dict):
            return ""
        lines = []
        kp = data.get('key_points') or []
        if kp:
            lines.append('### Key Points:')
            for item in kp:
                lines.append(f"- {item}")
        step = data.get('step_by_step')
        if step:
            lines.append('\n### Step-by-Step Explanation:')
            lines.append(step)
        ex = data.get('real_world_example')
        if ex:
            lines.append('\n### Real-world Example:')
            lines.append(ex)
        cm = data.get('common_mistakes') or []
        if cm:
            lines.append('\n### Common Mistakes:')
            for item in cm:
                lines.append(f"- {item}")
        tips = data.get('additional_tips') or []
        if tips:
            lines.append('\n### Additional Tips:')
            for item in tips:
                lines.append(f"- {item}")
        return "\n".join(lines).strip()

    def _generate_fallback_response(self, subject: str, question: str) -> Dict:
        """Generate fallback response when AI is unavailable"""
        structured = self._rule_based_generation(subject, question)
        markdown = self._structured_to_markdown(structured)
        practice_question = self._generate_practice_question(subject, question)
        return {
            'answer': markdown,
            'answer_markdown': markdown,
            'answer_structured': structured,
            'quiz_question': practice_question['question'],
            'quiz_options': practice_question['options'],
            'quiz_answer': practice_question['correct_answer'],
            'subject': subject,
            'timestamp': datetime.now().isoformat(),
            'fallback': True
        }

    # ---------------- internal helpers for provider cooldown & rule-based fallback -------------
    def _maybe_disable_openai(self, error_reason: str):
        from time import time
        if not error_reason:
            return
        if 'insufficient_quota' in error_reason or 'quota' in error_reason.lower():
            # Disable for 30 minutes to avoid repeated failing calls
            self._openai_disabled_until = time() + 1800
            print("⏸️  Disabling OpenAI for 30 minutes due to quota errors")
        elif 'HTTP 401' in error_reason or 'invalid_api_key' in error_reason.lower():
            # Disable until restart for authentication issues
            self._openai_disabled_until = time() + 3600
            print("⏸️  Disabling OpenAI for 60 minutes due to auth errors")

    def _is_openai_temporarily_disabled(self) -> bool:
        from time import time
        if self._openai_disabled_until is None:
            return False
        if time() < self._openai_disabled_until:
            return True
        self._openai_disabled_until = None
        return False

    def _rule_based_generation(self, subject: str, question: str) -> dict:
        """Produce a structured educational answer without external AI (core fields)."""
        key_points = []
        step = []
        example = ""
        mistakes = []
        tips = []

        q_lower = question.lower().strip()
        # Simple arithmetic evaluator
        import re as _re
        if subject.lower() in ('mathematics','math','arithmetic'):
            expr = _re.sub(r"[^0-9+\-*/().^ ]","", q_lower)
            expr = expr.replace('^','**')
            result = None
            try:
                if expr and any(ch.isdigit() for ch in expr):
                    result = eval(expr, {"__builtins__": {}}, {})  # safe limited eval
            except Exception:
                pass
            key_points = ["Addition combines quantities", "Basic arithmetic is foundational"]
            if result is not None:
                step.append(f"Compute the expression: {expr} = {result}.")
                example = f"If you have the expression {expr}, the evaluated result is {result}."
                tips.append("Break expressions into smaller parts you can solve stepwise.")
            else:
                step.append("Identify numbers and the operation (e.g., 1 + 1 means add one and one for 2).")
                example = "1 + 1 = 2 represents combining two single units."
                tips.append("Practise with small numbers to build confidence.")
            mistakes = ["Rushing and mis-reading symbols","Forgetting operator precedence"]
        else:
            key_points = [f"Core concept in {subject}", "Understand definitions first", "Relate idea to real examples"]
            step.append(f"Break down the question '{question}' into known terms and relationships. Explain each term, then show how they connect in {subject} context.")
            example = f"In {subject}, a simple example illustrating this is often the easiest concrete scenario you already know."
            mistakes = ["Memorizing without context","Skipping foundational definitions"]
            tips = ["Summarize what you learned in own words","Teach someone else to test understanding"]

        return {
            'key_points': key_points,
            'step_by_step': "\n".join(step),
            'real_world_example': example,
            'common_mistakes': mistakes,
            'additional_tips': tips
        }


# Global instance - will be initialized when needed
ai_tutor = None


def get_ai_tutor():
    """Get or create AI tutor instance"""
    global ai_tutor
    if ai_tutor is None:
        ai_tutor = SmartLearnTutor()
    return ai_tutor
