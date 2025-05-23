"""
This module handles core chat functionality with OpenAI Assistants API
"""
import os

import json

import logging

from datetime import datetime

from openai import OpenAI, BadRequestError

from services.storage import get_item_if_exists, store_thread as store_thread_in_db, update_thread as update_thread_in_db

from services.search import search_tool
from services.tools import application_form_tool

from dotenv import load_dotenv

load_dotenv()


# Define constants
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

# Define the message students will receive when they first message
# the bot to determine whether they are prospective or existing
STUDENT_TYPE_MESSAGE = """Hi, thank you for your message. To help me assist you with your query, please confirm whether you are an existing student with Laurus Education. Please reply with \"YES\" or \"NO\""""


logger = logging.getLogger()

client = OpenAI(api_key=OPENAI_API_KEY)


def get_student_type_from_user_message(
    message: str,
):
    """
    This will determine the student's type from their response to the above message.
    """
    message = message.upper().strip()

    if message == "YES":
        return "existing"

    if message == "NO":
        return "prospective"

    # if message does not match "YES" or "NO" we will return "unknown"
    return "unknown"


def create_and_store_thread(
    _id: str # primary key to store thread under
):
    thread = client.beta.threads.create()

    store_thread_in_db(_id, thread.id)

    return thread


def retrieve_thread(
    thread_id: str
):
    thread = client.beta.threads.retrieve(thread_id)
    return thread.id


def handle_tool_calls(
    run # run object from client.beta.threads.run.create
):
    tool_outputs = []

    if run.required_action:
        for tool in run.required_action.submit_tool_outputs.tool_calls:
            try:
                arguments = json.loads(tool.function.arguments)

                match tool.function.name:
                    case "search_knowledge":
                        query = arguments.get("query")

                        if not query:
                            raise ValueError("Argument 'query' was not provided")

                        tool_outputs.append({
                            "tool_call_id": tool.id,
                            "output": search_tool(query)
                        })

                    case "get_application_form":
                        college = arguments.get("college")

                        if not college:
                            raise ValueError("Argument 'college' was not provided")

                        tool_outputs.append({
                            "tool_call_id": tool.id,
                            "output": application_form_tool(college)
                        })

            except Exception as e:
                logger.error("Error handling tool calls: ", e)

                # prompt the model to apologise to the user and direct them to a human
                tool_outputs.append({
                    "tool_call_id": tool.id,
                    "output": "There is something wrong with the tool at the moment. Apologise to the user and direct them to contact a human."
                })

    return tool_outputs


def run_assistant(thread_id, name):
    """
    This function runs the assistant, handles any tool calls, and returns the response as a string
    """
    # retrieve assistant
    assistant = client.beta.assistants.retrieve(OPENAI_ASSISTANT_ID)

    additional_instructions = f"Today's date is {datetime.now().strftime('%A, %#d %B %Y')}."

    # add user name to thread if it is provided
    if name is not None:
        additional_instructions += f" You are now having a conversation with {name}"

    # run this assistant and wait until terminal state
    # https://platform.openai.com/docs/assistants/tools/function-calling?example=without-streaming
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant.id,
        additional_instructions=additional_instructions,
        timeout=60,
    )

    tool_outputs = handle_tool_calls(run)

    if len(tool_outputs) > 0:
        run = client.beta.threads.runs.submit_tool_outputs_and_poll(
            thread_id=thread_id,
            run_id=run.id,
            tool_outputs=tool_outputs,
            timeout=60,
        )

        if run.status != "completed":
            raise Exception("Submitting tool outputs failed")

    messages = client.beta.threads.messages.list(thread_id=thread_id)

    return messages.data[0].content[0].text.value


def generate_response(
    query: str,
    _id: str, # either Whatsapp user id, user's ip address, or any other unique id passed through the /chat endpoint
    name: str | None = None
):
    try:
        # Check if there is already a record for the corresponding id
        record = get_item_if_exists(_id)

        # If a thread doesn't exist, create one and store it
        if record is None:
            thread = create_and_store_thread(_id)
            student_type = None

        # Otherwise, retrieve the existing thread
        else:
            student_type = record.get("student_type", None)

            try:
                thread = client.beta.threads.retrieve(record.get("thread_id"))

            except Exception as e:
                logger.warning(f"Error retreiving thread with id {_id}, creating new thread instead")

                thread = create_and_store_thread(_id)

        # add user message to thread
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=query,
        )

        # If student type has not been determined, send a custom message
        if student_type is None:
            # Update student type to "pending" in database
            update_thread_in_db(_id, "pending")

            # Add the bot's response to thread history before returning
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="assistant",
                content=STUDENT_TYPE_MESSAGE,
            )

            return STUDENT_TYPE_MESSAGE

        # Determine student type from response and update database
        if student_type == "pending":
            student_type = get_student_type_from_user_message(query)

            update_thread_in_db(_id, student_type)

        # Run the assistant and get the new message
        response = run_assistant(thread.id, name)

        logger.debug("User message: ", query)
        logger.debug("AI response: ", response)

        return response

    except BadRequestError as e:
        logger.info("Could not generate response. It is likely an incoming message was received while the chatbot was responding to a previous message. Details below.")
        logger.info(e)

        return "Please wait while I look into your query."

    except Exception as e:
        logger.error(f"Error generating response: {e}")

        return "Something went wrong processing your request, please try again later or contact a human for support."
