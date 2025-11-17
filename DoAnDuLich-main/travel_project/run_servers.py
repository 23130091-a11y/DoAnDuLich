#!/usr/bin/env python
"""
Helper script to run Django + FastAPI servers together for testing.
This avoids PowerShell pipeline issues with background processes.
"""
import subprocess
import time
import sys

print("Starting Django (port 8000) and FastAPI (port 8001)...")
print("To stop both servers, press Ctrl+C")

# Start Django
django_proc = subprocess.Popen(
    [sys.executable, "manage.py", "runserver", "127.0.0.1:8000"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Start FastAPI
fastapi_proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "fastapi_app.app:app", "--host", "127.0.0.1", "--port", "8001"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

print("\n✓ Django running on http://127.0.0.1:8000")
print("✓ FastAPI running on http://127.0.0.1:8001")
print("\nPress Ctrl+C to stop both servers\n")

try:
    # Keep servers running
    django_proc.wait()
    fastapi_proc.wait()
except KeyboardInterrupt:
    print("\nShutting down servers...")
    django_proc.terminate()
    fastapi_proc.terminate()
    django_proc.wait(timeout=5)
    fastapi_proc.wait(timeout=5)
    print("Servers stopped.")
    sys.exit(0)
