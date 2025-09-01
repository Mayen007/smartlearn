# SmartLearn - AI-Powered Learning Companion

An AI-powered personalized tutor and learning companion designed specifically for high school students in Africa. Built with Flask, OpenAI GPT-4o, and modern web technologies.

## 🚀 Features

- **AI-Powered Tutoring**: Get personalized help with any subject using GPT-4o
- **Curriculum Aligned**: Content designed for KCSE, WAEC, and other African curricula
- **Interactive Quizzes**: AI-generated practice questions and explanations
- **Personalized Learning**: AI recommendations based on your progress
- **Learning Analytics**: Track progress, identify strengths, and discover learning gaps
- **Session Management**: Persistent learning sessions with progress tracking
- **Quiz Generator**: AI-powered quiz creation with automated grading
- **Modern UI**: Clean, responsive design optimized for all devices

## 📋 Prerequisites

- Python 3.7 or higher
- pip (Python package installer)
- OpenAI API key (required for AI features)

## 🛠️ Installation & Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd smartlearn
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the root directory:

```env
# Flask secret key (generate a random string for production)
SECRET_KEY=your-secret-key-here

# OpenAI API Key (REQUIRED for AI features)
OPENAI_API_KEY=your-openai-api-key-here

# IntaSend API Keys (for Phase 6)
INTASEND_PUBLIC_KEY=your-intasend-public-key-here
INTASEND_SECRET_KEY=your-intasend-secret-key-here
```

### 5. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## 🏗️ Project Structure

```
smartlearn/
├── app.py                 # Main Flask application with AI integration, session management, and quiz generator
├── ai_tutor.py           # AI tutor module with OpenAI integration
├── student_session.py    # Student session manager and learning analytics
├── quiz_generator.py     # AI-powered quiz generation and grading system
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables (create this)
├── templates/
│   └── index.html        # Main homepage template with dashboard and quiz generator
└── static/
    ├── css/
    │   └── style.css     # Main stylesheet with dashboard and quiz styles
    └── js/
        └── main.js       # Frontend JavaScript with AI, dashboard, and quiz features
```

## 📚 Development Phases

### ✅ Phase 1: Project Setup (COMPLETED)

- [x] Flask app initialization
- [x] Clean project structure
- [x] Homepage with navigation
- [x] "Ask the Tutor" placeholder section
- [x] Local Flask development server

### ✅ Phase 2: AI Tutor Integration (COMPLETED)

- [x] OpenAI GPT-4o API integration
- [x] Structured prompt engineering
- [x] Subject-specific responses
- [x] Curriculum-friendly explanations
- [x] AI-generated practice questions
- [x] Enhanced UI with AI status indicators

### ✅ Phase 3: Personalized Learning Flow (COMPLETED)

- [x] Session-based student tracking
- [x] Question history storage
- [x] AI learning recommendations
- [x] Learning analytics dashboard
- [x] Progress tracking and performance metrics
- [x] Subject-specific analytics
- [x] Recent activity monitoring

### ✅ Phase 4: Quiz Generator (COMPLETED)

- [x] AI-generated multiple-choice question sets
- [x] Interactive quiz interface with timer
- [x] Automated grading and performance tracking
- [x] Quiz history and review system
- [x] Multiple difficulty levels and quiz types
- [x] Real-time quiz analytics

### 🔄 Phase 5: Parent/Teacher Dashboard

- [ ] Progress tracking system
- [ ] Low-code dashboard integration
- [ ] Performance analytics

### 🔄 Phase 6: Payments Integration

- [ ] IntaSend API integration
- [ ] Subscription management
- [ ] Premium feature unlocking

### 🔄 Phase 7: Polish & Deployment

- [ ] TailwindCSS styling
- [ ] Animations and UX improvements
- [ ] Production deployment

## 🧪 Testing the Current Phase

1. **Start the application**: `python app.py`
2. **Open your browser**: Navigate to `http://localhost:5000`
3. **Test the AI Tutor feature**:
   - Select a subject from the dropdown
   - Type a question (e.g., "Can you explain photosynthesis?")
   - Click "Ask Question"
   - Watch the AI generate a personalized response with practice questions!
4. **Explore the Quiz Generator**:
   - Select subject, topic, difficulty, and quiz type
   - Click "Generate Quiz" to create AI-powered quizzes
   - Take interactive quizzes with timer and automated grading
   - Review detailed results and performance feedback
5. **Explore the Learning Dashboard**:
   - View your progress summary
   - Check personalized learning recommendations
   - Monitor subject analytics
   - Track recent learning activity and quiz performance

## 🧠 AI Tutor Features (Phase 2)

### What's New:

- **Real AI Responses**: GPT-4o powered explanations tailored to your subject
- **Curriculum Alignment**: Responses designed for KCSE and WAEC standards
- **Smart Practice Questions**: AI-generated quizzes related to your topic
- **Enhanced UI**: Loading states, success messages, and AI status indicators
- **Fallback System**: Graceful handling when AI is unavailable

