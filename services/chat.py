"""
This module handles core chat functionality with OpenAI Assistants API
"""
import os

import json

import logging

from openai import OpenAI

from services.storage import get_thread_if_exists, store_thread

from services.search import search_tool


client = OpenAI()

# OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")
OPENAI_ASSISTANT_ID = "asst_O7pqqqm3PEr98QlGQZ6VP0oC"


def handle_tool_calls(
    run # run object from client.beta.threads.run.create
):
    tool_outputs = []

    if run.required_action:
        print("tool calls", run.required_action.submit_tool_outputs.tool_calls)
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
                logging.error("Error handling tool calls: ", e)

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
    if name is not None:
        additional_instructions = f"You are now having a conversation with {name}"

    # run this assistant and wait until terminal state
    # https://platform.openai.com/docs/assistants/tools/function-calling?example=without-streaming
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id,
        additional_instructions=additional_instructions,
    )

    if run.status == "failed":
        raise Exception("Assistant run failed")

    tool_outputs = handle_tool_calls(run)

    if len(tool_outputs) > 0:
        try:
            run = client.beta.threads.runs.submit_tool_outputs_and_poll(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )

        except Exception as e:
            logging.error("Failed to submit tool outputs: ", e)

    messages = client.beta.threads.messages.list(thread_id=thread.id)

    return messages.data[0].content[0].text.value


def generate_response(
    message_body: str,
    _id: str,
    name: str | None = None
):
    # Check if there is already a thread_id for the wa_id
    thread_id = get_thread_if_exists(_id)

    # If a thread doesn't exist, create one and store it
    if thread_id is None:
        logging.info(f"Creating new thread for {name} with id {_id}")
        thread = client.beta.threads.create()
        store_thread(_id, thread.id)
        thread_id = thread.id

    # Otherwise, retrieve the existing thread
    else:
        logging.info(f"Retrieving existing thread for {name} with id {_id}")
        thread = client.beta.threads.retrieve(thread_id)

    try:
        # user message to thread
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message_body,
        )

        # run the assistant and get the new message
        new_message = run_assistant(thread, name)

        return new_message
    
    except Exception as e:
        logging.error("Error generating response: ", e)

        return "Something went wrong processing your request, please try again later or contact a human for support"
