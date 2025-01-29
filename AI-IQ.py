import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from datetime import datetime
import plotly.io as pio  # For exporting charts as images (optional)

###########################
# CONFIG & GLOBALS
###########################

# Read password from Streamlit secrets
PASSWORD = st.secrets["general"]["password"]  

# Scale labels mapped to numeric values
SCALE_LABELS = ["Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"]
SCALE_MAPPING = {
    "Strongly Agree": 5,
    "Agree": 4,
    "Neutral": 3,
    "Disagree": 2,
    "Strongly Disagree": 1
}

# Revised weights for each response level with negative weights
WEIGHT_MAPPING = {
    "Strongly Agree": 1.5,
    "Agree": 1,
    "Neutral": 0,
    "Disagree": -1.5,
    "Strongly Disagree": -3
}

# Survey Questions Configuration
survey_questions = {
    "Strategic Alignment and AI-Driven Innovation": {
        "questions": [
            "AI is integrated into our organization's strategic planning and supports our long-term business objectives.",
            "AI initiatives have enabled our organization to innovate and enter new markets or create new revenue streams.",
            "We effectively identify and prioritize AI use cases that deliver significant business value."
        ],
        "text": "Optional: Briefly describe any recent AI project that has significantly impacted your business strategy."
    },
    "Cultural Integration and Continuous Learning": {
        "questions": [
            "Our employees possess the necessary AI knowledge and collaborate effectively with AI systems.",
            "Our organization promotes continuous learning and upskilling related to AI and emerging technologies.",
            "Employees are empowered to leverage AI in their roles, and AI is viewed as a collaborative tool rather than a replacement."
        ],
        "text": "Optional: Describe any initiatives your organization has implemented to foster an AI-driven learning culture."
    },
    "Advanced AI Capabilities and Infrastructure": {
        "questions": [
            "Our AI technology stack (frameworks, libraries, DevOps/MLOps) is modern, well-integrated, and supports advanced AI initiatives.",
            "Our AI infrastructure is scalable and adaptable to incorporate emerging AI advancements and handle increasing demands.",
            "AI-driven automation is effectively implemented across key business functions to enhance operational efficiency."
        ],
        "text": "Optional: Note any significant technology gaps or constraints that impact your AI capabilities."
    },
    "Data Management and Utilization": {
        "questions": [
            "We maintain a unified data platform with minimal siloed data sources, ensuring data is accessible and integrated.",
            "We have strong data governance and data quality practices that support reliable AI initiatives.",
            "Our organization effectively leverages data analytics and insights to inform AI-driven decision-making processes."
        ],
        "text": "Optional: If data quality or availability is an issue, please explain."
    },
    "Ethics, Governance, and Responsible AI": {
        "questions": [
            "Ethical AI practices are integrated into the development, deployment, and management of our AI systems.",
            "We have robust governance frameworks to monitor AI biases, ensure transparency, and maintain data privacy.",
            "Our organization ensures accountability and compliance in AI-driven decision-making processes."
        ],
        "text": "Optional: Explain how your organization handles ethical considerations in AI projects."
    },
    "AI Deployment Patterns and Innovation": {
        "questions": [
            "We understand and effectively leverage common AI deployment patterns (e.g., batch processing, real-time analytics).",
            "We have a clear approach for integrating AI models internally versus using external AI services.",
            "We frequently reuse proven AI solution patterns across different projects to drive innovation."
        ],
        "text": "Optional: Describe any challenges your organization faces in adopting new AI deployment patterns or frameworks."
    }
}

CSV_FILE = "survey_responses.csv"
LOGO_FILE = "neuzeit_logo.png"

##########################
# DATA STORAGE FUNCTIONS
##########################

def load_data(csv_file=CSV_FILE):
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
        # Ensure RespondentID exists
        if 'RespondentID' not in df.columns:
            df.reset_index(inplace=True)
            df.rename(columns={'index': 'RespondentID'}, inplace=True)
        return df
    else:
        columns = ["RespondentID", "name", "email", "timestamp", "AI_IQ"]
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

    # Assign a unique RespondentID
    if 'RespondentID' in df.columns and not df.empty:
        new_id = df['RespondentID'].max() + 1
    else:
        new_id = 1
    row_dict["RespondentID"] = new_id

    new_df = pd.DataFrame([row_dict])
    df = pd.concat([df, new_df], ignore_index=True)
    df.to_csv(csv_file, index=False)

##########################
# CHART & SCORING LOGIC
##########################

def calculate_weighted_score(numeric_answers, selected_weights):
    """
    Calculate the weighted score based on weights only.
    The score is normalized to a 0-5 scale using the ratio of positive to total contributions.
    """
    positive_sum = 0
    negative_sum = 0
    for a, w in zip(numeric_answers, selected_weights):
        if w > 0:
            positive_sum += a * w
        elif w < 0:
            negative_sum += a * abs(w)
    
#    st.write(f"Positive Sum: {positive_sum}")
#    st.write(f"Negative Sum: {negative_sum}")
    
    if positive_sum + negative_sum == 0:
        return 2.5  # Neutral score when there's no impact
    
    dimension_score = (positive_sum / (positive_sum + negative_sum)) * 5
    
#    st.write(f"Uncapped Dimension Score: {dimension_score}")
    
    # Cap the score between 0 and 5
    dimension_score = max(0, min(dimension_score, 5))
    
#    st.write(f"Capped Dimension Score: {dimension_score}")
    
    return round(dimension_score, 2)

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

def determine_ai_iq_level(ai_iq_score):
    """
    Determine the AI IQ maturity level based on the weighted AI IQ score.
    The thresholds can be adjusted as needed.
    """
    if ai_iq_score >= 4.5:
        return "Level 5: Optimizing"
    elif ai_iq_score >= 3.5:
        return "Level 4: Innovating"
    elif ai_iq_score >= 2.5:
        return "Level 3: Managing"
    elif ai_iq_score >= 1.5:
        return "Level 2: Emerging"
    else:
        return "Level 1: Initial"

