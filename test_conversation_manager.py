from tools.conversationtool import ConversationManager


def test_conversation_save_load():
    # Create a sample conversation
    conversation_data = {
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant"},
            {"role": "user", "content": "Hello!"},
            {"role": "assistant", "content": "Hi! How can I help you today?"},
        ],
        "model": "claude-v3",
        "settings": {"temperature": 0.7, "max_tokens": 1000},
    }

    # Initialize conversation manager
    manager = ConversationManager()

    # Save conversation
    title = "Test Conversation"
    saved_path = manager.save_conversation(conversation_data, title)
    print(f"Conversation saved to: {saved_path}")

    # List all conversations
    conversations = manager.list_conversations()
    print("\nSaved conversations:")
    for conv in conversations:
        print(f"- {conv}")

    # Get metadata for the first conversation
    if conversations:
        metadata = manager.get_conversation_metadata(conversations[0])
        print("\nMetadata for first conversation:")
        print(metadata)


if __name__ == "__main__":
    test_conversation_save_load()
