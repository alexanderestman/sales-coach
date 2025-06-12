"""
Mini-Prototype: Sales Training Chat Simulation
================================================
Updated 12 June 2025
• Bot spielt konsequent die Rolle des Kunden/Leads
• Streaming wird in **einer** einzigen Chat-Nachricht aufgebaut (keine Wort-Spam-Nachrichten)

Start:
    streamlit run sales_training_prototype.py
Requirements:
    streamlit>=1.35
    openai==0.28.1  # alte SDK für schnelles Demo-Pinning
    python-dotenv>=1.0
"""

import os
import time
from typing import List, Dict

import streamlit as st
from dotenv import load_dotenv
import openai

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="Sales Trainer Prototype", layout="wide")

# -----------------------------
# SCENARIOS – Customer Personas
# -----------------------------
SCENARIOS: Dict[str, Dict] = {
    "SaaS Discovery Call": {
        "system": (
            "You are playing the role of the PROSPECT in a SaaS discovery call. "
            "Persona: CTO of a fast-growing scale-up, pressed for time and sceptical of new vendors. "
            "Goals: 1) Clarify pricing, 2) gauge integration effort, 3) push back on implementation timeline. "
            "Never reveal that you are an AI or coach; speak naturally as a potential customer."
        ),
        "temperature": 0.7,
    },
    "Enterprise Renewal": {
        "system": (
            "You are the procurement manager at a Fortune 500 company negotiating a software renewal. "
            "You want at least a 15 % discount and promises of new features. "
            "Respond strictly as the customer lead would in a tough negotiation; never break character."
        ),
        "temperature": 0.6,
    },
}

# -----------------------------
# Streamlit Session State
# -----------------------------
if "messages" not in st.session_state:
    st.session_state["messages"]: List[Dict] = []
if "scenario" not in st.session_state:
    st.session_state["scenario"] = None

# -----------------------------
# Sidebar – Choose Scenario
# -----------------------------
st.sidebar.title("⚙️ Settings")
scenario_name = st.sidebar.selectbox("Choose Scenario", SCENARIOS.keys())
if st.session_state["scenario"] != scenario_name:
    st.session_state["messages"] = []  # reset chat when scenario changes
    st.session_state["scenario"] = scenario_name

persona = SCENARIOS[scenario_name]

st.sidebar.markdown("**Scenario description**")
st.sidebar.write(persona["system"])

# -----------------------------
# Main Chat Interface
# -----------------------------
st.title("🤖💬 Sales Simulation Prototype")
chat_placeholder = st.container()
user_input = st.chat_input("Your turn – convince the customer …")

# -- Handle user input & get AI reply
if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})

    prompt = [{"role": "system", "content": persona["system"]}] + st.session_state["messages"]

    with st.spinner("Customer is thinking …"):
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # cost-efficient for demo
            messages=prompt,
            temperature=persona["temperature"],
            stream=True,
        )

        assistant_msg = ""
        # Create exactly ONE assistant message container and update it gradually
        assistant_container = chat_placeholder.chat_message("assistant")
        assistant_placeholder = assistant_container.empty()

        for chunk in response:
            delta = chunk.choices[0].delta
            if "content" in delta:
                assistant_msg += delta.content
                assistant_placeholder.markdown(assistant_msg)
                time.sleep(0.05)  # tiny delay for human-like typing feel

        st.session_state["messages"].append({"role": "assistant", "content": assistant_msg})

# -- Render entire chat history (after possible new exchange)
with chat_placeholder:
    for m in st.session_state["messages"]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

# -----------------------------
# Feedback / Coaching Section
# -----------------------------
if st.session_state["messages"]:
    if st.button("🔍 Generate Feedback"):
        transcript = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state["messages"]])
        eval_prompt = [
            {
                "role": "system",
                "content": (
                    "You are a strict sales coach. Analyse the transcript for discovery, listening, "
                    "objection handling and next steps. Score each criterion 0-10 and give two concrete "
                    "improvement suggestions for each. Return markdown."
                ),
            },
            {"role": "user", "content": transcript},
        ]
        with st.spinner("Analysing conversation …"):
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