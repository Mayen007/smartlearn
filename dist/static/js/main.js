// SmartLearn JavaScript - Phase 4
// Handles AI-powered Ask the Tutor functionality, session tracking, learning dashboard, and Quiz Generator

// Global variables
let currentQuizData = null;
let selectedAnswer = null;
let quizStartTime = null;

// Quiz Generator variables
let currentQuiz = null;
let currentQuizSession = null;
let quizTimer = null;
let quizAnswers = [];
let currentQuestionIndex = 0;

// Utility functions
function scrollToTutor() {
  document.getElementById('tutor').scrollIntoView({
    behavior: 'smooth'
  });
}

function scrollToDashboard() {
  document.getElementById('dashboard').scrollIntoView({
    behavior: 'smooth'
  });
}

function scrollToQuizGenerator() {
  document.getElementById('quiz-generator').scrollIntoView({
    behavior: 'smooth'
  });
}

function showLoading() {
  const responseArea = document.getElementById('response');
  responseArea.classList.remove('hidden');
  responseArea.innerHTML = `
        <div class="response-content">
            <div class="loading-container">
                <div class="loading-text">🤔 AI Tutor is thinking...</div>
                <div class="loading-spinner"></div>
                <div class="loading-subtext">Generating personalized response...</div>
            </div>
        </div>
    `;
}

function showError(message) {
  const responseArea = document.getElementById('response');
  responseArea.classList.remove('hidden');
  responseArea.innerHTML = `
        <div class="response-content">
            <div class="error-container">
                <div class="error-icon">❌</div>
                <div class="error-title">Error</div>
                <div class="error-message">${message}</div>
                <button class="btn btn-primary" data-action="retry-ask-tutor">Try Again</button>
            </div>
        </div>
    `;
}

