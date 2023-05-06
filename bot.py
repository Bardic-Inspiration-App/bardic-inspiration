import os
import random

import discord
import spotipy
import spotipy.util as util
import wavelink


from discord.ext import commands
from dotenv import load_dotenv
from wavelink.ext import spotify

load_dotenv()

# Global Variables
TOKEN = os.getenv('DISCORD_TOKEN')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI') 
spotify_scope = 'user-library-read playlist-read-private user-modify-playback-state'
WAVELINK_URI = os.getenv('WAVELINK_URI')
WAVELINK_PASSWORD = os.getenv('WAVELINK_PASSWORD')
# TODO: make this dynamic so that it still functions but doesn't need spotify login <- I think I will require spotify premium to protect my aims here
username = os.getenv('SPOTIFY_USERNAME')
token = util.prompt_for_user_token(
    username=username, 
    scope=spotify_scope, 
    client_id=SPOTIFY_CLIENT_ID, 
    client_secret=SPOTIFY_CLIENT_SECRET, 
    redirect_uri=redirect_uri
    )

class CustomPlayer(wavelink.Player):
    def __init__(self):
        super().__init__()
        self.queue = wavelink.Queue()
        # TODO: use this to implement after poc for other users spotify premium

class BardBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.all()
        super().__init__(intents=intents, command_prefix='!')

    async def on_ready(self) -> None:
        print(f'Logged in {self.user} | {self.user.id}')
        print('They are traveling in the following realms:')
        for guild in bot.guilds:
            print(f'{guild}(id: {guild.id})')
            members = '\n - '.join([member.name for member in guild.members])
            print(f'Guild Members:\n - {members}')
        print('Ready to rock!')

    async def setup_hook(self) -> None:
        """Connects bot to the wavelink server"""
        print('Starting Node connect')
        try:
            node: wavelink.Node = wavelink.Node(
                uri=WAVELINK_URI,
                password=WAVELINK_PASSWORD,
            )
            await wavelink.NodePool.connect(client=bot, nodes=[node], spotify=sp_wavelink)
            print(sp_wavelink)

        except Exception as e:
            print(f'Connection failed due to: {e}')
            pass
# Clients
# bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
bot = BardBot()
sp = spotipy.Spotify(auth=token)
sp_wavelink = spotify.SpotifyClient(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)

# async def node_connect():
#     """Connects bot to the wavelink server"""
#     print('Starting Node connect')
#     await bot.wait_until_ready()
#     try:
#         node: wavelink.Node = wavelink.Node(
#             uri=WAVELINK_URI,
#             password=WAVELINK_PASSWORD,
#         )
#         await wavelink.NodePool.connect(client=bot, nodes=[node], spotify=sp_wavelink)
#     except Exception as e:
#         print(f'Connection failed due to: {e}')
#         pass

# @bot.event
# async def on_wavelink_node_ready(node: wavelink.Node):
#     print(f'Node {node.id} is ready')


# @bot.event
# async def on_ready():
#     print(f'{bot.user} has connected to Discord!')
#     print('They are traveling in the following realms:')
#     for guild in bot.guilds:
#         print(f'{guild}(id: {guild.id})')
#         members = '\n - '.join([member.name for member in guild.members])
#         print(f'Guild Members:\n - {members}')
#     print('Connecting to Wavelink server...')
#     # TODO: when making this past POC, have it check if the user has configured spotify and prompt to if not
#     try:
#         bot.loop.create_task(node_connect())
#     except Exception as e:
#         print(f'Failed to connect to Wavelink server: {e}')

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
    # TODO: use python switch since we have 3.10
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

@bot.command(name='play')
async def play(ctx: commands.context, query: str):
    from wavelink.ext import spotify

    if not getattr(ctx.author.voice, "channel", None):
        ctx.send('Sorry, I can only play in voice channels!')
    custom_player = CustomPlayer()
    vc: wavelink.Player = ctx.voice_client if ctx.voice_client else await ctx.author.voice.channel.connect(cls=wavelink.Player)


    if vc.queue.is_empty and not vc.is_playing():
        try:
            results = sp.search(q='bardic-inspiration:combat', type='playlist')
            playlist = next((p for p in results['playlists']['items'] if p['owner']['display_name'] == 'Landon Turner'))
            tracks = sp.playlist_tracks(playlist_id=playlist.get('id'), fields='items',additional_types=('track',))
            print(tracks['items'][0]['track']['external_urls']['spotify'])
            track_url = tracks['items'][0]['track']['external_urls']['spotify']
            decoded = spotify.decode_url(track_url)
            print(decoded)

            vc.autoplay = True
            print('kosher')
            track = await spotify.SpotifyTrack.search(track_url)

            print('evry ting ire')
            await vc.play(track, populate=True)
            print('everyting still ire')
            await ctx.send(f'Playing `{tracks.title}`')
        except Exception as e:
            print(e)
            return await ctx.send("oops")
    else:
        await vc.queue.put_wait(track)


bot.run(TOKEN)