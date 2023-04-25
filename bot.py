import os
import random

import discord
import spotipy

from discord.ext import commands
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
)


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print('They are traveling in the following realms:')
    for guild in bot.guilds:
        print(f'{guild}(id: {guild.id})')
        members = '\n - '.join([member.name for member in guild.members])
        print(f'Guild Members:\n - {members}')

# TODO: implement command errors as the come up here
# @bot.event
# async def on_command_error(ctx, error):
#     if isinstance(error, commands.errors.CheckFailure):
#         await ctx.send('You do not have the correct role for this command.')

@bot.command(name='99', help='Responds with a random quote from Brooklyn 99')
async def nine_nine(ctx):
    print('I ran')
    brooklyn_99_quotes = [
        'I\'m the human form of the 💯 emoji.',
        'Bingpot!',
        (
            'Cool. Cool cool cool cool cool cool cool, '
            'no doubt no doubt no doubt no doubt.'
        ),
    ]

    response = random.choice(brooklyn_99_quotes)
    await ctx.send(response)

# TODO: turn this into a D&D specific roll function
## should take number of dice then the dX die string (use switch or something else)
@bot.command(name='roll')
async def roll(ctx, number_of_dice: int, number_of_sides: int):
    dice = [
        str(random.choice(range(1, number_of_sides + 1)))
        for _ in range(number_of_dice)
    ]
    await ctx.send(', '.join(dice))

#TODO: Implement 'play' spotify playlist command (may need to figure out how to configure)
@bot.command(name='play')
async def play(ctx, playlist: str):
    #FIXME: results in 403 because user needs to be premium
    # figure out who the 'user' is with my current creds
    # see if I can configure/make a method that  makes the auth call (check chatgpt) to spotify
    # the above should be it's own command probably
    results = sp.search(q=playlist, type='playlist')
    if len(results['playlists']['items']) > 0:
        playlist_uri = results['playlists']['items'][0]['uri']
        sp.start_playback(context_uri=playlist_uri)
    else:
        await ctx.send(f'No playlist found with the name {playlist}')



bot.run(TOKEN)