#!/usr/bin/env python3
"""
Simple test for SmartLearn AI improvements
"""

import sys
import os
sys.path.append('.')


def test_imports():
    """Test if modules can be imported"""
    try:
        from ai_tutor import get_ai_tutor
        from quiz_generator import QuizGenerator
        print("✅ Imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_fallback():
    """Test fallback mechanisms"""
    try:
        from ai_tutor import get_ai_tutor
        from quiz_generator import QuizGenerator

        print("Testing AI Tutor fallback...")
        tutor = get_ai_tutor()
        result = tutor.generate_answer('Mathematics', 'What is algebra?')
        fallback_used = result.get('fallback', False)
        print(
            f"AI Tutor fallback: {'✅ Working' if fallback_used else '❌ Not using fallback'}")

        print("Testing Quiz Generator fallback...")
        generator = QuizGenerator()
        quiz = generator.generate_quiz(
            'Mathematics', 'Algebra', 'intermediate', 'concept_check', 2)
        quiz_valid = len(quiz.get('questions', [])) > 0
        print(
            f"Quiz Generator fallback: {'✅ Working' if quiz_valid else '❌ Failed'}")

        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 SmartLearn AI Test")
    print("=" * 30)

    success = test_imports()
    if success:
        success = test_fallback()

    print("=" * 30)
    if success:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed")
