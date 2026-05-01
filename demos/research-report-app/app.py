"""Generate a structured research report from a PDF and download it as Markdown."""

import re
from typing import List

import streamlit as st
from openai import OpenAI
from pydantic import BaseModel
from pypdf import PdfReader

MODEL = "gpt-4o-mini"
REPORT_INSTRUCTIONS = (
    "You are an expert research analyst who creates detailed, structured "
    "reports about academic papers. Be thorough, accurate, and clear."
)


class KeyFinding(BaseModel):
    finding: str
    significance: str


class ResearchReport(BaseModel):
    title: str
    authors: str
    year: str
    executive_summary: str
    research_problem: str
    background: str
    methodology_summary: str
    key_techniques: List[str]
    key_findings: List[KeyFinding]
    strengths: List[str]
    limitations: List[str]
    practical_applications: List[str]
    future_directions: str


def extract_pdf_text(uploaded_file) -> str:
    reader = PdfReader(uploaded_file)
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def init_state() -> None:
    st.session_state.setdefault("report", None)
    st.session_state.setdefault("paper_text", None)


def format_report_as_markdown(report: ResearchReport) -> str:
    lines: List[str] = []
    lines.append(f"# {report.title}")
    lines.append("")
    lines.append(f"**Authors:** {report.authors}")
    lines.append(f"**Year:** {report.year}")
    lines.append("")
    lines.append("## Executive Summary")
    lines.append(report.executive_summary)
    lines.append("")
    lines.append("## Research Problem")
    lines.append(report.research_problem)
    lines.append("")
    lines.append("## Background")
    lines.append(report.background)
    lines.append("")
    lines.append("## Methodology Summary")
    lines.append(report.methodology_summary)
    lines.append("")
    lines.append("## Key Techniques")
    for item in report.key_techniques:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Key Findings")
    for kf in report.key_findings:
        lines.append(f"- **{kf.finding}** — {kf.significance}")
    lines.append("")
    lines.append("## Strengths")
    for item in report.strengths:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Limitations")
    for item in report.limitations:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Practical Applications")
    for item in report.practical_applications:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Future Directions")
    lines.append(report.future_directions)
    lines.append("")
    return "\n".join(lines)


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "research-report"


def render_report(report: ResearchReport) -> None:
    st.title(report.title)
    st.markdown(f"**Authors:** {report.authors}  \n**Year:** {report.year}")

    st.header("Executive Summary")
    st.markdown(report.executive_summary)

    st.header("Research Problem")
    st.markdown(report.research_problem)

    st.header("Background")
    st.markdown(report.background)

    st.header("Methodology")
    st.subheader("Summary")
    st.markdown(report.methodology_summary)
    st.subheader("Key Techniques")
    for item in report.key_techniques:
        st.markdown(f"- {item}")

    st.header("Key Findings")
    for kf in report.key_findings:
        st.markdown(f"- **{kf.finding}** — {kf.significance}")

    st.header("Strengths")
    for item in report.strengths:
        st.markdown(f"- {item}")

    st.header("Limitations")
    for item in report.limitations:
        st.markdown(f"- {item}")

    st.header("Practical Applications")
    for item in report.practical_applications:
        st.markdown(f"- {item}")

    st.header("Future Directions")
    st.markdown(report.future_directions)


def main() -> None:
    st.set_page_config(page_title="Research Report Generator", page_icon=":page_facing_up:")
    st.title("Research Paper Report Generator")
    st.caption("Upload a PDF to generate a structured analytical report.")

    init_state()
    client = OpenAI()

    uploaded_file = st.file_uploader("Upload a research paper (PDF)", type=["pdf"])
    if uploaded_file is not None:
        st.session_state.paper_text = extract_pdf_text(uploaded_file)

    if st.button("Generate Report", disabled=st.session_state.paper_text is None):
        with st.spinner("Analyzing the paper and writing the report..."):
            response = client.responses.parse(
                model=MODEL,
                instructions=REPORT_INSTRUCTIONS,
                input=(
                    "Create a detailed research report analyzing this paper:"
                    f"\n\n{st.session_state.paper_text}"
                ),
                text_format=ResearchReport,
            )
            st.session_state.report = response.output_parsed

    if st.session_state.report is not None:
        report = st.session_state.report
        render_report(report)

        markdown_text = format_report_as_markdown(report)
        filename = f"{slugify(report.title)}.md"
        st.download_button(
            label="Download report as Markdown",
            data=markdown_text,
            file_name=filename,
            mime="text/markdown",
        )
    else:
        st.info("Upload a PDF and click 'Generate Report' to begin.")


if __name__ == "__main__":
    main()
