import logging
import os
import traceback
from datetime import date

import discord
import openai
import spotipy
import wavelink

from discord.ext import commands
from dotenv import load_dotenv
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from wavelink.ext import spotify
from spotipy.oauth2 import SpotifyClientCredentials


from authenticate import write_creds
from utils.constants import REPEAT_PLAYLISTS
from utils.util import (
    get_spotify_playlist_url, 
    return_play_commands, 
    roll_dice, 
    shuffle_list, 
    generate_ai_prompt, 
    text_to_chunks
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", False)
logger.warning(f"DEVELOPMENT MODE IS FLAGGED AS: {DEVELOPMENT_MODE}")

# Load stuffs
load_dotenv()
logger.info("Writing GDrive credentials...")
# Google: s/o this guy https://ericmjl.github.io/blog/2023/3/8/how-to-automate-the-creation-of-google-docs-with-python/
write_creds()
g_settings = {
    "client_config_backend": "service",
    "service_config": {
        "client_json_file_path": os.getenv("GOOGLE_CREDENTIALS_FILENAME"),
    }
}
gauth = GoogleAuth(settings=g_settings)
gauth.ServiceAuth()


logger.info("Authenticating Spotipy...")
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SP_CLIENT = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
))  

# Global Variables
openai.api_key = os.getenv("OPENAI_API_KEY")
TOKEN = os.getenv('DISCORD_TOKEN')
WAVELINK_URI = os.getenv('WAVELINK_URI')
WAVELINK_PASSWORD = os.getenv('WAVELINK_PASSWORD')
MAX_VOLUME = 5
COMMAND_PREFIX = "!"




class CustomPlayer(wavelink.Player):
    """
    Extends Player so that each instance can have a separate queue. 
    Allows for multiple servers to play music independently. 
    This should be used for any voice client connection code.
    """
    def __init__(self):
        super().__init__()
        self.queue = wavelink.Queue()

class BardBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.all()
        super().__init__(intents=intents, command_prefix=COMMAND_PREFIX)
        self.scribe_cache = {} 
        self.g_drive = None

    async def on_ready(self) -> None:
        logger.info(f'Logged in {self.user} | {self.user.id}')
        logger.info('They are traveling in the following realms:')
        for guild in bot.guilds:
            guild_info = f'{guild}(id: {guild.id})'
            members = '\n - '.join([member.name for member in guild.members])
            logger.info(f'{guild_info}\nGuild Members:\n - {members}')
        logger.info('Ready to rock!')

    async def setup_hook(self) -> None:
        """Connects bot to the wavelink server and auths google"""
        try:
            logger.info('Setting up Spotify...')
            sc = spotify.SpotifyClient(
                client_id=SPOTIFY_CLIENT_ID, 
                client_secret=SPOTIFY_CLIENT_SECRET, 
            )
            logger.info('Starting Node connect...')
            node: wavelink.Node = wavelink.Node(
                uri=WAVELINK_URI,
                password=WAVELINK_PASSWORD,
            )
            await wavelink.NodePool.connect(client=bot, nodes=[node], spotify=sc)

            logger.info('Setting up Google services...')
            self.g_drive = GoogleDrive(gauth)

        except Exception as e:
            logger.error(f'Connection failed due to: {e}')
            pass



# CLIENTS
bot = BardBot()

# EVENTS
@bot.event
async def on_command_error(ctx, error):
    # set up logs for me to start catching stuff
    logger.error(error)
    # command invoke errors
    if isinstance(error, openai.error.RateLimitError):
        await ctx.send("I apologize but I have hit my limit for processing summaries.\nThe fault is mine!")
    if isinstance(error, spotipy.exceptions.SpotifyException):
        await ctx.send("I am sorry, I am not able to play my music at the moment.")


