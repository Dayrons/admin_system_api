import subprocess


def run_command(command: list):
    return subprocess.run(command, capture_output=True, text=True)