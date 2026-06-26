import os
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

class JobMatch(BaseModel):
    relevance_score: float = Field(description="Score from 0 to 100")
    reason: str = Field(description="Short explanation of why it matches")
    cover_letter: str = Field(description="A draft cover letter tailored to this job")

class Matcher:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0
        )
        self.parser = JsonOutputParser(pydantic_object=JobMatch)

        self.match_prompt = ChatPromptTemplate.from_template(
            "You are a career assistant. Evaluate the following job against the user's profile.\n\n"
            "User Profile/Resume: {resume}\n"
            "User Preferences: Keywords: {keywords}, Location: {location}, Remote Only: {remote_only}\n\n"
            "Job Title: {job_title}\n"
            "Company: {company}\n"
            "Job Description: {job_description}\n\n"
            "{format_instructions}"
        )

    async def score_job(self, user: Any, job: Any) -> Dict[str, Any]:
        """Scores a job for a user and generates a cover letter draft."""
        if not os.getenv("GOOGLE_API_KEY"):
            return {
                "relevance_score": 50.0,
                "reason": "AI features disabled (no API key)",
                "cover_letter": "AI features disabled (no API key)"
            }

        chain = self.match_prompt | self.llm | self.parser

        try:
            result = await chain.ainvoke({
                "resume": user.resume_text or "No resume provided",
                "keywords": user.keywords or "None",
                "location": user.location or "Any",
                "remote_only": "Yes" if user.remote_only else "No",
                "job_title": job.title,
                "company": job.company,
                "job_description": job.description[:2000], # Truncate to save tokens
                "format_instructions": self.parser.get_format_instructions()
            })
            return result
        except Exception as e:
            print(f"Error in AI scoring: {e}")
            return {
                "relevance_score": 0.0,
                "reason": f"Error during AI analysis: {str(e)}",
                "cover_letter": ""
            }
