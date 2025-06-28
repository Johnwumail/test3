import os
import subprocess
import time
import sys
import json
import asyncio
from openai import OpenAI
from playwright.async_api import async_playwright

# --- Configuration ---
VIDEO_FILENAME = "operation_video.mp4"
LOG_FILENAME = "procedure_log.json"

# OpenAI-Compatible API Settings
API_BASE_URL = "YOUR_API_BASE_URL"  # e.g., "http://localhost:1234/v1"
API_KEY = os.getenv("OPENAI_API_KEY", "your_api_key_if_not_in_env")
MODEL_NAME = "your_model_name"  # e.g., "local-model"

# --- Functions ---

def check_ffmpeg_installed():
    """Checks if ffmpeg is installed and in the system's PATH."""
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: ffmpeg is not installed or not found in your system's PATH.")
        print("Please install ffmpeg to use this script. (e.g., 'sudo apt-get install ffmpeg')")
        return False

def get_procedure_from_file(filepath):
    """Reads the procedure steps from a text file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: The file '{filepath}' was not found.")
        return None

async def get_llm_action(step_description, current_html_content=None):
    """
    Asks the LLM to determine the action for a given step.
    Expected LLM output format (JSON):
    {
        "action_type": "browser_goto" | "browser_click" | "browser_fill" | "cli_command" | "user_confirm" | "python_script",
        "value": "url" | "selector" | "command" | "text_to_fill" | "message" | "python_code",
        "selector_type": "css" | "xpath" | "text" (optional, for browser actions)
    }
    """
    if not API_KEY or API_KEY == "your_api_key_if_not_in_env":
        print("Error: API key is not set. Please set the OPENAI_API_KEY environment variable.")
        return {"action_type": "user_confirm", "value": "API key not set."}

    if not API_BASE_URL or API_BASE_URL == "YOUR_API_BASE_URL":
        print("Error: API base URL is not set. Please configure API_BASE_URL in the script.")
        return {"action_type": "user_confirm", "value": "API base URL not set."}

    client = OpenAI(
        base_url=API_BASE_URL,
        api_key=API_KEY,
    )

    system_prompt = """You are an intelligent agent designed to interpret procedural steps and determine the best action to take. Your responses must be in JSON format. Possible action_types are: 'browser_goto', 'browser_click', 'browser_fill', 'cli_command', 'user_confirm', 'python_script', 'browser_screenshot'.
