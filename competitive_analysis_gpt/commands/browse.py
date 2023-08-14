from bs4 import BeautifulSoup
import requests
import html2text
from duckduckgo_search import DDGS
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

from urllib.parse import urlparse
from competitive_analysis_gpt.llm_util import chat_completion_request, GPT35
from bs4 import NavigableString


def get_domain(url):
    result = urlparse(url)
    domain = result.netloc
    if domain.startswith("www."):
        domain = domain[4:]
    domain_name = domain.split(".")[0]
    return domain_name


def get_description_from_iframe_url(iframe_url):
    print(f"Fetching URL for Iframe {iframe_url}")
    response = requests.get(iframe_url)
    if response.status_code != 200:
        print(f"Failed to fetch URL for Iframe {iframe_url}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    # Locate the description or other content you want to extract
    # (this will depend on the specific structure of the target page)
    description_tag = soup.find("meta", attrs={"name": "description"})
    if description_tag and description_tag.get("content"):
        return description_tag.get("content")

    # return domain name without the tld
    return get_domain(iframe_url)


def clean_markdown(content):
    system_prompt = """
    # HTMLMarkdownGPT
    
    # Role 
    You carefully provide accurate, factual, thoughtful, nuanced responses, and are brilliant at reasoning.
    
    ## Instructions
    1. Take rough html markdown content and reduce it to the most important content while adding markdown structure where possible
    2. Remove irrelevant links that don't seem to be relevant to the main content
    3. Remove all irrelevant content such as ads
    4. Remove all repetitive content
    5. Add header sections and lists and bolding whenever appropriate to make it easier to read
    6. Return the cleaned markdown content
    """
    params = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ],
        "model": GPT35,
    }
    response = chat_completion_request(**params)
    full_message = response["choices"][0]["message"]["content"]
    return full_message


def collapse_single_child_divs(tag):
    # List to hold div tags to be replaced
    to_replace = []

    # Collect div tags with a single div child
    for div_tag in tag.find_all("div", recursive=True):
        if div_tag.div and len(list(div_tag.children)) == 1:
            to_replace.append(div_tag)

    # Replace collected div tags with their single div child
    for div_tag in to_replace:
        div_tag.replace_with(div_tag.div)


def scrape_and_convert_to_markdown(url, smart_mode=False):
    # make url whole
    if not url.startswith("http"):
        url = "http://" + url
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code != 200:
        print(f"Failed to fetch URL {url}")
        return f"Failed to fetch URL {url}"

    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup.find_all(["style", "script"]):
        tag.decompose()

    # Remove all image tags or links
    for img_tag in soup.find_all("img"):
        img_tag.decompose()

    iframes = soup.find_all("iframe")

    for iframe in iframes:
        # Get the src attribute from the iframe tag
        src = iframe.get("src")

        # Replace the iframe tag with a Markdown link to the URL
        if src:
            description = get_description_from_iframe_url(src)
            iframe_link = f"[Iframe Link: {src}]({src})"
            if description:
                iframe_link += f" - Description: {description}"
            iframe.replace_with(iframe_link)

    # Using html2text to convert HTML to Markdown
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    markdown = converter.handle(str(soup.body))

    if smart_mode:
        print("Cleaning markdown")
        return clean_markdown(markdown)
    return markdown


def get_youtube_transcript(url):
    """
    First retrive the youtube id and then use the youtube transcript api.
    Example urls:
    https://www.youtube.com/embed/ET822mQtO0I?rel=0&controls=1&autoplay=1&mute=1&start=0
    https://www.youtube.com/watch?v=0WGNnd3oe3Q
    """
    if "youtube.com/embed/" in url:
        youtube_id = url.split("youtube.com/embed/")[1].split("?")[0]
    elif "youtube.com/watch?v=" in url:
        youtube_id = url.split("youtube.com/watch?v=")[1].split("&")[0]
    else:
        print("Could not find youtube id in url")
        return

    try:
        transcript = YouTubeTranscriptApi.get_transcript(youtube_id)
    except Exception as e:
        print("Could not get transcript for youtube id", youtube_id)
        print(e)
        return
    text = TextFormatter().format_transcript(transcript)
    return text


def search_urls_and_preview(keywords, limit=None):
    num_results = 0
    with DDGS(timeout=20) as ddgs:
        for r in ddgs.text(keywords):
            yield r
            num_results += 1
            if limit and num_results >= limit:
                break
