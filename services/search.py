"""
This module handles searching of the knowledge base using Google Custom Search Engine
"""
import os

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

        return res["data"][0]["embedding"]
    except Exception as e:
        print(f"Could not get embedding for {text}: ", e)
        return None


def clean_soup(soup: BeautifulSoup):
    # remove all script and style elements
    for script in soup(["script", "style", "a", "header", "footer", "nav"]):
        script.extract()

    # extract text
    text = soup.get_text()

    return text


def split_and_group_text(text: str, min_group_size: int = 50):
    # split text into paragraphs
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    # group paragraphs with neighbours into chunks of reasonable size
    grouped_paragraphs = []
    
    curr = paragraphs[0]

    for paragraph in paragraphs[1:]:
        if len(curr.split(" ")) + len(paragraph.split(" ")) < min_group_size:
            curr += " " + paragraph
        else:
            grouped_paragraphs.append(curr)
            curr = paragraph

    if curr:
        grouped_paragraphs.append(curr)
    
    return grouped_paragraphs


def scrape(url):
    try:
        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')

        return clean_soup(soup)

        # break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines() if len(line)>128)
        # break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        #split text into chunks of 400 words
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1200,
            chunk_overlap=20
        )
        docs = text_splitter.split_text(text)
        return [{"text": s, "url": url} for s in docs]
    except Exception as e:
        return None


def scrape_webpages(result: dict):
    """
    Returns text content of pages return by Google Search query
    """

    scraped_results = []

    for item in result["items"]:
        url = item["link"]

        text = scrape(url)

        print(text)

        if text is not None:
            text_groups = split_and_group_text(text)

            for group in text_groups:
                scraped_results.append({
                    "url": url,
                    "text": group,
                })

        break

    print("scraped_results", scraped_results)

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

    return sorted(chunks, key=lambda x: cosine_similarity(x["embedding"], query_embedding), reverse=True)[:n]


def conduct_search(query: str):
    # see Custom Search Engine docs below
    # https://google-api-client-libraries.appspot.com/documentation/customsearch/v1/python/latest/customsearch_v1.cse.html

    resource = build("customsearch", "v1", developerKey=GOOGLE_API_KEY).cse()
    result = resource.list(q=query, cx=GOOGLE_CSE_ID).execute()

    return result


def search_tool(
    query: str
):
    """
    This is the tool the AI Assistant will use to search webpages to answer user's enquiry
    """
    search_results = conduct_search(query)

    scraped_results = scrape_webpages(search_results)

    print(scraped_results)

    # return conduct_text_similarity_search(query, scraped_results)

if __name__ == "__main__":

    print(search_tool("What is Laurus Education"))