import os.path
import shutil
import asyncio

import discord
from discord.ext import commands
from scripts import env, downloader

# channel-audio mapping
channel_audio_paths = {}
# channel-loop mapping: None = infinite, int = remaining plays
channel_loop_counts = {}


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
            await ctx.send("> You are not in a voice channel.")
            return

        author = ctx.author
        channel = author.voice.channel
        channel_audio_paths[channel] = None
        await channel.connect()
        await ctx.send(f"Joined [{channel}] upon request of **{author.display_name}**")

    @bot.command()
    async def leave(ctx):
        await ctx.message.delete()
        if ctx.voice_client is None:
            await ctx.send("> I am not currently in a voice channel.")
            return

        if ctx.voice_client.is_playing():
            await ctx.send("> Please stop the music with !stop before leaving.")
            return

        channel = ctx.voice_client.channel
        del channel_audio_paths[channel]
        channel_loop_counts.pop(channel, None)
        audio_folder_path = os.path.join(os.getcwd(), "audio", str(channel.id))
        shutil.rmtree(audio_folder_path)
        await ctx.voice_client.disconnect()
        await ctx.send(f"Left [{channel}] upon request of **{ctx.author.display_name}**")

    @bot.command()
    async def play(ctx, url):
        await ctx.message.delete()
        if ctx.voice_client is None:
            await ctx.send("> I am not currently in a voice channel. Use !join to summon me.")
            return

        channel = ctx.voice_client.channel

        if ctx.voice_client.is_playing() or channel_audio_paths[channel] is not None:
            await ctx.send("> The previous music has not properly ended, you can use !stop to force")
            return

        message = await ctx.send("Preparing audio...")
        music_data = await asyncio.to_thread(downloader.try_download, url, ctx.voice_client.channel.id)

        if music_data is None:
            await message.edit(content="Failed downloading audio")
            return

        def unregister(error):
            if error:
                print(f"An error occurred while playing the audio: {error}")
            channel_audio_paths[channel] = None

        audio_source = discord.FFmpegOpusAudio(music_data[1], options='-af volume=0.5')
        ctx.voice_client.play(audio_source, after=unregister)
        channel_audio_paths[channel] = music_data[1]
        await message.edit(content=f":notes: {music_data[0]}")

    @bot.command()
    async def loop(ctx, url, times: int = None):
        await ctx.message.delete()
        if ctx.voice_client is None:
            await ctx.send("> I am not currently in a voice channel. Use !join to summon me.")
            return

        channel = ctx.voice_client.channel

        if ctx.voice_client.is_playing() or channel_audio_paths[channel] is not None:
            await ctx.send("> The previous music has not properly ended, you can use !stop to force.")
            return

        message = await ctx.send("Preparing audio...")
        music_data = await asyncio.to_thread(downloader.try_download, url, ctx.voice_client.channel.id)

        if music_data is None:
            await message.edit(content="Failed downloading audio")
            return

        # None = infinite loop, int = countdown
        channel_loop_counts[channel] = None if times is None else times

        def play_loop(error):
            if error:
                print(f"Loop playback error: {error}")
                channel_audio_paths[channel] = None
                channel_loop_counts.pop(channel, None)
                return

            remaining = channel_loop_counts.get(channel)

            # Finite loop: decrement and stop when exhausted
            if remaining is not None:
                if remaining <= 1:
                    channel_audio_paths[channel] = None
                    channel_loop_counts.pop(channel, None)
                    return
                else:
                    channel_loop_counts[channel] = remaining - 1

            # Re-queue if the voice client is still active (not stopped manually)
            vc = channel.guild.voice_client
            if vc and vc.is_connected() and channel_audio_paths.get(channel) is not None:
                audio_source = discord.FFmpegOpusAudio(music_data[1], options='-af volume=0.5')
                vc.play(audio_source, after=play_loop)

        audio_source = discord.FFmpegOpusAudio(music_data[1], options='-af volume=0.5')
        ctx.voice_client.play(audio_source, after=play_loop)
        channel_audio_paths[channel] = music_data[1]

        loop_label = "∞" if times is None else str(times)
        await message.edit(content=f":repeat: {music_data[0]} `[{loop_label}x]`")

    @bot.command()
    async def stop(ctx):
        await ctx.message.delete()

        if ctx.voice_client is None:
            await ctx.send("> Bot is not in voice channel.")
            return

        channel = ctx.voice_client.channel

        if not ctx.voice_client.is_playing() and channel_audio_paths[channel] is None:
            await ctx.send("> There is no audio being played.")
            return

        # Clear loop state before stopping so the after-callback doesn't re-queue
        channel_loop_counts.pop(channel, None)
        channel_audio_paths[channel] = None

        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        await ctx.send(f"Music cancelled by **{ctx.author.display_name}**")

    @bot.command()
    async def pause(ctx):
        await ctx.message.delete()
        if ctx.voice_client is None or not ctx.voice_client.is_playing():
            await ctx.send("> There is no audio being played.")
            return

        ctx.voice_client.pause()
        await ctx.send(f"Music paused by **{ctx.author.display_name}**")

    @bot.command()
    async def resume(ctx):
        await ctx.message.delete()
        if ctx.voice_client is None or not ctx.voice_client.is_paused():
            await ctx.send("> There is no audio paused.")
            return

        ctx.voice_client.resume()
        await ctx.send(f"Music resumed by **{ctx.author.display_name}**")

    @bot.event
    async def on_voice_state_update(member, before, after):
        # If the bot itself was unexpectedly disconnected, reset the channel state
        if member.id == bot.user.id and before.channel is not None and after.channel is None:
            channel = before.channel
            if channel in channel_audio_paths:
                channel_audio_paths[channel] = None
            channel_loop_counts.pop(channel, None)

    # Start bot
    bot.run(env.get_token(), reconnect=True)