"""Main entry for the CollegeMaxxing ML workflow."""

import asyncio
from io import BytesIO

from pypdf import PdfReader

from CMagent import CMAgent
from inputs import CMInputs
from langgraph.graph import END, START, StateGraph

# main async run func
async def cm_run(
    user_essay: str,
    intended_university: str | None = None,
    user_interview_response: str | None = None,
    essay_file_name: str | None = None,
    notes: str | None = None,
    sat_score: int | None = None,
    gpa: float | None = None,
    essay_pdf_bytes: bytes | None = None,
):
    """Run one college app analysis task."""
    # store one app's inputs in state
    user_state = CMInputs(
        user_essay=user_essay,
        intended_university=intended_university,
        user_interview_response=user_interview_response,
        essay_file_name=essay_file_name,
        notes=notes,
        sat_score=sat_score,
        gpa=gpa,
        essay_pdf_bytes=essay_pdf_bytes,
    )

    # agent node does the actual review
    agent_node = CMAgent(
        prompt=(
            "You are an expert college application adviser. Analyze the "
            "provided information and return helpful, specific feedback "
            "about the intended university for each analysis. If essay or "
            "interview details are incomplete, make reasonable assumptions "
            "and still provide an answer. Do not ask the user to clarify "
            "or provide more details. Return concise sections: Applicant "
            "Score (0-100 scale), Essay Strengths, Missing Elements, "
            "Suggested Edits, and AI Insights. The score should be diverse, "
            "reasonable, and as quantitative as possible."
        ),
        inputs=user_state,
    )

    # state graph for one run
    workflow = StateGraph(CMInputs)
    workflow.add_node("chat", agent_node)
    workflow.add_edge(START, "chat")
    workflow.add_edge("chat", END)

    resume_go = workflow.compile()
    result_state = await resume_go.ainvoke(user_state)

    return result_state


if __name__ == "__main__":
    # quick local demo block
    def _extract_pdf_text(pdf_bytes: bytes) -> str:
        """Pull text from a PDF for testing."""
        if not pdf_bytes:
            return "pdf uploading error, make sure it's a pdf file!"

        reader = PdfReader(BytesIO(pdf_bytes))
        pages_text = [(page.extract_text() or "").strip() for page in reader.pages]
        return "\n\n".join(text for text in pages_text if text).strip()

    # with open(FILE_PATH, "rb") as file_obj:
    #     essay_pdf_bytes = file_obj.read()
    # extracted_text = _extract_pdf_text(essay_pdf_bytes or b"")

    output = asyncio.run(
        cm_run(
            user_essay="Essay about becoming next tony stark",
            essay_file_name="no",
            essay_pdf_bytes=b"",
            gpa=4.0,
            notes="super smart, mit material",
            user_interview_response="Great",
            intended_university="NYU",
            sat_score=1500,
        )
    )
    # just prints demo output for now
    print(output["result"])
