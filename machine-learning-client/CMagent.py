from llmSetUp import GetLLM
# from request_prompt import FILTER_PROMPT | will work on prompt engineering soon
from langchain_core.prompts import ChatPromptTemplate #need it to make my request into langchain model redable ones


class CWAgent(GetLLM):# inherited from myllm.py where I set up the model

    def __init__(self, prompt: str, inputs):
        super().__init__(prompt=prompt)
        self.llm = self.get_llm() 

    async def run(self, inputs):
        
        prompt_template = ChatPromptTemplate.from_messages([
            ('system', self.prompt), #the system prompt here is higher priority that the agent should follow.
            ('human', 
                "Analyze the essay and mock interview response of the student, specially about his/hers credential/odds/potentials to get into the intended university he/she assigns. Based on these info provided, give a detailed result/rating categorized in:\n"
                "1) Applicant Score (0-100)\n"
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
                "Mock Interview response text:\n{user_interview_response}\n\n"
                "PDF bytes metadata: {pdf_bytes_info}"
            ) #human prompt here is the task request I want the agent to do. broke into details and formating.
        ])

        chain = prompt_template | self.llm #I pipe the prompt into the LLM to create an executable LangChain pipeline. output of left -> right basically



        return inputs 

    async def __call__(self, inputs):
        return await self.run(inputs)
    
    # CMAgent("How is the odds of this student getting into this unversity based on his provided credential?") example question for agent

