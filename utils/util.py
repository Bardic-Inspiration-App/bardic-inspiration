import random
import spotipy


VALID_PLAYLIST_COMMANDS = {
    'combat': 'https://open.spotify.com/playlist/78ltcr3ORGi6rd7sYuHrs3?si=2058e49413904d3e', 
    'tense': 'https://open.spotify.com/playlist/3LiFqKplInrSBonY0S2XHL?si=b166ddcabe7e4212', 
    'explore': 'https://open.spotify.com/playlist/7fP4RQVz1JiTXFXbF9r0Zl?si=d78370f6ae594c33', 
    'seas': 'https://open.spotify.com/playlist/5Jd0bOUh7T1WFnjLlcdlvw',
    'city': 'https://open.spotify.com/playlist/7fP4RQVz1JiTXFXbF9r0Zl?si=7ecbe72fdf324cf2', 
    'tavern': 'https://open.spotify.com/playlist/3Mv1DlaXOkjrYXYeWdUShU?si=9cf0c517ee374941', 
    'infernal': 'https://open.spotify.com/playlist/0vaLOSVvWp5gU4jqc0r99x?si=6ac8ef0755c44bcb', 
    'forest': 'https://open.spotify.com/playlist/7exDFRZz3vAFVxL1BHAmRC?si=c1ca1bb21c77455d', 
    'jungle': 'https://open.spotify.com/playlist/5ZOzPkXTKBIwEz2i9dDQKd?si=bb527547901044a7', 
    'defeat': 'https://open.spotify.com/playlist/5CCAMhzuyfRWDyTGIJUqYH?si=247d8539b68a4100'
    }

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

def get_spotify_playlist_url(query: str, sp: spotipy.Spotify) -> str:
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