import os
import traceback

import discord
import wavelink
from discord.ext import commands
from dotenv import load_dotenv
from utils.util import get_playlist_url, return_play_commands, roll_dice, shuffle_list

load_dotenv()

# Global Variables
TOKEN = os.getenv('DISCORD_TOKEN')
WAVELINK_URI = os.getenv('WAVELINK_URI')
WAVELINK_PASSWORD = os.getenv('WAVELINK_PASSWORD')
MAX_VOLUME = 5

class CustomPlayer(wavelink.Player):
    def __init__(self):
        super().__init__()
        self.queue = wavelink.Queue()

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
            await wavelink.NodePool.connect(client=bot, nodes=[node])

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
        # set a standard that plays at a background level. default volume is aggressive
        await vc.set_volume(3)
        # if play is run again and it is playing have it stop and reset
        await vc.stop()
        vc.queue = wavelink.Queue()
        url = get_playlist_url(query)
        if not url:
            await ctx.send(f'Sorry, I could not play your request of "{query}"\nI can play the following commands:{return_play_commands()}')
            return
        playlist = await wavelink.YouTubePlaylist.search(url)
        shuffled_tracks = shuffle_list(playlist.tracks.copy())
        vc.autoplay = True
        for track in shuffled_tracks:
            if vc.queue.is_empty and not vc.is_playing():
                await vc.play(track, populate=True) 
                await ctx.send(f'Playing `{query}`')
            else:
                await vc.queue.put_wait(track)

    except Exception as e:
        print('damn', e)
        print(traceback.print_exc())
        return await ctx.send("Apologies, something unforseen has gone wrong.")

@bot.command(name='stop')
async def stop(ctx: commands.Context):
    if not getattr(ctx.author.voice, "channel", None):
        ctx.send('Sorry, I can only stop in voice channels!')
        return
    try:
        vc: wavelink.Player = ctx.voice_client if ctx.voice_client else None
        if vc:
            await vc.stop()
            vc.queue = wavelink.Queue()
            await vc.disconnect()
    except Exception as e:
        print('damn', e)
        print(traceback.print_exc())
        return await ctx.send("Apologies, something unforseen has gone wrong.")

@bot.command(name='volume')
async def volume(ctx: commands.Context, command: str):   
    try:
        vc: wavelink.Player = ctx.voice_client if ctx.voice_client else None
        if not getattr(ctx.author.voice, "channel", None) or not vc:
            await ctx.send('Sorry, I can only adjust volume if I\'m connected in a voice channel!')
            return
        current_volume = vc.volume
        print(current_volume)
        print(command)
        match command:
            case 'up':
                if current_volume <= MAX_VOLUME:
                    await vc.set_volume(current_volume + 1)
            case 'down':
                if current_volume > 0:
                    await vc.set_volume(current_volume - 1)
            case 'max':
                await vc.set_volume(MAX_VOLUME)
            case 'mute':
                await vc.set_volume(0)
            case _:
                await ctx.send(f"I couldn\'t adjust the volume with command: `{command}`. Try these:\n- `up`\n- `down`\n- `max`\n- `mute` ")
        
    except Exception as e:
        print('damn', e)
        print(traceback.print_exc())
        return await ctx.send("Apologies, something unforseen has gone wrong.")
    
bot.run(TOKEN)