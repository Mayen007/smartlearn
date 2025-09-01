#!/usr/bin/env python3
"""
Test script for SmartLearn AI improvements
"""

from quiz_generator import QuizGenerator
from ai_tutor import get_ai_tutor
import os
import sys
sys.path.append('.')


def test_ai_tutor():
    """Test the improved AI tutor functionality"""
    print("🧪 Testing AI Tutor...")

    tutor = get_ai_tutor()

    # Test with a simple question
    try:
        result = tutor.generate_answer("Mathematics", "What is algebra?")
        print("✅ AI Tutor test successful!")
        print(f"📄 Response length: {len(result.get('answer', ''))} characters")
        print(f"🤖 AI Provider: {result.get('ai_provider', 'unknown')}")
        return True
    except Exception as e:
        print(f"❌ AI Tutor test failed: {str(e)}")
        return False


def test_quiz_generator():
    """Test the improved quiz generator functionality"""
    print("🧪 Testing Quiz Generator...")

    generator = QuizGenerator()

    # Test quiz generation
    try:
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
    print("🚀 Starting SmartLearn AI Tests...\n")

    # Check environment variables
    print("🔧 Environment Check:")
    openai_key = os.getenv('OPENAI_API_KEY')
    hf_key = os.getenv('HUGGINGFACE_API_KEY')
    use_hf = os.getenv('USE_HUGGINGFACE', 'false').lower() == 'true'

    print(f"   OpenAI API Key: {'✅ Set' if openai_key else '❌ Not set'}")
    print(f"   Hugging Face API Key: {'✅ Set' if hf_key else '❌ Not set'}")
    print(f"   Use Hugging Face: {'✅ Enabled' if use_hf else '❌ Disabled'}")
    print()

    # Run tests
    tutor_success = test_ai_tutor()
    print()
    quiz_success = test_quiz_generator()
    print()

    # Summary
    print("📊 Test Results:")
    print(f"   AI Tutor: {'✅ PASS' if tutor_success else '❌ FAIL'}")
    print(f"   Quiz Generator: {'✅ PASS' if quiz_success else '❌ FAIL'}")

    if tutor_success and quiz_success:
        print("\n🎉 All tests passed! SmartLearn AI is ready for production.")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")


if __name__ == "__main__":
    main()
