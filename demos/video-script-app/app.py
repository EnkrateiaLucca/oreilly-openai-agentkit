"""Generate a 60-second educational video script (and optional DALL-E images) from a research paper."""

import base64
from typing import List

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from pypdf import PdfReader

load_dotenv()

MODEL = "gpt-4o-mini"
IMAGE_MODEL = "gpt-image-1"
SCRIPT_INSTRUCTIONS = (
    "You are an expert at creating educational video scripts about research "
    "papers. Make them simple, engaging, and visual-friendly."
)


class ScriptScene(BaseModel):
    scene_number: int
    narration: str
    image_prompt: str


class VideoScript(BaseModel):
    title: str
    hook: str
    scenes: List[ScriptScene]
    conclusion: str


def extract_pdf_text(uploaded_file) -> str:
    reader = PdfReader(uploaded_file)
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def init_state() -> None:
    st.session_state.setdefault("script", None)
    st.session_state.setdefault("paper_text", None)
    st.session_state.setdefault("images", {})


def render_script(script: VideoScript) -> None:
    st.header(script.title)
    st.subheader("Hook")
    st.markdown(script.hook)

    st.subheader("Scenes")
    for scene in script.scenes:
        with st.container(border=True):
            st.markdown(f"**Scene {scene.scene_number}**")
            st.markdown(f"*Narration:* {scene.narration}")
            st.markdown(f"*Image prompt:* {scene.image_prompt}")

    st.subheader("Conclusion")
    st.markdown(script.conclusion)


def main() -> None:
    st.set_page_config(page_title="Video Script Generator", page_icon=":clapper:")
    st.title("Research Paper to Video Script")
    st.caption("Upload a paper, generate a script, and optionally illustrate each scene.")

    init_state()
    client = OpenAI()

    uploaded_file = st.file_uploader("Upload a research paper (PDF)", type=["pdf"])
    if uploaded_file is not None:
        st.session_state.paper_text = extract_pdf_text(uploaded_file)

    generate_images = st.checkbox("Generate images with DALL-E (costs more)")

    if st.button("Generate Script", disabled=st.session_state.paper_text is None):
        with st.spinner("Drafting your video script..."):
            response = client.responses.parse(
                model=MODEL,
                instructions=SCRIPT_INSTRUCTIONS,
                input=(
                    "Create a 60-second educational video script about this paper:"
                    f"\n\n{st.session_state.paper_text}"
                ),
                text_format=VideoScript,
            )
            st.session_state.script = response.output_parsed
            st.session_state.images = {}

    if st.session_state.script is not None:
        render_script(st.session_state.script)

        if generate_images:
            if st.button("Generate Images"):
                with st.spinner("Generating scene images..."):
                    for scene in st.session_state.script.scenes:
                        image_response = client.images.generate(
                            model=IMAGE_MODEL,
                            prompt=scene.image_prompt,
                            n=1,
                            size="1024x1024",
                        )
                        image_bytes = base64.b64decode(image_response.data[0].b64_json)
                        st.session_state.images[scene.scene_number] = image_bytes

            if st.session_state.images:
                st.subheader("Scene Images")
                for scene in st.session_state.script.scenes:
                    image_bytes = st.session_state.images.get(scene.scene_number)
                    if image_bytes:
                        st.image(
                            image_bytes,
                            caption=f"Scene {scene.scene_number}",
                            width="stretch",
                        )
    else:
        st.info("Upload a PDF and click 'Generate Script' to begin.")


if __name__ == "__main__":
    main()
