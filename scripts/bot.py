import os.path
import shutil

import discord
from discord.ext import commands
from scripts import env, downloader, scheduler

# channel-audio mapping
channel_audio_paths = {}


def start_bot():
    # Print OAuth URL
    client_id = '1115631469616971819'
    permissions_int = 35184375245824
    print("OAuth2 URL:", discord.utils.oauth_url(client_id, permissions=discord.Permissions(permissions_int)))

    # Create bot
    intents = discord.Intents.default()
    intents.message_content = True
    intents.messages = True
    bot = commands.Bot(command_prefix='!', intents=intents)

    # Commands
    @bot.command()
    async def join(ctx):
        await ctx.message.delete()
        if ctx.author.voice is None:
            message = await ctx.send("> You are not in a voice channel.")
            scheduler.schedule_delete(30, message)
            return

        author = ctx.author
        channel = author.voice.channel
        channel_audio_paths[channel] = None
        await channel.connect()
        await ctx.send(f"Joined [{channel}] upon request of [{author.display_name}]")

    @bot.command()
    async def leave(ctx):
        await ctx.message.delete()
        if ctx.voice_client is None:
            message = await ctx.send("> I am not currently in a voice channel.")
            scheduler.schedule_delete(30, message)
            return

        if ctx.voice_client.is_playing():
            message = await ctx.send("> Please stop the music with !stop before leaving.")
            scheduler.schedule_delete(30, message)
            return

        channel = ctx.voice_client.channel
        del channel_audio_paths[channel]
        audio_folder_path = os.path.join(os.getcwd(), "audio", str(channel.id))
        shutil.rmtree(audio_folder_path)
        await ctx.voice_client.disconnect()
        await ctx.send(f"Left [{channel}] upon request of [{ctx.author.display_name}]")

    @bot.command()
    async def play(ctx, url):
        await ctx.message.delete()
        if ctx.voice_client is None:
            message = await ctx.send("> I am not currently in a voice channel. Use !join to summon me.")
            scheduler.schedule_delete(30, message)
            return

        channel = ctx.voice_client.channel

        if ctx.voice_client.is_playing() or channel_audio_paths[channel] is not None:
            message = await ctx.send("> The previous music has not properly ended, you can use !stop to force")
            scheduler.schedule_delete(30, message)
            return

        message = await ctx.send("Preparing audio...")
        music_data = downloader.try_download(url, ctx.voice_client.channel.id)

        if music_data is None:
            await message.edit(content="Failed downloading audio")
            return

        def unregister(error):
            if error:
                print(f"An error occurred while playing the audio: {error}")
            else:
                channel_audio_paths[channel] = None

        audio_source = discord.FFmpegOpusAudio(music_data[1], options='-af volume=0.5')
        ctx.voice_client.play(audio_source, after=unregister)
        channel_audio_paths[channel] = music_data[1]
        await message.edit(content=f":notes: {music_data[0]}")

    @bot.command()
    async def stop(ctx):
        await ctx.message.delete()

        if ctx.voice_client is None:
            message = await ctx.send("> Bot is not in voice channel.")
            scheduler.schedule_delete(30, message)
            return

        channel = ctx.voice_client.channel

        if not ctx.voice_client.is_playing() and channel_audio_paths[channel] is None:
            message = await ctx.send("> There is no audio being played.")
            scheduler.schedule_delete(30, message)
            return

        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        channel_audio_paths[channel] = None
        await ctx.send(f"Music cancelled by [{ctx.author.display_name}]")

    @bot.command()
    async def pause(ctx):
        await ctx.message.delete()
        if ctx.voice_client is None or not ctx.voice_client.is_playing():
            message = await ctx.send("> There is no audio being played.")
            scheduler.schedule_delete(30, message)
            return

        ctx.voice_client.pause()
        await ctx.send(f"Music paused by [{ctx.author.display_name}]")

    @bot.command()
    async def resume(ctx):
        await ctx.message.delete()
        if ctx.voice_client is None or not ctx.voice_client.is_paused():
            message = await ctx.send("> There is no audio paused.")
            scheduler.schedule_delete(30, message)
            return

        ctx.voice_client.resume()
        await ctx.send(f"Music resumed by [{ctx.author.display_name}]")

    # Start bot
    bot.run(env.get_token())
