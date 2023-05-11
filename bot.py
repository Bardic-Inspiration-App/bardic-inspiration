import os
import random
import traceback

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

sp = spotipy.Spotify(auth=token)
sp_wavelink = spotify.SpotifyClient(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)

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
async def play(ctx: commands.Context, query: str):
    if not getattr(ctx.author.voice, "channel", None):
        ctx.send('Sorry, I can only play in voice channels!')
    # TODO: Use custom player to have separate queues youtube.com/watch?v=mRzv6Zcowz0 for reference <- must be done before published (Beta)
    try:
        vc: wavelink.Player = ctx.voice_client if ctx.voice_client else await ctx.author.voice.channel.connect(cls=wavelink.Player)
        search = None
        # set a standard that plays at a backgroung level. default volume is aggressive
        await vc.set_volume(5)
        
        # command always starts with a clean playlist queue
        # vc.queue = wavelink.Queue()
        # TODO: see if we will need to pause/stop as well so that the most recent play command always overrides the last 
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
        # TODO: Make jumble the track list so that it starts with a new song each time
        vc.autoplay = True
        for track in playlist.tracks:
            if vc.queue.is_empty and not vc.is_playing():
                await vc.play(track, populate=True) #test volume
                await ctx.send(f'Playing `{track.title}`')
            else:
                await vc.queue.put_wait(track)

        # TODO: add case if playlist runs out of songs
    except Exception as e:
        print('damn', e)
        print(traceback.print_exc())
        return await ctx.send("Apologies, something unforseen has gone wrong.")


# The below is not implemented and proven difficult to work with in current versions, hopeful to be revisited
@bot.command(name='splay')
async def splay(ctx: commands.Context, query: str):
    """Play type of playlist from Spotify"""
    if not getattr(ctx.author.voice, "channel", None):
        ctx.send('Sorry, I can only play in voice channels!')
    vc: wavelink.Player = ctx.voice_client if ctx.voice_client else await ctx.author.voice.channel.connect(cls=wavelink.Player)
    results = sp.search(q='bardic-inspiration:combat', type='playlist')
    playlist = next((p for p in results['playlists']['items'] if p['owner']['display_name'] == 'Landon Turner'))
    tracks = sp.playlist_tracks(playlist_id=playlist.get('id'), fields='items',additional_types=('track',))
    # print(tracks['items'][0]['track']['external_urls']['spotify'])
    track_url = tracks['items'][0]['track']['external_urls']['spotify']
    decoded = spotify.decode_url(track_url)
    if not decoded or decoded['type'] is not spotify.SpotifySearchType.track:
        await ctx.send('Sorry, I had an issue finding the lyrics to a song.')
        return
    try:
        vc.autoplay = True
        track = find_track(track_url)
        # track = await spotify.SpotifyTrack.search(track_url)
        if vc.queue.is_empty and not vc.is_playing():
            print('evry ting ire')
            await vc.play(track, populate=True)
            print('everyting still ire')
            await ctx.send(f'Playing `{tracks.title}`')
        else:
            await vc.queue.put_wait(track)
    except Exception as e:
        print('damn', e)
        print(traceback.print_exc())
       
        return await ctx.send("oops")

# @tasks.loop(seconds=5)
async def find_track(query):
    """Finds the track using the wavelink Spotify extensions. Has to run in it's own async function."""
    track = await spotify.SpotifyTrack.search(query)
    print('track', track)
    return track


bot.run(TOKEN)