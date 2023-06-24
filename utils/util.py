import random
import spacy

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

def get_playlist_url(query: str) -> str:
    match query:
        case 'combat':
            return 'https://www.youtube.com/playlist?list=PLMK9kbhhnbp0At0z5aiNmjyBoL9Vvj_G1'
        case 'tense':
            return 'https://www.youtube.com/playlist?list=PLMK9kbhhnbp2VI5evDa_Lpqff5hwL7vg5'
        case 'explore':
            return 'https://www.youtube.com/playlist?list=PLMK9kbhhnbp10P0s0EkmWzFenouJe-04b'
        case 'seas':
            return 'https://www.youtube.com/playlist?list=PLMK9kbhhnbp2uW9l7DFC6dZNNvw9OGzG2'
        case 'city':
            return 'https://www.youtube.com/playlist?list=PLMK9kbhhnbp0DX8_Ki3O-8xKNycAL0tRC'
        case 'tavern':
            return 'https://www.youtube.com/playlist?list=PLMK9kbhhnbp21M7xsacZmVxptF_Wv0s3y'
        case 'infernal':
            return 'https://www.youtube.com/playlist?list=PLMK9kbhhnbp2WDTlRv5oADdO_dP9DSJPD'
        case 'forest':
            return 'https://www.youtube.com/playlist?list=PLMK9kbhhnbp1VdBX3o5iKpk_8RZ3FWjXN'
        case 'jungle':
            return 'https://www.youtube.com/playlist?list=PLMK9kbhhnbp2ULvcO1F2UNAg9kkQSH-rt'
        case _:
            return ''

def return_play_commands() -> str:
    playlists = ['combat', 'tense', 'explore', 'seas', 'city', 'tavern', 'infernal', 'forest', 'jungle']
    return " ".join([f"\n- `{command}`" for command in playlists])


def generate_ai_prompt(content: list[str]) -> str:
    return "Convert these tabletop rpg notes into a readable story summary. Add minimal extra details, but only if necessary.\n\n" + ". ".join(content)

def text_to_chunks(text: str) -> list:
    # https://stackoverflow.com/questions/70060847/how-to-work-with-openai-maximum-context-length-is-2049-tokens
    chunks = [[]]
    chunk_total_words = 0

    nlp = spacy.load("en_core_web_sm")
    sentences = nlp(text)

    for sentence in sentences.sents:
        chunk_total_words += len(sentence.text.split(" "))

    if chunk_total_words > 2700:
        chunks.append([])
        chunk_total_words = len(sentence.text.split(" "))

    chunks[len(chunks)-1].append(sentence.text)

    return chunks