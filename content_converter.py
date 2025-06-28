import os
import re
from atlassian import Confluence
from jira import JIRA
from markdownify import markdownify as md
from jira2markdown import convert as jira_convert

# --- Configuration ---
# Confluence
CONFLUENCE_URL = "YOUR_CONFLUENCE_URL"  # e.g., "https://your-domain.atlassian.net/wiki"
CONFLUENCE_USERNAME = "YOUR_EMAIL"
CONFLUENCE_API_TOKEN = "YOUR_API_TOKEN"
SPACE_KEY = "YOUR_SPACE_KEY"

# Jira
JIRA_URL = "YOUR_JIRA_URL" # e.g., "https://your-domain.atlassian.net"
JIRA_USERNAME = "YOUR_EMAIL"
JIRA_API_TOKEN = "YOUR_API_TOKEN"


OUTPUT_DIR = "markdown_pages"
URL_FILE = "urls.txt"

# --- Functions ---

def get_confluence_instance():
    """Initializes and returns a Confluence instance."""
    return Confluence(
        url=CONFLUENCE_URL,
        username=CONFLUENCE_USERNAME,
        password=CONFLUENCE_API_TOKEN
    )

def get_jira_instance():
    """Initializes and returns a Jira instance."""
    return JIRA(
        server=JIRA_URL,
        basic_auth=(JIRA_USERNAME, JIRA_API_TOKEN)
    )

def get_urls_from_file(filename):
    """Reads a list of URLs from a text file."""
    if not os.path.exists(filename):
        return []
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def get_url_type(url):
    """Determines if a URL is for Confluence or Jira."""
    if "/wiki/" in url:
        return "confluence"
    elif "/browse/" in url:
        return "jira"
    return "unknown"

def get_page_id_from_url(url):
    """Extracts the page ID from a Confluence page URL."""
    match = re.search(r'/pages/(\d+)', url)
    if match:
        return match.group(1)
    return None

def get_issue_key_from_url(url):
    """Extracts the issue key from a Jira URL."""
    match = re.search(r'/browse/([A-Z]+-\d+)', url)
    if match:
        return match.group(1)
    return None

def get_all_pages_from_space(confluence, space_key):
    """Fetches all pages from a given Confluence space."""
    start = 0
    limit = 50
    all_pages = []

    while True:
        pages = confluence.get_all_pages_from_space(space_key, start=start, limit=limit, expand='body.storage')
        if not pages:
            break
        all_pages.extend(pages)
        start += limit

    return all_pages

def convert_html_to_markdown(html_content):
    """Converts HTML content to Markdown."""
    return md(html_content)

def save_confluence_page_as_markdown(page):
    """Saves a Confluence page as a Markdown file."""
    title = page['title']
    content_html = page['body']['storage']['value']
    content_markdown = convert_html_to_markdown(content_html)

    # Create a filename-safe version of the title
    filename = "".join(c for c in title if c.isalnum() or c in (' ', '_')).rstrip()
    filepath = os.path.join(OUTPUT_DIR, f"CONFLUENCE-{filename}.md")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content_markdown)

    print(f"Saved Confluence page: {title} -> {filepath}")

def save_jira_issue_as_markdown(issue):
    """Saves a Jira issue as a Markdown file."""
    title = issue.fields.summary
    key = issue.key
    description = issue.fields.description or ""
    comments = issue.fields.comment.comments or []

    content_markdown = f"# {key}: {title}\n\n"
    content_markdown += "## Description\n\n"
    content_markdown += jira_convert(description)
    content_markdown += "\n\n"

    if comments:
        content_markdown += "## Comments\n\n"
        for comment in comments:
            author = comment.author.displayName
            body = jira_convert(comment.body)
            content_markdown += f"**{author}**:\n\n{body}\n\n---\n\n"

    # Create a filename-safe version of the title
    filename = "".join(c for c in title if c.isalnum() or c in (' ', '_')).rstrip()
    filepath = os.path.join(OUTPUT_DIR, f"JIRA-{key}-{filename}.md")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content_markdown)

    print(f"Saved Jira issue: {key} -> {filepath}")


def main():
    """Main function to run the script."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    page_urls = get_urls_from_file(URL_FILE)

    if page_urls:
        confluence = None
        jira = None

        for url in page_urls:
            url_type = get_url_type(url)

            if url_type == "confluence":
                if not confluence:
                    confluence = get_confluence_instance()
                page_id = get_page_id_from_url(url)
                if page_id:
                    try:
                        page = confluence.get_page_by_id(page_id, expand='body.storage')
                        save_confluence_page_as_markdown(page)
                    except Exception as e:
                        print(f"Could not fetch Confluence page with ID {page_id}. Error: {e}")
                else:
                    print(f"Could not extract page ID from URL: {url}")

            elif url_type == "jira":
                if not jira:
                    jira = get_jira_instance()
                issue_key = get_issue_key_from_url(url)
                if issue_key:
                    try:
                        issue = jira.issue(issue_key)
                        save_jira_issue_as_markdown(issue)
                    except Exception as e:
                        print(f"Could not fetch Jira issue with key {issue_key}. Error: {e}")
                else:
                    print(f"Could not extract issue key from URL: {url}")
            else:
                print(f"Unknown URL type: {url}")

    else:
        # Fallback to fetching all pages from a Confluence space
        confluence = get_confluence_instance()
        pages = get_all_pages_from_space(confluence, SPACE_KEY)
        for page in pages:
            save_confluence_page_as_markdown(page)

    print("\nConversion complete!")

if __name__ == "__main__":
    main()