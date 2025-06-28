# Content Converter & GraphRAG & Doc Generator

This project provides three main functionalities:

1.  **Content Converter:** Converts Confluence pages and Jira issues into Markdown files.
2.  **GraphRAG:** Builds a knowledge graph from the generated Markdown files and allows you to query it.
3.  **Product Doc Generator:** Uses an LLM to generate a product introduction document from a selection of Markdown files.

## Prerequisites

- Python 3.x
- A Confluence account with API token access
- A Jira account with API token access
- Access to an OpenAI-compatible LLM API

## Setup

1.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Download NLP model (for GraphRAG):**

    ```bash
    python -m spacy download en_core_web_sm
    ```

3.  **Configure the Content Converter:**

    Open `content_converter.py` and fill in your Confluence and Jira credentials.

4.  **Configure the Product Doc Generator:**

    -   Open `product_doc_generator.py` and set the `API_BASE_URL` and `MODEL_NAME` for your LLM.
    -   Set your API key as an environment variable:
        ```bash
        export OPENAI_API_KEY='your_api_key_here'
        ```

## Usage

### 1. Content Converter

-   Run `python content_converter.py` to fetch and convert your documents into Markdown files, which will be saved in the `markdown_pages` directory.

### 2. GraphRAG

-   Run `python graph_rag.py` to build and query a knowledge graph from your Markdown files.

### 3. Product Doc Generator

-   Once you have generated your Markdown files, run the following command:

    ```bash
    python product_doc_generator.py
    ```

-   The script will list all available Markdown files and prompt you to select which ones to include.
-   Enter the numbers of the files you want to include, separated by commas.
-   The generated document will be saved as `product_introduction.md`.
