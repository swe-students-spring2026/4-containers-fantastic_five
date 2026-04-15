from CMagent import CMAgent
import asyncio  # Needed to run the async ResumeGoRun() entry point from this standalone script.
from inputs import CMInputs
from langgraph.graph import StateGraph, START, END #this is the workflow that will pass Agent STATE and update variables of it



async def CMRun(
    user_essay: str,
    intended_university: str | None = None,
    user_interview_response: bytes | None = None,
    essay_file_name: str | None = None,
    notes: str | None = None,
    sat_score: str | None = None,
    gpa: str | None = None,
    essay_pdf_bytes: bytes | None = None

):
    #create an state that store resume analysis inputs for each run
    userState= CMInputs(
            user_essay=user_essay, #resume content
            essay_file_name=essay_file_name,
            essay_pdf_bytes=essay_pdf_bytes,
            gpa=gpa,
            notes=notes,
            user_interview_response=user_interview_response,
            intended_university=intended_university,
            sat_score=sat_score

        )
    agentNode  = CMAgent( # this node is set in workflow to pass State in to analysis resume with agent
        prompt=(
            "You are an expert college application adviser. Analyze the provided information and return helpful, specific feedback regarding to the intended university for each analysis. "
            "If essay or interview response details are incomplete, make reasonable assumptions and still provide an answer. "
            "Do not ask the user to clarify or provide more details. "
            "Return concise sections: Applicant Score (0-100 scale), Essay Strengths, Missing elements, Suggested Edits, and AI Insights. The score 1-100 should be very diverse,reasonable, which try your best to make it quantitative"
        ), inputs=userState
    )

    
    workflow = StateGraph(CMInputs) #state is the main input/output for my langgraph workflow
    workflow.add_node("chat", agentNode)

  
    workflow.add_edge(START, "chat")
    workflow.add_edge("chat", END) #the goal is to put all the anaysis input and store agent output in state.result 
   
   
    resumeGo  = workflow.compile()
    return await resumeGo.ainvoke(userState) #this will return the entire updated state(AppState) object
    

if __name__ == "__main__":
    import asyncio  # to create/manage the event loop for testing for this file.
    from pypdf import PdfReader
    from io import BytesIO

    ###this is the test run for this appRun.py, you can import your own pdf resume files to see the output from my agent on your on terminal
    def _extract_pdf_text(pdf_bytes: bytes) -> str:
        if not pdf_bytes:
            return "pdf uploading error, make sure it's a pdf file!"

        reader = PdfReader(BytesIO(pdf_bytes))
        pages_text = [(page.extract_text() or "").strip() for page in reader.pages]
        return "\n\n".join(text for text in pages_text if text).strip()

    file_path="~/Desktop/filename.pdf"
    # with open(file_path, 'rb') as f:
    #         resume_pdf_bytes = f.read()

    # extracted_resume_text = _extract_pdf_text(resume_pdf_bytes or b"")

    output = asyncio.run(
        CMRun(
            user_essay="Essay about becoming next tony stark",
            essay_file_name="no",
            essay_pdf_bytes="",
            gpa=4.0,
            notes="super smart, mit material",
            user_interview_response="Great",
            intended_university="NYU",
            sat_score=1500
        )
    )
    #I used this fixed input for demo, it will later on be the AppState(check state.py) object that load the pdf from our frontend website
    print(output['result'])