@bot.event
async def on_message(message) -> None:
    # scribe command logic
    scribe_channel = bot.scribe_cache.get(message.channel.id)
    is_command = message.content.split()[0].startswith(COMMAND_PREFIX)
    if scribe_channel and scribe_channel.get('on') and not message.author.bot and not is_command:
        # TODO: verify this is viable for a sessions worth of notes
        scribe_channel['content'].append(message.content)

    # THIS MUST RUN FOR COMMANDS TO STILL WORK
    await bot.process_commands(message)

# COMMANDS
@bot.command(name='roll')
async def roll(ctx, dice_string: str):
    number, sides = dice_string.split('d')
    if not number:
        number = 1
    result = roll_dice(int(number), int(sides))
    await ctx.send(result)

@bot.command(name='play')
async def play(ctx: commands.Context, query: str):
    if not getattr(ctx.author.voice, "channel", None):
        await ctx.send('Sorry, I can only play in voice channels that you are in!')
    
    if ctx.voice_client and ctx.voice_client.channel.id != ctx.channel.id and ctx.voice_client.is_connected:
        await ctx.send(f'OOF! Sorry friend, I am already playing in `{ctx.voice_client.channel.name}`.')
        return
    try:
        vc: CustomPlayer = ctx.voice_client if ctx.voice_client else await ctx.author.voice.channel.connect(cls=CustomPlayer())
        # autoplay goes through the list without human interaction, must be on
        playlist_url = get_spotify_playlist_url(query)
        if not playlist_url:
            await ctx.send(f'Sorry, I could not play your request of "{query}"\nI can play the following commands:{return_play_commands()}')
            return
        # if play is run again and it is playing have it stop and reset
        # this includes setting autoplay to false so we don't have the autoqueue leak in random songs
        vc.autoplay = False
        await vc.stop()
        vc.queue.reset()
        vc.auto_queue.reset()
        
        
        # send feedback to the channel while we gather the tracks async
        await ctx.send("`*clears throat*...`")
        shuffled_tracks = shuffle_list(
            [track async for track in spotify.SpotifyTrack.iterator(query=playlist_url)]
        )
        # set a standard that plays at a background level. default volume is AGGRESSIVE
        await vc.set_volume(3) 
        vc.autoplay = True

        for track in shuffled_tracks:
            if vc.queue.is_empty and not vc.is_playing():
                print(track.name)
                print(vc.auto_queue)
                # DON'T set populate=True, it creates the autoqueue that throws off subsequent play commands
                await vc.play(track) 
                await ctx.send(f'Playing `{query}`')
            else:
                await vc.queue.put_wait(track)
        if query in REPEAT_PLAYLISTS:
            for _ in range(10):
                await vc.queue.put_wait(shuffled_tracks[0])
        
        vc.auto_queue.reset()

    except Exception as e:
        logger.error('damn', e)
        logger.error(traceback.print_exc())
        return await ctx.send("Apologies, something unforseen has gone wrong.")

@bot.command(name='stop')
async def stop(ctx: commands.Context):
    goodbye_sayings = [
        "Time to sheathe the lute and stow the enchanted flute. May your future battles be filled with critical hits!",
        "As I take my final bow, may your next adventure be filled with treasure, triumph, and legendary loot!",
        "The mystical music comes to an end, but the dungeon of life awaits your next roll. Keep slayin' and playin'!",
    ]
    if not getattr(ctx.author.voice, "channel", None):
        await ctx.send('Sorry, I can only stop in voice channels!')
        return
    try:
        vc: wavelink.Player = ctx.voice_client if ctx.voice_client else None
        if vc:
            await vc.stop()
            vc.queue = wavelink.Queue()
            await ctx.send(shuffle_list(goodbye_sayings)[0])
            await vc.disconnect()
    except Exception as e:
        logger.error('damn', e)
        logger.error(traceback.print_exc())
        return await ctx.send("Apologies, something unforseen has gone wrong.")

