"""
chat_parser.py

Parses a conversation string into a list of (speaker, message) tuples.
"""

import re


def parse_conversation(conversation_text: str):
    """
    Example Input:

    Riya: Hi
    Kai: Hello
    Riya: How are you?

    Returns:

    [
        ("Riya", "Hi"),
        ("Kai", "Hello"),
        ("Riya", "How are you?")
    ]
    """

    conversation = []

    for line in conversation_text.strip().splitlines():

        line = line.strip()

        if not line:
            continue

        match = re.match(r"^([^:]+):(.*)$", line)

        if not match:
            continue

        speaker = match.group(1).strip()
        message = match.group(2).strip()

        if message:
            conversation.append((speaker, message))

    return conversation


if __name__ == "__main__":

    sample = """
        Riya: Are you awake?
        Kai: Yeah. Can't sleep.
        Riya: Me neither.
        Kai: What's on your mind?
        Riya: How everything changed.
        Kai: I know what you mean.
        """

    parsed = parse_conversation(sample)

    for speaker, message in parsed:
        print(speaker, "->", message)