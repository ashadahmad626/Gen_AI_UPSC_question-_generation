import streamlit as st
import pandas as pd
from utils import QuestionGenerator
import os
from datetime import datetime

# ⚠️ CRITICAL: st.set_page_config MUST BE FIRST Streamlit command
st.set_page_config(
    page_title="UPSC Mastery Quiz", 
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .main-header {
        font-size: 3rem !important;
        font-weight: 800 !important;
        color: #1e3a8a !important;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .quiz-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
    }
    .question-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #1e3a8a;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .correct { color: #10b981; font-weight: bold; }
    .wrong { color: #ef4444; font-weight: bold; }
    .metric-container { background: linear-gradient(90deg, #10b981, #34d399); }
</style>
""", unsafe_allow_html=True)

class QuizManager:
    def __init__(self):
        self.questions = []
        self.user_answers = {}
        self.results = []
    
    def generate_questions(self, generator, topic, question_type, difficulty, num_questions):
        """Generate questions using the QuestionGenerator"""
        try:
            st.info(f"🔄 Generating {num_questions} {difficulty} questions on: {topic[:50]}...")
            self.questions = generator.generate_questions(topic, question_type, difficulty, num_questions)
            self.user_answers = {}
            self.results = []
            
            if self.questions:
                st.success(f"✅ Generated {len(self.questions)} UPSC questions!")
                return self.questions
            else:
                st.error("❌ No questions generated. Using mock data.")
                return self._get_mock_questions(topic, question_type, num_questions)
        except Exception as e:
            st.error(f"❌ Error generating questions: {str(e)}")
            return self._get_mock_questions(topic, question_type, num_questions)
    
    def _get_mock_questions(self, topic, question_type, num_questions):
        """Fallback mock UPSC questions"""
        mock_questions = {
            "Article 370, Fundamental Rights, Panchayati Raj": [
                {
                    "question": "Which articles of the Indian Constitution deal with Fundamental Rights?",
                    "type": "multiple_choice",
                    "options": ["Article 12-35", "Article 36-51", "Article 51A", "Article 368"],
                    "correct_answer": "Article 12-35"
                },
                {
                    "question": "Panchayati Raj was introduced by which amendment?",
                    "type": "multiple_choice",
                    "options": ["73rd", "42nd", "44th", "86th"],
                    "correct_answer": "73rd"
                },
                {
                    "question": "Article _____ is the 'heart and soul' of the Constitution.",
                    "type": "fill_in_blank",
                    "correct_answer": "32"
                }
            ]
        }
        available = mock_questions.get(topic, [{"question": "Mock question", "type": "multiple_choice", "options": ["A", "B", "C", "D"], "correct_answer": "A"}])
        self.questions = available[:num_questions]
        return self.questions
    
    def attempt_quiz(self):
        """Display quiz questions for user to answer"""
        for i, q in enumerate(self.questions, 1):
            with st.container():
                st.markdown(f"**Q{i}:** {q['question']}")
                
                if q['type'] == 'multiple_choice':
                    options = q['options']
                    selected = st.radio(
                        "",
                        options,
                        key=f"q_{i}",
                        index=None,
                        horizontal=True
                    )
                    if selected is not None:
                        self.user_answers[i] = selected
                else:  # fill_in_blank
                    answer = st.text_input(
                        "",
                        key=f"q_{i}_fill",
                        placeholder="Type answer here...",
                        label_visibility="collapsed"
                    )
                    if answer.strip():
                        self.user_answers[i] = answer.strip()
    
    def evaluate_quiz(self):
        """Evaluate user answers and generate results"""
        self.results = []
        for i, question in enumerate(self.questions, 1):
            user_answer = self.user_answers.get(i, "").strip()
            correct_answer = question['correct_answer'].strip()
            
            # Case-insensitive matching
            is_correct = user_answer.lower() == correct_answer.lower()
            
            self.results.append({
                'question_number': i,
                'question': question['question'],
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct
            })
    
    def generate_result_dataframe(self):
        """Convert results to DataFrame"""
        return pd.DataFrame(self.results)
    
    def save_to_csv(self):
        """Save results to CSV file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"upsc_quiz_results_{timestamp}.csv"
        results_df = self.generate_result_dataframe()
        results_df.to_csv(filename, index=False)
        return filename

def main():
    # Initialize session state
    if 'quiz_manager' not in st.session_state:
        st.session_state.quiz_manager = QuizManager()
    if 'quiz_progress' not in st.session_state:
        st.session_state.quiz_progress = 0
    if 'quiz_generated' not in st.session_state:
        st.session_state.quiz_generated = False
    if 'quiz_submitted' not in st.session_state:
        st.session_state.quiz_submitted = False

    # Hero Section
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<h1 class="main-header">📚 UPSC Mastery Quiz</h1>', unsafe_allow_html=True)
        st.markdown("#### *Powered by Llama3 • Instant AI Questions • Real Exam Experience*")
    
    # Progress Bar
    progress_col1, progress_col2 = st.columns([3, 1])
    with progress_col1:
        st.progress(st.session_state.quiz_progress / 100)
    with progress_col2:
        total_questions = len(st.session_state.quiz_manager.questions) if st.session_state.quiz_manager.questions else 0
        st.metric("Questions", f"{total_questions}/8")

    # Sidebar - Quiz Controls
    with st.sidebar:
        st.markdown("## 🎯 Quiz Controls")
        st.markdown("---")
        
        subjects = {
            "🇮🇳 Indian Polity": "Article 370, Fundamental Rights, Panchayati Raj",
            "📜 Modern History": "Indian National Movement, Quit India, 1857 Revolt", 
            "🌍 Geography": "Monsoon, Himalayas, River systems",
            "💰 Economy": "GST, RBI, Fiscal Policy",
            "🌿 Environment": "Biodiversity, Climate Protocols",
            "🔬 Science": "ISRO, Biotech, Physics basics"
        }
        
        subject = st.selectbox("**Select Subject**", list(subjects.keys()), index=0)
        topic = subjects[subject]
        
        question_type = st.radio("**Question Type**", 
                               ["Multiple Choice ✅", "Fill in Blank ✍️"], 
                               horizontal=True)
        
        difficulty = st.selectbox("**Difficulty**", 
                                ["🟢 Easy", "🟡 Medium", "🔴 Hard"], 
                                index=1)
        
        num_questions = st.slider("**Questions**", 3, 10, 8, 1)
        
        if st.button("🚀 **GENERATE UPSC QUIZ**", 
                    type="primary", 
                    use_container_width=True,
                    help="AI generates real UPSC-level questions"):
            st.session_state.quiz_submitted = False
            st.session_state.quiz_progress = 33
            
            try:
                generator = QuestionGenerator()
                st.session_state.quiz_generated = st.session_state.quiz_manager.generate_questions(
                    generator, topic, question_type, difficulty, num_questions
                )
                st.session_state.quiz_progress = 100
            except Exception as e:
                st.session_state.quiz_progress = 0
                st.error(f"Generation failed: {str(e)}")
            
            st.rerun()
    
    # Main Content Area
    if st.session_state.quiz_generated and st.session_state.quiz_manager.questions:
        st.markdown("### 🎯 **Take Your UPSC Quiz**")
        st.info(f"📖 **Subject**: {subject} | 🎯 **{len(st.session_state.quiz_manager.questions)} Questions** | 📊 **{difficulty} Level**")
        
        st.session_state.quiz_manager.attempt_quiz()
        
        # Submit Button
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("✅ **SUBMIT & SCORE QUIZ**", type="primary", use_container_width=True):
                st.session_state.quiz_manager.evaluate_quiz()
                st.session_state.quiz_submitted = True
                st.rerun()
        with col2:
            if st.button("🔄 New Quiz", use_container_width=True):
                # Reset quiz state
                st.session_state.quiz_generated = False
                st.session_state.quiz_submitted = False
                st.session_state.quiz_progress = 0
                st.session_state.quiz_manager = QuizManager()
                st.rerun()
    
    # Results Section
    if st.session_state.quiz_submitted:
        st.markdown("### 🏆 **Your UPSC Results**")
        
        results_df = st.session_state.quiz_manager.generate_result_dataframe()
        correct = results_df['is_correct'].sum()
        score_pct = (correct / len(results_df)) * 100
        
        # Score Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Score", f"{correct}/{len(results_df)}", f"{score_pct:.0f}%")
        with col2:
            st.metric("🎯 Accuracy", f"{score_pct:.1f}%")
        with col3:
            level = "IAS Ready" if score_pct >= 80 else "Good Progress" if score_pct >= 60 else "Keep Practicing"
            st.metric("📈 Level", level)
        
        # Question-wise Results
        for _, result in results_df.iterrows():
            with st.container():
                if result['is_correct']:
                    st.markdown(f"""
                    <div class="question-card">
                        <h4>✅ Q{int(result['question_number'])} <span class="correct">CORRECT!</span></h4>
                        <p><strong>{result['question'][:100]}...</strong></p>
                        <p><span class="correct">✓ Your Answer:</span> {result['user_answer']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="question-card">
                        <h4>❌ Q{int(result['question_number'])} <span class="wrong">Try Again</span></h4>
                        <p><strong>{result['question'][:100]}...</strong></p>
                        <p><span class="wrong">✗ Your Answer:</span> {result['user_answer']}</p>
                        <p><span class="correct">✅ Correct:</span> <strong>{result['correct_answer']}</strong></p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Download Section
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 **Save Detailed Report**", use_container_width=True):
                saved_file = st.session_state.quiz_manager.save_to_csv()
                if saved_file and os.path.exists(saved_file):
                    with open(saved_file, 'rb') as f:
                        st.download_button(
                            label="📥 Download CSV Report",
                            data=f.read(),
                            file_name="upsc_quiz_results.csv",
                            mime="text/csv"
                        )
                    os.remove(saved_file)
        with col2:
            st.balloons()

if __name__ == "__main__":
    main()
