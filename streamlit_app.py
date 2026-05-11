from __future__ import annotations

import streamlit as st

from app.agent import build_response
from app.catalog import load_catalog
from app.models import ChatMessage


SCENARIOS = {
    "Vague query": "I need an assessment for a role I am hiring for.",
    "Technical + stakeholder fit": "Hiring a Java developer who works with stakeholders.",
    "Refinement": "Actually, add personality tests too.",
    "Comparison": "What is the difference between OPQ and G+?",
}


st.set_page_config(
    page_title="SHL Assessment Recommender",
    page_icon=":clipboard:",
    layout="wide",
)


def init_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_response" not in st.session_state:
        st.session_state.last_response = None


def reset_conversation() -> None:
    st.session_state.messages = []
    st.session_state.last_response = None


def render_chat_history() -> None:
    if not st.session_state.messages:
        with st.chat_message("assistant"):
            st.write(
                "Describe the role you are hiring for, paste a short job description, "
                "or ask me to compare two SHL assessments."
            )
        return

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])


def render_recommendations() -> None:
    response = st.session_state.last_response
    st.subheader("Latest shortlist")
    if not response or not response.recommendations:
        st.info("Recommendations will appear here after the agent has enough context.")
        return

    for item in response.recommendations:
        duration_text = ""
        for catalog_item in load_catalog():
            if catalog_item["name"] == item.name and catalog_item.get("duration_minutes"):
                duration_text = f"Approx. {catalog_item['duration_minutes']} min"
                break

        with st.container(border=True):
            st.markdown(f"**{item.name}**")
            st.caption(f"Type `{item.test_type}`")
            if duration_text:
                st.write(duration_text)
            st.link_button("Open SHL catalog page", item.url, use_container_width=True)

    if response.end_of_conversation:
        st.success("The agent marked the current recommendation task as complete.")


def run_turn(user_text: str) -> None:
    st.session_state.messages.append({"role": "user", "content": user_text})
    response = build_response([ChatMessage(**message) for message in st.session_state.messages])
    st.session_state.messages.append({"role": "assistant", "content": response.reply})
    st.session_state.last_response = response


init_state()

st.title("SHL Conversational Assessment Recommender")
st.caption(
    "Streamlit demo wrapper around the assignment logic. "
    "This is useful for Streamlit deployment demos, while the FastAPI app remains in `app/main.py`."
)

left, right = st.columns([2, 1], gap="large")

with right:
    st.subheader("Quick scenarios")
    for label, prompt in SCENARIOS.items():
        if st.button(label, use_container_width=True):
            run_turn(prompt)
            st.rerun()

    if st.button("Reset conversation", use_container_width=True):
        reset_conversation()
        st.rerun()

    st.subheader("Coverage")
    st.write("- Clarifies vague prompts")
    st.write("- Returns grounded SHL recommendations")
    st.write("- Handles refinements")
    st.write("- Compares SHL assessments")
    st.write("- Refuses off-topic or prompt-injection requests")
    render_recommendations()

with left:
    render_chat_history()
    prompt = st.chat_input("Example: Hiring a mid-level Java developer who works with stakeholders.")
    if prompt:
        run_turn(prompt)
        st.rerun()
