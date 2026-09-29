"""Execute the two core notebooks without inference, writing outputs only to outputs/."""

import os
import sys
from pathlib import Path

import nbformat
from jupyter_client import AsyncKernelManager
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
os.environ["PYTHON_DOTENV_DISABLED"] = "1"
output = ROOT / "outputs/notebooks"
output.mkdir(parents=True, exist_ok=True)

for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
    notebook = nbformat.read(path, as_version=4)
    manager = AsyncKernelManager(kernel_name="python3")
    manager.kernel_spec.argv = [
        sys.executable,
        "-m",
        "ipykernel_launcher",
        "-f",
        "{connection_file}",
    ]
    runner = NotebookClient(
        notebook, timeout=90, km=manager, resources={"metadata": {"path": str(path.parent)}}
    )
    runner.execute(cleanup_kc=True)
    nbformat.write(notebook, output / path.name)
    print(f"Executed offline: {path.name}")
