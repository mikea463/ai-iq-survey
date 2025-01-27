import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from datetime import datetime

###########################
# CONFIG & GLOBALS
###########################

# Instead of a hard-coded password, we read from st.secrets.
# In your secrets.toml (local) or Streamlit Cloud secrets, you have:
#   [general]
#   password = "NeuZeit"

# If the user hasn't set "general.password" in secrets, this will raise a KeyError.
# You can use a get() with default if you want a fallback password.
PASSWORD = st.secrets["general"]["password"]  

# Scale labels (Strongly Agree -> Strongly Disagree) mapped to 5..1
SCALE_LABELS = ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]
SCALE_MAPPING = {
    "Strongly Agree": 5,
    "Agree": 4,
    "Neutral": 3,
    "Disagree": 2,
    "Strongly Disagree": 1
}

# Example dimensions + questions + optional text prompt
survey_questions = {
    "Business Domain Understanding": {
        "questions": [
            "Our organization has in-depth domain knowledge where AI will be applied.",
            "We effectively identify & prioritize AI use cases that bring real business value.",
            "We have a clear understanding of AI’s potential ROI or tangible benefits."
        ],
        "text": "Optional: Briefly describe any recent AI project or domain-specific challenge."
    },
    "People": {
        "questions": [
            "Our Data Science team effectively translates business needs and collaborates with stakeholders.",
            "Our Data Science team has the necessary technical depth (ML, MLOps, relevant tools).",
            "Our business stakeholders are willing & able to sponsor and guide AI projects."
        ],
        "text": "Optional: Describe any communication or alignment challenges among teams."
    },
    "Process": {
        "questions": [
            "We have a structured, iterative process for conducting AI experiments (POCs) quickly.",
            "We have a mature process for deploying AI models from pilot to production.",
            "We have robust monitoring and a clear human-in-the-loop for AI-driven decisions."
        ],
        "text": "Optional: Highlight any bottlenecks or pain points in the AI lifecycle."
    },
    "Technology": {
        "questions": [
            "Our AI tech stack (frameworks, libraries, DevOps/MLOps) is modern and well-integrated.",
            "We have well-defined standards or governance for AI tools & data usage.",
            "Our architecture supports ‘plug-and-play’ integration for new AI models."
        ],
        "text": "Optional: Note any tech gaps or constraints (legacy systems, cloud limits, etc.)."
    },
    "Data": {
        "questions": [
            "We have a unified data platform (not many siloed sources).",
            "Our data sources (structured/unstructured) are well-documented and discoverable.",
            "We have strong data governance and data quality practices."
        ],
        "text": "Optional: If data quality or availability is an issue, explain."
    },
    "Patterns": {
        "questions": [
            "We understand and leverage common AI deployment patterns (batch, real-time, RAG, etc.).",
            "We have a clear approach for integrating AI models internally vs. using external services.",
            "We frequently reuse proven AI solution patterns across projects."
        ],
        "text": "Optional: Describe any challenges adopting new AI patterns or frameworks."
    }
}

CSV_FILE = "survey_responses.csv"
LOGO_FILE = "neuzeit_logo.png"

##########################
# DATA STORAGE FUNCTIONS
##########################

def load_data(csv_file=CSV_FILE):
    if os.path.exists(csv_file):
        return pd.read_csv(csv_file)
    else:
        columns = ["name", "email", "timestamp", "AI_IQ"]
        for dim in survey_questions.keys():
            columns.append(dim + "_score")
        for dim in survey_questions.keys():
            columns.append(dim + "_text_response")
        return pd.DataFrame(columns=columns)

def save_response(name, email, dimension_scores, dimension_texts, ai_iq, csv_file=CSV_FILE):
    df = load_data(csv_file)
    row_dict = {
        "name": name,
        "email": email,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "AI_IQ": ai_iq
    }
    for dim, score in dimension_scores.items():
        row_dict[dim + "_score"] = score
    for dim, txt in dimension_texts.items():
        row_dict[dim + "_text_response"] = txt

    new_df = pd.DataFrame([row_dict])
    df = pd.concat([df, new_df], ignore_index=True)
    df.to_csv(csv_file, index=False)

##########################
# CHART & SCORING LOGIC
##########################

def calculate_dimension_score(numeric_answers):
    return round(sum(numeric_answers) / len(numeric_answers), 2)

