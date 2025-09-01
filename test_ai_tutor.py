#!/usr/bin/env python3
"""
Test script for SmartLearn AI Tutor
Run this to verify the AI integration is working correctly.
"""

import os
from dotenv import load_dotenv
from ai_tutor import SmartLearnTutor


def test_ai_tutor():
    """Test the AI tutor functionality"""

    print("🧠 SmartLearn AI Tutor Test")
    print("=" * 40)

    # Load environment variables
    load_dotenv()

    # Check OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables!")
        print("   AI features will use fallback responses.")
        print("   To enable AI features, add your OpenAI API key to .env file")
        print()
        return False

    print(f"✅ OpenAI API key found: {api_key[:8]}...")

    # Initialize AI tutor
    try:
        tutor = SmartLearnTutor()
        print("✅ AI Tutor initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize AI Tutor: {e}")
        return False

    # Test prompt generation
    try:
        prompt = tutor.generate_structured_prompt(
            "Mathematics", "What is the quadratic formula?")
        print("✅ Prompt generation working")
        print(f"   Prompt length: {len(prompt)} characters")
    except Exception as e:
        print(f"❌ Prompt generation failed: {e}")
        return False

    # Test fallback quiz generation
    try:
        question, options, answer = tutor._generate_fallback_quiz("Physics")
        print("✅ Fallback quiz generation working")
        print(f"   Question: {question}")
        print(f"   Options: {options}")
        print(f"   Answer: {answer}")
    except Exception as e:
        print(f"❌ Fallback quiz generation failed: {e}")
        return False

    # Test AI response generation (if API key is valid)
    if api_key and api_key != "your-openai-api-key-here":
        try:
            print("\n🧠 Testing AI response generation...")
            print("   This may take a few seconds...")

            response = tutor.generate_answer(
                "Biology", "What is photosynthesis?")

            if response and 'answer' in response:
                print("✅ AI response generation working!")
                print(
                    f"   Response length: {len(response['answer'])} characters")
                print(f"   Quiz question: {response['quiz_question']}")
                print(f"   Quiz options: {response['quiz_options']}")
                print(f"   Quiz answer: {response['quiz_answer']}")
            else:
                print("❌ AI response generation failed - invalid response format")
                return False

        except Exception as e:
            print(f"❌ AI response generation failed: {e}")
            print("   This might be due to:")
            print("   - Invalid API key")
            print("   - Network issues")
            print("   - OpenAI API rate limits")
            return False
    else:
        print("\n⚠️  Skipping AI response test - using placeholder API key")

    print("\n🎉 All tests completed!")
    return True


def test_flask_integration():
    """Test Flask app integration"""

    print("\n🌐 Testing Flask Integration")
    print("=" * 40)

    try:
        from app import app
        print("✅ Flask app imports successfully")

        # Test health endpoint
        with app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health endpoint working")
                data = response.get_json()
                print(f"   Status: {data.get('status')}")
                print(f"   Phase: {data.get('phase')}")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False

    except Exception as e:
        print(f"❌ Flask integration test failed: {e}")
        return False

    return True


if __name__ == "__main__":
    print("🚀 Starting SmartLearn Phase 2 Tests...\n")

    # Run tests
    ai_test_passed = test_ai_tutor()
    flask_test_passed = test_flask_integration()

    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)

    if ai_test_passed:
        print("✅ AI Tutor Tests: PASSED")
    else:
        print("❌ AI Tutor Tests: FAILED")

    if flask_test_passed:
        print("✅ Flask Integration Tests: PASSED")
    else:
        print("❌ Flask Integration Tests: FAILED")

    if ai_test_passed and flask_test_passed:
        print("\n🎉 All tests passed! SmartLearn Phase 2 is ready!")
        print("\n🚀 Next steps:")
        print("   1. Run 'python app.py' to start the server")
        print("   2. Open http://localhost:5000 in your browser")
        print("   3. Test the AI Tutor with real questions!")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("   1. Verify your .env file is configured correctly")
        print("   2. Check that all dependencies are installed")
        print("   3. Ensure your OpenAI API key is valid")

    print("\n" + "=" * 50)
