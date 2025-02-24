"""
This module handles searching of the knowledge base using Google Custom Search Engine
"""
import os

import json

import requests

from openai import OpenAI

from googleapiclient.discovery import build

from bs4 import BeautifulSoup

import numpy as np

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")


def get_embedding(
    text: str,
    openai_client: OpenAI = OpenAI()
):
    if len(text) == 0:
            return None

    try:
        res = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=[text],
            encoding_format="float"
        )

        return res.data[0].embedding
    except Exception as e:
        print(f"Could not get embedding for {text}: ", e)
        return None


def summarise_search_results(
    query: str,
    search_results: list[dict],
    client: OpenAI = OpenAI(),
) -> str:
    system = (
        "You are part of a team of customer service assistants for Laurus Education, a provider of educational programs to Australian and international students. "
        + "You will receive a query from another team member which has been used to search Laurus Education's affiliated web sites for information. "
        + "Your job is to summarise the raw search results tp answer the incoming query. "
        + "If the answer to the query is not apparent from the search results you should say so. "
        + "You should also provide a url that the team member should go to for more information."
        + "Do not use markdown, respond with text only."
    )

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "developer",
                "content": system
            },
            {
                "role": "user",
                "content": (
                    f"Query: {query}\n\nSearch results:{json.dumps(search_results)}"
                )
            }
        ]
    )

    return completion.choices[0].message.content


def clean_soup(soup: BeautifulSoup):
    # remove all script, style, header and fotter elements
    for script in soup(["script", "style", "a", "header", "footer", "nav"]):
        script.extract()

    # extract text
    text = soup.get_text()

    # remove unnecessary line breaks and return as string
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    return "\n".join(paragraphs)


def scrape(url):
    try:
        html = requests.get(url).text
        soup = BeautifulSoup(html, "html.parser")

        return clean_soup(soup)
    except Exception as e:
        print(e)
        return None


def scrape_webpages(results: list[dict]):
    """
    Returns text content of pages return by Google Search query
    """

    scraped_results = []

    for item in results:
        url = item["link"]

        text = scrape(url)

        scraped_results.append({
            "title": item["title"],
            "url": url,
            "text": text,
        })

    return scraped_results


def cosine_similarity(a, b):
    """
    Cosine similarity function for text similarity search
    """
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def conduct_text_similarity_search(
    query: str,
    chunks: list[dict], # list of results from "search" function
    n: int = 10 # number of chunks to return
):
    """
    Returns n closest chunks
    """
    chunks_with_embedding = []

    for chunk in chunks:
        embedding = get_embedding(chunk["text"])

        if embedding is not None:
            chunks_with_embedding.append({
                "url": chunk["url"],
                "text": chunk["text"],
                "embedding": embedding
            })

    query_embedding = get_embedding(query)

    sorted_chunks = sorted(chunks_with_embedding, key=lambda x: cosine_similarity(x["embedding"], query_embedding), reverse=True)

    return sorted_chunks[:n]


def conduct_search(
    query: str,
    site: str | None = None, # limit results to specific site
    num: int = 3, # number search results to return
) -> list[dict]:
    # see Custom Search Engine docs below
    # https://google-api-client-libraries.appspot.com/documentation/customsearch/v1/python/latest/customsearch_v1.cse.html

    resource = build("customsearch", "v1", developerKey=GOOGLE_API_KEY).cse()
    result = resource.list(q=query, num=num, siteSearch=site, cx=GOOGLE_CSE_ID).execute()

    return result["items"][:num]


def search_tool(
    query: str
):
    """
    This is the tool the AI Assistant will use to search webpages to answer user's enquiry
    """
    search_results = conduct_search(query)

    scraped_results = scrape_webpages(search_results)

    summary = summarise_search_results(query, scraped_results)

    return summary

if __name__ == "__main__":

    print(search_tool("What is Laurus Education"))