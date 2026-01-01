"""FastAPI server for the planning agent with subprocess control."""

import uuid
import gc
import sys
import threading
import subprocess
import asyncio
from pathlib import Path
from collections import deque
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict

from .executor import PERSISTENT_GLOBALS

app = FastAPI(title="Planning Agent API")

# In-process state (no cross-process Manager)
tasks_store: Dict[str, dict] = {}  # task_id -> {status, task, result, error, input_path, output_path}
tasks_lock = threading.Lock()
pending_queue: deque[str] = deque()  # task_ids waiting to start
active_processes: Dict[str, subprocess.Popen] = {}  # task_id -> Popen
active_processes_lock = threading.Lock()

# Spool directory for worker I/O
SPOOL_DIR = Path("/app/agent_spool")
MAX_CONCURRENT = 4

# Supervisor thread
supervisor_thread = None
supervisor_stop_event = threading.Event()


def kill_process_group(proc: subprocess.Popen, timeout_term=2, timeout_kill=1):
    """Kill a process and its entire process group."""
    import os
    import signal
    
    exit_code = proc.poll()
    if exit_code is not None:
        # Already finished - reap to avoid zombies
        try:
            proc.wait(timeout=0)
        except Exception:
            pass
        return
    
    try:
        # Get process group ID
        pgid = os.getpgid(proc.pid)
        
        # Try SIGTERM first (graceful)
        try:
            os.killpg(pgid, signal.SIGTERM)
        except ProcessLookupError:
            return  # Already dead
        
        # Wait for termination
        try:
            proc.wait(timeout=timeout_term)
            return  # Terminated gracefully
        except subprocess.TimeoutExpired:
            pass
        
        # Escalate to SIGKILL (force)
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            return  # Already dead
        
        proc.wait(timeout=timeout_kill)
    except Exception as e:
        # Fallback to single process kill
        try:
            proc.kill()
            proc.wait(timeout=timeout_kill)
        except:
            pass


def start_task_subprocess(task_id: str):
    """
    Start a subprocess for the given task_id. 
    Returns the Popen object on success, None on failure.
    Caller must hold active_processes_lock and add proc to active_processes.
    """
    import json
    
    with tasks_lock:
        if task_id not in tasks_store:
            return None
        task_data = tasks_store[task_id]
        task = task_data["task"]
    
    # Create spool directory for this task
    task_spool = SPOOL_DIR / task_id
    task_spool.mkdir(parents=True, exist_ok=True)
    
    input_path = task_spool / "input.json"
    output_path = task_spool / "output.json"
    stdout_path = task_spool / "stdout.log"
    stderr_path = task_spool / "stderr.log"
    
    # Write input JSON
    with open(input_path, "w") as f:
        json.dump({"task_id": task_id, "task": task}, f)
    
    # Start subprocess with start_new_session for process group control
    try:
        stdout_log = open(stdout_path, "wb", buffering=0)
        stderr_log = open(stderr_path, "wb", buffering=0)
        
        proc = subprocess.Popen(
            [sys.executable, "-m", "agent.agent_worker", "--input", str(input_path), "--output", str(output_path)],
            start_new_session=True,
            cwd=str(Path(__file__).parent.parent),  # Project root (/app) for module imports
            stdout=stdout_log,
            stderr=stderr_log
        )
        
        # Update task status to running
        with tasks_lock:
            if task_id in tasks_store:
                tasks_store[task_id]["status"] = "running"
                tasks_store[task_id]["input_path"] = str(input_path)
                tasks_store[task_id]["output_path"] = str(output_path)
                tasks_store[task_id]["stdout_path"] = str(stdout_path)
                tasks_store[task_id]["stderr_path"] = str(stderr_path)
        
        print(f"✓ Task {task_id[:8]} started PID={proc.pid}")
        return proc
    except Exception as e:
        print(f"✗ Task {task_id[:8]} spawn failed: {e}")
        with tasks_lock:
            if task_id in tasks_store:
                tasks_store[task_id]["status"] = "failed"
                tasks_store[task_id]["error"] = f"Failed to spawn: {e}"
        return None


def supervisor_loop():
    """Supervisor thread that reaps finished processes and starts pending tasks."""
    import json
    
    while not supervisor_stop_event.is_set():
        # 1. Reap finished processes
        with active_processes_lock:
            finished_ids = []
            for task_id, proc in list(active_processes.items()):
                exit_code = proc.poll()
                if exit_code is not None:
                    # Process finished
                    proc.wait()  # Reap
                    finished_ids.append(task_id)
                    
                    # Read output JSON
                    with tasks_lock:
                        if task_id in tasks_store:
                            output_path = Path(tasks_store[task_id].get("output_path", ""))
                            if output_path.exists():
                                try:
                                    with open(output_path, "r") as f:
                                        output = json.load(f)
                                    
                                    # Clamp status to only valid values
                                    status = output.get("status", "")
                                    if status not in ("completed", "failed"):
                                        tasks_store[task_id]["status"] = "failed"
                                        tasks_store[task_id]["error"] = f"Worker returned invalid status: {status}"
                                    else:
                                        tasks_store[task_id]["status"] = status
                                        if "result" in output:
                                            tasks_store[task_id]["result"] = output["result"]
                                        if "error" in output:
                                            tasks_store[task_id]["error"] = output["error"]
                                except Exception as e:
                                    tasks_store[task_id]["status"] = "failed"
                                    tasks_store[task_id]["error"] = f"Failed to parse output: {e}"
                            else:
                                # No output file, crashed
                                tasks_store[task_id]["status"] = "failed"
                                tasks_store[task_id]["error"] = f"Worker exited with code {exit_code} (no output)"
            
            # Remove finished processes
            for task_id in finished_ids:
                active_processes.pop(task_id, None)
        
        # 2. Start pending tasks (concurrency cap)
        with active_processes_lock:
            while len(active_processes) < MAX_CONCURRENT and len(pending_queue) > 0:
                task_id = pending_queue.popleft()
                proc = start_task_subprocess(task_id)
                if proc:
                    active_processes[task_id] = proc
        
        # Interruptible wait for shutdown
        supervisor_stop_event.wait(0.1)


