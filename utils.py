# utils.py - FIXED for UPSC Quiz App
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field, validator
import json
import re

load_dotenv()

class MCQQuestion(BaseModel):
    question: str = Field(description="The question text")
    options: List[str] = Field(description="List of 4 possible answers")
    correct_answer: str = Field(description="The correct answer from the options")

    @validator('question', pre=True)
    def clean_question(cls, v):
        if isinstance(v, dict):
            return v.get('description', str(v))
        return str(v)

class FillBlankQuestion(BaseModel):
    question: str = Field(description="The question text with '_____' for the blank")
    answer: str = Field(description="The correct word or phrase for the blank")

    @validator('question', pre=True)
    def clean_question(cls, v):
        if isinstance(v, dict):
            return v.get('description', str(v))
        return str(v)

class QuestionGenerator:
    def __init__(self):
        self.llm = ChatGroq(
            api_key=os.getenv('GROQ_API_KEY'), 
            model="llama3-70b-8192",  # ✅ Better model for UPSC
            temperature=0.3  # ✅ Lower for accuracy
        )

    def generate_questions(self, topic: str, question_type: str, difficulty: str, num_questions: int) -> List[Dict[str, Any]]:
        """
        ✅ MAIN METHOD - Compatible with app.py QuizManager
        Returns list of questions in exact format your app expects
        """
        questions = []
        
        for i in range(num_questions):
            try:
                if "multiple" in question_type.lower():
                    question = self.generate_mcq(topic, difficulty)
                    questions.append({
                        "question": question.question,
                        "type": "multiple_choice",
                        "options": question.options,
                        "correct_answer": question.correct_answer
                    })
                else:
                    question = self.generate_fill_blank(topic, difficulty)
                    questions.append({
                        "question": question.question,
                        "type": "fill_in_blank",
                        "correct_answer": question.answer
                    })
            except Exception as e:
                # Fallback mock question
                questions.append(self._get_mock_question(topic, question_type, difficulty, i+1))
        
        return questions

    def generate_mcq(self, topic: str, difficulty: str = 'medium') -> MCQQuestion:
        mcq_parser = PydanticOutputParser(pydantic_object=MCQQuestion)
        prompt = PromptTemplate(
            template="You are a UPSC exam expert. Generate 1 {difficulty} MCQ about '{topic}' for IAS prelims.\n\n"
                    "{format_instructions}\n\n"
                    "Make options realistic. Return ONLY valid JSON.",
            input_variables=["topic", "difficulty"],
            partial_variables={"format_instructions": mcq_parser.get_format_instructions()}
        )
        
        for attempt in range(3):
            try:
                response = self.llm.invoke(prompt.format(topic=topic, difficulty=difficulty))
                parsed = mcq_parser.parse(response.content)
                
                if (parsed.correct_answer in parsed.options and 
                    len(parsed.options) == 4 and parsed.question):
                    return parsed
            except:
                continue
        
        raise RuntimeError("Failed to generate MCQ")

    def generate_fill_blank(self, topic: str, difficulty: str = 'medium') -> FillBlankQuestion:
        fill_parser = PydanticOutputParser(pydantic_object=FillBlankQuestion)
        prompt = PromptTemplate(
            template="You are a UPSC exam expert. Generate 1 {difficulty} fill-in-the-blank question about '{topic}'.\n\n"
                    "{format_instructions}\n\n"
                    "Use '_____' for blanks. Return ONLY valid JSON.",
            input_variables=["topic", "difficulty"],
            partial_variables={"format_instructions": fill_parser.get_format_instructions()}
        )
        
        for attempt in range(3):
            try:
                response = self.llm.invoke(prompt.format(topic=topic, difficulty=difficulty))
                parsed = fill_parser.parse(response.content)
                
                if parsed.question and parsed.answer and "_____" in parsed.question:
                    return parsed
            except:
                continue
        
        raise RuntimeError("Failed to generate fill-in-blank")

    def _get_mock_question(self, topic: str, question_type: str, difficulty: str, index: int) -> Dict[str, Any]:
        """Fallback mock questions"""
        mocks = {
            "Article 370, Fundamental Rights, Panchayati Raj": [
                {
                    "question": "Which articles deal with Fundamental Rights?",
                    "type": "multiple_choice",
                    "options": ["Article 12-35", "Article 36-51", "Article 51A", "Article 368"],
                    "correct_answer": "Article 12-35"
                }
            ]
        }
        return mocks.get(topic, [{"question": f"Mock Q{index} on {topic}", "type": "multiple_choice", "options": ["A", "B", "C", "D"], "correct_answer": "A"}])[0]
