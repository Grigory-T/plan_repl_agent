#!/usr/bin/env python3
"""
Subprocess worker entrypoint for agent tasks.
Reads input JSON, runs agent, writes output JSON, exits with proper code.
"""
import sys
import os
import json
import argparse
from pathlib import Path

from .run_agent import run_agent


def main():
    parser = argparse.ArgumentParser(description="Agent worker subprocess")
    parser.add_argument("--input", required=True, help="Input JSON file path")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    try:
        # Read input
        with open(input_path, "r") as f:
            data = json.load(f)
        
        task_id = data["task_id"]
        task = data["task"]
        
        # Change to work directory for agent file operations
        work_dir = Path(__file__).parent.parent / "work" / task_id
        work_dir.mkdir(exist_ok=True)
        os.chdir(work_dir)
        
        # Run agent, pass task_id to align log directory name with work directory
        result = run_agent(task, log_dir_name=task_id)
        
        # Write success output
        with open(output_path, "w") as f:
            json.dump({
                "status": "completed",
                "result": result
            }, f)
        
        sys.exit(0)
    
    except Exception as e:
        # Write failure output
        try:
            with open(output_path, "w") as f:
                json.dump({
                    "status": "failed",
                    "error": str(e)
                }, f)
        except:
            pass  # Can't write output, exit anyway
        
        sys.exit(1)


if __name__ == "__main__":
    main()
