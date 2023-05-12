import random

def shuffle_list(items: list):
    n = len(items)
    for i in range(n -1, 0, -1):
        j = random.randint(0, i)
        items[i], items[j] = items[j], items[i]
    return items

def roll_dice(number: int, sides: int):
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
    
