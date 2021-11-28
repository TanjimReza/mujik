
import discord
from discord.ext import commands
import os
import youtube_dl
import shutil
import asyncio
from youtube_search import YoutubeSearch
import gspread
from gspread.utils import accepted_kwargs
from MaxEmbeds import EmbedBuilder
global VERIFIED_SERVERS
VERIFIED_SERVERS = []
BOT_TOKEN = "ODg4NjkzNzk3NDQ4NDc4Nzcw.YUWamA.uQAnHaxkLOxHMHJRC6AV31hC9s4"
queue = {}
intents = discord.Intents().all()
bot = commands.Bot(command_prefix='!',intents=intents)
youtube_dl.utils.bug_reports_message = lambda: ''
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
youtube_dl.utils.bug_reports_message = lambda: ''
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
def setup(bot): 
    for guild in bot.guilds:
        queue[guild.name] = []
    print(queue)

@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.listening, name="Music")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    for guild in bot.guilds:
        queue[guild.name] = []
        print(queue)
    print("Bot Started!")
    
filename = None

istrue = False
nowPlayingIndex = 0 
voice_client = None
global ctxx 
global voice

async def getFileName(name): 
    global filename
    filename = await YTDLSource.from_url(queue[0], loop=bot.loop,stream=True)
    return filename

def getSongLink(url):
    print(f"Received {url}")
    query = url 
    results = YoutubeSearch(query, max_results=10).to_dict()
    result = results[0]
    link = "https://www.youtube.com"+result['url_suffix']
    title = result['title']
    img = result['thumbnails'][0]
    duration = result['duration']
    return link, title, img,duration


async def play_next(ctx):
    try: 
        if len(queue[ctx.guild.name])>0: 
            await play_music(ctx,queue[ctx.guild.name][0])
    except Exception as e: 
        print("PlayNextE:",e)
        pass
async def play_music(ctx,song_link=None):
    try:
        print("In play music ")
        if len(queue[ctx.guild.name]) > 0: 
            print(f"Queue:{queue}")
            global filename
            song_link,title,img,duration = getSongLink(queue[ctx.guild.name][0])
            filename = await YTDLSource.from_url(queue[ctx.guild.name][0], loop=bot.loop,stream=True)    
            embed = EmbedBuilder (
                title = "Now Playing",
                description = "",
                color = int("65535"),
                fields = [  ["Name:", title, True], 
                            ["Link:",song_link, True],
                            ["\u200B", "[Not Playing from YouTube | Don't Sue Me Ples](https://www.youtube.com/watch?v=dQw4w9WgXcQ )", False],
                            ["Requested by:", ctx.message.author, True],
                            ["Duration:", duration, True]                     
                            ],
                footer = ["Made with 💓 by Tanjim Reza [https://www.facebook.com/tanjimreza]"],
                # author = [message.author.name, message.author.avatar_url],
                thumbnail = img
                ).build()
            
            
            
            # ctx.voice_client.play(discord.FFmpegPCMAudio(filename), after=lambda e: play_next(ctx))
            ctx.voice_client.play(filename, after=lambda e: bot.loop.create_task(play_next(ctx)))
            print(f"{queue[ctx.guild.name].pop(0)} popped. Now Q:{queue}")
            await ctx.send(embed=embed)
    except Exception as e: 
        print("Excepting in play_music")
        print(e)
        

@bot.command(name='p', help='To play song')
async def play(ctx,*url):
    wow = True
    if wow:
        searchString = " ".join(url)
        print(f"Searching: {searchString}")
        
        global ctxx 
        ctxx = ctx 
        print("Got:",ctx)
        if not ctx.message.author.voice: 
            await ctx.send(f"{ctx.message.author} not connected to voice channel")
            return
        song_link,title,img,duration= getSongLink(searchString)
        print(f"Returned {song_link},{title}")
        queue[ctx.guild.name].append(song_link)
        embed = EmbedBuilder (
        title = "Added to Queue",
        description = "",
        color = int("65535"),
        fields = [  ["Name:", title, True], 
                    ["Link:",song_link, True],
                    ["It may take some time to fetch the song", "[Not Playing from YouTube | Don't Sue Me Ples](https://www.youtube.com/watch?v=dQw4w9WgXcQ )", False],
                    ["Requested by:", ctx.message.author, True],
                    ["Duration:", duration, True]                     
                    ],
        footer = ["Made with 💓 by Tanjim Reza [https://www.facebook.com/tanjimreza]"],
        # author = [message.author.name, message.author.avatar_url],
        thumbnail = img
        ).build()        
        await ctx.send(embed=embed, delete_after=5.0)
        await ctx.message.add_reaction("✅")
        await ctx.message.add_reaction("⏳")
        if ctx.voice_client is None: 
            print("Connecting to voice")
            await ctx.author.voice.channel.connect()
            await play_music(ctx,None)
        else: 
            print("Already connected, proceeding!")
            await play_music(ctx,None)
    else:
        await ctx.message.reply(f"**⚠️ Server not Verified ⚠️**\n\nVerification is necessary to avoid issues.\nContact:**`The Batman#2198`** with `{ctx.guild.name}` for verification.\nThanks")