// Main Ask Tutor function
async function askTutor() {
  const subject = document.getElementById('subject').value;
  const question = document.getElementById('question').value.trim();

  // Validation
  if (!question) {
    alert('Please enter your question!');
    return;
  }

  // Show loading with AI-specific message
  showLoading();

  try {
    const response = await fetch('/ask', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        subject: subject,
        question: question
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    displayResponse(data);

    // Auto-load dashboard after asking a question
    setTimeout(() => {
      loadDashboard();
    }, 1000);

  } catch (error) {
    console.error('Error:', error);
    showError(`Failed to get response from AI tutor: ${error.message}`);
  }
}

// Display the AI response
function displayResponse(data) {
  console.log('displayResponse called with data:', data);

  const responseArea = document.getElementById('response');

  // Check if response area exists
  if (!responseArea) {
    console.error('Response area not found');
    return;
  }

  // Validate required data fields
  if (!data || typeof data !== 'object') {
    console.error('Invalid response data:', data);
    showError('Received invalid response from AI tutor');
    return;
  }

  // Check for required fields
  if (!data.answer) {
    console.error('Missing answer field in response:', data);
    showError('AI tutor response is missing the answer');
    return;
  }

  console.log('Data validation passed, proceeding with display...');

  // RESTORE the original HTML structure that was destroyed by showLoading()
  responseArea.innerHTML = `
    <div class="response-content">
      <h3>Answer:</h3>
      <div id="answer-text"></div>
      
      <!-- Learning Tip -->
      <div id="learning-tip" class="learning-tip hidden"></div>
      
      <div class="quiz-section">
        <h4>Practice Question:</h4>
        <div id="quiz-question"></div>
        <div id="quiz-options"></div>
        <button class="btn btn-secondary" onclick="checkAnswer()">Check Answer</button>
        <div id="quiz-result"></div>
      </div>
    </div>
  `;

  console.log('HTML structure restored');

  // Debug: Check all elements we need AFTER restoring HTML
  console.log('=== DOM ELEMENT CHECK AFTER RESTORE ===');
  console.log('response element:', document.getElementById('response'));
  console.log('answer-text element:', document.getElementById('answer-text'));
  console.log('learning-tip element:', document.getElementById('learning-tip'));
  console.log('quiz-question element:', document.getElementById('quiz-question'));
  console.log('quiz-options element:', document.getElementById('quiz-options'));
  console.log('quiz-result element:', document.getElementById('quiz-result'));
  console.log('=== END DOM CHECK ===');

  // Store quiz data globally (with fallbacks)
  currentQuizData = {
    question: data.quiz_question || 'No practice question available',
    options: data.quiz_options || ['Option A', 'Option B', 'Option C', 'Option D'],
    correctAnswer: data.quiz_answer || 'Option A',
    subject: data.subject || 'General'
  };

  console.log('Stored quiz data:', currentQuizData);

  // Display answer with better formatting
  const answerText = document.getElementById('answer-text');
  console.log('Answer text element found:', !!answerText);
  if (answerText) {
    const formattedAnswer = formatAIResponse(data.answer);
    console.log('Formatted answer:', formattedAnswer);
    answerText.innerHTML = `
          <div class="answer-content">
              ${formattedAnswer}
          </div>
      `;
    console.log('Answer text populated');
  }

  // Display learning tip if available
  if (data.learning_tip) {
    const learningTipDiv = document.getElementById('learning-tip');
    console.log('Learning tip element found:', !!learningTipDiv);
    if (learningTipDiv) {
      learningTipDiv.innerHTML = `
              <div class="learning-tip-content">
                  <span class="learning-tip-icon">💡</span>
                  <span class="learning-tip-text"><strong>Learning Tip:</strong> ${data.learning_tip}</span>
              </div>
          `;
      learningTipDiv.classList.remove('hidden');
      console.log('Learning tip populated and displayed');
    }
  }

  // Display quiz question
  const quizQuestion = document.getElementById('quiz-question');
  console.log('Quiz question element found:', !!quizQuestion);
  if (quizQuestion) {
    quizQuestion.innerHTML = `
          <div class="quiz-question-content">
              <strong>🧠 Practice Question:</strong><br>
              ${data.quiz_question || 'No practice question available'}
          </div>
      `;
    console.log('Quiz question populated');
  }

  // Display quiz options
  const quizOptionsContainer = document.getElementById('quiz-options');
  console.log('Quiz options container found:', !!quizOptionsContainer);
  if (quizOptionsContainer) {
    quizOptionsContainer.innerHTML = '';

    const options = data.quiz_options || ['Option A', 'Option B', 'Option C', 'Option D'];
    console.log('Quiz options to display:', options);
    options.forEach((option, index) => {
      const optionDiv = document.createElement('div');
      optionDiv.className = 'quiz-option';
      optionDiv.setAttribute('data-answer', option);
      optionDiv.innerHTML = `
              <span class="quiz-option-letter">${String.fromCharCode(65 + index)})</span>
              <span class="quiz-option-text">${option}</span>
          `;
      quizOptionsContainer.appendChild(optionDiv);
    });
    console.log('Quiz options populated');
  }

  // Show response area
  console.log('Response area current display style:', responseArea.style.display);
  responseArea.classList.remove('hidden');
  console.log('Response area display set to visible');

  // Reset quiz result
  const quizResult = document.getElementById('quiz-result');
  if (quizResult) {
    quizResult.innerHTML = '';
  }
  selectedAnswer = null;

  // Start quiz timer
  quizStartTime = Date.now();

  // Add success message
  showSuccessMessage();

  console.log('displayResponse function completed successfully');
}

// Format AI response for better readability
function formatAIResponse(response) {
  // Convert line breaks to HTML
  let formatted = response.replace(/\n/g, '<br>');

  // Highlight key sections with CSS classes
  formatted = formatted.replace(/(Key Points?:)/gi, '<span class="highlight-key-points">$1</span>');
  formatted = formatted.replace(/(Real-world Example?:)/gi, '<span class="highlight-real-world">$1</span>');
  formatted = formatted.replace(/(Common Mistakes?:)/gi, '<span class="highlight-common-mistakes">$1</span>');

  return formatted;
}

// Show success message after AI response
function showSuccessMessage() {
  const responseArea = document.getElementById('response');
  if (!responseArea) {
    console.error('Response area not found for success message');
    return;
  }

  const successDiv = document.createElement('div');
  successDiv.className = 'success-message';
  successDiv.innerHTML = `
        <div class="success-content">
            🎉 AI Tutor response generated successfully! 
            <div class="success-subtext">
                Try the practice question below to test your understanding.
            </div>
        </div>
    `;

  responseArea.appendChild(successDiv);
}

// Handle quiz answer selection
function selectAnswer(answer, element) {
  // Remove previous selection
  document.querySelectorAll('.quiz-option').forEach(opt => {
    opt.classList.remove('selected');
  });

  // Select current answer
  element.classList.add('selected');
  selectedAnswer = answer;
}

// Check quiz answer
async function checkAnswer() {
  if (!selectedAnswer) {
    alert('Please select an answer first!');
    return;
  }

  if (!currentQuizData) {
    alert('No quiz data available!');
    return;
  }

  const isCorrect = selectedAnswer === currentQuizData.correctAnswer;
  const resultDiv = document.getElementById('quiz-result');

  // Calculate time taken
  const timeTaken = quizStartTime ? Math.round((Date.now() - quizStartTime) / 1000) : 0;

  // Calculate score (100% for correct, 0% for incorrect)
  const score = isCorrect ? 100 : 0;

  // Submit quiz result to backend
  try {
    await submitQuizResult(score, timeTaken);
  } catch (error) {
    console.error('Failed to submit quiz result:', error);
  }

  if (isCorrect) {
    resultDiv.innerHTML = `
            <div class="quiz-result correct">
                <div class="quiz-result-icon">🎉</div>
                <div class="quiz-result-title">Correct! Well done!</div>
                <div class="quiz-result-subtitle">You're mastering this topic! Keep up the great work.</div>
            </div>
        `;
  } else {
    resultDiv.innerHTML = `
            <div class="quiz-result incorrect">
                <div class="quiz-result-icon">❌</div>
                <div class="quiz-result-title">Incorrect. The correct answer is: <strong>${currentQuizData.correctAnswer}</strong></div>
                <div class="quiz-result-subtitle">Don't worry! Learning is a process. Review the explanation above and try again.</div>
            </div>
        `;
  }

  // Auto-refresh dashboard after quiz
  setTimeout(() => {
    loadDashboard();
  }, 1000);
}

// Submit quiz result to backend
async function submitQuizResult(score, timeTaken) {
  try {
    const response = await fetch('/quiz/result', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        subject: currentQuizData.subject,
        quiz_data: currentQuizData,
        score: score,
        time_taken: timeTaken
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    console.log('Quiz result submitted:', result);

  } catch (error) {
    console.error('Error submitting quiz result:', error);
    throw error;
  }
}

// Quiz Generator Functions
function initializeQuizGenerator() {
  // Populate topic dropdowns based on subject
  const subjectSelect = document.getElementById('quiz-subject');
  const topicSelect = document.getElementById('quiz-topic');

  const topicsBySubject = {
    'Mathematics': ['Algebra', 'Geometry', 'Trigonometry', 'Calculus', 'Statistics'],
    'Physics': ['Mechanics', 'Electricity', 'Waves', 'Optics', 'Modern Physics'],
    'Chemistry': ['Organic Chemistry', 'Inorganic Chemistry', 'Physical Chemistry', 'Analytical Chemistry'],
    'Biology': ['Cell Biology', 'Genetics', 'Ecology', 'Evolution', 'Human Biology'],
    'History': ['Ancient History', 'Medieval History', 'Modern History', 'African History', 'World History'],
    'Geography': ['Physical Geography', 'Human Geography', 'Economic Geography', 'Political Geography', 'Climate'],
    'English': ['Grammar', 'Literature', 'Comprehension', 'Essay Writing', 'Poetry']
  };

  subjectSelect.addEventListener('change', function () {
    const selectedSubject = this.value;
    const topics = topicsBySubject[selectedSubject] || [];

    topicSelect.innerHTML = '<option value="">Select a topic</option>';
    topics.forEach(topic => {
      const option = document.createElement('option');
      option.value = topic;
      option.textContent = topic;
      topicSelect.appendChild(option);
    });
  });
}

async function generateQuiz() {
  const subject = document.getElementById('quiz-subject').value;
  const topic = document.getElementById('quiz-topic').value;
  const difficulty = document.getElementById('quiz-difficulty').value;
  const quizType = document.getElementById('quiz-type').value;
  const numQuestions = parseInt(document.getElementById('quiz-questions').value);

  // Validation
  if (!subject || !topic) {
    alert('Please select both subject and topic!');
    return;
  }

  // Show loading
  showQuizLoading();

  try {
    const response = await fetch('/quiz/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        subject: subject,
        topic: topic,
        difficulty: difficulty,
        quiz_type: quizType,
        num_questions: numQuestions
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    if (data.success) {
      currentQuiz = data.quiz;
      displayQuiz(currentQuiz);
    } else {
      throw new Error(data.error || 'Failed to generate quiz');
    }

  } catch (error) {
    console.error('Error generating quiz:', error);
    showQuizError(`Failed to generate quiz: ${error.message}`);
  }
}

function showQuizLoading() {
  const quizDisplay = document.getElementById('quiz-display');
  const quizResults = document.getElementById('quiz-results');

  quizDisplay.style.display = 'none';
  quizResults.style.display = 'none';

  // Show loading in quiz creation form
  const generateBtn = document.querySelector('#quiz-generator .btn');
  const originalText = generateBtn.textContent;
  generateBtn.textContent = '🔄 Generating Quiz...';
  generateBtn.disabled = true;

  // Re-enable button after a delay
  setTimeout(() => {
    generateBtn.textContent = originalText;
    generateBtn.disabled = false;
  }, 3000);
}

function showQuizError(message) {
  alert(`Quiz Generation Error: ${message}`);
}

function displayQuiz(quizData) {
  currentQuiz = quizData;
  quizAnswers = new Array(quizData.questions.length).fill(null);
  currentQuestionIndex = 0;

  // Display quiz header
  document.getElementById('quiz-title').textContent = quizData.title;
  document.getElementById('quiz-subject-display').textContent = quizData.subject;
  document.getElementById('quiz-topic-display').textContent = quizData.topic;
  document.getElementById('quiz-difficulty-display').textContent = quizData.difficulty.charAt(0).toUpperCase() + quizData.difficulty.slice(1);

  // Show timer if time limit exists
  const timerDiv = document.getElementById('quiz-timer');
  if (quizData.metadata && quizData.metadata.time_limit) {
    timerDiv.style.display = 'block';
    startQuizTimer(quizData.metadata.time_limit);
  } else {
    timerDiv.style.display = 'none';
  }

  // Display first question
  displayQuestion(0);

  // Show quiz display
  document.getElementById('quiz-display').style.display = 'block';

  // Hide quiz creation form
  document.querySelector('.quiz-creation-form').style.display = 'none';
}

function displayQuestion(questionIndex) {
  if (!currentQuiz || questionIndex >= currentQuiz.questions.length) {
    return;
  }

  currentQuestionIndex = questionIndex;
  const question = currentQuiz.questions[questionIndex];
  const container = document.getElementById('quiz-questions-container');

  container.innerHTML = `
        <div class="quiz-question">
            <h4>Question ${questionIndex + 1} of ${currentQuiz.questions.length}</h4>
            <p>${question.question}</p>
            <div class="quiz-options">
                ${question.options.map((option, index) => `
                    <div class="quiz-option-radio ${quizAnswers[questionIndex] === option ? 'selected' : ''}" onclick="selectQuizAnswer(${questionIndex}, '${option}')">
                        <input type="radio" name="q${questionIndex}" value="${option}" ${quizAnswers[questionIndex] === option ? 'checked' : ''}>
                        <label>${String.fromCharCode(65 + index)}) ${option}</label>
                    </div>
                `).join('')}
            </div>
        </div>
    `;

  // Update navigation buttons
  updateQuizNavigation();
}

function selectQuizAnswer(questionIndex, answer) {
  quizAnswers[questionIndex] = answer;

  // Update visual selection
  const options = document.querySelectorAll(`#quiz-questions-container .quiz-option-radio`);
  options.forEach((option, index) => {
    option.classList.remove('selected');
    const radio = option.querySelector('input[type="radio"]');
    if (radio.value === answer) {
      option.classList.add('selected');
      radio.checked = true;
    }
  });

  // Update navigation buttons
  updateQuizNavigation();
}

function updateQuizNavigation() {
  const prevBtn = document.getElementById('prev-question');
  const nextBtn = document.getElementById('next-question');
  const submitBtn = document.getElementById('submit-quiz');

  // Previous button
  if (currentQuestionIndex === 0) {
    prevBtn.style.display = 'none';
  } else {
    prevBtn.style.display = 'inline-block';
  }

  // Next/Submit button
  if (currentQuestionIndex === currentQuiz.questions.length - 1) {
    nextBtn.style.display = 'none';
    submitBtn.style.display = 'inline-block';
  } else {
    nextBtn.style.display = 'inline-block';
    submitBtn.style.display = 'none';
  }

  // Enable submit only if all questions are answered
  const allAnswered = quizAnswers.every(answer => answer !== null);
  submitBtn.disabled = !allAnswered;
}

function previousQuestion() {
  if (currentQuestionIndex > 0) {
    displayQuestion(currentQuestionIndex - 1);
  }
}

function nextQuestion() {
  if (currentQuestionIndex < currentQuiz.questions.length - 1) {
    displayQuestion(currentQuestionIndex + 1);
  }
}

function startQuizTimer(timeLimitSeconds) {
  let timeRemaining = timeLimitSeconds;
  const timeDisplay = document.getElementById('time-remaining');

  function updateTimer() {
    const minutes = Math.floor(timeRemaining / 60);
    const seconds = timeRemaining % 60;
    timeDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;

    if (timeRemaining <= 0) {
      // Time's up - auto-submit quiz
      clearInterval(quizTimer);
      alert('Time\'s up! Submitting quiz automatically.');
      submitQuiz();
      return;
    }

    timeRemaining--;
  }

  updateTimer();
  quizTimer = setInterval(updateTimer, 1000);
}

async function submitQuiz() {
  // Stop timer
  if (quizTimer) {
    clearInterval(quizTimer);
    quizTimer = null;
  }

  // Calculate time taken
  const timeTaken = Math.round((Date.now() - (currentQuizSession?.start_time || Date.now())) / 1000);

  try {
    const response = await fetch(`/quiz/${currentQuiz.metadata?.id || 'temp'}/submit`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        answers: quizAnswers,
        time_taken: timeTaken
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();

    if (data.success) {
      displayQuizResults(data.results);
    } else {
      throw new Error(data.error || 'Failed to submit quiz');
    }

  } catch (error) {
    console.error('Error submitting quiz:', error);
    alert(`Failed to submit quiz: ${error.message}`);
  }
}

function displayQuizResults(results) {
  // Hide quiz display
  document.getElementById('quiz-display').style.display = 'none';

  // Display results summary
  const summaryDiv = document.getElementById('results-summary');
  summaryDiv.innerHTML = `
        <div class="score-display">${results.score_percentage.toFixed(1)}%</div>
        <div class="score-label">Score</div>
        <div class="quiz-results-summary">
            <div>Correct: ${results.correct_answers}/${results.total_questions}</div>
            <div>Time: ${Math.floor(results.time_taken / 60)}:${(results.time_taken % 60).toString().padStart(2, '0')}</div>
        </div>
    `;

  // Display question breakdown
  const breakdownDiv = document.getElementById('results-breakdown');
  breakdownDiv.innerHTML = `
        <h4>Question Breakdown</h4>
        ${results.question_results.map((result, index) => `
            <div class="question-result ${result.is_correct ? 'correct' : 'incorrect'}">
                <h5>Question ${index + 1}</h5>
                <div class="student-answer">Your answer: ${result.student_answer}</div>
                ${!result.is_correct ? `<div class="correct-answer">Correct answer: ${result.correct_answer}</div>` : ''}
                <div class="explanation">${result.explanation}</div>
            </div>
        `).join('')}
    `;

  // Display feedback
  const feedbackDiv = document.getElementById('results-feedback');
  feedbackDiv.innerHTML = `
        <h4>Performance Feedback</h4>
        ${results.feedback.map(item => `<div class="feedback-item">${item}</div>`).join('')}
    `;

  // Show results
  document.getElementById('quiz-results').style.display = 'block';

  // Auto-refresh dashboard
  setTimeout(() => {
    loadDashboard();
  }, 1000);
}

function generateNewQuiz() {
  // Reset quiz state
  currentQuiz = null;
  currentQuizSession = null;
  quizAnswers = [];
  currentQuestionIndex = 0;

  // Clear timer
  if (quizTimer) {
    clearInterval(quizTimer);
    quizTimer = null;
  }

  // Hide results and show creation form
  document.getElementById('quiz-results').style.display = 'none';
  document.querySelector('.quiz-creation-form').style.display = 'block';

  // Reset form
  document.getElementById('quiz-subject').value = 'Mathematics';
  document.getElementById('quiz-topic').value = '';
  document.getElementById('quiz-difficulty').value = 'intermediate';
  document.getElementById('quiz-type').value = 'concept_check';
  document.getElementById('quiz-questions').value = '5';

  // Trigger subject change to populate topics
  document.getElementById('quiz-subject').dispatchEvent(new Event('change'));
}

function reviewQuiz() {
  // Go back to quiz display to review answers
  document.getElementById('quiz-results').style.display = 'none';
  document.getElementById('quiz-display').style.display = 'block';

  // Display first question
  displayQuestion(0);
}

// Dashboard Functions
async function loadDashboard() {
  try {
    // Show loading states
    showDashboardLoading();

    // Load dashboard data
    const response = await fetch('/learning/dashboard');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    displayDashboard(data);

  } catch (error) {
    console.error('Error loading dashboard:', error);
    showDashboardError('Failed to load dashboard data');
  }
}

function showDashboardLoading() {
  const sections = ['progress-summary', 'learning-recommendations', 'subject-analytics', 'recent-activity'];
  sections.forEach(sectionId => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.innerHTML = `
                <div class="loading-placeholder">
                    <div class="loading-spinner"></div>
                    <p>Loading...</p>
                </div>
            `;
    }
  });
}

function showDashboardError(message) {
  const sections = ['progress-summary', 'learning-recommendations', 'subject-analytics', 'recent-activity'];
  sections.forEach(sectionId => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.innerHTML = `
                <div class="dashboard-error-state">
                    <div>❌ Error</div>
                    <div>${message}</div>
                </div>
            `;
    }
  });
}

