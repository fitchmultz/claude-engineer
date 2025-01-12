import json
import os
import unicodedata
from datetime import datetime
from typing import Dict, List, Optional

from tools.base import BaseTool


class ConversationTool(BaseTool):
    name = "conversationtool"
    description = """
    Manages conversation exports and imports.
    - Saves conversations to JSON files with metadata
    - Imports previously saved conversations
    - Maintains conversation context and history
    - Handles file operations with error checking
    - Supports special character encoding/decoding
    - Manages separate import/export directories
    - Uses AI for intelligent title generation
    - Includes comprehensive metadata and versioning
    """
    input_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["save", "load", "list"],
                "description": "Whether to save, load, or list conversations",
            },
            "conversation_data": {
                "type": "object",
                "description": "Conversation data to save (required for save action)",
            },
            "file_path": {
                "type": "string",
                "description": "File path for loading conversation (required for load action)",
            },
        },
        "required": ["action"],
    }

    VERSION = "1.1.0"

    def __init__(self):
        super().__init__()
        self.base_path = "conversations"
        self.exports_path = os.path.join(self.base_path, "exports")
        self.imports_path = os.path.join(self.base_path, "imports")

        # Ensure all directories exist
        os.makedirs(self.exports_path, exist_ok=True)
        os.makedirs(self.imports_path, exist_ok=True)

    def _generate_title(self, conversation_data: Dict) -> str:
        """Generate a title from the first message in the conversation."""
        messages = conversation_data.get("messages", [])
        if not messages:
            return "Empty Conversation"
        first_message = messages[0].get("content", "")
        return first_message[:50].strip() + "..."

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename by removing invalid characters."""
        filename = unicodedata.normalize("NFKD", filename)
        filename = "".join(c for c in filename if c.isalnum() or c in (" ", "-", "_"))
        return filename.strip()

    def _save_conversation(self, conversation_data: Dict) -> str:
        """Save conversation data to a file in the exports directory."""
        try:
            timestamp = datetime.now()
            title = self._generate_title(conversation_data)
            sanitized_title = self._sanitize_filename(title)

            metadata = {
                "timestamp": timestamp.isoformat(),
                "conversation_id": conversation_data.get(
                    "conversation_id", str(hash(timestamp.isoformat()))
                ),
                "model": conversation_data.get("model", "unknown"),
                "title": title,
                "export_date": timestamp.isoformat(),
            }

            full_data = {"metadata": metadata, "conversation": conversation_data}

            filename = f"{sanitized_title}_{metadata['conversation_id'][:8]}.convo"
            file_path = os.path.join(self.exports_path, filename)

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(full_data, f, ensure_ascii=False, indent=2)

            return f"Conversation saved successfully to {filename}"

        except Exception as e:
            raise Exception(f"Error saving conversation: {str(e)}")

    def _load_conversation(self, file_path: str) -> Dict:
        """Load conversation data from a file in either imports or exports directory."""
        try:
            if not file_path.endswith(".convo"):
                raise ValueError("Invalid file format. Must be a .convo file")

            # Try both import and export paths
            full_paths = [
                os.path.join(self.imports_path, file_path),
                os.path.join(self.exports_path, file_path),
                file_path,  # Try the exact path as fallback
            ]

            for path in full_paths:
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)

                    if (
                        not isinstance(data, dict)
                        or "metadata" not in data
                        or "conversation" not in data
                    ):
                        raise ValueError("Invalid conversation file format")

                    return data

            raise FileNotFoundError(f"Conversation file not found: {file_path}")

        except Exception as e:
            raise Exception(f"Error loading conversation: {str(e)}")

    def _list_conversations(self) -> List[Dict]:
        """List all available conversations from both imports and exports directories."""
        conversations = []

        # List conversations from both directories
        for directory in [self.exports_path, self.imports_path]:
            for filename in os.listdir(directory):
                if filename.endswith(".convo"):
                    try:
                        with open(
                            os.path.join(directory, filename), "r", encoding="utf-8"
                        ) as f:
                            data = json.load(f)
                            metadata = data.get("metadata", {})
                            metadata["filename"] = filename
                            metadata["location"] = (
                                "exports"
                                if directory == self.exports_path
                                else "imports"
                            )
                            conversations.append(metadata)
                    except Exception:
                        continue

        return conversations

    def execute(self, **kwargs) -> str:
        """Execute the conversation tool with the given parameters."""
        action = kwargs.get("action")

        if action == "save":
            conversation_data = kwargs.get("conversation_data")
            if not conversation_data:
                raise ValueError("conversation_data is required for save action")
            return self._save_conversation(conversation_data)

        elif action == "load":
            file_path = kwargs.get("file_path")
            if not file_path:
                raise ValueError("file_path is required for load action")
            data = self._load_conversation(file_path)
            # Convert dictionary to string for Claude API compatibility
            return json.dumps(data, ensure_ascii=False, indent=2)

        elif action == "list":
            conversations = self._list_conversations()
            # Convert list to formatted string for Claude API compatibility
            return json.dumps(conversations, ensure_ascii=False, indent=2)

        else:
            raise ValueError("Invalid action. Must be 'save', 'load', or 'list'")
