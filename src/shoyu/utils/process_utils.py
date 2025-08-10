import subprocess

import psutil

__all__= [
    "terminate_process_tree",
]

def terminate_process_tree(process: subprocess.Popen) -> None:
    """
    Gracefully terminate a subprocess and its children, with fallback to force kill.

    Args:
        process (subprocess.Popen): Process to terminate.

    Notes:
        1. Send SIGTERM for graceful shutdown.
        2. Wait 5 seconds for voluntary exit.
        3. Send SIGKILL if still running.
        4. Clean up any child processes using psutil.
    """
    if process.poll() is None:
        try:
            process.terminate()
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        except ProcessLookupError:
            pass

        try:
            parent = psutil.Process(process.pid)
            for child in parent.children(recursive=True):
                child.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
