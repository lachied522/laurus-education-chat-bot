"""
This module handles storing of OpenAI Thread IDs with DynamoDB
"""
import boto3


dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("laurus-education-chat-bot-table")

def get_thread_if_exists(_id: str):
    response = table.get_item(Key={"id": _id})

    if "Item" in response:
        return response["Item"].get("thread")
    
    return None

def store_thread(_id: str, thread_id: str):
    table.put_item(Item={"id": _id, "thread": thread_id})