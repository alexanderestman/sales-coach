"""
Mini-Prototype: Sales Training Chat Simulation
================================================
A single-file Streamlit app that lets a sales rep
1. Selects a scenario (customer persona & playbook)
2. Chats with an LLM-powered "customer"
3. Clicks **Generate Feedback** to receive an evaluation of the call

Prerequisites:
    pip install streamlit openai python-dotenv

Environment:
    Put your OpenAI key in a .env file:  OPENAI_API_KEY=sk-...

Run:
    streamlit run sales_training_prototype.py
"""

import os
import json
from typing import List, Dict

import streamlit as st
from dotenv import load_dotenv
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Sales Trainer Prototype", layout="wide")

# -----------------------------
# --- SCENARIO & PLAYBOOKS  ---
# -----------------------------
SCENARIOS: Dict[str, Dict] = {
    "SaaS Discovery Call": {
        "system": "You are the prospect: a time-pressed CTO of a scale-up. You are evaluating CRM systems but sceptical of yet another SaaS vendor.",
        "goals": "1) Get clear on pricing; 2) Assess integration effort; 3) Push back on implementation timeline.",
        "temperature": 0.7,
    },
    "Enterprise Renewal": {
        "system": "You are the procurement manager at a Fortune 500. Your SaaS contract is up for renewal and you want at least 15% discount.",
        "goals": "1) Negotiate discount; 2) Ask for new features; 3) Threaten to churn if price not matched.",
        "temperature": 0.6,
    },
}

# -----------------------------
# --- SESSION STATE HELPERS ---
# -----------------------------
if "messages" not in st.session_state:
    st.session_state["messages"]: List[Dict] = []
if "scenario" not in st.session_state:
    st.session_state["scenario"] = None

# -----------------------------
# --- UI – SIDEBAR -----------
# -----------------------------
st.sidebar.title("⚙️ Settings")
scenario_name = st.sidebar.selectbox("Choose Scenario", SCENARIOS.keys())
if st.session_state["scenario"] != scenario_name:
    # Reset chat if scenario changes
    st.session_state["messages"] = []
    st.session_state["scenario"] = scenario_name

persona = SCENARIOS[scenario_name]

st.sidebar.markdown("**Scenario description**")
st.sidebar.write(persona["system"])

# -----------------------------
# --- MAIN CHAT --------------
# -----------------------------
st.title("🤖💬 Sales Simulation Prototype")
chat_placeholder = st.container()
user_input = st.chat_input("Type your message and press Enter…")

if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    # Build prompt with persona system + chat history
    prompt = [
        {"role": "system", "content": persona["system"]},
    ] + st.session_state["messages"]

    with st.spinner("Bot is typing…"):
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # small cost for prototype
            messages=prompt,
            temperature=persona["temperature"],
            stream=True,
        )

        assistant_msg = ""
        for chunk in response:
            delta = chunk.choices[0].delta
            if "content" in delta:
                assistant_msg += delta.content
                # Progressive reveal in UI
                with chat_placeholder.chat_message("assistant"):
                    st.write(assistant_msg)
        st.session_state["messages"].append({"role": "assistant", "content": assistant_msg})

# Render chat history
with chat_placeholder:
    for m in st.session_state["messages"]:
        with st.chat_message(m["role"]):
            st.write(m["content"])

# -----------------------------
# --- FEEDBACK BUTTON --------
# -----------------------------
if st.session_state["messages"]:
    if st.button("🔍 Generate Feedback", key="get_feedback"):
        transcript = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state["messages"]])
        eval_prompt = [
            {"role": "system", "content": "You are a strict sales coach. Analyse the transcript for discovery, listening, objection handling and next steps. Score each 0-10 and give concrete suggestions."},
            {"role": "user", "content": transcript},
        ]
        with st.spinner("Analysing conversation…"):
            feedback = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=eval_prompt,
                temperature=0.3,
            )
        st.success("Feedback ready!")
        st.subheader("📊 Coaching Feedback")
        st.markdown(feedback.choices[0].message.content)

        st.download_button(
            "📥 Download Transcript (.txt)",
            data=transcript,
            file_name="sales_call_transcript.txt",
        )