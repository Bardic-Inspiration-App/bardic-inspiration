import os
import traceback

import discord
import spotipy
import spotipy.util as util
import wavelink
from discord.ext import commands
from dotenv import load_dotenv
from wavelink.ext import spotify

from utils.util import shuffle_list, roll_dice

load_dotenv()

# Global Variables
TOKEN = os.getenv('DISCORD_TOKEN')
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI') 
spotify_scope = 'user-library-read playlist-read-private user-modify-playback-state'
WAVELINK_URI = os.getenv('WAVELINK_URI')
WAVELINK_PASSWORD = os.getenv('WAVELINK_PASSWORD')

username = os.getenv('SPOTIFY_USERNAME')
token = util.prompt_for_user_token(
    username=username, 
    scope=spotify_scope, 
    client_id=SPOTIFY_CLIENT_ID, 
    client_secret=SPOTIFY_CLIENT_SECRET, 
    redirect_uri=redirect_uri
    )

sp = spotipy.Spotify(auth=token)
sp_wavelink = spotify.SpotifyClient(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)

class CustomPlayer(wavelink.Player):
    def __init__(self):
        super().__init__()
        self.queue = wavelink.Queue()
        # TODO: use this to implement after poc for other users 

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

        except Exception as e:
            print(f'Connection failed due to: {e}')
            pass
# Clients
bot = BardBot()

@bot.event
async def on_command_error(ctx, error):
    # command invoke errors
    if isinstance(error, commands.errors.CommandInvokeError):
        if hasattr(error.original, 'reason') and error.original.reason == 'PREMIUM_REQUIRED':
            await ctx.send('You do not have a premium Spotify account configured to run this command.\nRun: `!configure spotify`.')

@bot.command(name='roll')
async def roll(ctx, dice_string: str):
    number, sides = dice_string.split('d')
    result = roll_dice(int(number), int(sides))
    await ctx.send(result)

@bot.command(name='play')
async def play(ctx: commands.Context, query: str):
    if not getattr(ctx.author.voice, "channel", None):
        ctx.send('Sorry, I can only play in voice channels!')
    # TODO: Use custom player to have separate queues youtube.com/watch?v=mRzv6Zcowz0 for reference <- must be done before published (Beta)
    try:
        vc: wavelink.Player = ctx.voice_client if ctx.voice_client else await ctx.author.voice.channel.connect(cls=wavelink.Player)
        search = None
        # set a standard that plays at a backgroung level. default volume is aggressive
        await vc.set_volume(5)

        # if play is run again and it is playing have it stop and reset
        await vc.stop()
        vc.queue = wavelink.Queue()

        # TODO: create a function that returns a playlist from this switch statement
        match query:
            case 'combat':
                search = 'https://www.youtube.com/playlist?list=PLMK9kbhhnbp0At0z5aiNmjyBoL9Vvj_G1'
            case 'tense':
                search = 'https://www.youtube.com/playlist?list=PLMK9kbhhnbp2VI5evDa_Lpqff5hwL7vg5'
            case 'explore':
                search = 'https://www.youtube.com/playlist?list=PLMK9kbhhnbp10P0s0EkmWzFenouJe-04b'
            case _:
                await ctx.send(f'Sorry, I could not play your request of "{query}"\nI can play the following commands:\n`- combat`\n`- tense`\n`- explore`')
                return
        playlist = await wavelink.YouTubePlaylist.search(search)
        shuffled_tracks = shuffle_list(playlist.tracks.copy())
        vc.autoplay = True
        for track in shuffled_tracks:
            if vc.queue.is_empty and not vc.is_playing():
                await vc.play(track, populate=True) 
                await ctx.send(f'Playing `{query}`')
            else:
                await vc.queue.put_wait(track)

        # TODO: add case if playlist runs out of songs?
    except Exception as e:
        print('damn', e)
        print(traceback.print_exc())
        return await ctx.send("Apologies, something unforseen has gone wrong.")

bot.run(TOKEN)