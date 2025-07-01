# Video and Description Generator for Playwright Scripts

This tool automates the creation of a video recording and a timed JSON description by intelligently mapping your high-level steps to the actions in a Playwright script.

## How it Works

This workflow provides a powerful way to generate accurate video descriptions:

1.  **You Provide Inputs**:
    *   A **Playwright script** (`.py`) where you have added comments (`# Step 1`, `# Step 2`, etc.) to mark the beginning of a logical step.
    *   A **steps file** (`.txt`) containing your own human-readable descriptions for each of those steps.

2.  **The Script Analyzes and Maps**:
    *   The `video_generator.py` script first reads your Playwright script to understand how many actions belong to each step block (by counting the `await page...` calls after each `# Step` comment).
    *   It then runs the Playwright script, which generates a video and a detailed trace file with timestamps for every action.

3.  **Correlation and Output**:
    *   The script correlates your high-level descriptions with the groups of timed actions from the trace file.
    *   It then generates a `description.json` file where each of your steps has a precise `start_time` and `end_time` corresponding to the actions in the video.

This approach allows a single one of your descriptions (e.g., "Log into the website") to correctly map to multiple actions in the code (e.g., `fill username`, `fill password`, `click login`).

## Prerequisites

1.  **Python 3.7+**
2.  **Playwright**: If you don't have it installed, run:
    ```bash
    pip install playwright
    playwright install
    ```

## Usage

### 1. Prepare your Playwright Script

Add comments (`# Step 1`, `# Step 2`, etc.) to your script to mark where each logical step begins. Also, ensure your script is set up for video and trace recording.

See `example_playwright_script.py` for a full example.

```python
# ... setup ...

# Step 1: Navigate to the website and log in.
await page.goto("https://example.com")
await page.get_by_label("Username").fill("user")
await page.get_by_label("Password").fill("pass")
await page.get_by_role("button", name="Log in").click()

# Step 2: Perform a search.
await page.get_by_label("Search").fill("My query")
await page.get_by_label("Search").press("Enter")

# ... etc ...
```

### 2. Create Your Steps Description File

Create a text file (e.g., `example_steps.txt`) where each line is a high-level description that corresponds to a `# Step` block in your script.

**`example_steps.txt`:**
```
Navigate to the website and log in.
Perform a search for "My query".
```

### 3. Run the Generator Script

Execute the `video_generator.py` script, providing both your Playwright script and your steps file as arguments:

```bash
python video_generator.py your_playwright_script.py your_steps.txt
```

For example:

```bash
python video_generator.py example_playwright_script.py example_steps.txt
```

### 4. Check the Output

The script will create:

*   A `videos` directory with the recorded `.webm` video file.
*   A `description.json` file with your high-level steps and their accurate start and end times.