function displayDashboard(data) {
  // Display progress summary
  displayProgressSummary(data.progress_summary);

  // Display learning recommendations
  displayLearningRecommendations(data.learning_recommendations);

  // Display subject analytics
  displaySubjectAnalytics(data.subject_analytics);

  // Display recent activity
  displayRecentActivity(data.recent_activity);
}

function displayProgressSummary(progress) {
  const container = document.getElementById('progress-summary');

  container.innerHTML = `
        <div class="progress-item">
            <span class="progress-label">Session Duration</span>
            <span class="progress-value">${progress.session_duration_minutes} min</span>
        </div>
        <div class="progress-item">
            <span class="progress-label">Questions Asked</span>
            <span class="progress-value">${progress.total_questions}</span>
        </div>
        <div class="progress-item">
            <span class="progress-label">Quiz Attempts</span>
            <span class="progress-value">${progress.total_quizzes}</span>
        </div>
        <div class="progress-item">
            <span class="progress-label">Average Quiz Score</span>
            <span class="progress-value">${progress.average_quiz_score.toFixed(1)}%</span>
        </div>
        <div class="progress-item">
            <span class="progress-label">Subjects Explored</span>
            <span class="progress-value">${progress.subjects_explored.length}</span>
        </div>
        <div class="progress-item">
            <span class="progress-label">Most Active Subject</span>
            <span class="progress-value">${progress.most_active_subject || 'None'}</span>
        </div>
        ${progress.quiz_performance ? `
        <div class="progress-item">
            <span class="progress-label">Quizzes Generated</span>
            <span class="progress-value">${progress.quiz_performance.quizzes_generated}</span>
        </div>
        <div class="progress-item">
            <span class="progress-label">Best Subject</span>
            <span class="progress-value">${progress.quiz_performance.best_performing_subject || 'None'}</span>
        </div>
        ` : ''}
    `;
}

