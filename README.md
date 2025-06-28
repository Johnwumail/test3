# Content Converter & GraphRAG & Doc Generator & Automated Procedure Executor

This project provides four main functionalities:

1.  **Content Converter:** Converts Confluence pages and Jira issues into Markdown files.
2.  **GraphRAG:** Builds a knowledge graph from the generated Markdown files and allows you to query it.
3.  **Product Doc Generator:** Uses an LLM to generate a product introduction document from a selection of Markdown files.
4.  **Automated Procedure Executor:** Guides you through a step-by-step procedure, records your screen and audio, and attempts to automate browser and CLI actions using an LLM.

## Prerequisites

- Python 3.x
- A Confluence account with API token access
- A Jira account with API token access
- Access to an OpenAI-compatible LLM API
- **ffmpeg** installed on your system (for Procedure Executor)

## Setup

1.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Download NLP model (for GraphRAG):**

    ```bash
    python -m spacy download en_core_web_sm
    ```

3.  **Install Playwright browsers (for Automated Procedure Executor):**

    ```bash
    playwright install
    ```

4.  **Configure the Content Converter:**

    Open `content_converter.py` and fill in your Confluence and Jira credentials.

5.  **Configure the Product Doc Generator:**

    -   Open `product_doc_generator.py` and set the `API_BASE_URL` and `MODEL_NAME` for your LLM.
    -   Set your API key as an environment variable:
        ```bash
        export OPENAI_API_KEY='your_api_key_here'
        ```

6.  **Configure the Automated Procedure Executor:**

    -   Open `automated_procedure_executor.py` and set the `API_BASE_URL` and `MODEL_NAME` for your LLM.
    -   Ensure your `OPENAI_API_KEY` environment variable is set.

## Usage

### 1. Content Converter

-   Run `python content_converter.py` to fetch and convert your documents into Markdown files, which will be saved in the `markdown_pages` directory.

### 2. GraphRAG

-   Run `python graph_rag.py` to build and query a knowledge graph from your Markdown files.

### 3. Product Doc Generator

-   Run `python product_doc_generator.py`.
-   The script will list all available Markdown files and prompt you to select which ones to include.
-   Enter the numbers of the files you want to include, separated by commas.
-   The generated document will be saved as `product_introduction.md`.

### 4. Automated Procedure Executor

-   **Prepare your procedure:** Create a text file (e.g., `my_procedure.txt`) where each line is a single step of the operation.
    -   See `procedure_example.txt` for an example of browser and CLI steps.
    -   The LLM can now also generate `python_script` actions. For these, the `value` will be a Python code snippet that has access to the Playwright `page` object. For example, a step like "Extract the title of the current page and print it" could lead the LLM to generate `action_type: "python_script", value: "print(await page.title())"`. 
-   **Audio Configuration (Linux):** The script uses `ffmpeg` with `alsa` for audio input (`-f alsa -i default`). You might need to adjust `default` to your specific audio input device (e.g., `hw:0,0` or a PulseAudio source name). You can list PulseAudio sources with `pactl list short sources`.
-   **Run the script:**

    ```bash
    python automated_procedure_executor.py
    ```

-   The script will prompt you for the path to your procedure file.
-   It will then start recording your screen and audio, and attempt to automate each step using the configured LLM, Playwright, and CLI. Manual intervention will be requested if the LLM cannot determine an action or if an automated action fails.
-   Upon completion, a video (`operation_video.mp4`) and a log file (`procedure_log.json`) will be saved in the current directory.