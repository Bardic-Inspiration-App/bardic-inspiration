import os
import traceback

import discord
import openai
import wavelink
from discord.ext import commands
from dotenv import load_dotenv
from utils.util import get_playlist_url, return_play_commands, roll_dice, shuffle_list, generate_ai_prompt
from service import GoogleDriveService

load_dotenv()

# Global Variables
openai.api_key = os.getenv("OPENAI_API_KEY")
TOKEN = os.getenv('DISCORD_TOKEN')
WAVELINK_URI = os.getenv('WAVELINK_URI')
WAVELINK_PASSWORD = os.getenv('WAVELINK_PASSWORD')
MAX_VOLUME = 5
COMMAND_PREFIX = "!"

class CustomPlayer(wavelink.Player):
    def __init__(self):
        super().__init__()
        self.queue = wavelink.Queue()

class BardBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.all()
        super().__init__(intents=intents, command_prefix=COMMAND_PREFIX)
        self.scribe_cache = {} # ? need to save the scribe messages
        self.g_drive_service = None

    async def on_ready(self) -> None:
        print(f'Logged in {self.user} | {self.user.id}')
        print('They are traveling in the following realms:')
        for guild in bot.guilds:
            print(f'{guild}(id: {guild.id})')
            members = '\n - '.join([member.name for member in guild.members])
            print(f'Guild Members:\n - {members}')
        print('Ready to rock!')

    async def setup_hook(self) -> None:
        """Connects bot to the wavelink server and auths google"""
        try:
            print('Starting Node connect...')
            node: wavelink.Node = wavelink.Node(
                uri=WAVELINK_URI,
                password=WAVELINK_PASSWORD,
            )
            await wavelink.NodePool.connect(client=bot, nodes=[node])

            print('Starting build for Google service auth...')
            self.g_drive_service = GoogleDriveService().build()

        except Exception as e:
            print(f'Connection failed due to: {e}')
            pass



# CLIENTS
bot = BardBot()

# EVENTS
@bot.event
async def on_command_error(ctx, error):
    # command invoke errors
    match error:
        case isinstance(error, commands.errors.CommandInvokeError):
            if hasattr(error.original, 'reason') and error.original.reason == 'PREMIUM_REQUIRED':
                await ctx.send('You do not have a premium Spotify account configured to run this command.\nRun: `!configure spotify`.')
        case isinstance(error, openai.error.RateLimitError):
            print(error)
        case _:
            print("An Unknown error has occurred")

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
        await ctx.send('Sorry, I can only stop in voice channels!')
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

@bot.command(name='scribe')
async def scribe(ctx: commands.Context):
    '''Landon add a blurb about what this does'''
    # TODO: for now, only have it scribe in text channels, speech to text is in beta for openai -> later iteration
    # If this channel isn't in our scribe cache, add it with desired default; treats it like it was off from here forward
    if not ctx.channel.id in bot.scribe_cache:
        bot.scribe_cache[ctx.channel.id] = {"on": False, "content": []}
    # flip `on` switch
    bot.scribe_cache[ctx.channel.id]['on'] = not bot.scribe_cache[ctx.channel.id]['on']
    channel_content = bot.scribe_cache.get(ctx.channel.id)

    if channel_content and channel_content.get('on'):
      await ctx.send(f'Okay! I\'m recording in `#{ctx.channel.name}`. Run the `!scribe` command again to ask me to stop.\nKeep in mind that I can only do about 3000 words before I need a Short Rest.')
    elif channel_content:   
        await ctx.send(f'Okay! Finished recording in `#{ctx.channel.name}`. Working on my summary.')
        # TODO: Stretch - save a backup of ai_prompt if there's a failure so the notes are not lost
        # TODO: turn this logic into a util 
        ai_prompt = generate_ai_prompt(channel_content['content'])
        # TODO: if bot.g_drive_service is not available, raise and don't call openai
        try: 
            response = openai.Completion.create(
                model="text-davinci-003", # latest model available for non-chat function
                prompt=ai_prompt,
                temperature=0,
                max_tokens=4000,
                top_p=1.0,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            # TODO: save summary id somewhere to audit/pull them if something went wrong
            summary_id = response.get('id')
            print("Summary OpenAI ID", summary_id)
            summary_text = response['choices'][0]['text'] if response and 'choices' in response else "I rolled a 1 on my performance..."
            print("Summary", summary_text)
        except Exception as e:
            print('damn', e)
            print(traceback.print_exc())
            return await ctx.send("Apologies, something unforseen has gone wrong.")
        # swich flag to off, and wipe content
        bot.scribe_cache[ctx.channel.id] = {"on": False, "content": []}


@bot.command(name="goo")
async def goo(ctx: commands.Context):
    if not bot.g_drive_service:
        raise Exception('G Drive build not available')
    title = 'My Document'
    body = {
        'title': title
    }
    try:
        doc = bot.g_drive_service.documents().create(body=body).execute()
        title = doc.get('title')
        _id = doc.get('documentId')
        print(f'Created document with title: {title}, id: {_id}')

        # Text insertion
        text = "Some sample text. VERY HUGE CHARACTERS. CamelCaseSentence."
        requests = [
            {
                'insertText': {
                    'location': {
                        'index': 1,
                    },
                    'text': text
                }
            }
        ]
        result = bot.g_drive_service.documents().batchUpdate(documentId=_id, body={'requests': requests}).execute()
        print("RESULTS", result)
    except Exception as e:
        print('damn', e)
        print(traceback.print_exc())
        return await ctx.send("Apologies, something unforseen has gone wrong.")
    
bot.run(TOKEN)