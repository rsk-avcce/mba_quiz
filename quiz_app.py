import streamlit as st
import pandas as pd

# 1. Load and Clean Data
@st.cache_data
def load_data():
    # Read the CSV file
    file_name = "Data/BC_Quizzes.csv"
    try:
        df = pd.read_csv(file_name)
        
        # Clean up whitespace from all string columns to avoid matching errors
        df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
        return df
    except FileNotFoundError:
        st.error(f"File not found: {file_name}. Please make sure the file is in the same directory.")
        return pd.DataFrame()

df = load_data()

if not df.empty:
    # 2. Initialize Session State
    # current_question: Tracks the index of the question currently being displayed
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    
    # answers: Dictionary to store user's selected option for each question index
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    
    # quiz_submitted: Boolean flag to check if the quiz is finished
    if 'quiz_submitted' not in st.session_state:
        st.session_state.quiz_submitted = False

    # 3. Define Navigation Functions
    def next_question():
        st.session_state.current_question += 1

    def prev_question():
        st.session_state.current_question -= 1

    def submit_quiz():
        st.session_state.quiz_submitted = True

    # 4. Main App Logic
    if not st.session_state.quiz_submitted:
        # --- Display Question Page ---
        
        current_idx = st.session_state.current_question
        question_data = df.iloc[current_idx]
        
        # Display Question
        st.title("Business Communication - Quiz")
        st.subheader(f"Question {current_idx + 1} of {len(df)}")
        st.write(question_data['Question'])
        
        # Prepare Options
        options = [
            question_data['Option_A'],
            question_data['Option_B'],
            question_data['Option_C'],
            question_data['Option_D']
        ]
        
        # Check if there is a previously saved answer for this question
        saved_answer = st.session_state.answers.get(current_idx, None)
        
        # Determine the index for the radio button (default to 0 if not answered yet)
        try:
            radio_index = options.index(saved_answer) if saved_answer in options else 0
        except ValueError:
            radio_index = 0

        # Display Options
        # We use a specific key for each question so Streamlit knows they are different widgets
        selected_option = st.radio(
            "Select an answer:", 
            options, 
            index=radio_index,
            key=f"q_radio_{current_idx}" 
        )
        
        # Save the selection immediately to session state
        st.session_state.answers[current_idx] = selected_option
        
        # Navigation Buttons
        st.write("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            # Show Previous button if not on the first question
            if current_idx > 0:
                st.button("Previous", on_click=prev_question)
        
        with col3:
            # Show Next button if not on the last question, else Show Submit
            if current_idx < len(df) - 1:
                st.button("Next", on_click=next_question)
            else:
                st.button("Submit", on_click=submit_quiz)

    else:
        # --- Display Results Page ---
        st.title("Quiz Results")
        
        correct_answer_count = 0
        summary_data = []

        # Calculate Score and Build Summary
        for idx, row in df.iterrows():
            user_selection = st.session_state.answers.get(idx, None)
            
            # Map the correct answer letter (A, B, C, D) to the actual option text
            correct_option_letter = row['Answer'] # e.g., 'A'
            correct_option_text = row[f"Option_{correct_option_letter}"]
            
            # Check if correct
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
        
        # Display Detailed Summary
        st.write("### Quiz Summary & Score")
        summary_df = pd.DataFrame(summary_data)

        # Function to style the 'Your Answer' column based on correctness
        def highlight_user_answer(row):
            # Check if the user's answer matches the correct answer
            is_correct = row['Your Answer'] == row['Correct Answer']
            color = 'green' if is_correct else 'red'
            
            # return a list of css styles, one for each column in the row
            return [f'color: {color}' if col == 'Your Answer' else '' for col in row.index]

        # Apply the style row-wise (axis=1) and display
        st.dataframe(
            summary_df.style.apply(highlight_user_answer, axis=1),
            hide_index=True
        )

        # Restart Button
        if st.button("Restart Quiz"):
            # Reset all state variables
            st.session_state.current_question = 0
            st.session_state.answers = {}
            st.session_state.quiz_submitted = False
            st.rerun()