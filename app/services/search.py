"""
This module handles searching of the knowledge base using Google Custom Search Engine
"""
import os

import logging

import json

import requests

from openai import OpenAI

from googleapiclient.discovery import build

from bs4 import BeautifulSoup


# Define constants
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

logger = logging.getLogger()


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
        model="gpt-4o", # must use gpt-4o for the context window
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


def scrape_webpages(
    results: list[dict],
    # Maximum characters to be returned. If too long, results will not fit inside gpt-4o context window plus function will run too long
    max_length = 30_000,
):
    """
    Returns text content of pages return by Google Search query
    """

    # Keep track of total length
    total_length = 0

    scraped_results = []

    for item in results:
        url = item["link"]

        text = scrape(url)

        length = len(text)

        should_break = False
        # Truncate text to fit inside maximum context window if necessary
        if total_length + length > 0.95 * max_length:
            text = text[:max_length - total_length]
            should_break = True

        scraped_results.append({
            "title": item["title"],
            "url": url,
            "text": text,
        })

        total_length += length

        if should_break:
            break

    return scraped_results


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

    logger.debug("Searched: ", query, "\n", "Got: ", summary)

    return summary
