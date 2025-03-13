"""
This module defines the route that will receive and respond to Whatsapp messages
"""
import os 

from typing import Dict, Any

import logging

from fastapi import APIRouter, Request, HTTPException

from services.whatsapp import process_whatsapp_message


WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")

router = APIRouter()

logger = logging.getLogger()

def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )


def is_status_update(body):
    return (
        body.get("entry", [{}])[0]
        .get("changes", [{}])[0]
        .get("value", {})
        .get("statuses")
    )


@router.get("/webhook")
def get_webhook(
    request: Request,
):
    """
    This endpoint is for Whatsapp to verify the application's webhook
    """
    # parse params from the webhook verification request
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode and token:
        # check the mode and token sent are correct
        if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
            logger.info("WEBHOOK_VERIFIED")
            # must return challenge from the body as an int type
            return int(challenge)
        else:
            logger.info("VERIFICATION_FAILED")
            raise HTTPException(status_code=403, detail="Verification failed")
    else:
        logger.info("MISSING_PARAMETER")
        raise HTTPException(status_code=400, detail="Missing parameters")


@router.post(
    "/webhook",
    status_code = 200 # Whatsapp will ping this endpoint until it receives a 200 status code
)
def post_webhook(
    body: Dict[str, Any],
):
    if is_status_update(body):
        logger.info("Received a WhatsApp status update")
        return "OK"

    if is_valid_whatsapp_message(body):
        try:
            process_whatsapp_message(body)

            return "OK"

        except Exception as e:
            logger.error("Could not process message: ", e)
            raise e

    else:
        raise HTTPException(status_code=400, detail="Not a valid request")
