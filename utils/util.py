import random
import spotipy


VALID_PLAYLIST_COMMANDS = ['combat', 'tense', 'explore', 'seas', 'city', 'tavern', 'infernal', 'forest', 'jungle', 'defeat']

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
    number = number if number else 1
    return ', '.join([
        str(random.choice(range(1, sides + 1)))
        for _ in range(number)
    ])

def get_spotify_tracks(query: str, sp: spotipy.Spotify) -> list[str]:
    """ Returns a list of spotify urls for tracks in the playlist from the query string; if it's a valid query """
    if not query in VALID_PLAYLIST_COMMANDS:
        return []
    # The spotify playlist naming convention; must exist like this on spotify
    search = f"bardic-inspiration:{query}"
    results = sp.search(q=search, type='playlist')
    # find the playlist created for this bot; an extra layer to ensure search gets the right playlist
    playlist = next((p for p in results['playlists']['items'] if p['owner']['display_name'] == 'Landon Turner'))
    tracks = sp.playlist_tracks(playlist_id=playlist.get('id'), fields='items',additional_types=('track',))
    track_urls = [item['track']['external_urls']['spotify'] for item in tracks['items']]
    return track_urls


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