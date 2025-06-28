
import os
from openai import OpenAI

# --- Configuration ---
# OpenAI-Compatible API Settings
# IMPORTANT: Set your environment variables for the API key.
# For example, export OPENAI_API_KEY='your_api_key_here'
# The base_url should be the endpoint of your self-hosted or custom model.
API_BASE_URL = "YOUR_API_BASE_URL"  # e.g., "http://localhost:1234/v1"
API_KEY = os.getenv("OPENAI_API_KEY", "your_api_key_if_not_in_env")
MODEL_NAME = "your_model_name"  # e.g., "local-model"

# --- File Configuration ---
MARKDOWN_DIR = "markdown_pages"
OUTPUT_FILE = "product_introduction.md"

# --- Functions ---

def select_and_read_markdown_files():
    """Lists available Markdown files and prompts the user to select which ones to include."""
    files = [f for f in os.listdir(MARKDOWN_DIR) if f.endswith(".md")]
    if not files:
        print(f"No Markdown files found in the '{MARKDOWN_DIR}' directory.")
        return None

    print("Please select the files to include in the document:")
    for i, filename in enumerate(files):
        print(f"  {i + 1}: {filename}")

    print("\nEnter the numbers of the files you want to include, separated by commas (e.g., 1, 3, 4).")
    selected_indices_str = input("> ")

    try:
        selected_indices = [int(i.strip()) - 1 for i in selected_indices_str.split(',')]
    except ValueError:
        print("Invalid input. Please enter numbers separated by commas.")
        return None

    consolidated_content = ""
    for i in selected_indices:
        if 0 <= i < len(files):
            filename = files[i]
            filepath = os.path.join(MARKDOWN_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                consolidated_content += f"--- Start of {filename} ---\n\n"
                consolidated_content += f.read()
                consolidated_content += f"\n\n--- End of {filename} ---\n\n"
        else:
            print(f"Warning: Index {i + 1} is out of range and will be ignored.")

    return consolidated_content

def generate_product_document(content):
    """Connects to the LLM and generates the product introduction document."""
    if not API_KEY or API_KEY == "your_api_key_if_not_in_env":
        print("Error: API key is not set. Please set the OPENAI_API_KEY environment variable.")
        return None

    if not API_BASE_URL or API_BASE_URL == "YOUR_API_BASE_URL":
        print("Error: API base URL is not set. Please configure API_BASE_URL in the script.")
        return None

    client = OpenAI(
        base_url=API_BASE_URL,
        api_key=API_KEY,
    )

    system_prompt = (
        "You are an expert technical writer tasked with creating a product introduction document for a service team. "
        "Your audience is familiar with technical concepts but needs a clear, concise overview of the specific product features provided. "
        "The document should focus on two key areas: the selected product features and their operational procedures. "
        "Structure the document logically, starting with a high-level overview, then detailing each feature and its corresponding step-by-step instructions."
    )

    user_prompt = (
        "Based on the following collection of documents, please generate a comprehensive product introduction for the selected features. "
        "The documents contain information about various product features and how to use them. "
        "Synthesize this information into a single, well-organized document suitable for the service team.\n\n" 
        f"Here is the content:\n\n{content}"
    )

    print("Sending request to the LLM. This may take a moment...")

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred while communicating with the LLM: {e}")
        return None

def save_document(content):
    """Saves the generated content to the output file."""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Product introduction document saved to {OUTPUT_FILE}")

def main():
    """Main function to run the script."""
    print("Starting the product document generation process...")
    markdown_content = select_and_read_markdown_files()

    if not markdown_content:
        print("No content was selected or an error occurred. Aborting.")
        return

    generated_doc = generate_product_document(markdown_content)

    if generated_doc:
        save_document(generated_doc)
        print("Process completed successfully.")
    else:
        print("Failed to generate the document.")

if __name__ == "__main__":
    main()
