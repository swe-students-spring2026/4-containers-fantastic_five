"""College Maxing AI service: LangGraph workflow for college application analysis."""

import os
import sys

from CMagent import CMAgent
from inputs import CMInputs
from langgraph.graph import StateGraph, START, END

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "web-app"))

from parser import parse_agent_output
from storage import SessionStorage


async def CMRun(
    user_essay: str,
    session_id: str | None = None,
    intended_university: str | None = None,
    user_interview_response: bytes | None = None,
    essay_file_name: str | None = None,
    notes: str | None = None,
    sat_score: str | None = None,
    gpa: str | None = None,
    essay_pdf_bytes: bytes | None = None,
):
    # create an state that store resume analysis inputs for each run
    userState = CMInputs(
        session_id=session_id,
        user_essay=user_essay,  # resume content
        essay_file_name=essay_file_name,
        essay_pdf_bytes=essay_pdf_bytes,
        gpa=gpa,
        notes=notes,
        user_interview_response=user_interview_response,
        intended_university=intended_university,
        sat_score=sat_score,
    )
    agentNode = CMAgent(  # this node is set in workflow to pass State in to analysis resume with agent
        prompt=(
            "You are an expert college application adviser. Analyze the provided information and return helpful, specific feedback regarding to the intended university for each analysis. "
            "If essay or interview response details are incomplete, make reasonable assumptions and still provide an answer. "
            "Do not ask the user to clarify or provide more details. "
            "Return concise sections: Applicant Score (0-100 scale), Essay Strengths, Missing elements, Suggested Edits, and AI Insights. The score 1-100 should be very diverse,reasonable, which try your best to make it quantitative"
        ),
        inputs=userState,
    )

    workflow = StateGraph(
        CMInputs
    )  # state is the main input/output for my langgraph workflow
    workflow.add_node("chat", agentNode)

    workflow.add_edge(START, "chat")
    workflow.add_edge(
        "chat", END
    )  # the goal is to put all the anaysis input and store agent output in state.result

    resumeGo = workflow.compile()
    result_state = await resumeGo.ainvoke(
        userState
    )  # this will return the entire updated state(AppState) object

    # Parse agent output and save to MongoDB
    if result_state.result and session_id:
        parsed = parse_agent_output(result_state.result)

        mongo_uri = os.environ.get("MONGO_URI", "mongodb://mongodb:27017/appdb")
        storage = SessionStorage("/tmp/sessions", mongo_uri=mongo_uri)

        storage.save_analysis_result(
            session_id=session_id,
            applicant_score=parsed["applicant_score"],
            strength=parsed["strength"],
            missing_elements=parsed["missing_elements"],
            suggested_edits=parsed["suggested_edits"],
            ai_insights=parsed["ai_insights"],
        )

    return result_state