function displayLearningRecommendations(recommendations) {
  const container = document.getElementById('learning-recommendations');

  if (!recommendations || recommendations.length === 0) {
    container.innerHTML = `
            <div class="dashboard-empty-state">
                <div>🎯</div>
                <div>Ask more questions to get personalized recommendations!</div>
            </div>
        `;
    return;
  }

  container.innerHTML = recommendations.map(rec => `
        <div class="recommendation-item priority-${rec.priority}">
            <div class="recommendation-title">${rec.title}</div>
            <div class="recommendation-description">${rec.description}</div>
            <div class="recommendation-action">💡 ${rec.action}</div>
        </div>
    `).join('');
}

function displaySubjectAnalytics(analytics) {
  const container = document.getElementById('subject-analytics');

  if (!analytics || Object.keys(analytics).length === 0) {
    container.innerHTML = `
            <div class="dashboard-empty-state">
                <div>📚</div>
                <div>No subject data yet. Start learning to see analytics!</div>
            </div>
        `;
    return;
  }

  container.innerHTML = Object.entries(analytics).map(([subject, data]) => `
        <div class="subject-item">
            <div class="subject-name">${subject}</div>
            <div class="subject-stats">
                <div class="stat-item">
                    <span class="stat-label">Questions:</span>
                    <span class="stat-value">${data.questions_asked}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Quizzes:</span>
                    <span class="stat-value">${data.quiz_attempts}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Avg Score:</span>
                    <span class="stat-value">${data.average_quiz_score.toFixed(1)}%</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Topics:</span>
                    <span class="stat-value">${data.topics_covered.length}</span>
                </div>
            </div>
        </div>
    `).join('');
}

