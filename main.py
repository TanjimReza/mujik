from sys import set_coroutine_origin_tracking_depth
from typing import AsyncContextManager
import discord
from requests.api import delete
import youtube_dl
from discord.ext import commands
from MaxEmbeds import EmbedBuilder
import youtube_dl
import asyncio
from youtube_search import YoutubeSearch
from config import config

intents = discord.Intents.all()
bot = discord.Bot(command_prefix=",")


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
queue = {}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
youtube_dl.utils.bug_reports_message = lambda: ''
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
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

#! Supporting Methods !# 

def getSongLink(url):
    print(f"Received {url}")
    query = url 
    results = YoutubeSearch(query, max_results=10).to_dict()
    result = results[0]
    link = "https://www.youtube.com"+result['url_suffix']
    title = result['title']
    img = result['thumbnails'][0]
    duration = result['duration']
    return link, title, img, duration
def addedEmbed(ctx,title,song_link,duration,img):
    embed = EmbedBuilder (
            title = "Added to Queue",
            description = "",
            color = int("65535"),
            fields = [  ["Name:", title, True], 
                        ["Link:",song_link, True],
                        ["It may take some time to fetch the song", "[Not Playing from YouTube | Don't Sue Me Ples](https://www.youtube.com/watch?v=dQw4w9WgXcQ )", False],
                        ["Requested by:", ctx.author, True],
                        ["Duration:", duration, True]                     
                        ],
            footer = ["Made with 💓 by Tanjim Reza [https://www.facebook.com/tanjimreza]"],
            thumbnail = img
            ).build()       
    return embed
@bot.event
async def on_ready():
    activity = discord.Activity(type=discord.ActivityType.listening, name="Music")
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print("Building Guilds")
    for guild in bot.guilds:
        queue[guild.name] = []
        print(queue)
    print(bot.guilds)
    print("Bot is ready!")


async def play_next(ctx):
    try: 
        if len(queue[ctx.guild.name]) > 0:
            await play_music(ctx,queue[ctx.guild.name][0])
    except:
        print("No songs in queue")

async def play_music(ctx):
    try:
        if len(queue[ctx.guild.name]) > 0: 
            print(f"Current Queue: {queue[ctx.guild.name]}")
            #TODO:Combine Two Embeds into one with conditional args
            song_link, title, img, duration = getSongLink(queue[ctx.guild.name][0])
            filename = await YTDLSource.from_url(queue[ctx.guild.name][0], loop=bot.loop)
            embed = EmbedBuilder (
                    title = "Now Playing",
                    description = "",
                    color = int("65535"),
                    fields = [  ["Name:", title, True], 
                                ["Link:",song_link, True],
                                ["\u200B", "[Not Playing from YouTube | Don't Sue Me Ples](https://www.youtube.com/watch?v=dQw4w9WgXcQ )", False],
                                ["Requested by:", ctx.author, True],
                                ["Duration:", duration, True]                     
                                ],
                    footer = ["Made with 💓 by Tanjim Reza [https://www.facebook.com/tanjimreza]"],
                    # author = [message.author.name, message.author.avatar_url],
                    thumbnail = img
                    ).build()
            ctx.voice_client.play(filename, after=lambda e: bot.loop.create_task(play_next(ctx)))
            # await ctx.voice_client.play(filename, after=lambda e: print('Player error: %s' % e) if e else play_music(ctx))
            print(f"{queue[ctx.guild.name].pop(0)} popped. Now Q:{queue}")
            await ctx.respond(embed=embed)
    except Exception as e:
        print(f"Exception at play_music: {e}")


@bot.slash_command(guild_ids=config.GUILD_IDS)
async def play(ctx, name: str = None):
    name = " ".join(name)
    if not ctx.author.voice:
        await ctx.respond("You are not in a voice channel!")
        return
    song_link, title, img, duration = getSongLink(name)
    #? Adding Current Song to Queue
    queue[ctx.guild.name].append(song_link)
    embed = addedEmbed(ctx,title,song_link,duration,img)
    await ctx.respond(embed=embed,delete_after=5.0)
    # await ctx.message.add_reaction("✅")
    # await ctx.message.add_reaction("⏳")
    if ctx.voice_client is None:
        print("Creating Voice Client")
        print("Connecting to Voice Channel")
        voice = await ctx.author.voice.channel.connect()
        await play_music(ctx)

@bot.slash_command(guild_ids=config.GUILD_IDS)
async def pause(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.respond("Paused")
    else:
        await ctx.respond("Not Playing")

@bot.slash_command(guild_ids=config.GUILD_IDS)
async def resume(ctx):
    if ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.respond("Resumed")
    else:
        await ctx.respond("Not Paused")

@bot.slash_command(guild_ids=config.GUILD_IDS)
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.respond("Disconnected")
    else:
        await ctx.respond("Not Connected")
@bot.slash_command(guild_ids=config.GUILD_IDS)
async def skip(ctx):
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.respond("Skipped")
        ctx.voice_client.play()
    else:
        await ctx.respond("Not Playing")

bot.run(config.BOT_TOKEN)
