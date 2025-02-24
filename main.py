import logging

from dotenv import load_dotenv

from fastapi import FastAPI, Request

from pydantic import BaseModel

from services.chat import generate_response

from routes.webhook import router


def create_app():
    # ensure env is loaded
    load_dotenv()

    # set logging config
    logging.basicConfig(
        level=logging.INFO
    )

    app = FastAPI()

    app.include_router(router)

    return app

app = create_app()


@app.get("/")
def hello_world():
    return "Hello World"


class ChatRequestBody(BaseModel):
    """
    Defines the expected body of the below /chat endpoint
    """
    message: str

    # customer name
    name: str | None = None

    # unique customer id for storage of Thread in DynamoDB
    # if not provided, client ip address will be used
    customer_id: str | None = None

# this route is for regular chat messages sent from anywhere other than Whatsapp, e.g. the Laurus Education website
@app.post("/chat")
def chat(
    body: ChatRequestBody,
    request: Request
):
    if body.customer_id:
        _id = body.customer_id
    else:
        _id = request.client.host

    response = generate_response(body.message, _id, body.name)

    return {
        "message": response
    }
