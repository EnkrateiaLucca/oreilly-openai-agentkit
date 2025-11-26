from pathlib import Path

FILE_TOOL_DEFINITIONS = [
    {
        "type": "function",
        "name": "create_file",
        "description": "Create a text file at the provided filepath with optional content.",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Absolute or relative path for the new file."},
                "content": {"type": "string", "description": "Initial contents for the file. Defaults to empty."},
            },
            "required": ["filepath"],
        },
    },
    {
        "type": "function",
        "name": "move_file",
        "description": "Move or rename a file on disk.",
        "parameters": {
            "type": "object",
            "properties": {
                "src": {"type": "string", "description": "Existing file path to move."},
                "dst": {"type": "string", "description": "Destination path for the file."},
            },
            "required": ["src", "dst"],
        },
    },
    {
        "type": "function",
        "name": "edit_file",
        "description": "Overwrite an existing file with new content.",
        "parameters": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path of the file to edit."},
                "new_content": {"type": "string", "description": "Full content that should replace the file's current contents."},
            },
            "required": ["filepath", "new_content"],
        },
    },
]

def create_file(filepath: str, content: str = "") -> str:
    """
    Create a new file at the specified filepath with the given content.
    Returns a message about the result.
    """
    try:
        path = Path(filepath).expanduser()
        if path.exists():
            return f"File already exists: {filepath}"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"File created: {filepath}"
    except Exception as e:
        return f"Error creating file {filepath}: {e}"

def move_file(src: str, dst: str) -> str:
    """
    Move a file from src to dst.
    Returns a message about the result.
    """
    try:
        src_path = Path(src).expanduser()
        dst_path = Path(dst).expanduser()
        if not src_path.exists():
            return f"Source file not found: {src}"
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        src_path.rename(dst_path)
        return f"Moved {src} to {dst}"
    except Exception as e:
        return f"Error moving file {src} to {dst}: {e}"

def edit_file(filepath: str, new_content: str) -> str:
    """
    Overwrite the content of the file at filepath with new_content.
    Returns a message about the result.
    """
    try:
        path = Path(filepath).expanduser()
        if not path.exists():
            return f"File does not exist: {filepath}"
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return f"File edited: {filepath}"
    except Exception as e:
        return f"Error editing file {filepath}: {e}"


