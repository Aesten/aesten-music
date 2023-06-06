import os

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
            message = await ctx.send("You are not in a voice channel.")
            scheduler.delete_after(30, message)
            return

        channel = ctx.author.voice.channel
        channel_audio_paths[channel] = None
        await ctx.author.voice.channel.connect()

    @bot.command()
    async def leave(ctx):
        await ctx.message.delete()
        if ctx.voice_client is None:
            message = await ctx.send("I am not currently in a voice channel.")
            scheduler.delete_after(30, message)
            return

        if ctx.voice_client.is_playing():
            message = await ctx.send("Please stop the music with !stop before leaving.")
            scheduler.delete_after(30, message)
            return

        channel = ctx.author.voice.channel
        del channel_audio_paths[channel]
        await ctx.voice_client.disconnect()

    @bot.command()
    async def play(ctx, url):
        await ctx.message.delete()
        if ctx.voice_client is None:
            message = await ctx.send("I am not currently in a voice channel. Use !join to summon me.")
            scheduler.delete_after(30, message)
            return

        if ctx.voice_client.is_playing():
            message = await ctx.send("The previous music has not ended, you can use !stop to force")
            scheduler.delete_after(30, message)
            return

        message = await ctx.send("Preparing audio...")
        music_data = downloader.try_download(url)

        if music_data is None:
            await message.edit(content="Failed downloading audio")
            return

        def delete_audio_file(error):
            if error:
                print(f"An error occurred while playing the audio: {error}")
            else:
                os.remove(music_data[1])

        channel = ctx.voice_client.channel
        audio_source = discord.FFmpegOpusAudio(music_data[1], options='-af volume=0.5')
        ctx.voice_client.play(audio_source, after=delete_audio_file)
        channel_audio_paths[channel] = music_data[1]
        await message.edit(content=f"Now playing: {music_data[0]}")

    @bot.command()
    async def stop(ctx):
        await ctx.message.delete()
        if ctx.voice_client is None or not ctx.voice_client.is_playing():
            message = await ctx.send("There is no audio being played.")
            scheduler.delete_after(30, message)
            return

        ctx.voice_client.stop()
        channel = ctx.voice_client.channel
        os.remove(channel_audio_paths[channel])

    @bot.command()
    async def pause(ctx):
        await ctx.message.delete()
        if ctx.voice_client is None or not ctx.voice_client.is_playing():
            message = await ctx.send("There is no audio being played.")
            scheduler.delete_after(30, message)
            return

        ctx.voice_client.pause()

    @bot.command()
    async def resume(ctx):
        await ctx.message.delete()
        if ctx.voice_client is None or not ctx.voice_client.is_paused():
            message = await ctx.send("There is no audio paused.")
            scheduler.delete_after(30, message)
            return

        ctx.voice_client.resume()

    # Start bot
    bot.run(env.get_token())
