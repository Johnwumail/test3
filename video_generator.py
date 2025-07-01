import json
import subprocess
import zipfile
import os
import argparse
import re
from pathlib import Path

def map_steps_to_actions(script_content: str, trace_events: list) -> list:
    """
    Maps high-level steps to groups of Playwright actions using comments as anchors.

    Args:
        script_content: The string content of the Playwright script.
        trace_events: The list of action events from the Playwright trace.

    Returns:
        A list of tuples, where each tuple contains (step_description, start_time, end_time).
    """
    step_pattern = re.compile(r"#\s*Step\s*(\d+):\s*(.*)", re.IGNORECASE)
    action_pattern = re.compile(r"await\s+page\.")

    lines = script_content.splitlines()
    
    step_action_counts = {}
    current_step = 0

    for line in lines:
        step_match = step_pattern.search(line)
        if step_match:
            current_step = int(step_match.group(1))
            step_action_counts[current_step] = 0
            continue

        if action_pattern.search(line) and current_step > 0:
            step_action_counts[current_step] += 1

    mapped_steps = []
    action_index = 1  # Skip the first internal action

    for step_num in sorted(step_action_counts.keys()):
        count = step_action_counts[step_num]
        if count == 0:
            continue

        start_action = trace_events[action_index]
        end_action = trace_events[action_index + count - 1]
        
        start_time = start_action["startTime"]
        end_time = end_action["endTime"]
        
        mapped_steps.append((start_time, end_time))
        action_index += count

    return mapped_steps

def generate_video_description(playwright_script_path: str, steps_path: str, output_dir: str = "."):
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    print(f"Running Playwright script: {playwright_script_path}")
    process = subprocess.run(["python3", playwright_script_path], capture_output=True, text=True)
    if process.returncode != 0:
        print(f"Error running Playwright script:\n{process.stderr}")
        return

    print("Playwright script finished.")
    video_path = next(Path("videos").glob("*.webm"), None)
    if not video_path:
        print("Error: No video file found.")
        return

    trace_zip_path = "trace.zip"
    if not os.path.exists(trace_zip_path):
        print(f"Error: {trace_zip_path} not found.")
        return

    with zipfile.ZipFile(trace_zip_path, 'r') as zip_ref:
        zip_ref.extractall("trace_data")

    trace_file = next(Path("trace_data").glob("**/*.json"), None)
    if not trace_file:
        print("Error: No JSON trace file found.")
        return

    with open(trace_file, 'r') as f:
        trace_data = json.load(f)
    
    with open(playwright_script_path, 'r') as f:
        script_content = f.read()

    with open(steps_path, 'r') as f:
        user_steps = [line.strip() for line in f if line.strip()]

    actions = [event for event in trace_data["events"] if event["type"] == "action"]
    timed_steps = map_steps_to_actions(script_content, actions)

    if len(user_steps) != len(timed_steps):
        print(f"Warning: Mismatch between user steps ({len(user_steps)}) and mapped actions ({len(timed_steps)}).")

    video_description = {
        "overall_description": "A video demonstrating the steps in the Playwright script.",
        "video_file": video_path.name,
        "steps": [],
    }

    base_time = actions[0]["startTime"]
    for i, description in enumerate(user_steps):
        if i < len(timed_steps):
            start_time, end_time = timed_steps[i]
            step_info = {
                "start_time": (start_time - base_time) / 1000,
                "end_time": (end_time - base_time) / 1000,
                "description": description,
            }
            video_description["steps"].append(step_info)

    json_output_path = output_path / "description.json"
    with open(json_output_path, 'w') as f:
        json.dump(video_description, f, indent=4)

    print(f"Successfully generated description.json at {json_output_path}")
    subprocess.run(["rm", "-rf", "trace_data", "trace.zip"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a video and description from a Playwright script.")
    parser.add_argument("playwright_script", help="Path to the Playwright script with step comments.")
    parser.add_argument("steps_file", help="Path to the file with high-level step descriptions.")
    parser.add_argument("--output_dir", default=".", help="Directory to save the output files.")
    args = parser.parse_args()
    generate_video_description(args.playwright_script, args.steps_file, args.output_dir)