@bot.command(name='volume')
async def volume(ctx: commands.Context, command: str):   
    try:
        vc: wavelink.Player = ctx.voice_client if ctx.voice_client else None
        if not getattr(ctx.author.voice, "channel", None) or not vc:
            await ctx.send('Sorry, I can only adjust volume if I\'m connected in a voice channel!')
            return
        current_volume = vc.volume
        match command:
            case 'up':
                if current_volume <= MAX_VOLUME:
                    await vc.set_volume(current_volume + 1)
            case 'down':
                if current_volume > 0:
                    await vc.set_volume(current_volume - 1)
            case 'min':
                await vc.set_volume(1)
            case 'max':
                await vc.set_volume(MAX_VOLUME)
            case 'mute':
                await vc.set_volume(0)
            case _:
                await ctx.send(f"I couldn\'t adjust the volume with command: `{command}`. Try these:\n- `up`\n- `down`\n- `min`\n- `max`\n- `mute` ")
                return
        await ctx.send(f"Volume adjusted to `{command}`.")
        
    except Exception as e:
        logger.error('damn', e)
        logger.error(traceback.print_exc())
        return await ctx.send("Apologies, something unforseen has gone wrong.")

@bot.command(name='scribe')
async def scribe(ctx: commands.Context):
    '''
    When ran toggles a flag to collect messages  in the context of the channel it was called in.\n 
    When run a second time:
    * Joins collected messages together in a string
    * Sends the string to OpenAI to get a summary
    * Creates a google dock and sends the link to the channel the command was run in
    '''
    # TODO: for now, only have it scribe in text channels, speech to text is in beta for openai -> later iteration
    # If this channel isn't in our scribe cache, add it with desired default; treats it like it was off from here forward
    if not ctx.channel.id in bot.scribe_cache:
        bot.scribe_cache[ctx.channel.id] = {"on": False, "content": []}
    # flip `on` switch
    bot.scribe_cache[ctx.channel.id]['on'] = not bot.scribe_cache[ctx.channel.id]['on']
    channel_content = bot.scribe_cache.get(ctx.channel.id)

    if channel_content and channel_content.get('on'):
      await ctx.send(f'Okay! I\'m recording in `#{ctx.channel.name}`. Run the `!scribe` command again to ask me to Long Rest.')
    elif channel_content:   
        await ctx.send(f'Okay! Finished recording in `#{ctx.channel.name}`. Working on my summary.')
        if not bot.g_drive:
            bot.scribe_cache[ctx.channel.id]['on'] = False
            raise Exception('Google Drive not available! I cannot run `!scribe` right now I\m so sorry...')
        try: 
            logger.info('Generating AI summary...')
            # TODO: Stretch - save a backup of summary if there's a failure so the notes are not lost
            # break down the summary into chunks of text so we can stay within openai token limit
            summary_chunks = text_to_chunks(" ".join(channel_content['content']))
            summary_text = " ".join([_summarize_text(chunk) for chunk in summary_chunks])
            doc = bot.g_drive.CreateFile({
                # TODO: Think of a clever title name based on the guild or something or just Session: Date
                "title": f"Session Notes: {date.today()}",
                "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            })
            doc.SetContentString(summary_text)
            doc.Upload()
            # Most permissive, see if you can/should make it read only
            doc.InsertPermission({"type": "anyone", "role": "writer", "value": "anyone"})
            logger.info('AI summary completed.')
            await ctx.send(f"Finished my summary!\n`*bows*`\n{doc['alternateLink']}")
    
        except Exception as e:
            logger.error('damn', e)
            logger.error(traceback.print_exc())
            return await ctx.send("Apologies, something unforseen has gone wrong.")
        # swich flag to off, and wipe content
        bot.scribe_cache[ctx.channel.id] = {"on": False, "content": []}

def _summarize_text(text: str) -> str:
    prompt = generate_ai_prompt(text)
    response = openai.Completion.create(
        model="text-davinci-003", # latest model available for non-chat function (as of this PR)
        prompt=prompt,
        temperature=0,
        max_tokens=1000,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0
    )
    return response["choices"][0].text.strip()


bot.run(TOKEN)