# Video and Description Generator for Playwright Scripts (Automated)

This tool automates the creation of a video recording and a timed JSON description directly from a commented Playwright script.

## How it works

The `video_generator.py` script now has a new, smarter workflow:

1.  **Analyzes Your Script**: It reads your Playwright script and looks for comments formatted like `# Step 1: ...`, `# Step 2: ...`, etc. It uses these comments to automatically generate the list of steps. This simulates an AI understanding the code.
2.  **Runs Playwright**: It executes your Playwright script, which must be configured to produce a video and a `trace.zip` file.
3.  **Processes Trace**: It unzips the trace file to get precise timestamps for each action.
4.  **Generates JSON**: It correlates the auto-generated steps with the action timestamps and outputs a `description.json` file.

This means you no longer need to create a separate `steps.txt` file.

## Prerequisites

1.  **Python 3.7+**
2.  **Playwright**: If you don't have it installed, run:
    ```bash
    pip install playwright
    playwright install
    ```

## Usage

### 1. Prepare your Playwright script

You need to modify your Playwright script to enable video recording, tracing, and add step comments.

See `example_playwright_script.py` for a full example. The key is to add comments for each logical step.

```python
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(record_video_dir="videos")
        await context.tracing.start(screenshots=True, snapshots=True, sources=True)
        page = await context.new_page()

        # Step 1: Navigate to the Playwright website.
        await page.goto("https://playwright.dev/")

        # Step 2: Click on the search bar.
        await page.get_by_label("Search").click()

        # ... more steps ...

        await context.tracing.stop(path="trace.zip")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
```

**Key changes:**

*   **Step Comments**: Add comments like `# Step 1: Your description` before each action.
*   `record_video_dir="videos"`: Enables video recording.
*   `context.tracing.start(...)`: Starts tracing.
*   `context.tracing.stop(path="trace.zip")`: Stops tracing.

### 2. Run the generator script

Execute the `video_generator.py` script, passing only your Playwright script as an argument:

```bash
python video_generator.py your_playwright_script.py
```

For example:

```bash
python video_generator.py example_playwright_script.py
```

### 3. Check the output

The script will create:

*   A `videos` directory with the recorded `.webm` video file.
*   A `description.json` file in the root directory with the timed, auto-generated step descriptions.

## Important Notes

*   The script now relies on comments in your Playwright file to generate steps. Make sure they are formatted correctly (e.g., `# Step 1: ...`).
*   The script will still delete and recreate a `trace_data` directory and `trace.zip` file during execution.