def delete_response(respondent_id, csv_file=CSV_FILE):
    """ Delete a specific respondent's record from the CSV file. """
    df = load_data(csv_file)

    # Ensure RespondentID column exists
    if "RespondentID" in df.columns:
        df = df[df["RespondentID"] != respondent_id]  # Filter out the row with the given ID
        df.to_csv(csv_file, index=False)  # Save the updated data

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
    # Tab 1 - Take Survey
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
            selected_weights = []
            for question in content["questions"]:
                selected_label = st.radio(
                    label=question,
                    options=SCALE_LABELS,
                    index=2,  # default to "Neutral"
                    key=f"{dim}_{question}"  # Unique key to prevent Streamlit warnings
                )
                numeric_value = SCALE_MAPPING[selected_label]
                weight = WEIGHT_MAPPING[selected_label]
                numeric_answers.append(numeric_value)
                selected_weights.append(weight)

            # dimension score with weights
            dim_score = calculate_weighted_score(numeric_answers, selected_weights)
            dimension_scores[dim] = dim_score

            # optional text
            text_label = content["text"]
            text_response = st.text_area(text_label, value="", height=80, key=f"{dim}_text")
            dimension_texts[dim] = text_response

        if st.button("Calculate AI IQ & Submit"):
            all_scores = list(dimension_scores.values())
            ai_iq = round(sum(all_scores) / len(all_scores), 2)
            ai_iq_level = determine_ai_iq_level(ai_iq)

            st.write("### Results")
            st.write(f"**Your AI IQ Score:** {ai_iq} (out of 5)")
            st.write(f"**Maturity Level:** {ai_iq_level}")
            fig = create_swimlane_chart(dimension_scores)
            st.plotly_chart(fig, use_container_width=True)

            if name.strip() and email.strip():
                save_response(name, email, dimension_scores, dimension_texts, ai_iq)
                st.success("Your response has been saved!")
            else:
                st.warning("Provide both name and email if you want your results saved.")

    ##########
    # Tab 2 - View Results
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

                # Add a horizontal line separator for clarity
                st.markdown("---")

                # Section for Individual Radar Chart Series
                st.subheader("Individual AI IQ Profiles")

                # Create a multi-select widget to choose respondents to display
                respondent_options = df.apply(
                    lambda row: f"Respondent {row['RespondentID']}: {row['name']} (AI IQ: {row['AI_IQ']})",
                    axis=1
                ).tolist()
                selected_respondents = st.multiselect(
                    "Select Respondents to Display on Radar Chart",
                    options=respondent_options,
                    default=respondent_options[:5]  # Default to first 5 respondents
                )

                # Limit the number of respondents to prevent clutter
                MAX_RESPONDENTS = 10
                if len(selected_respondents) > MAX_RESPONDENTS:
                    st.warning(f"Please select up to {MAX_RESPONDENTS} respondents to display.")
                    selected_respondents = selected_respondents[:MAX_RESPONDENTS]

                if selected_respondents:
                    # Extract RespondentIDs based on selection
                    selected_ids = [int(option.split(":")[0].split()[-1]) for option in selected_respondents]
                    selected_df = df[df['RespondentID'].isin(selected_ids)]

                    # Prepare data for radar chart
                    radar_fig = go.Figure()

                    for _, row in selected_df.iterrows():
                        scores = [row[f"{dim}_score"] for dim in survey_questions.keys()]
                        radar_fig.add_trace(go.Scatterpolar(
                            r=scores,
                            theta=list(survey_questions.keys()),
                            fill='toself',
                            name=f"{row['name']} (AI IQ: {row['AI_IQ']})"
                        ))

                    radar_fig.update_layout(
                        polar=dict(
                            radialaxis=dict(
                                visible=True,
                                range=[1,5],
                                tickvals=[1,2,3,4,5]
                            )
                        ),
                        showlegend=True,
                        title="Individual AI IQ Profiles"
                    )

                    st.plotly_chart(radar_fig, use_container_width=True)

                    # Optional: Add a download button for the radar chart
                    radar_fig_bytes = pio.to_image(radar_fig, format="png")
                    st.download_button(
                        label="Download Radar Chart as PNG",
                        data=radar_fig_bytes,
                        file_name="individual_ai_iq_radar_chart.png",
                        mime="image/png"
                    )
                else:
                    st.write("No respondents selected for the radar chart.")

                # Display Aggregate AI IQ Score
                st.markdown("---")
                st.subheader("Aggregate AI IQ Score")
                average_ai_iq = df["AI_IQ"].mean()
                ai_iq_level = determine_ai_iq_level(average_ai_iq)
                st.metric("Average AI IQ", f"{average_ai_iq:.2f} / 5")
                st.write(f"**Overall Maturity Level:** {ai_iq_level}")

                # Section to show individual submissions
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
                        st.markdown(f"**Maturity Level:** {determine_ai_iq_level(row['AI_IQ'])}")

                        # Individual Swimlane Chart
                        fig_row = create_swimlane_chart(row_scores)
                        st.plotly_chart(fig_row, use_container_width=True)

                        # Expandable section for text responses
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
                                     # DELETE BUTTON
                        if st.button(f"🗑️ Delete Evaluation {respondent_id}", key=f"delete_{respondent_id}"):
                            delete_response(respondent_id)
                            st.success(f"Deleted evaluation for {name}. Please refresh to see changes.")
                            st.experimental_rerun()  # Refresh the app to reflect changes

        else:
            st.error("Access denied. Please enter the correct password.")

if __name__ == "__main__":
    main()