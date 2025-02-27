"""
This module handles storing of OpenAI Thread IDs with DynamoDB
"""
import os

import boto3


TABLE_NAME = os.getenv("TABLE_NAME")

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def get_thread_if_exists(_id: str):
    response = table.get_item(Key={"id": _id})

    if "Item" in response:
        return response["Item"].get("thread")
    
    return None

def store_thread(_id: str, thread_id: str):
    table.put_item(Item={"id": _id, "thread": thread_id})
