"""Chat with a research paper using the OpenAI Conversations API."""

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader

load_dotenv()

MODEL = "gpt-4o-mini"
SYSTEM_INSTRUCTIONS = (
    "You are a helpful research assistant who explains academic papers "
    "in clear, simple terms. Answer questions accurately and concisely."
)


def extract_pdf_text(uploaded_file) -> str:
    reader = PdfReader(uploaded_file)
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def init_state() -> None:
    st.session_state.setdefault("conversation_id", None)
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("paper_loaded", False)


def main() -> None:
    st.set_page_config(page_title="Chat with a Paper", page_icon=":books:")
    st.title("Chat with a Research Paper")
    st.caption("Upload a PDF, then ask questions about it.")

    init_state()
    client = OpenAI()

    uploaded_file = st.file_uploader("Upload a research paper (PDF)", type=["pdf"])

    if uploaded_file is not None and not st.session_state.paper_loaded:
        with st.spinner("Reading the paper and preparing the conversation..."):
            paper_text = extract_pdf_text(uploaded_file)

            conversation = client.conversations.create()
            st.session_state.conversation_id = conversation.id

            client.responses.create(
                model=MODEL,
                instructions=SYSTEM_INSTRUCTIONS,
                input=(
                    "Here is the research paper you'll be answering questions about:"
                    f"\n\n{paper_text}\n\n"
                    "Please confirm you've read and understood the paper."
                ),
                conversation=conversation.id,
            )

            st.session_state.paper_loaded = True
            st.session_state.messages = []
        st.success("Paper loaded. Ask away.")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if st.session_state.paper_loaded:
        question = st.chat_input("Ask a question about the paper")
        if question:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = client.responses.create(
                        model=MODEL,
                        input=question,
                        conversation=st.session_state.conversation_id,
                    )
                    answer = response.output_text
                st.markdown(answer)

            st.session_state.messages.append({"role": "assistant", "content": answer})
    else:
        st.info("Upload a PDF to start chatting.")


if __name__ == "__main__":
    main()
