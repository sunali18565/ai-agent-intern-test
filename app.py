import streamlit as st
from app.agent import AsterRowAgent


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Aster & Row Support",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    /* Main background */
    .stApp {
        background-color: #f7f8fa;
    }

    /* Header */
    .main-title {
        font-size: 34px;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .subtitle {
        color: #6b7280;
        font-size: 16px;
        margin-bottom: 25px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e7eb;
    }

    /* Cards */
    .info-card {
        background-color: white;
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        margin-bottom: 12px;
    }

    .source-box {
        background-color: #f3f4f6;
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 13px;
        color: #6b7280;
        margin-top: 8px;
    }

    .handoff-box {
        background-color: #fff7ed;
        padding: 10px 14px;
        border-radius: 8px;
        border: 1px solid #fed7aa;
        color: #9a3412;
        font-size: 13px;
        margin-top: 8px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# LOAD AGENT
# =========================================================

@st.cache_resource
def load_agent():
    return AsterRowAgent()


agent = load_agent()


# =========================================================
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown("## 🛍️ Aster & Row")

    st.caption("Customer Support Assistant")

    st.divider()

    st.markdown("### 💡 Example Questions")

    examples = [
        "How long does a regular customer have to return an unused backpack?",
        "My TrailPlus membership was active when I ordered. What is my return window?",
        "Can you ship an Atlas Weekender to Germany?",
        "What is the warranty on bags?",
        "Where is ORD-1007 and when should it arrive?",
        "Is a gift card returnable?",
    ]

    for example in examples:

        if st.button(
            example,
            use_container_width=True,
            key=example,
        ):
            st.session_state.selected_question = example

    st.divider()

    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True,
    ):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    st.markdown("### 🔒 Privacy")

    st.caption(
        "This assistant does not disclose private customer "
        "information, internal notes, risk scores, or fraud-review data."
    )


# =========================================================
# MAIN HEADER
# =========================================================

st.markdown(
    '<div class="main-title">🛍️ Aster & Row Customer Support</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Ask about returns, shipping, warranties, orders, "
    "gift cards, and customer-support policies."
    "</div>",
    unsafe_allow_html=True,
)


# =========================================================
# WELCOME CARD
# =========================================================

if not st.session_state.messages:

    st.markdown(
        """
        <div class="info-card">
            <h3>👋 Welcome!</h3>
            <p>
                I can help you find information from the
                Aster & Row customer-support knowledge base.
            </p>
            <p>
                Use the example questions in the sidebar
                or type your own question below.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# CHAT HISTORY
# =========================================================

for message in st.session_state.messages:

    role = message["role"]

    with st.chat_message(role):

        st.markdown(message["content"])

        if role == "assistant":

            sources = message.get("sources", [])
            handoff = message.get("handoff", False)

            if sources:

                st.markdown(
                    '<div class="source-box">'
                    "📚 <b>Sources:</b> "
                    + ", ".join(sources)
                    + "</div>",
                    unsafe_allow_html=True,
                )

            if handoff:

                st.markdown(
                    '<div class="handoff-box">'
                    "⚠️ Human support confirmation is recommended."
                    "</div>",
                    unsafe_allow_html=True,
                )


# =========================================================
# SELECTED SIDEBAR QUESTION
# =========================================================

selected_question = st.session_state.pop(
    "selected_question",
    None,
)


# =========================================================
# CHAT INPUT
# =========================================================

question = st.chat_input(
    "Ask a customer-support question..."
)


# If sidebar example selected
if selected_question:
    question = selected_question


# =========================================================
# PROCESS QUESTION
# =========================================================

if question:

    question = question.strip()

    if question:

        # -------------------------------------------------
        # USER MESSAGE
        # -------------------------------------------------

        st.session_state.messages.append(
            {
                "role": "user",
                "content": question,
            }
        )

        with st.chat_message("user"):
            st.markdown(question)

        # -------------------------------------------------
        # AGENT RESPONSE
        # -------------------------------------------------

        with st.chat_message("assistant"):

            with st.spinner("Checking knowledge base..."):

                result = agent.ask(question)

            answer = result.get(
                "answer",
                "Sorry, I could not generate an answer.",
            )

            sources = result.get(
                "sources",
                [],
            )

            handoff = result.get(
                "handoff",
                False,
            )

            st.markdown(answer)

            # Sources
            if sources:

                st.markdown(
                    '<div class="source-box">'
                    "📚 <b>Sources:</b> "
                    + ", ".join(sources)
                    + "</div>",
                    unsafe_allow_html=True,
                )

            # Human handoff
            if handoff:

                st.markdown(
                    '<div class="handoff-box">'
                    "⚠️ Human support confirmation is recommended."
                    "</div>",
                    unsafe_allow_html=True,
                )

        # -------------------------------------------------
        # SAVE ASSISTANT MESSAGE
        # -------------------------------------------------

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": answer,
                "sources": sources,
                "handoff": handoff,
            }
        )