@app.on_event("startup")
async def startup_event():
    global supervisor_thread
    SPOOL_DIR.mkdir(parents=True, exist_ok=True)
    supervisor_stop_event.clear()
    supervisor_thread = threading.Thread(target=supervisor_loop, daemon=True)
    supervisor_thread.start()
    print("✓ Agent server started")


@app.on_event("shutdown")
async def shutdown_event():
    supervisor_stop_event.set()
    if supervisor_thread:
        supervisor_thread.join(timeout=2)
    
    with active_processes_lock:
        for proc in active_processes.values():
            kill_process_group(proc)
        active_processes.clear()
    print("✓ Agent server shutdown")


class TaskRequest(BaseModel):
    task: str


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatus(BaseModel):
    task_id: str
    status: str  # "pending", "running", "completed", "failed"
    result: Optional[str] = None
    error: Optional[str] = None


@app.post("/run", response_model=TaskResponse)
async def run_task(request: TaskRequest):
    task_id = str(uuid.uuid4())
    
    with tasks_lock:
        tasks_store[task_id] = {
            "status": "pending",
            "task": request.task + (
                "\n\nВАЖНОрезультаты запиши в result.md (CWD)."
                "Даже если результатов нет или задачу невозможно выполнить, запиши в result.md (CWD)"),
            "result": None,
            "error": None,
        }
    
    # Enqueue for supervisor to start (synchronized)
    with active_processes_lock:
        pending_queue.append(task_id)
    print(f"✓ Task {task_id[:8]} queued")
    
    # Paths for worker outputs
    work_dir = Path("/app/work") / task_id
    result_file = work_dir / "result.md"
    
    # Poll until the supervisor marks the task finished (completed or failed)
    status = "pending"
    while True:
        await asyncio.sleep(1)
        with tasks_lock:
            status = tasks_store.get(task_id, {}).get("status", "not_found")
            error = tasks_store.get(task_id, {}).get("error")
        if status in ("completed", "failed"):
            break

    # Try to read result.md; fall back to error or a default message
    if result_file.exists():
        try:
            result_text = result_file.read_text()
        except Exception as e:
            result_text = f"result.md could not be read: {e}"
    else:
        result_text = error or "no result produced"

    return TaskResponse(
        task_id=task_id,
        status=status,
        message=result_text
    )


@app.get("/status/{task_id}", response_model=TaskStatus)
async def get_status(task_id: str):
    with tasks_lock:
        if task_id not in tasks_store:
            return TaskStatus(task_id=task_id, status="not_found", error="Task not found")
        task_info = tasks_store[task_id]
        return TaskStatus(
            task_id=task_id,
            status=task_info["status"],
            result=task_info.get("result"),
            error=task_info.get("error")
        )


@app.get("/health")
async def health():
    with tasks_lock:
        running_count = len([t for t in tasks_store.values() if t["status"] == "running"])
    
    with active_processes_lock:
        process_count = len(active_processes)
        pending_count = len(pending_queue)
    
    return {
        "status": "ok",
        "active_tasks": running_count,
        "active_processes": process_count,
        "pending": pending_count
    }


@app.get("/tasks")
async def list_tasks():
    with tasks_lock:
        return {
            "tasks": [
                {
                    "task_id": tid,
                    "status": info["status"],
                    "task_preview": info["task"][:100] + "..." if len(info["task"]) > 100 else info["task"]
                }
                for tid, info in tasks_store.items()
            ]
        }


@app.get("/reset")
async def reset():
    killed_count = 0
    
    # Clear task store
    with tasks_lock:
        cleared_count = len(tasks_store)
        tasks_store.clear()
    
    # Clear pending queue and kill active processes (synchronized)
    with active_processes_lock:
        pending_count = len(pending_queue)
        pending_queue.clear()
        
        for task_id, proc in list(active_processes.items()):
            try:
                kill_process_group(proc)
                killed_count += 1
                print(f"✓ Killed {task_id[:8]}")
            except Exception as e:
                print(f"✗ Kill failed {task_id[:8]}: {e}")
        active_processes.clear()
    
    # Clear main process globals
    keys_to_remove = [k for k in PERSISTENT_GLOBALS.keys() if k != "__builtins__"]
    for key in keys_to_remove:
        del PERSISTENT_GLOBALS[key]
    gc.collect()
    
    return {
        "status": "reset_complete",
        "tasks_cleared": cleared_count,
        "pending_cancelled": pending_count,
        "killed": killed_count
    }