function displayRecentActivity(activities) {
  const container = document.getElementById('recent-activity');

  if (!activities || activities.length === 0) {
    container.innerHTML = `
            <div class="dashboard-empty-state">
                <div>🕒</div>
                <div>No recent activity. Start learning to see your history!</div>
            </div>
        `;
    return;
  }

  container.innerHTML = activities.map(activity => {
    const icon = activity.type === 'question' ? '❓' : '🧠';
    const iconClass = activity.type === 'question' ? 'question' : 'quiz';
    const title = activity.type === 'question' ? 'Question Asked' : 'Quiz Completed';
    const subtitle = activity.data.subject;
    const time = new Date(activity.timestamp).toLocaleTimeString();

    return `
            <div class="activity-item">
                <div class="activity-icon ${iconClass}">${icon}</div>
                <div class="activity-content">
                    <div class="activity-title">${title}</div>
                    <div class="activity-subtitle">${subtitle}</div>
                </div>
                <div class="activity-time">${time}</div>
            </div>
        `;
  }).join('');
}

// Session management
async function resetSession() {
  if (confirm('Are you sure you want to reset your learning session? This will clear all progress data.')) {
    try {
      const response = await fetch('/session/reset', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.ok) {
        alert('Session reset successfully! Your learning journey starts fresh.');
        loadDashboard(); // Refresh dashboard
      } else {
        throw new Error('Failed to reset session');
      }
    } catch (error) {
      console.error('Error resetting session:', error);
      alert('Failed to reset session. Please try again.');
    }
  }
}

