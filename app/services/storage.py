"""
This module handles storing of OpenAI Thread IDs with DynamoDB
"""
import os

from datetime import datetime, timedelta

import shelve


# Directory for shelve module
DIRECTORY = "storage"
FILE_NAME = "thread_store"
PATH = f"{DIRECTORY}/{FILE_NAME}"


def configure_storage():
    """
    Create directory for storage if it doesn't exist
    """
    if not os.path.exists(DIRECTORY):
        os.makedirs(DIRECTORY)


def get_item_if_exists(user_id: str):
    cleanup_old_threads()

    with shelve.open(PATH) as store:
        return store.get(user_id, None)


def store_thread(user_id: str, thread_id: str):
    """
    Store thread id associated with user id
    """
    with shelve.open(PATH) as store:
        store[user_id] = {
            "thread_id": thread_id,
            "student_type": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }


def update_thread(user_id: str, student_type: str):
    """
    Update student type for thread
    """
    current_value = get_item_if_exists(user_id)

    if current_value is None:
        raise Exception("Attempted to update value that does not exist")

    with shelve.open(PATH) as store:
        store[user_id] = {
            **current_value,
            "student_type": student_type,
            "updated_at": datetime.now().isoformat(),
        }


def cleanup_old_threads():
    """
    OpenAI threads expire after 30 days. Remove records where 'updated_at' is more than 30 days ago
    """
    three_months_ago = datetime.now() - timedelta(days=30)

    with shelve.open(PATH, writeback=True) as store:
        keys_to_delete = []

        for user_id, data in store.items():
            updated_at = data.get("updated_at")

            if updated_at is None:
                keys_to_delete.append(user_id)
                continue

            if datetime.fromisoformat(updated_at) < three_months_ago:
                keys_to_delete.append(user_id)

        for key in keys_to_delete:
            del store[key]