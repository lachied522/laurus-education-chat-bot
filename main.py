from dotenv import load_dotenv

from fastapi import FastAPI


# ensure env is loaded
load_dotenv()

app = FastAPI()

@app.get("/")
def hello_world():

    return "Hello World"
