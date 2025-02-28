"""
This module handles sending messages via Whatsapp
"""
import os

import logging

import requests

from fastapi import HTTPException

from .chat import generate_response


WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

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
        raise HTTPException(status_code=408, detail="Request timed out")

    except requests.RequestException as e:  # This will catch any general request exception
        logger.error(f"Request failed due to: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")

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
