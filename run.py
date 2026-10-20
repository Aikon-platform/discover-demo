"""
run.py - run and manage an AIKON-demo instance.

Usage:
    python run.py (up|build|down|logs)

as a reminder:
- if MODE="dev", front/ webapp and api both run on the host server, other services (DB) run in Dockers
- if MODE="local"|"prod", all processes (api and front) run in Dockers

adapted from https://github.com/Aikon-platform/aikon/blob/main/run.py
"""

import os
import shutil
import signal
import subprocess
import sys
import json
import socket
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONT = ROOT / "front"
API = ROOT / "api"
DOCKER_DIR = ROOT / "docker"
VENV_BIN = FRONT / ".venv"
WIN = os.name == "nt"

# frontend processes in dev (to have the webapp running on localhost)
DEV_PROCS = [
    ("django", ["uv", "run", "manage.py", "runserver", "0.0.0.0:{DJANGO_PORT}"], FRONT),
    (
        "dramatiq",
        ["uv", "run", "manage.py", "rundramatiq", "-t", "1", "-p", "1"],
        FRONT,
    ),
]


# read a .env file
def read_env(path: Path = ROOT / ".env") -> dict:
    if not path.exists():
        sys.exit(f"no {path.name} found: run `python install.py` first")
    return dict(
        line.split("=", 1)
        for line in path.read_text().splitlines()
        if "=" in line and not line.startswith("#")
    )


# kill a stale process
def kill_stale(*patterns: str) -> None:
    if WIN:
        return
    for p in patterns:
        if not subprocess.run(["pkill", "-f", p], capture_output=True).returncode:
            print(f"killed stale '{p}'")
    time.sleep(1)


# check if docker runs
def docker_ok() -> bool:
    return not subprocess.run(["docker", "info"], capture_output=True).returncode


# run the dockerized services
def compose(*args) -> None:
    subprocess.run(["docker", "compose", *args], cwd=DOCKER_DIR, check=True)


# run a subprocess
def spawn(name: str, cmd: list, cwd: Path, env: dict = None) -> subprocess.Popen:
    cmd = [c.format(**ENV) for c in cmd]
    cmd[0] = shutil.which(cmd[0]) or sys.exit(
        f"'{cmd[0]}' not found, run `python install.py` first"
    )
    kwargs = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        if WIN
        else {"start_new_session": True}
    )
    print(f"starting {name}: {' '.join(cmd)}")
    return subprocess.Popen(cmd, cwd=cwd, env={**os.environ, **(env or {})}, **kwargs)


# stop a subprocess started in this script with `spawn`
def stop(name: str, proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    try:
        if WIN:
            proc.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            os.killpg(proc.pid, signal.SIGTERM)
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        if WIN:
            proc.kill()
        else:
            os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()
    except ProcessLookupError:
        pass
    print(f"stopped {name}")


# call api/run.py with a command ("up"|"down"). used if MODE!="dev" to start/stop the dockerized API
def run_api(action: str) -> None:
    if not (ROOT / "api/.env").exists() or ENV.get("MODE") == "dev":
        return
    subprocess.run([sys.executable, str(ROOT / "api/run.py"), action], cwd=ROOT / "api")


# define API processes to run in dev mode
def api_dev_procs() -> list:
    kill_stale("dramatiq app.main", "flask --app app.main")
    api_env = read_env(API / ".env")
    port = api_env.get("API_PORT", "5001")
    device = api_env.get("DEVICE_NB", "") or "0"
    return [
        (
            "api-flask",
            ["uv", "run", "flask", "--app", "app.main", "run", "--debug", "-p", port],
            ROOT / "api",
            {"CUDA_VISIBLE_DEVICES": device},
        ),
        (
            "api-dramatiq",
            ["uv", "run", "dramatiq", "app.main", "-t", "1", "-p", "1"],
            ROOT / "api",
            {"CUDA_VISIBLE_DEVICES": device},
        ),
    ]


# run loop for all processes running on host in dev mode (frontend + api)
def run_dev() -> None:
    kill_stale("manage.py rundramatiq", "manage.py runserver")
    procs_def = [(name, cmd, cwd, None) for name, cmd, cwd in DEV_PROCS]
    if (API / "run.py").exists():
        procs_def += api_dev_procs()
    procs = {name: spawn(name, cmd, cwd, env) for name, cmd, cwd, env in procs_def}
    # run the app
    try:
        # while True keeps monitoring the processes after starting them:
        # every 2 seconds, we poll for process status. without while True, we would exit
        while True:
            for name, p in procs.items():
                if p.poll() not in (None, 0):
                    print(f"\n'{name}' exited with code {p.returncode}, shutting down")
                    raise KeyboardInterrupt
            time.sleep(2)
    # processes stop (either by crash or user input) => the `pass` does nothing and flows to finally
    except KeyboardInterrupt:
        pass
    # graceful shutdown
    finally:
        print("\nstopping host processes (hit ctrl+C to also stop docker services)")

        # if ctrl+C is pressed during app shutdown (`signal.SIGINT` emitted => `on_sigint` called),
        # teardown is set to True => also stop docker processes.
        teardown = False

        def on_sigint(*_):
            nonlocal teardown
            teardown = True

        signal.signal(signal.SIGINT, on_sigint)

        # kill host processes
        for name, p in procs.items():
            stop(name, p)

        # host processes are cleaned => change signal handing of SIGINT:
        # if `signal.SIGINT` is emitted, ignore it with `SIG_IGN`
        # => stop listening to ctrl+C
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        # kill docker processes if necessary
        if teardown:
            compose("down")
        else:
            print(
                "docker services still running. run `python run.py down` to stop them"
            )
    return


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "up"
    ENV = read_env()
    if not docker_ok():
        sys.exit("docker daemon not reachable. start docker and retry")

    if action == "down":
        compose("down")
        run_api("down")
    elif action == "build":
        compose("up", "-d", "--build")
        run_api("build")
    elif action == "logs":
        compose("logs -f")
    elif action == "up":
        compose("up", "-d", "--remove-orphans")
        run_api("up")
        if ENV["MODE"] == "dev":
            run_dev()
        else:
            port = ENV.get("NGINX_PORT", "8080")
            url = (
                f"https://{ENV['PROD_URL']}"
                if ENV["MODE"] == "prod"
                else f"http://localhost:{port}"
            )
            print(f"→ {url} (stop with `python run.py down`)")
    else:
        print(f"❌ Unknown action: '{action}' !")
        print(__doc__)
