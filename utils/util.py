import random
from .constants import VALID_PLAYLIST_COMMANDS

def shuffle_list(items: list) -> list:
    n = len(items)
    for i in range(n -1, 0, -1):
        j = random.randint(0, i)
        items[i], items[j] = items[j], items[i]
    return items

def roll_dice(number: int, sides: int) -> str:
    """
    Rolls set of common die based on args
    params:
    - number: the amount of dice to roll
    - type: the type of die to roll
    """
    print(number)
    number = number if number else 1
    return ', '.join([
        str(random.choice(range(1, sides + 1)))
        for _ in range(number)
    ])

def get_spotify_playlist_url(query: str) -> str:
    """ Returns a spotify playlist url if it's a valid command"""
    if not query in VALID_PLAYLIST_COMMANDS:
        return ''
    return VALID_PLAYLIST_COMMANDS[query]


def return_play_commands() -> str:
    return " ".join([f"\n- `{command}`" for command in VALID_PLAYLIST_COMMANDS])


def generate_ai_prompt(content: list[str]) -> str:
    return "Convert these tabletop rpg notes into a readable story summary. Add minimal extra details, but only if necessary.\n\n" + ". ".join(content)

def text_to_chunks(text: str) -> list:
    max_chunk_size = 2048
    chunks = []
    current_chunk = ""
    for sentence in text.split("."):
        if len(current_chunk) + len(sentence) < max_chunk_size:
            current_chunk += sentence + "."
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + "."
    if current_chunk:
        chunks.append(current_chunk.strip())


    return chunks