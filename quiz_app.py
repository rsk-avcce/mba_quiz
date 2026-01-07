import streamlit as st
import pandas as pd
import os

# --- 1. Session State Initialization ---
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'quiz_submitted' not in st.session_state:
    st.session_state.quiz_submitted = False
if 'quiz_active' not in st.session_state:
    st.session_state.quiz_active = False
if 'selected_subject' not in st.session_state:
    st.session_state.selected_subject = None
if 'selected_week' not in st.session_state:
    st.session_state.selected_week = None

# --- 2. Helper Functions ---

@st.cache_data
def load_data(subject, week):
    # Map the Subject Name (from Dropdown) to the Folder/File Abbreviation
    subject_to_abbr = {
        "Principles of Management": "POM",
        "Managerial Economics": "ME",
        "Financial Accounting": "FA",
        "Business Communication": "BC",
        "Business statistics": "BS"
    }
    
    abbr = subject_to_abbr.get(subject)
    
    if abbr:
        # Construct the file path: Data/{Abbr}/{Abbr}_Quizzes.xlsx
        # Example: Data/POM/POM_Quizzes.xlsx
        file_path = os.path.join("Data", abbr, f"{abbr}_Quizzes.xlsx")
        
        # Check if the Excel file exists
        if os.path.exists(file_path):
            try:
                # Read the specific sheet corresponding to the selected week
                # sheet_name expects exact string match, e.g., "Week 1"
                df = pd.read_excel(file_path, sheet_name=week)
                
                # Drop QuestionID if it exists, as requested
                if 'QuestionID' in df.columns:
                    df = df.drop(columns=['QuestionID'])
                
                # Clean up whitespace from string columns
                df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
                
                return df
                
            except ValueError:
                # This error occurs if the specific Sheet (e.g., "Week 5") 
                # doesn't exist in the Excel file.
                st.error(f"Sheet '{week}' not found in file: {file_path}")
                return None
            except Exception as e:
                st.error(f"Error reading file: {e}")
                return None
        else:
            # File does not exist at the expected path
            st.error(f"File not found: {file_path}")
            return None
    else:
        return None

def next_question():
    st.session_state.current_question += 1

def prev_question():
    st.session_state.current_question -= 1

def submit_quiz():
    st.session_state.quiz_submitted = True

def restart_quiz():
    st.session_state.current_question = 0
    st.session_state.answers = {}
    st.session_state.quiz_submitted = False
    # We do NOT reset quiz_active here, so they can retry the same subject.
    # To go back to home, they can reload the page or we add a "Home" button.
    st.rerun()

def go_home():
    st.session_state.quiz_active = False
    st.session_state.current_question = 0
    st.session_state.answers = {}
    st.session_state.quiz_submitted = False
    st.rerun()

# --- 3. Main Application Flow ---

# A. SELECTION SCREEN (Display this if quiz is not active)
if not st.session_state.quiz_active:
    st.title("Student Quiz Portal")
    st.write("Please select your Subject and Week to begin.")

    # 1. Subject Dropdown
    subjects = [
        "--Select Subject--",
        "Principles of Management",
        "Managerial Economics",
        "Financial Accounting",
        "Business Communication",
        "Business Statistics"
    ]
    
    selected_subject = st.selectbox("Subject:", subjects)

    # 2. Week Dropdown
    # Validation: Logic to prompt user if subject is not selected
    week_options = ["--Select Week--"]
    if selected_subject != "--Select Subject--":
        week_options += [f"Week {i}" for i in range(1, 13)]
        selected_week = st.selectbox("Week:", week_options)
    else:
        # If subject not selected, show disabled or dummy box and a warning if they try to interact
        selected_week = st.selectbox("Week:", ["--Select Subject First--"], disabled=True)
        st.info("Please select a Subject to unlock the Week selection.")

    # 3. Start Button with Validation
    if st.button("Start Quiz"):
        if selected_subject == "--Select Subject--":
            st.error("❗ You must select a Subject.")
        elif selected_week == "--Select Week--" or selected_week == "--Select Subject First--":
            st.error("❗ You must select a Week.")
        else:
            # Check if file exists before starting
            df_check = load_data(selected_subject, selected_week)
            if df_check is not None and not df_check.empty:
                st.session_state.selected_subject = selected_subject
                st.session_state.selected_week = selected_week
                st.session_state.quiz_active = True
                st.rerun()
            else:
                st.error(f"❌ Could not find the quiz file for: {selected_subject} ({selected_week}). Please ensure the file exists.")

# B. QUIZ SCREEN (Display this if quiz IS active)
else:
    # Load the data based on saved state
    df = load_data(st.session_state.selected_subject, st.session_state.selected_week)
    
    # Sidebar for context
    with st.sidebar:
        st.write(f"**Subject:** {st.session_state.selected_subject}")
        st.write(f"**Week:** {st.session_state.selected_week}")
        if st.button("Back to Home"):
            go_home()

    if not st.session_state.quiz_submitted:
        # --- Display Question Page ---
        current_idx = st.session_state.current_question
        question_data = df.iloc[current_idx]
        
        st.title(f"Question {current_idx + 1}")
        st.progress((current_idx + 1) / len(df)) # Optional: Progress bar
        
        st.write(question_data['Question'])
        
        options = [
            question_data['Option_A'],
            question_data['Option_B'],
            question_data['Option_C'],
            question_data['Option_D']
        ]
        
        saved_answer = st.session_state.answers.get(current_idx, None)
        try:
            radio_index = options.index(saved_answer) if saved_answer in options else 0
        except ValueError:
            radio_index = 0

        selected_option = st.radio(
            "Select an answer:", 
            options, 
            index=radio_index,
            key=f"q_radio_{current_idx}" 
        )
        
        st.session_state.answers[current_idx] = selected_option
        
        st.write("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if current_idx > 0:
                st.button("Previous", on_click=prev_question)
        
        with col3:
            if current_idx < len(df) - 1:
                st.button("Next", on_click=next_question)
            else:
                st.button("Submit", on_click=submit_quiz)

    else:
        # --- Display Results Page ---
        st.title("Quiz Results")
        
        correct_answer_count = 0
        summary_data = []

        # Calculate Score and Build Summary Data
        for idx, row in df.iterrows():
            user_selection = st.session_state.answers.get(idx, None)
        
            correct_option_letter = row['Answer']
            correct_option_text = row[f"Option_{correct_option_letter}"]
            
            is_correct = (user_selection == correct_option_text)
            
            if is_correct:
                correct_answer_count += 1
            
            summary_data.append({
                "Question No.": idx + 1,
                "Question": row['Question'],
                "Your Answer": user_selection if user_selection else "Not Answered",
                "Correct Answer": correct_option_text
            })

        # Display Final Score
        st.success(f"You scored {correct_answer_count} out of {len(df)}")
        
        # --- Display Detailed Summary as a List ---
        st.subheader("Detailed Summary")
        
        for item in summary_data:
            # Display Question
            st.write(f"**{item['Question No.']}. {item['Question']}**")
            
            # Display User Answer with Green/Red Logic
            if item['Your Answer'] == item['Correct Answer']:
                st.markdown(f"**Your Answer:** :green[{item['Your Answer']}]")
            else:
                st.markdown(f"**Your Answer:** :red[{item['Your Answer']}]")
                
            # Display Correct Answer
            st.write(f"**Correct Answer:** {item['Correct Answer']}")
            
            # Add a visual separator line
            st.divider()
        
        col_restart, col_home = st.columns(2)
        with col_restart:
            st.button("Retry This Quiz", on_click=restart_quiz)
        with col_home:
            st.button("Select New Quiz", on_click=go_home)