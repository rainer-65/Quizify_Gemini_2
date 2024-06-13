import streamlit as st
import matplotlib.pyplot as plt


def generate_pie_chart(correct_percentage, incorrect_percentage):
    fig, ax = plt.subplots()
    labels = 'Correct', 'Incorrect'
    sizes = [correct_percentage, incorrect_percentage]
    colors = ['#4CAF50', '#F44336']
    explode = (0.1, 0)  # explode the 1st slice (Correct)
    ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    # Display the plot in the Streamlit app
    st.pyplot(fig)
