import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import typing

load_dotenv()
TOKEN = os.getenv('TOKEN')

# Define intents
intents = discord.Intents.default()
intents.messages = True
intents.presences = False
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Dictionary to store game data
game_data = {}

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    await tree.sync()
    print("Ready!")

@tree.command(name='join', description='Join the Exquisite Corpse game')
async def join_game(ctx):
    global game_data
    channel_id = ctx.channel.id
    user_id = ctx.user.id
    
    if channel_id not in game_data:
        game_data[channel_id] = {"players": [], "sentence": [], "turn_player": None, "game_started": False, "visible_words": 5}

    if user_id not in game_data[channel_id]["players"] and game_data[channel_id]["game_started"]:
        await ctx.response.send_message(f"{ctx.user.mention} Sorry, the game has already been started, and you are not in it.")
        return

    if user_id not in game_data[channel_id]["players"]:
        game_data[channel_id]["players"].append(user_id)
        await ctx.response.send_message(f'{ctx.user.mention} has joined the game!')
    else:
        await ctx.response.send_message(f'{ctx.user.mention} is already in the player list!')

@tree.command(name='start', description='Start a new game')
async def start_game(ctx, visible_words: typing.Optional[int] = 5):
    global game_data
    channel_id = ctx.channel.id
    user_id = ctx.user.id

    if channel_id not in game_data:
        await ctx.response.send_message("No game data found for this channel. Use `/join` to begin creating a new game.")
        return

    # Check if there are enough players
    if len(game_data[channel_id]["players"]) < 1:
        await ctx.response.send_message("Not enough players! At least 1 player is required. Use `/join` to add more players.")
        return

    try:
        game_data[channel_id]["visible_words"] = int(visible_words)
    except Exception as e:
        await ctx.response.send_message("Visible_words must be a number.")
        return

    game_data[channel_id]["sentence"] = []
    game_data[channel_id]["turn_player"] = user_id
    game_data[channel_id]["game_started"] = True
    
    player_ids_string = ' '.join(f'<@{value}>' for value in game_data[channel_id]["players"])

    await ctx.response.send_message(f"Starting a new game!\nPlayers in this game: {player_ids_string}\nNumber of words that will be visible to the next player: {game_data[channel_id]['visible_words']}\n<@{game_data[channel_id]['turn_player']}>'s turn. Use `/play` to continue the sentence.")

@tree.command(name='play', description='Continue the sentence')
async def play_turn(ctx, sentence: str):
    global game_data
    channel_id = ctx.channel.id
    user_id = ctx.user.id

    if channel_id not in game_data:
        await ctx.response.send_message("No game data found for this channel. Use `/join` to begin creating a new game.")
        return
    
    if not game_data[channel_id]["game_started"]:
        await ctx.response.send_message(f"The game has not been started. The player who wants to go first should do `/start`.")
        return
    
    if user_id not in game_data[channel_id]["players"] and game_data[channel_id]["game_started"]:
        await ctx.response.send_message(f"{ctx.user.mention} Sorry, the game has already been started, and you are not in it.")
        return

    if user_id not in game_data[channel_id]["players"]:
        await ctx.response.send_message(f"{ctx.user.mention} You're not in the game. Use `/join` to join.")
        return

    if user_id != game_data[channel_id]["turn_player"]:
        await ctx.response.send_message(f"{ctx.user.mention} It's not your turn yet. Wait for your turn to play.")
        return
    
    new_words = sentence.split()
    game_data[channel_id]["sentence"].append({"player": ctx.user.id, "words": new_words})

    current_sentence = new_words.copy()
    while len(current_sentence) > int(game_data[channel_id]["visible_words"]):
        current_sentence.pop(0)
    current_sentence = ' '.join(current_sentence)

    # Get the next player in the order they joined
    player_index = game_data[channel_id]["players"].index(user_id)
    next_player_index = (player_index + 1) % len(game_data[channel_id]["players"])
    next_player_id = game_data[channel_id]["players"][next_player_index]
    game_data[channel_id]["turn_player"] = next_player_id

    await ctx.response.send_message(f"Turn is complete! Current sentence: {current_sentence}\n<@{game_data[channel_id]['turn_player']}>'s turn!")

@tree.command(name='reveal', description='Reveal the full story')
async def reveal_story(ctx):
    global game_data
    channel_id = ctx.channel.id

    if channel_id not in game_data or not game_data[channel_id]["sentence"]:
        await ctx.response.send_message("The story is not ready yet.")
        return
    
    story = ' '.join([word for part in game_data[channel_id]["sentence"] for word in part["words"]])
    
    # Split the story into chunks that fit within the Discord message character limit
    chunks = [story[i:i+1940] for i in range(0, len(story), 1940)]
    
    for i, chunk in enumerate(chunks):
        if i == 0:
            await ctx.response.send_message(f"The story so far (Part {i + 1}):\n{chunk}")
        else:
            await ctx.response.send_message(f"Part {i + 1}:\n{chunk}")

@tree.command(name='clear', description='Clear the current story')
async def clear_story(ctx):
    global game_data
    channel_id = ctx.channel.id
    user_id = ctx.user.id

    if channel_id not in game_data:
        await ctx.response.send_message("No game data found for this channel. Use `/join` and `/start` to begin a new game.")
        return

    if user_id not in game_data[channel_id]["players"]:
        await ctx.response.send_message(f"{ctx.user.mention} You're not authorized to clear the story.")
        return

    #game_data[channel_id].clear()
    game_data[channel_id]["sentence"] = []
    game_data[channel_id]["turn_player"] = None
    game_data[channel_id]["players"] = []
    game_data[channel_id]["game_started"] = False
    game_data[channel_id]["visible_words"] = 5

    await ctx.response.send_message("The story has been cleared. Starting fresh!")

client.run(TOKEN)
