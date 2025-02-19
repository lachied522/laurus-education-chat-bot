"""
This module handles core chat functionality with OpenAI Assistants API
"""
import os

import logging

import time

import shelve # TO DO: get rid of this

from openai import OpenAI

# from services.search import search_tool

client = OpenAI()

# OPENAI_ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")
OPENAI_ASSISTANT_ID = "asst_80MFf5TEsLT1B1FAjGHueMUn"

# Use context manager to ensure the shelf file is closed properly
def check_if_thread_exists(wa_id):
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(wa_id, None)


def store_thread(wa_id, thread_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[wa_id] = thread_id


def handle_tool_calls(
    run # run object from client.beta.threads.run.create
):
    tool_outputs = []

    print(run.required_action.submit_tool_outputs.tool_calls)

    for tool in run.required_action.submit_tool_outputs.tool_calls:
        if tool.function.name == "search_knowledge":
            tool_outputs.append({
                "tool_call_id": tool.id,
                "output": "There is something wrong with the tool at the moment"
                # "output": search_tool(**tool.function.arguments)
            })

    return tool_outputs

def run_assistant(thread, name):
    """
    This function runs the assistant, handles any tool calls, and returns the response as a string
    """
    # retrieve assistant
    assistant = client.beta.assistants.retrieve(OPENAI_ASSISTANT_ID)

    # run this assistant and wait until terminal state
    # https://platform.openai.com/docs/assistants/tools/function-calling?example=without-streaming
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant.id,
        additional_instructions=f"You are now having a conversation with {name}",
    )

    if run.status == "completed":
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        print(messages)
    else:
        print(run.status)

    tool_outputs = handle_tool_calls(run)

    # Submit all tool outputs at once after collecting them in a list
    if len(tool_outputs) > 0:
        try:
            run = client.beta.threads.runs.submit_tool_outputs_and_poll(
                thread_id=thread.id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
            print("Tool outputs submitted successfully.")
        except Exception as e:
            print("Failed to submit tool outputs:", e)
    else:
        print("No tool outputs to submit.")

    # Retrieve the Messages
    messages = client.beta.threads.messages.list(thread_id=thread.id)

    print(messages)
    new_message = messages.data[0].content[0].text.value
    logging.info(f"Generated message: {new_message}")
    return new_message


def generate_response(message_body, wa_id, name):
    # Check if there is already a thread_id for the wa_id
    thread_id = check_if_thread_exists(wa_id)

    # If a thread doesn't exist, create one and store it
    if thread_id is None:
        logging.info(f"Creating new thread for {name} with wa_id {wa_id}")
        thread = client.beta.threads.create()
        store_thread(wa_id, thread.id)
        thread_id = thread.id

    # Otherwise, retrieve the existing thread
    else:
        logging.info(f"Retrieving existing thread for {name} with wa_id {wa_id}")
        thread = client.beta.threads.retrieve(thread_id)

    # user message to thread
    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_body,
    )

    # run the assistant and get the new message
    new_message = run_assistant(thread, name)

    return new_message


if __name__ == "__main__":
    print(generate_response("What certificates do you provide?", "123", "Lachie"))