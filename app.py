import os
import time

import keyboard
import psutil
import streamlit as st

from model import (
    DocumentProcessor,
    EmbeddingClient,
    ChromaCollectionCreator,
    QuizGenerator,
    QuizManager,
)
from model.database import quiz_storage_firebase
from quiz_statistics import display_statistics

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gemini-quiz.json"
firebase_coll = "quizCollection"

if __name__ == "__main__":

    embed_config = {
        "model_name": "textembedding-gecko@003",
        "project": "gemini-quiz",
        "location": "us-central1"
    }

    # Add Session State
    if 'question_bank' not in st.session_state or len(st.session_state['question_bank']) == 0:

        st.session_state['question_bank'] = []

        screen = st.empty()
        with screen.container():
            st.header("Quiz Builder")

            # Create a new st.form flow control for Data Ingestion
            with st.form("Load Data to Chroma"):
                st.write(
                    "Select PDFs for the domain you need, the topic for the quiz, and click Generate!")

                processor = DocumentProcessor()
                processor.ingest_documents()

                embed_client = EmbeddingClient(**embed_config)

                chroma_creator = ChromaCollectionCreator(
                    processor, embed_client)

                topic_input = st.text_input(
                    "Topic for Generative Quiz", placeholder="Enter the topic of the document")
                questions = st.slider("Number of Questions",
                                      min_value=1, max_value=10, value=1)

                submitted = st.form_submit_button("Generate question list")

                if submitted:
                    chroma_creator.create_chroma_collection()

                    if len(processor.pages) > 0:
                        st.write(f"Trying to generate {questions} questions for the topic: {topic_input}")

                    # Initialize a QuizGenerator class using the topic, number of questions, and the chroma collection
                    generator = QuizGenerator(
                        topic=topic_input, num_questions=questions, vectorstore=chroma_creator)
                    question_bank = generator.generate_quiz()

                    # Initialize the question bank list in st.session_state
                    st.session_state['question_bank'] = [
                        question for question in question_bank]
                    # Set a display_quiz flag in st.session_state to True
                    st.success(str(len(st.session_state['question_bank'])) + " questions successfully generated!",
                               icon="✅")
                    # Writing questions to Firebase DB
                    for count, question in enumerate(question_bank):
                        if quiz_storage_firebase.store_data_in_firebase(firebase_coll, question):
                            st.success('Question ' + str(count + 1) + ' successfully stored on Firebase!', icon="✅")
                        else:
                            st.error('Question ' + str(count + 1) + 'NOT successfully stored ON Firebase !', icon="🚨")

                    st.session_state['display_quiz'] = True
                    # Set the question_index to 0 in st.session_state
                    st.session_state['question_index'] = 0

    elif st.session_state["display_quiz"]:

        st.empty()
        with st.container():
            st.header("Generated Quiz Questions")
            quiz_manager = QuizManager(st.session_state['question_bank'])

            # Format the question and display it
            with st.form("MCQ"):
                # Set index_question using the Quiz Manager method get_question_at_index passing the st.session_state["question_index"]
                index_question = quiz_manager.get_question_at_index(
                    st.session_state['question_index'])
                # Counter for correct answers
                if 'correct_answers' not in st.session_state:
                    st.session_state['correct_answers'] = 0
                # Unpack choices for radio button
                choices = []
                for choice in index_question['choices']:
                    key = choice['key']
                    value = choice['value']
                    choices.append(f"{key}) {value}")

                # Display the Question
                st.write(
                    f"{st.session_state['question_index'] + 1}. {index_question['question']}")
                answer = st.radio(
                    "Choose an answer",
                    choices,
                    index=None
                )

                answer_choice = st.form_submit_button("Submit answer")

                st.form_submit_button(
                    "Next Question", on_click=lambda: quiz_manager.next_question_index(direction=1))

                if answer_choice and answer is not None:
                    correct_answer_key = index_question['answer']
                    if answer.startswith(correct_answer_key):
                        st.success("Correct!")
                        st.session_state['correct_answers'] += 1
                    else:
                        st.error("Incorrect!")
                    st.write(f"Explanation: {index_question['explanation']}")

                # End of test reached
                if st.session_state['question_index'] + 1 == len(st.session_state['question_bank']) and answer:
                    st.info("End of test reached ...", icon="ℹ️")
                    # Generating quiz_statistics
                    st.subheader("Quiz Answer Percentage Visualizer")
                    correct_percentage = st.session_state['correct_answers'] / len(
                        st.session_state['question_bank']) * 100
                    incorrect_percentage = 100 - correct_percentage
                    st.info(f"Correct Answers: {correct_percentage:.2f}%", icon="ℹ️")
                    st.info(f"Incorrect Answers: {incorrect_percentage:.2f}%", icon="ℹ️")
                    # Generate pie chart
                    display_statistics.generate_pie_chart(correct_percentage, incorrect_percentage)
                    # Reset for re-taking test
                    st.session_state['correct_answers'] = 0
                    # Deleting Firebase DB
                    # Setting parameters
                    batch_size = 500
                    if quiz_storage_firebase.delete_collection(firebase_coll, batch_size):
                        st.success('Firebase collection successfully deleted!', icon="✅")
                    else:
                        st.error('Firebase collection NOT successfully deleted!', icon="🚨")
                    # Shutdown
                    if st.form_submit_button("Close application"):
                        st.empty()
                        # Give a bit of delay for user experience
                        time.sleep(3)
                        # Close streamlit browser tab
                        keyboard.press_and_release('ctrl+w')
                        # Terminate streamlit python process
                        pid = os.getpid()
                        p = psutil.Process(pid)
                        p.terminate()