// Initialize page
document.addEventListener('DOMContentLoaded', function () {
  console.log('SmartLearn Phase 4 - Quiz Generator initialized! 🚀🧠📊🎲');

  // Verify all required DOM elements exist
  const requiredElements = [
    'response', 'answer-text', 'quiz-question', 'quiz-options',
    'quiz-result', 'learning-tip', 'subject', 'question'
  ];

  const missingElements = [];
  requiredElements.forEach(id => {
    if (!document.getElementById(id)) {
      missingElements.push(id);
    }
  });

  if (missingElements.length > 0) {
    console.error('Missing required DOM elements:', missingElements);
    // Don't proceed if critical elements are missing
    return;
  }

  // Set up event delegation for all button actions
  document.addEventListener('click', handleButtonActions);

  // Set up event delegation for quiz options
  document.addEventListener('click', handleQuizOptionSelection);

  // Set up navigation link handlers
  setupNavigationHandlers();

  // Add AI status indicator
  addAIStatusIndicator();

  // Initialize quiz generator
  initializeQuizGenerator();

  // Load dashboard on page load
  loadDashboard();

  console.log('All required elements found, application ready');
});

// Centralized button action handler
function handleButtonActions(event) {
  const target = event.target;
  const action = target.getAttribute('data-action');

  if (!action) return;

  event.preventDefault();

  switch (action) {
    case 'scroll-to-tutor':
      scrollToTutor();
      break;
    case 'scroll-to-quiz':
      scrollToQuizGenerator();
      break;
    case 'ask-tutor':
    case 'retry-ask-tutor':
      askTutor();
      break;
    case 'check-answer':
      checkAnswer();
      break;
    default:
      console.warn('Unknown action:', action);
  }
}

