import os
import random

import asyncio
import discord
import spotipy
import spotipy.util as util


from discord.ext import commands
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials


load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI') #TODO: env me
spotify_scope = 'user-library-read playlist-read-private user-modify-playback-state'
# TODO: make this dynamic so that it still functions but doesn't need spotify login
username = os.getenv('SPOTIFY_USERNAME')
token = util.prompt_for_user_token(
    username=username, 
    scope=spotify_scope, 
    client_id=SPOTIFY_CLIENT_ID, 
    client_secret=SPOTIFY_CLIENT_SECRET, 
    redirect_uri=redirect_uri
    )

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
# sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
# )
sp = spotipy.Spotify(auth=token)


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print('They are traveling in the following realms:')
    for guild in bot.guilds:
        print(f'{guild}(id: {guild.id})')
        members = '\n - '.join([member.name for member in guild.members])
        print(f'Guild Members:\n - {members}')

@bot.event
async def on_command_error(ctx, error):
    # command invoke errors
    if isinstance(error, commands.errors.CommandInvokeError):
        if hasattr(error.original, 'reason') and error.original.reason == 'PREMIUM_REQUIRED':
            await ctx.send('You do not have a premium Spotify account configured to run this command.\nRun: `!configure spotify`.')

# TODO: I am going to hardcode my username here at first
## I would need a way to store the user authenticating in their respective guilds for this
### would also need it to be the creator of the guild maybe?
@bot.command(name='configure')
async def configure(ctx, aspect: str):
    if aspect.lower().strip() == 'spotify':
        #FIXME: hard authing to POC but authing should be handled here
        pass

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
async def play(ctx, name: str):
    # figure out who the 'user' is with my current creds
    # TODO: with prem spotify I should be able to access any public playlist
    ## SO, look at chatgpt for suggestion and refactor to have set args (combat, tense, etc)
    ## use discord.py to stream into the voice channel
    # TODO: change this so that it checks for prediscribed args
    results = sp.search(q=name, type='playlist')
    playlist = next((item for item in results['playlists']['items'] if item['owner']['display_name'] == 'Landon Turner'), None)
    if not playlist:
        print("Valid playlist not found for:", playlist)
        return
    # user_id = sp.me()['id']
    # get the tracks from the playlist
    tracks = sp.playlist_tracks(playlist.get('id'))
    track_urls = [track['track']['preview_url'] for track in tracks['items'] if track['track']['preview_url']]
    stream_url = track_urls[0] if track_urls else None

    # if stream_url:
    # join the voice channel
    voice_channel = ctx.author.voice.channel
    print(voice_channel)
    voice_client = await voice_channel.connect()





bot.run(TOKEN)