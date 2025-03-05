"""
This module handles storing of OpenAI Thread IDs with DynamoDB
"""
import os

import boto3


TABLE_NAME = os.getenv("TABLE_NAME")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def get_item_if_exists(_id: str):
    response = table.get_item(Key={"id": _id})

    if "Item" in response:
        return response["Item"]

    return None


def store_thread(user_id: str, thread_id: str):
    """
    Store thread id associated with user id
    """
    value = {
        "id": user_id,
        "thread_id": thread_id,
        "student_type": None
    }

    table.put_item(Item=value)


def update_thread(user_id: str, student_type: str):
    """
    Update student type for thread
    """
    return table.update_item(
        Key={
            "id": user_id
        },
        UpdateExpression='SET student_type = :val1',
        ExpressionAttributeValues={
            ':val1': student_type
        }
    )