"""
This module handles sending messages via Whatsapp
"""
import os

import logging

import requests

from .chat import generate_response

from dotenv import load_dotenv

load_dotenv()


WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

# Had issues with duplicate messages coming from Whatsapp
# Keep track of messages being processed in a map
PROCESSING_MESSAGES: set[str] = set()


logger = logging.getLogger()

def log_http_response(response):
    logger.info(f"Status: {response.status_code}")
    logger.info(f"Content-type: {response.headers.get('content-type')}")
    logger.info(f"Body: {response.text}")


def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
    }

    url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{PHONE_NUMBER_ID}/messages"

    try:
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=10
        )

        response.raise_for_status()

    except requests.Timeout:
        logger.error("Timeout occurred while sending message")
        raise Exception("Request timed out")

    except requests.RequestException as e:  # This will catch any general request exception
        logger.error(f"Request failed due to: {e}")
        raise Exception("Failed to send message")

    else:
        # Process the response as normal
        log_http_response(response)
        return response


def process_whatsapp_message(body):
    """
    Extract fields from request body, generate response, and send reply
    """
    # see Whatsapp payload structure below
    # https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples#text-messages
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

    message = body["entry"][0]["changes"][0]["value"]["messages"][0]

    if message["type"] != "text":
        logger.info("Non-text message was received")
        return

    text = message["text"]["body"]

    key = f"{wa_id}:{text}"

    if key in PROCESSING_MESSAGES:
        logger.info("Received duplicate message")
        return

    PROCESSING_MESSAGES.add(key)

    response = generate_response(text, wa_id, name)

    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": wa_id,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": response
        },
    }

    send_message(data)

    PROCESSING_MESSAGES.remove(key)
