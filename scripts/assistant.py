"""
This module contains code for creating an OpenAI Assistant.
Once the assistant is created, the assistant ID should be stored as an environment variable
"""

import os

from openai import OpenAI, pydantic_function_tool

from pydantic import BaseModel, Field


# define constants
DEFAULT_OPENAI_MODEL = "gpt-4o"
DEFUAULT_ASSISTANT_NAME = "Laurus Education Customer Service Assistant"


# change these instructions as you see fit
SYSTEM_INSTRUCTIONS = """
You're a helpful customer service agent for Laurus Education, a provider of high quality education programs to Australian and international students. \
Laurus provide a variety of educational programs in areas such as English language, Hospitality, Aged Care, Automotive, Business, and Construction. \
You will be answering enquiries from prospective and existing students. If you don't know the answer, say simply that you cannot help with question and advice to contact a human customer service representative directly. \
Be friendly and funny.
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
    assistant = create_assistant()

    print("Assistant created with id: ", assistant.id)

    os.environ["OPENAI_ASSISTANT_ID"] = assistant.id