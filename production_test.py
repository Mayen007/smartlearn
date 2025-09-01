#!/usr/bin/env python3
"""
Test SmartLearn AI with configured API keys
"""

from dotenv import load_dotenv
import os
from ai_tutor import get_ai_tutor
from quiz_generator import QuizGenerator

# Load environment variables
load_dotenv()


def test_environment():
    """Test environment variable loading"""
    print("🔧 Environment Check:")
    openai_key = os.getenv('OPENAI_API_KEY')
    hf_key = os.getenv('HUGGINGFACE_API_KEY')
    use_hf = os.getenv('USE_HUGGINGFACE', 'false').lower() == 'true'

    print(f"   OpenAI API Key: {'✅ Set' if openai_key else '❌ Not set'}")
    print(f"   Hugging Face API Key: {'✅ Set' if hf_key else '❌ Not set'}")
    print(f"   Use Hugging Face: {'✅ Enabled' if use_hf else '❌ Disabled'}")
    print()

    return openai_key is not None or (hf_key is not None and use_hf)


def test_ai_tutor():
    """Test the AI tutor with real API keys"""
    print("🧪 Testing AI Tutor...")

    try:
        tutor = get_ai_tutor()
        result = tutor.generate_answer(
            "Mathematics", "What is the Pythagorean theorem?")

        print("✅ AI Tutor test successful!")
        print(f"📄 Response length: {len(result.get('answer', ''))} characters")
        print(f"🤖 AI Provider: {result.get('ai_provider', 'unknown')}")
        print(
            f"❓ Practice Question: {result.get('quiz_question', 'None')[:50]}...")
        return True
    except Exception as e:
        print(f"❌ AI Tutor test failed: {str(e)}")
        return False


def test_quiz_generator():
    """Test the quiz generator with real API keys"""
    print("🧪 Testing Quiz Generator...")

    try:
        generator = QuizGenerator()
        quiz = generator.generate_quiz(
            "Mathematics", "Algebra", "intermediate", "concept_check", 3)

        print("✅ Quiz Generator test successful!")
        print(f"📚 Quiz title: {quiz.get('title', 'No title')}")
        print(f"❓ Number of questions: {len(quiz.get('questions', []))}")
        print(
            f"🤖 AI Provider: {quiz.get('metadata', {}).get('ai_provider', 'unknown')}")
        return True
    except Exception as e:
        print(f"❌ Quiz Generator test failed: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("🚀 SmartLearn AI Production Test")
    print("=" * 40)

    # Test environment
    env_ok = test_environment()
    if not env_ok:
        print("❌ Environment not properly configured!")
        return

    # Test AI systems
    tutor_success = test_ai_tutor()
    print()
    quiz_success = test_quiz_generator()
    print()

    # Summary
    print("=" * 40)
    print("📊 Test Results:")
    print(f"   Environment: {'✅ PASS' if env_ok else '❌ FAIL'}")
    print(f"   AI Tutor: {'✅ PASS' if tutor_success else '❌ FAIL'}")
    print(f"   Quiz Generator: {'✅ PASS' if quiz_success else '❌ FAIL'}")

    if env_ok and tutor_success and quiz_success:
        print("\n🎉 All systems operational! SmartLearn is production-ready.")
        print("🚀 Ready to provide AI-powered tutoring to African students!")
    else:
        print("\n⚠️  Some systems need attention. Check the error messages above.")


if __name__ == "__main__":
    main()
