import os
import random

import asyncio
import discord
import spotipy
import spotipy.util as util
import wavelink


from discord.ext import commands
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials


load_dotenv()

# Global Variables
TOKEN = os.getenv('DISCORD_TOKEN')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI') #TODO: env me
spotify_scope = 'user-library-read playlist-read-private user-modify-playback-state'
WAVELINK_HOST = os.getenv('WAVELINK_HOST')
WAVELINK_PORT = os.getenv('WAVELINK_PORT')
WAVELINK_PASSWORD = os.getenv('WAVELINK_PASSWORD')
# TODO: make this dynamic so that it still functions but doesn't need spotify login
username = os.getenv('SPOTIFY_USERNAME')
token = util.prompt_for_user_token(
    username=username, 
    scope=spotify_scope, 
    client_id=SPOTIFY_CLIENT_ID, 
    client_secret=SPOTIFY_CLIENT_SECRET, 
    redirect_uri=redirect_uri
    )

# Clients
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
# sp = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
# )
sp = spotipy.Spotify(auth=token)

async def node_connect():
    """Connects bot to the wavelink server"""
    # TODO: plug in wavelink values for host, port and password (use https one)
    ### looks like I can create as many nodes as possible?
    #### perhaps I can host my own and just use that as a node? idk
    print('Starting Node connect')
    await bot.wait_until_ready()
    try:
        node: wavelink.Node = wavelink.Node(
            uri='http://162.243.160.15:2333',
            password='countryroadstakemehome',
        )
        await wavelink.NodePool.connect(client=bot, nodes=[node])
    except Exception as e:
        print(f'Connection failed due to: {e}')
        pass

@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f'Node {node.id} is ready')

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print('They are traveling in the following realms:')
    for guild in bot.guilds:
        print(f'{guild}(id: {guild.id})')
        members = '\n - '.join([member.name for member in guild.members])
        print(f'Guild Members:\n - {members}')
    print('Connecting to Wavelink server...')
    try:
        bot.loop.create_task(node_connect())
    except Exception as e:
        print(f'Failed to connect to Wavelink server: {e}')

# plays a video from youtube, intended for tutorial purposes, remove me if in repo
@bot.command()
async def yt(ctx: commands.Context):
    # if not ctx.voice_client:
    #     vc:wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
    # else:
    #     vc: wavelink.Player = ctx.voice_client
    # join the voice chat if not already there
    vc: wavelink.Player = ctx.voice_client if ctx.voice_client else await ctx.author.voice.channel.connect(cls=wavelink.Player)
    
    vc.play('https://www.youtube.com/watch?v=dQw4w9WgXcQ')


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



bot.run(TOKEN)