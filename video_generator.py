import json
import subprocess
import zipfile
import os
import argparse
import re
from pathlib import Path

def generate_steps_from_playwright_script(script_content: str) -> list[str]:
    """
    Parses a Playwright script to extract human-readable steps from comments.
    This simulates an LLM analyzing the code to generate step descriptions.

    Args:
        script_content: The string content of the Playwright script.

    Returns:
        A list of step descriptions.
    """
    steps = []
    # Find comments that likely describe a step (e.g., "# Step 1: ...")
    step_pattern = re.compile(r"#\s*Step\s*\d+:\s*(.*)", re.IGNORECASE)
    for line in script_content.splitlines():
        match = step_pattern.search(line)
        if match:
            steps.append(match.group(1).strip())
    return steps

def generate_video_description(playwright_script_path: str, output_dir: str = "."):
    """
    Runs a Playwright script, generates a video and trace, and then processes the trace
    to create a JSON description of the video with timed, auto-generated steps.

    Args:
        playwright_script_path: Path to the user's Playwright script.
        output_dir: Directory to save the generated description.json.
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # 1. Read the Playwright script content to generate steps
    print(f"Analyzing Playwright script: {playwright_script_path}")
    with open(playwright_script_path, 'r') as f:
        script_content = f.read()
    
    steps = generate_steps_from_playwright_script(script_content)
    if not steps:
        print("Warning: Could not automatically generate steps from the script comments.")
        print("Please add comments like '# Step 1: Do something' to your script.")

    print(f"Generated {len(steps)} steps from the script.")

    # 2. Run the playwright script
    print(f"Running Playwright script to record video...")
    process = subprocess.run(["python3", playwright_script_path], capture_output=True, text=True)
    if process.returncode != 0:
        print("Error running Playwright script:")
        print(process.stderr)
        return

    print("Playwright script finished.")
    
    video_files = list(Path("videos").glob("*.webm"))
    if not video_files:
        print("Error: No video file found in the 'videos' directory.")
        return
        
    video_path = video_files[0]
    print(f"Video saved to: {video_path}")

    # 3. Unzip the trace file
    trace_zip_path = "trace.zip"
    if not os.path.exists(trace_zip_path):
        print(f"Error: {trace_zip_path} not found. Make sure your script creates it.")
        return

    with zipfile.ZipFile(trace_zip_path, 'r') as zip_ref:
        zip_ref.extractall("trace_data")
    print("Trace file unzipped.")

    # 4. Parse the trace file
    json_files = list(Path("trace_data").glob("**/*.json"))
    if not json_files:
        print("Error: No JSON trace file found in the unzipped trace data.")
        return

    trace_file_path = json_files[0]

    with open(trace_file_path, 'r') as f:
        trace_data = json.load(f)

    # 5. Correlate steps and generate JSON
    actions = [event for event in trace_data["events"] if event["type"] == "action"]
    
    if len(steps) != len(actions) - 1:
        print(f"Warning: Number of generated steps ({len(steps)}) does not match number of actions ({len(actions)-1}). Timestamps might be inaccurate.")
        
    start_time = actions[0]["startTime"]
    video_description = {
        "overall_description": "A video demonstrating the steps in the Playwright script.",
        "video_file": str(video_path.name),
        "steps": []
    }

    for i, step_description in enumerate(steps):
        if i + 1 < len(actions):
            action = actions[i+1]
            step_info = {
                "start_time": (action["startTime"] - start_time) / 1000,
                "end_time": (action["endTime"] - start_time) / 1000,
                "description": step_description
            }
            video_description["steps"].append(step_info)

    # 6. Write the JSON file
    json_output_path = output_path / "description.json"
    with open(json_output_path, 'w') as f:
        json.dump(video_description, f, indent=4)

    print(f"Successfully generated description.json at {json_output_path}")
    print(f"Cleaning up trace files.")
    subprocess.run(["rm", "-rf", "trace_data", "trace.zip"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a video and description from a Playwright script.")
    parser.add_argument("playwright_script", help="Path to the Playwright script.")
    parser.add_argument("--output_dir", default=".", help="Directory to save the output files.")
    args = parser.parse_args()

    generate_video_description(args.playwright_script, args.output_dir)