For 'browser_goto', 'value' is the URL.
For 'browser_click', 'value' is the selector (CSS or XPath) and 'selector_type' is 'css' or 'xpath'.
For 'browser_fill', 'value' is the text to fill, and 'selector' is the input field selector.
For 'cli_command', 'value' is the exact shell command to execute.
For 'user_confirm', 'value' is a message to display to the user, indicating manual intervention is needed.
For 'python_script', 'value' is a Python code snippet that will be executed. This snippet will have access to the 'page' object (Playwright Page). Use 'await page.' for Playwright operations.
For 'browser_screenshot', 'value' is the filename (e.g., 'screenshot_step_1.png') where the screenshot should be saved.
If current HTML content is provided, use it to determine the most accurate selectors for browser actions.
Always provide a 'value' field. If a selector is needed, also provide 'selector_type'."""

    user_prompt = f"Given the following step, what action should be taken? Step: \"{step_description}\""
    if current_html_content:
        user_prompt += f"\n\nCurrent HTML content:\n\n```html\n{current_html_content[:5000]}\n```\n(Truncated to 5000 characters)"

    print(f"LLM: Analyzing step: \"{step_description}\"...")
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.0, # Keep temperature low for deterministic actions
            response_format={"type": "json_object"}
        )
        llm_output = response.choices[0].message.content
        print(f"LLM Raw Output: {llm_output}")
        return json.loads(llm_output)
    except json.JSONDecodeError as e:
        print(f"LLM returned invalid JSON: {llm_output}. Error: {e}")
        return {"action_type": "user_confirm", "value": f"LLM JSON error: {e}"}
    except Exception as e:
        print(f"An error occurred with LLM communication: {e}")
        return {"action_type": "user_confirm", "value": f"LLM communication error: {e}"}

async def perform_browser_action(page, action):
    """Performs a browser action using Playwright."""
    action_type = action.get("action_type")
    value = action.get("value")
    selector = action.get("selector")
    selector_type = action.get("selector_type", "css") # Default to css

    try:
        if action_type == "browser_goto":
            print(f"Browser: Navigating to {value}")
            await page.goto(value)
        elif action_type == "browser_click":
            print(f"Browser: Clicking on {value} (type: {selector_type})")
            if selector_type == "css":
                await page.click(value)
            elif selector_type == "xpath":
                await page.click(f"xpath={value}")
            else:
                raise ValueError(f"Unsupported selector type: {selector_type}")
        elif action_type == "browser_fill":
            print(f"Browser: Filling '{value}' into {selector}")
            await page.fill(selector, value)
        else:
            print(f"Browser: Unknown action type {action_type}. Requires user confirmation.")
            return False # Indicate failure, requires user confirm
        return True
    except Exception as e:
        print(f"Browser action failed: {e}")
        return False # Indicate failure

async def perform_browser_screenshot(page, filename):
    """Takes a screenshot of the current browser page."""
    print(f"Browser: Taking screenshot and saving to {filename}")
    try:
        await page.screenshot(path=filename)
        return True
    except Exception as e:
        print(f"Failed to take screenshot: {e}")
        return False

async def perform_cli_action(command):
    """Executes a CLI command and returns its output."""
    print(f"CLI: Executing command: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        print(f"CLI Output:\n{result.stdout}")
        if result.stderr:
            print(f"CLI Error Output:\n{result.stderr}")
        return True, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        print(f"CLI command failed with error: {e}")
        print(f"Stderr: {e.stderr}")
        return False, e.stdout, e.stderr
    except Exception as e:
        print(f"An error occurred during CLI execution: {e}")
        return False, "", str(e)

async def execute_python_script(page, script_code):
    """Executes a Python script with access to the Playwright page object."""
    print(f"Executing Python script:\n---\n{script_code}\n---")
    try:
        # Create a local dictionary to serve as the execution environment
        # This makes 'page' available within the script_code
        local_vars = {"page": page, "asyncio": asyncio}
        # Execute the script. Use exec() for multi-line code.
        # Wrap in an async function and await it if it contains await calls.
        exec_code = f"async def _temp_script_func():\n{script_code}"
        exec(exec_code, globals(), local_vars)
        await local_vars['_temp_script_func']()
        print("Python script executed successfully.")
        return True
    except Exception as e:
        print(f"Error executing Python script: {e}")
        return False

async def record_procedure(steps):
    """Guides the user through the procedure, records screen, and logs timings."""
    print("\nStarting screen recording...")
    for i in range(3, 0, -1):
        print(f"Recording starts in {i}...")
        time.sleep(1)

    # Command to start ffmpeg recording. Adjust parameters as needed.
    ffmpeg_command = [
        'ffmpeg',
        '-y',  # Overwrite output file if it exists
        '-f', 'x11grab',
        '-s', '1920x1080', # Adjust resolution to your screen size
        '-i', ':0.0',
        '-f', 'alsa', # Input format for audio (ALSA for Linux)
        '-i', 'default', # Audio input device (e.g., 'default', 'hw:0,0', or PulseAudio source)
        '-c:v', 'libx264',
        '-r', '30', # Video frame rate
        '-c:a', 'aac', # Audio codec
        '-strict', 'experimental', # Needed for aac in some ffmpeg versions
        '-b:a', '128k', # Audio bitrate
        VIDEO_FILENAME
    ]
    # NOTE: For audio, you might need to adjust '-f alsa -i default' based on your system.
    # On some systems, PulseAudio sources might be 'pactl list short sources' or similar.
    # For example, for PulseAudio, you might use '-f pulse -i default' or '-f pulse -i <source_name>'
    # You can test audio input with: ffmpeg -f alsa -i default -t 10 test_audio.wav

    recorder_process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("Recording started! Follow the steps below.")

    log_entries = []
    procedure_start_time = time.time()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # Set headless=True for no visible browser UI
        page = await browser.new_page()

        for i, step in enumerate(steps):
            print(f"\n--- Step {i + 1} of {len(steps)} ---")
            print(f">>> {step}")

            step_start_time = time.time() - procedure_start_time # Time relative to procedure start

            current_html = None
            # Only fetch HTML if the action is likely to be browser-related
            # This avoids unnecessary calls for CLI or user_confirm steps
            if any(keyword in step.lower() for keyword in ["browser", "web", "page", "click", "fill", "navigate", "screenshot"]):
                try:
                    current_html = await page.content()
                except Exception as e:
                    print(f"Warning: Could not get page content: {e}")
                    current_html = ""

            action = await get_llm_action(step, current_html_content=current_html)
            action_type = action.get("action_type")
            action_value = action.get("value")

            step_success = False
            if action_type.startswith("browser_") and action_type != "browser_screenshot":
                step_success = await perform_browser_action(page, action)
            elif action_type == "browser_screenshot":
                screenshot_filename = os.path.join("screenshots", action_value) # Save screenshots to a subfolder
                os.makedirs("screenshots", exist_ok=True)
                step_success = await perform_browser_screenshot(page, screenshot_filename)
            elif action_type == "cli_command":
                step_success, cli_stdout, cli_stderr = await perform_cli_action(action_value)
            elif action_type == "python_script":
                step_success = await execute_python_script(page, action_value)
            elif action_type == "user_confirm":
                print(f"Manual intervention required: {action_value}")
                input("Press Enter to confirm you have completed this step manually...")
                step_success = True # Assume user confirmed
            else:
                print(f"Unknown action type from LLM: {action_type}. Requires user confirmation.")
                input("Press Enter to confirm you have completed this step manually...")
                step_success = True

            if not step_success:
                print(f"Action for step '{step}' failed or required manual intervention. Please review.")
                input("Press Enter to continue to the next step (or Ctrl+C to abort)...")

            step_end_time = time.time() - procedure_start_time # Time relative to procedure start
            log_entries.append({
                "step": step,
                "action_type": action_type,
                "action_value": action_value,
                "start_time_seconds": round(step_start_time, 2),
                "end_time_seconds": round(step_end_time, 2),
                "success": step_success
            })

        await browser.close()

    print("\nProcedure complete. Stopping the recording...")
    # Send 'q' to ffmpeg stdin to stop it gracefully
    recorder_process.communicate(input=b'q')
    time.sleep(2) # Give ffmpeg a moment to finalize the file

    return log_entries

def save_log_file(log_entries):
    """Saves the procedure steps and timings to a JSON file."""
    with open(LOG_FILENAME, 'w', encoding='utf-8') as f:
        json.dump(log_entries, f, indent=4)

    print(f"Log file saved to {LOG_FILENAME}")

def main():
    """Main function to run the script."""
    if not check_ffmpeg_installed():
        sys.exit(1)

    procedure_file = input("Enter the path to your procedure text file: ")
    steps = get_procedure_from_file(procedure_file)

    if not steps:
        print("Could not read procedure steps. Aborting.")
        return

    log = asyncio.run(record_procedure(steps))
    save_log_file(log)

    print(f"\nProcess finished successfully! Check {LOG_FILENAME} for details.")
    print(f"Your video is saved as: {VIDEO_FILENAME}")


if __name__ == "__main__":
    main()
