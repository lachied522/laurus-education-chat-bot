"""
This module contains code for creating an OpenAI Assistant.
Once the assistant is created, the assistant ID should be stored as an environment variable
"""
from openai import OpenAI, pydantic_function_tool

from pydantic import BaseModel, Field


# define constants
DEFAULT_OPENAI_MODEL = "gpt-4o"
DEFUAULT_ASSISTANT_NAME = "Laurus Education Customer Service Assistant"


# change these instructions as you see fit
SYSTEM_INSTRUCTIONS = """You're a helpful customer service agent for Laurus Education, a provider of high quality education programs to Australian and international students. \
You will be answering enquiries from prospective and existing students. \
Laurus Education partners with a variety of Colleges that provide educational programs in areas such as English language, Hospitality, Aged Care, Automotive, Business, and Construction. \
Laurus' partner colleges and the courses they provide are:
- Future English - General English and IELTS preparation courses
- Hilton Academy - variety of certificates and diplomas in cookery, hospitality, and kitchen management
- Allied Instite - variety of certificates and diplomas in aged care, child care, and individual support
- Paragon Polytechnic - variety of mechanical and automative certificates and diplomas
- Collins Academy - variety of business and project management certificates, diplomas, graduate diplomas, and advanced diplomas
- Everthough College of Construction - variety of certificates and diplomas in carpentry, bricklaying, painting, and construction management
You should rely on your knowledge base to answer user questions through the search_knowledge function to ensure you always have accurate information. \
If you don't know the answer, say simply that you cannot help with question and advice to contact a human customer service representative directly. \
Do not use markdown, respond with text only. Be friendly and approachable.
"""

# define schema for the search tool
class SearchKnowledgeBase(BaseModel):
    query: str = Field(
        ...,
        description="Query used to search knowledge base"
    )


def create_assistant():
    """
    Create an OpenAI Assistant
    """
    client = OpenAI()

    assistant = client.beta.assistants.create(
        name=DEFUAULT_ASSISTANT_NAME,
        instructions=SYSTEM_INSTRUCTIONS,
        model=DEFAULT_OPENAI_MODEL,
        tools=[pydantic_function_tool(SearchKnowledgeBase, name="search_knowledge", description="Search Laurus Education knowledge base for relevant information to help you answer the user's enquiries")]
    )

    return assistant


if __name__ == "__main__":
    import os

    assistant = create_assistant()

    print("Assistant created with id: ", assistant.id)

    os.environ["OPENAI_ASSISTANT_ID"] = assistant.id