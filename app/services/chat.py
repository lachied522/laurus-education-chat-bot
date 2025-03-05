"""
This module handles core chat functionality with OpenAI Assistants API
"""
import os

import json

import logging

from openai import OpenAI

from services.storage import get_item_if_exists, store_thread, update_thread

from services.search import search_tool


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


def handle_tool_calls(
    run # run object from client.beta.threads.run.create
):
    tool_outputs = []

    if run.required_action:
        for tool in run.required_action.submit_tool_outputs.tool_calls:
            try:
                arguments = json.loads(tool.function.arguments)

                query = arguments.get("query")

                if not query:
                    raise Exception("Query was not found in function arguments")

                if tool.function.name == "search_knowledge":
                    tool_outputs.append({
                        "tool_call_id": tool.id,
                        "output": search_tool(query)
                    })

            except Exception as e:
                logger.error("Error handling tool calls: ", e)

                # prompt the model to apologise to the user and direct them to a human
                tool_outputs.append({
                    "tool_call_id": tool.id,
                    "output": "There is something wrong with the tool at the moment. Apologise to the user and direct them to contact a human."
                })

    return tool_outputs


def run_assistant(thread, name):
    """
    This function runs the assistant, handles any tool calls, and returns the response as a string
    """
    # retrieve assistant
    assistant = client.beta.assistants.retrieve(OPENAI_ASSISTANT_ID)

    # add user name to thread if it is provided
    additional_instructions = None
    if name is not None:
        additional_instructions = f"You are now having a conversation with {name}"

    # run this assistant and wait until terminal state
    # https://platform.openai.com/docs/assistants/tools/function-calling?example=without-streaming
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id,
        additional_instructions=additional_instructions,
        timeout=45,
    )

    if run.status == "failed":
        raise Exception("Assistant run failed")

    tool_outputs = handle_tool_calls(run)

    if len(tool_outputs) > 0:
        run = client.beta.threads.runs.submit_tool_outputs_and_poll(
            thread_id=thread.id,
            run_id=run.id,
            tool_outputs=tool_outputs,
            timeout=45,
        )

        if run.status == "failed":
            raise Exception("Submitting tool outputs failed")

    messages = client.beta.threads.messages.list(thread_id=thread.id)

    return messages.data[0].content[0].text.value


def generate_response(
    message: str,
    _id: str, # either Whatsapp user id, user's ip address, or any other unique id passed through the /chat endpoint
    name: str | None = None
):
    # Check if there is already a record for the corresponding id
    record = get_item_if_exists(_id)

    # If a thread doesn't exist, create one and store it
    if record is None:
        logger.info(f"Creating new thread for {name} with id {_id}")
        thread = client.beta.threads.create()

        store_thread(_id, thread.id)

        thread_id = thread.id
        student_type = None

    # Otherwise, retrieve the existing thread
    else:
        logger.info(f"Retrieving existing thread for {name} with id {_id}")
        thread = client.beta.threads.retrieve(record.get("thread_id"))

        thread_id = thread.id
        student_type = record.get("student_type")

    # add user message to thread
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message,
    )

    # If student type has not been determined, send a custom message
    if student_type is None:
        # Update student type to "pending" in database
        update_thread(_id, "pending")

        # Add the bot's response to thread history before returning
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="assistant",
            content=STUDENT_TYPE_MESSAGE,
        )

        return STUDENT_TYPE_MESSAGE

    # Determine student type from response and update database
    if student_type == "pending":
        student_type = get_student_type_from_user_message(message)

        update_thread(_id, student_type)

    try:
        # Run the assistant and get the new message
        response = run_assistant(thread, name)

        logger.info("User message: ", message)
        logger.info("AI response: ", response)

        return response

    except Exception as e:
        logger.error("Error generating response: ", e)

        return "Something went wrong processing your request, please try again later or contact a human for support"
