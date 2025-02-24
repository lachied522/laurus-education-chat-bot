"""
This module handles sending messages via Whatsapp
"""
import os

import logging

import requests

from fastapi import HTTPException

from services.chat import generate_response


WHATSAPP_API_VERSION = "v18.0"
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


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
        logging.error("Timeout occurred while sending message")
        raise HTTPException(status_code=408, detail="Request timed out")

    except requests.RequestException as e:  # This will catch any general request exception
        logging.error(f"Request failed due to: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")

    else:
        # Process the response as normal
        log_http_response(response)
        return response

def process_whatsapp_message(body):
    """
    Extract fields from request body, generate response, and send reply
    """
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

    message_body = body["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"]

    response = generate_response(message_body, wa_id, name)

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