### How It Works:

1. **Structured Prompts**: AI receives carefully crafted prompts for each subject
2. **Curriculum Context**: Responses include African educational context
3. **Interactive Learning**: Practice questions test understanding
4. **Error Handling**: Graceful fallbacks when AI services are unavailable

## 📊 Personalized Learning Features (Phase 3)

### What's New:

- **Session Tracking**: Persistent learning sessions with unique IDs
- **Learning Analytics**: Comprehensive progress monitoring and performance metrics
- **AI Recommendations**: Personalized learning suggestions based on your progress
- **Subject Analytics**: Detailed breakdown of performance by subject
- **Activity History**: Track all questions and quiz attempts
- **Learning Tips**: Contextual advice based on your learning journey

### How It Works:

1. **Session Management**: Each student gets a unique session ID for tracking
2. **Progress Analytics**: Monitor questions asked, quiz scores, and time spent
3. **Smart Recommendations**: AI analyzes your patterns to suggest next steps
4. **Performance Tracking**: Identify strengths and areas for improvement
5. **Real-time Updates**: Dashboard refreshes automatically as you learn

### Dashboard Components:

- **Progress Summary**: Session duration, questions asked, quiz attempts, average scores
- **Learning Recommendations**: AI-powered suggestions for continued learning
- **Subject Analytics**: Performance breakdown by subject with topic coverage
- **Recent Activity**: Timeline of your learning journey

## 🎲 Quiz Generator Features (Phase 4)

### What's New:

- **AI-Generated Quizzes**: Create personalized quizzes on any subject and topic
- **Multiple Difficulty Levels**: Beginner, intermediate, and advanced options
- **Quiz Types**: Concept check, problem solving, critical thinking, and real-world application
- **Interactive Interface**: Navigate through questions with progress tracking
- **Timer System**: Automatic quiz submission when time runs out
- **Automated Grading**: Instant scoring with detailed feedback
- **Performance Analytics**: Track quiz history and improvement areas

### How It Works:

1. **Quiz Creation**: Select subject, topic, difficulty, and number of questions
2. **AI Generation**: GPT-4o creates curriculum-aligned multiple-choice questions
3. **Interactive Quiz**: Navigate through questions with radio button selection
4. **Automated Grading**: Instant scoring with explanations for each answer
5. **Performance Tracking**: Results integrated with learning analytics
6. **Fallback System**: Pre-built questions when AI generation fails

### Quiz Features:

- **Subject Coverage**: Mathematics, Physics, Chemistry, Biology, History, Geography, English
- **Topic Selection**: Specific topics within each subject (e.g., Algebra, Mechanics, Genetics)
- **Difficulty Scaling**: Questions adapt to student level
- **Time Management**: Automatic timer with configurable limits
- **Result Review**: Detailed breakdown of correct/incorrect answers
- **Learning Feedback**: Personalized suggestions based on performance

## 🔧 Customization

### Adding New Subjects

Edit `templates/index.html` and add new options to the subject dropdown:

```html
<option value="NewSubject">New Subject</option>
```

### AI Prompt Engineering

Modify `ai_tutor.py` to customize:

- Subject-specific teaching styles
- Curriculum frameworks
- Response formatting
- Quiz generation logic

### Learning Analytics

Modify `student_session.py` to customize:

- Learning pattern analysis
- Recommendation algorithms
- Progress metrics
- Session management

### Quiz Generation

Modify `quiz_generator.py` to customize:

- Quiz prompt engineering
- Difficulty assessment
- Question types and formats
- Grading algorithms

### Styling Changes

Modify `static/css/style.css` to customize colors, fonts, and layout.

### JavaScript Functionality

Edit `static/js/main.js` to add new interactive features.

## 🚀 Next Steps

**Phase 5: Parent/Teacher Dashboard**

- Low-code dashboard integration (Glide, Airtable, Supabase)
- Progress tracking and performance analytics
- Student engagement monitoring
- Learning outcome reporting

## ⚠️ Important Notes

- **OpenAI API Key Required**: AI features won't work without a valid API key
- **API Costs**: Be aware of OpenAI API usage costs
- **Rate Limits**: Consider implementing rate limiting for production use
- **Fallback Mode**: App works with fallback responses when AI is unavailable
- **Session Storage**: Currently uses in-memory storage (use Redis/database for production)
- **Data Persistence**: Session data is lost on server restart (implement persistent storage for production)
- **Quiz Generation**: AI-generated quizzes require OpenAI API access

## 📞 Support

For questions or issues:

- Check the current phase implementation
- Review the code comments for guidance
- Ensure all dependencies are properly installed
- Verify your OpenAI API key is correctly configured

## 📄 License

This project is created for educational and hackathon purposes.

---

**Happy Learning with AI, Analytics, and Interactive Quizzes! 🎓✨🧠📊🎲**
