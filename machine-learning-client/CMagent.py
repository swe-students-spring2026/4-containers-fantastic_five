"""Agent wrapper for running college app analysis."""

# from request_prompt import FILTER_PROMPT | will work on prompt engineering soon
# need it to make my request into langchain model redable ones
from langchain_core.prompts import ChatPromptTemplate

from llmSetUp import GetLLM


# inherited from myllm.py where I set up the model
class CMAgent(GetLLM):
    """Simple agent wrapper."""

    def __init__(self, prompt: str, inputs):
        super().__init__(prompt=prompt)
        self.llm = self.get_llm()
        self._inputs = inputs

    async def run(self, inputs):
        """Run one agent call."""

        prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    self.prompt,
                ),
                # the system prompt here is higher priority that the agent should follow.
                (
                    "human",
                    "Analyze the essay and mock interview response of the "
                    "student, specially about his/hers "
                    "credential/odds/potentials to get into the intended"
                    "university he/she assigns. Based on these info "
                    "provided, give a detailed result/rating categorized in:\n"
                    "1) Applicant Score (you can only give one number from 1 to 100, make sure it's only a number)\n"
                    "2) Essay Strengths (bullet list)\n"
                    "3) Missing elements (bullet list)\n"
                    "4) Suggested Edits (bullet list)\n"
                    "5) AI Insights (paragraph)\n\n"
                    "Uploaded essay filename: {essay_file_name}\n"
                    "Applicant notes: {notes}\n"
                    "SAT score:\n{sat_score}\n\n"
                    "gpa:\n{gpa}\n\n"
                    "intended_university:\n{intended_university}\n\n"
                    "Extracted essay text:\n{user_essay}\n\n"
                    "Mock Interview response text:\n"
                    "{user_interview_response}\n\n"
                    "PDF bytes metadata: {pdf_bytes_info}",
                ),
                # human prompt here is the task request I want the agent to do. broke into details and formating.
            ]
        )

        # I pipe the prompt into the LLM to create an executable LangChain pipeline. output of left -> right basically
        chain = prompt_template | self.llm

        answer = await chain.ainvoke(
            {
                # the university that the student(user) wants to get in, which is the analysis for
                "intended_university": inputs.intended_university,
                # this is the content on essay
                "user_essay": inputs.user_essay,
                # this is student's resposne of the two questions about the intended university
                "user_interview_response": inputs.user_interview_response,
                # just keep the file name for reference, not going to weight analysis
                "essay_file_name": inputs.essay_file_name,
                # user's(student) personal extra notes regarding to the analysis, consider when it's not empty
                "notes": inputs.notes,
                # the SAT score of this student
                "sat_score": inputs.sat_score,
                # current gpa of this student
                "gpa": inputs.gpa,
                # the original bytes of the essay file for backup, storing in the database.
                "pdf_bytes_info": inputs.essay_pdf_bytes,
            }
        )

        # I store the output of agent on varible {result} withing inputs object, which carries all the inputs of the student for each analysis session. On Flask frontend, we will use output['result'] to get it since the agent return a dictionary type.
        inputs.result = answer.content

        return inputs

    async def __call__(self, inputs):
        """Allow instance to be called like a func."""
        return await self.run(inputs)

    # CMAgent("How is the odds of this student getting into this unversity based on his provided credential?") example question for agent