// Handle quiz option selection
function handleQuizOptionSelection(event) {
  const target = event.target.closest('.quiz-option');

  if (!target) return;

  const answer = target.getAttribute('data-answer');
  if (answer) {
    selectAnswer(answer, target);
  }
}

// Setup navigation handlers
function setupNavigationHandlers() {
  // Handle navigation links
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function (e) {
      e.preventDefault();
      const targetId = this.getAttribute('href');
      const targetSection = document.querySelector(targetId);

      if (targetSection) {
        const offsetTop = targetSection.offsetTop - 80; // Account for fixed navbar
        window.scrollTo({
          top: offsetTop,
          behavior: 'smooth'
        });
      }

      // Close mobile menu
      closeMobileMenu();
    });
  });

  // Professional navbar scroll effect
  const navbar = document.querySelector('.navbar');
  let lastScrollTop = 0;

  window.addEventListener('scroll', function () {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    
    // Add scrolled class for enhanced styling
    if (scrollTop > 50) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }

    // Enhanced auto-hide navbar on scroll down
    if (scrollTop > lastScrollTop && scrollTop > 100) {
      navbar.style.transform = 'translateY(-100%)';
      navbar.style.transition = 'transform 0.3s ease-in-out';
    } else {
      navbar.style.transform = 'translateY(0)';
      navbar.style.transition = 'transform 0.3s ease-in-out';
    }
    
    lastScrollTop = scrollTop;
  });

  // Enhanced smooth scrolling for navigation links
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function (e) {
      const href = this.getAttribute('href');
      
      // Only prevent default for anchor links
      if (href && href.startsWith('#')) {
        e.preventDefault();
        const targetSection = document.querySelector(href);

        if (targetSection) {
          const navbar = document.querySelector('.navbar');
          const navbarHeight = navbar.offsetHeight;
          const targetPosition = targetSection.offsetTop - navbarHeight - 20;
          
          window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
          });
          
          // Close mobile menu
          closeMobileMenu();
        }
      }
    });
  });

  // Enhanced mobile menu toggle with body scroll prevention
  const navToggle = document.getElementById('nav-toggle');
  const navMenu = document.getElementById('nav-menu');

  if (navToggle && navMenu) {
    navToggle.addEventListener('click', function () {
      navToggle.classList.toggle('active');
      navMenu.classList.toggle('active');
      
      // Prevent body scroll when menu is open
      if (navMenu.classList.contains('active')) {
        document.body.style.overflow = 'hidden';
      } else {
        document.body.style.overflow = '';
      }
    });
  }

  // Enhanced click outside detection
  document.addEventListener('click', function (event) {
    if (navToggle && navMenu && !navToggle.contains(event.target) && !navMenu.contains(event.target)) {
      navToggle.classList.remove('active');
      navMenu.classList.remove('active');
      document.body.style.overflow = '';
    }
  });

  // Add escape key support for mobile menu
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && navMenu && navMenu.classList.contains('active')) {
      closeMobileMenu();
    }
  });
}

// Add AI status indicator
function addAIStatusIndicator() {
  const nav = document.querySelector('.nav-container');
  if (nav) {
    const statusDiv = document.createElement('div');
    statusDiv.className = 'ai-status-indicator';
    statusDiv.innerHTML = `
      <div class="ai-status-content">
        <div class="ai-status-dot"></div>
        <span class="ai-status-label">AI Tutor + Quiz Generator</span>
      </div>
    `;
    nav.appendChild(statusDiv);
  }
}

// Enhanced mobile menu closure
function closeMobileMenu() {
  const navToggle = document.getElementById('nav-toggle');
  const navMenu = document.getElementById('nav-menu');

  if (navToggle && navMenu) {
    navToggle.classList.remove('active');
    navMenu.classList.remove('active');
    document.body.style.overflow = ''; // Restore body scrolling
  }
}