@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    else:
        try:
            await ctx.message.author.voice.channel.connect()
        except: 
            print("Already in voice")
            pass
@bot.command(name='pause', help='This command pauses the song')
async def pause(ctx):

    try: 
        if ctx.message.guild.voice_client is not None:
            print("Currently Connected!")
            if ctx.voice_client.is_playing:
                print("Currently playing")
                ctx.voice_client.pause()
                await ctx.message.reply(f"⏸️ Paused")
        else:
            await ctx.message.reply(f"Not Playing Anything!")   
    except Exception as e:
        print(f"Pause Exception:\,{e}")

 
@bot.command(name='resume', help='Resumes the song')
async def resume(ctx):
    # if voice.is_playing() == False:
    #     voice.resume()
    #     await ctx.message.reply(f"Resumed ▶️")
    # else: 
    #     await ctx.message.reply(f"Nothing is paused!")
    try: 
        if ctx.message.guild.voice_client is not None:
            print("Currently Connected!")
            if ctx.voice_client.is_stopped:
                print("Nothing to resume!")
                await ctx.message.reply(f"Nothing to Resume!")

            else:
                if ctx.voice_client.is_paused:
                    print("Currently paused")
                    ctx.voice_client.resume()
                    await ctx.message.reply(f"▶️ Resumed")
        else:
            await ctx.message.reply(f"Not Pausing Anything!")   
    except Exception as e:
        print(f"Resume Exception:\,{e}")

@bot.command(name='leave', help='To make the bot leave the voice channel')
async def leave(ctx):
    # try:
    #     global voice
    #     await voice.disconnect()
    #     await ctx.message.reply("Left voice channel 🥺. Ping me if you want me to play a song.")
    # except: 
    #     pass
    if ctx.voice_client is not None: 
        await ctx.voice_client.disconnect()
        print(f"Disconnected from {ctx.guild.name}")
        print(f"Queue:{queue}\nClearing this Queue...")
        queue[ctx.guild.name] = []
        print(f"After Clearing Queue:{queue}")

    else: 
        print(f"Not connected here in {ctx.guild.name}")

@bot.command(name='clear')
async def clear(ctx):
    folder = 'music'
    for song in os.listdir(folder):
      file_path = os.path.join(folder, song)
      if os.path.isfile(file_path) or os.path.islink(file_path):
        os.unlink(file_path)
      elif os.path.isdir(file_path):
          shutil.rmtree(file_path)
    await ctx.message.reply("All downloaded files have been cleared!")


@bot.command(name='skip', help='Skips the song')
async def skip(ctx):
    # voice.stop()
    try:
        if ctx.message.guild.voice_client is not None: 
            print("In here Skip")
            ctx.voice_client.stop()
            try:
                await ctx.message.reply(f"⏭️ Skipped Current Song")
                ctx.voice_client.play()
            except Exception as e:
                print("Retrying to play")
                pass
    except Exception as e:
        print(f"Skip Exception:{e}")
        
@bot.command(name='stop', help='Stops the song')
async def stop(ctx):
    try: 
        if ctx.message.guild.voice_client is not None:
            print("Currently Connected!")
            if ctx.voice_client.is_playing or ctx.voice_client.is_paused:
                print("Currently playing or paused")
                ctx.voice_client.stop()
                queue[ctx.guild.name] = []
                await ctx.message.reply(f"🛑 Stopped Playing. Cleared Queue.")
                print(queue)
        else:
            await ctx.message.reply(f"Not Playing Anything!")   
    except Exception as e:
        print(f"Stop Exception:\{e}")

@bot.command(name='commandlist', help='usage')
async def commandlist(ctx):
    text = "Use !p play, !pause,!resume,!leave"
    await ctx.send(text)


@bot.command(name='verify', help='SUDO: Temporary Verification')
async def verify(ctx):
    ADMIN = str((ctx.message.author)).replace(" ","")
    TANJIM = "TheBatman#2198"
    print(ADMIN,TANJIM)
    if ADMIN == TANJIM:
        await ctx.message.reply("Temporary Approval initiated by Tanjim",delete_after=5.0)
        await ctx.send(f"Server Information:\nServer Name:{ctx.guild.name}\nServer Owner:{ctx.guild.owner}",delete_after=5.0)
        VERIFIED_SERVERS.append(ctx.guild.name)
        await ctx.send(f"✅ Server temporarily verified!")
    else: 
        print("Else")
@bot.command(name='servers', help='Server List')
async def servers(ctx):
    ADMIN = str((ctx.message.author)).replace(" ","")
    TANJIM = "TheBatman#2198"
    print(ADMIN,TANJIM)
    if ADMIN == TANJIM:
        servers = []
        for guild in bot.guilds:
            servers.append(guild.name)
            print(servers)
        await ctx.send(f"Currently Connected Servers: {servers}")
    else: 
        print("Else")

if __name__ == "__main__" :
    print("Stored Verified Servers:", VERIFIED_SERVERS)
    print("Starting Bot")
    bot.run(BOT_TOKEN)