def create_swimlane_chart(dimension_scores):
    dimensions = list(dimension_scores.keys())
    values = list(dimension_scores.values())

    fig = go.Figure()
    lane_positions = list(range(1, len(dimensions) + 1))

    # Draw horizontal lines
    for y in lane_positions:
        fig.add_shape(
            type='line',
            x0=1, x1=5,
            y0=y, y1=y,
            line=dict(color='lightgray', width=2, dash='dot')
        )

    # Plot circles + text
    for i, dim in enumerate(dimensions):
        fig.add_trace(go.Scatter(
            x=[values[i]],
            y=[lane_positions[i]],
            mode='markers+text',
            text=[f"{dim}: {values[i]}"],
            textposition="top center",
            marker=dict(size=12, color='blue'),
            showlegend=False
        ))

    # Connect with a line
    fig.add_trace(go.Scatter(
        x=values,
        y=lane_positions,
        mode='lines',
        line=dict(color='blue', width=2),
        showlegend=False
    ))

    # NeuZeit logo
    if os.path.exists(LOGO_FILE):
        fig.add_layout_image(
            dict(
                source=LOGO_FILE,
                xref="paper", yref="paper",
                x=1.15, y=1.15,
                sizex=0.25, sizey=0.25,
                xanchor="right", yanchor="top"
            )
        )

    fig.update_layout(
        title="Dimension Scores (1–5)",
        xaxis=dict(range=[1, 5], title="Score"),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            tickvals=lane_positions,
            ticktext=dimensions,
            autorange='reversed'
        ),
        height=600
    )
    return fig

######################
# MAIN STREAMLIT APP
######################

def main():
    st.set_page_config(layout="wide")

    # NeuZeit logo at top
    col1, col2 = st.columns([1,4])
    with col1:
        if os.path.exists(LOGO_FILE):
            st.image(LOGO_FILE, width=180)
    with col2:
        st.title("AI Readiness (AI IQ) Survey")

    # Two tabs
    tab1, tab2 = st.tabs(["Take Survey", "View Results"])

    ##########
    # Tab 1
    ##########
    with tab1:
        st.subheader("User Information")
        name = st.text_input("Name")
        email = st.text_input("Email")

        st.write("Please respond from **Strongly Agree** to **Strongly Disagree**, then add optional feedback.")
        dimension_scores = {}
        dimension_texts = {}

        for dim, content in survey_questions.items():
            st.subheader(dim)
            numeric_answers = []
            for question in content["questions"]:
                selected_label = st.radio(
                    label=question,
                    options=SCALE_LABELS,
                    index=2  # default to "Neutral"
                )
                numeric_value = SCALE_MAPPING[selected_label]
                numeric_answers.append(numeric_value)

            # dimension score
            dim_score = calculate_dimension_score(numeric_answers)
            dimension_scores[dim] = dim_score

            # optional text
            text_label = content["text"]
            text_response = st.text_area(text_label, value="", height=80)
            dimension_texts[dim] = text_response

        if st.button("Calculate AI IQ & Submit"):
            all_scores = list(dimension_scores.values())
            ai_iq = round(sum(all_scores) / len(all_scores), 2)

            st.write("### Results")
            st.write(f"**Your AI IQ Score:** {ai_iq} (out of 5)")
            fig = create_swimlane_chart(dimension_scores)
            st.plotly_chart(fig, use_container_width=True)

            if name.strip() and email.strip():
                save_response(name, email, dimension_scores, dimension_texts, ai_iq)
                st.success("Your response has been saved!")
            else:
                st.warning("Provide both name and email if you want your results saved.")

    ##########
    # Tab 2
    ##########
    with tab2:
        entered_password = st.text_input("Enter password to view results", type="password")
        if entered_password == PASSWORD:
            st.success("Access granted. Here are all submissions.")

            df = load_data()
            if df.empty:
                st.write("No submissions yet.")
            else:
                st.dataframe(df)

                st.write("### Show/Hide Individual Submissions")
                for i, row in df.iterrows():
                    show_row = st.checkbox(
                        f"{i+1}) {row['name']} (AI IQ: {row['AI_IQ']})",
                        value=False,
                        key=f"submission_{i}"
                    )
                    if show_row:
                        row_scores = {}
                        row_texts = {}
                        for dim in survey_questions.keys():
                            row_scores[dim] = row[f"{dim}_score"]
                            text_col = f"{dim}_text_response"
                            row_texts[dim] = row[text_col] if text_col in row else ""

                        st.markdown(f"**Name:** {row['name']}")
                        st.markdown(f"**Email:** {row['email']}")
                        st.markdown(f"**Timestamp:** {row['timestamp']}")
                        st.markdown(f"**AI IQ:** {row['AI_IQ']}")

                        fig_row = create_swimlane_chart(row_scores)
                        st.plotly_chart(fig_row, use_container_width=True)

                        with st.expander("Dimension Text Responses", expanded=False):
                            for dim in survey_questions.keys():
                                txt = row_texts[dim]
                                if isinstance(txt, str):
                                    if txt.strip():
                                        st.markdown(f"**{dim}:** {txt}")
                                    else:
                                        st.markdown(f"**{dim}:** (No additional comments)")
                                else:
                                    st.markdown(f"**{dim}:** (Not a string)")

        else:
            st.error("Access denied. Please enter the correct password.")

if __name__ == "__main__":
    main()