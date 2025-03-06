import streamlit as st
import json
import cohere
import os
from typing import List, Dict, Any

# Load data from JSON file
def load_data() -> Dict[str, Any]:
    try:
        if not os.path.exists('data.json'):
            raise FileNotFoundError("data.json file not found")
        with open('data.json', 'r') as f:
            data = json.load(f)
            if not isinstance(data, dict) or 'subjects' not in data:
                raise ValueError("Invalid data format in data.json")
            return data
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return {"subjects": {}}

# Initialize session states
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'progress' not in st.session_state:
    st.session_state.progress = {}
    data = load_data()
    for subject, content in data['subjects'].items():
        for topic in content['topics']:
            st.session_state.progress[f"{subject} - {topic}"] = 0

# Set custom theme
st.set_page_config(
    page_title="Personalized Learning Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for blue/white theme
st.markdown("""
    <style>
        .stApp {
            background-color: #1e1e1e;
            color: #e0e0e0;
        }
        .stButton>button {
            background-color: #2c5282;
            color: white;
        }
        .stProgress .st-bo {
            background-color: #2c5282;
        }
        .sidebar .sidebar-content {
            background-color: #2d3748;
            color: #e0e0e0;
        }
        /* Additional dark theme styles */
        .stSelectbox [data-baseweb="select"] {
            background-color: #2d3748;
            color: #e0e0e0;
        }
        .stTextInput>div>div>input {
            background-color: #2d3748;
            color: #e0e0e0;
        }
        .stMarkdown {
            color: #e0e0e0;
        }
    </style>
""", unsafe_allow_html=True)

# Load data from JSON file
def load_data() -> Dict[str, Any]:
    with open('data.json', 'r') as f:
        return json.load(f)

# Initialize Cohere client
def get_cohere_response(query: str, api_key: str, subject: str) -> str:
    try:
        co = cohere.Client(api_key)
        response = co.generate(
            prompt=f"Answer this student query about {subject}: {query}",
            max_tokens=150,
            temperature=0.7,
            k=0,
            stop_sequences=[],
            return_likelihoods='NONE'
        )
        return response.generations[0].text.strip()
    except Exception as e:
        return "I'm not sure—check the Learning Hub!"

# Check quiz answers
def check_quiz_answers(selected_answers: List[int], correct_answers: List[int]) -> int:
    return sum(1 for s, c in zip(selected_answers, correct_answers) if s == c)

# Main app
def main():
    # Sidebar navigation
    st.sidebar.title("Navigation")
    
    # Subject selection
    data = load_data()
    subject = st.sidebar.selectbox("Select Subject", list(data['subjects'].keys()))
    
    # Page selection
    page = st.sidebar.selectbox(
        "Go to",
        ["Home", "Learning Hub", "Chat Support", "Video Lectures"]
    )
    
    # Get current subject content
    current_subject = data['subjects'][subject]
    
    if page == "Home":
        st.title("Personalized Learning Platform – Intro to Psychology")
        st.write("Explore notes, chat for help, or watch lectures!")
        
        # Create three columns for the main options
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("### 📚 Learning Hub")
            st.write("Access study materials and notes")
        with col2:
            st.write("### 💬 Chat Support")
            st.write("Get help from our AI tutor")
        with col3:
            st.write("### 📹 Video Lectures")
            st.write("Watch lectures and take quizzes")
    
    elif page == "Learning Hub":
        st.title("📚 Learning Hub")
        
        # Search functionality
        search_query = st.text_input("🔍 Search topics and content", "")
        
        # Display progress in sidebar
        st.sidebar.write("### Your Progress")
        for topic, progress in st.session_state.progress.items():
            st.sidebar.progress(progress)
            st.sidebar.write(f"{topic}: {progress}%")
        
        # Filter topics based on search
        filtered_topics = [topic for topic in current_subject["topics"] 
                         if search_query.lower() in topic.lower() or 
                         search_query.lower() in current_subject["notes"][topic]["text"].lower()]
        
        topic = st.selectbox("Select a topic", filtered_topics if filtered_topics else current_subject["topics"])
        
        if topic:
            st.write("### Notes")
            st.write(current_subject["notes"][topic]["text"])
            
            st.write("### Key Highlights")
            with st.expander("Show Highlights", expanded=True):
                for highlight in current_subject["notes"][topic]["highlights"]:
                    st.markdown(f"- {highlight}")
            
            # Download notes button
            notes_text = f"{topic}\n\n{current_subject['notes'][topic]['text']}\n\nHighlights:\n"
            for highlight in current_subject['notes'][topic]['highlights']:
                notes_text += f"- {highlight}\n"
            st.download_button(
                label="Download Notes",
                data=notes_text,
                file_name=f"{topic.lower().replace(' ', '_')}_notes.txt"
            )
    
    elif page == "Chat Support":
        st.title("💬 Chat Support")
        
        # API key input
        api_key = st.text_input("Enter your Cohere API key", type="password", placeholder="Enter your API key here")
        
        # Suggested questions
        st.write("### Suggested Questions")
        suggestions = [
                f"What is {subject}?",
                f"Explain a key concept in {subject}",
                f"How can I apply {subject} in real life?"
            ]
        cols = st.columns(len(suggestions))
        for i, suggestion in enumerate(suggestions):
            if cols[i].button(suggestion):
                st.session_state.user_input = suggestion
        
        # Chat interface
        user_input = st.text_input("Ask me anything about Psychology!", key="user_input")
        
        # Export chat button
        if st.session_state.chat_history:
            chat_export = "\n\n".join([f"You: {msg}\nAI: {resp}" for msg, resp in st.session_state.chat_history])
            st.download_button(
                label="Export Chat History",
                data=chat_export,
                file_name="chat_history.txt",
                mime="text/plain"
            )
        
        if st.button("Send"):
            try:
                if not api_key:
                    st.error("Please enter your Cohere API key to continue.")
                elif not user_input:
                    st.warning("Please enter your question.")
                else:
                    with st.spinner("Getting response..."):
                        response = get_cohere_response(user_input, api_key, subject)
                        if response == "I'm not sure—check the Learning Hub!":
                            st.warning("Could not get a response. Please check your API key and try again.")
                        else:
                            st.session_state.chat_history.append((user_input, response))
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
        
        # Display chat history (limited to last 2 interactions)
        st.write("### Recent Chat History")
        for user_msg, ai_msg in list(reversed(st.session_state.chat_history))[:2]:
            st.write("---")
            st.write("🧑 You:", user_msg)
            st.write("🤖 AI:", ai_msg)
    
    elif page == "Video Lectures":
        st.title("📹 Video Lectures")
        
        for topic in current_subject["topics"][:2]:  # Show first two topics
            st.write(f"### {topic}")
            if "Video Lectures" in current_subject and topic in current_subject["Video Lectures"].get("videos", {}):
                video = current_subject["Video Lectures"]["videos"][topic]
                st.write(f"Duration: {video['duration']}")
                st.write(f'<iframe width="100%" height="400" src="{video["url"]}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>', unsafe_allow_html=True)
            
            # Quiz section
            if "Video Lectures" in current_subject and topic in current_subject["Video Lectures"].get("quizzes", {}):
                st.write("### Quiz")
                quiz = current_subject["Video Lectures"]["quizzes"][topic]
                user_answers = []
                
                for i, q in enumerate(quiz["questions"]):
                    st.write(f"**{q['q']}**")
                    answer = st.radio(
                        f"Question {i+1}",
                        options=q["options"],
                        key=f"{topic}_{i}"
                    )
                    user_answers.append(q["options"].index(answer))
                
                if st.button(f"Submit Quiz for {topic}"):
                    correct_answers = [q["answer"] for q in quiz["questions"]]
                    score = check_quiz_answers(user_answers, correct_answers)
                    st.write(f"Score: {score}/{len(quiz['questions'])}")

if __name__ == "__main__":
    main()