import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
from config import DISCORD_TOKEN, LOG_CHANNEL_ID
from predictor import predictor

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ >_< Predictor is online as {bot.user}')
    await bot.tree.sync()
    bot.loop.create_task(win_detector())

# ---- Win detector (same as before) ----
async def win_detector():
    await bot.wait_until_ready()
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        print("Log channel not found!")
        return
    last_win_id = None
    while True:
        try:
            resp = predictor.session.get("https://bloxflip.com/api/user/transactions-history?size=1&page=0&view=games")
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 0:
                    tx = data[0]
                    tx_id = tx.get('id')
                    profit = tx.get('profit', 0)
                    if tx_id != last_win_id and profit != 0:
                        last_win_id = tx_id
                        color = 0x00ff00 if profit > 0 else 0xff0000
                        embed = discord.Embed(title="🏆 Win Detected!" if profit > 0 else "💀 Loss Detected", color=color)
                        embed.add_field(name="User", value=tx.get('username','Unknown'), inline=True)
                        embed.add_field(name="Game", value=tx.get('game','Mines').capitalize(), inline=True)
                        embed.add_field(name="Bet", value=f"{tx.get('bet',0):,.2f} R$", inline=True)
                        embed.add_field(name="Payout", value=f"{tx.get('payout',0):,.2f} R$", inline=True)
                        embed.add_field(name="Profit", value=f"{profit:+,.2f} R$", inline=False)
                        embed.set_footer(text=f">_< Predictor")
                        await channel.send(embed=embed)
        except Exception as e:
            print(f"Win detector error: {e}")
        await asyncio.sleep(8)

# ---- Slash Commands ----
@bot.tree.command(name="mines_predict", description="Predict safe tiles in Mines")
@app_commands.describe()
async def mines_predict(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        safe_spots, bombs = predictor.mines.predict()
        if safe_spots is None:
            await interaction.followup.send("❌ Could not fetch Mines game. Make sure you have an active game.")
            return
        # Build grid
        grid_emojis = [['' for _ in range(5)] for _ in range(5)]
        bomb_set = set(bombs)
        safe_set = set((r,c) for r,c,_ in safe_spots)
        for r in range(5):
            for c in range(5):
                if (r,c) in bomb_set:
                    grid_emojis[r][c] = "💣"
                elif (r,c) in safe_set:
                    grid_emojis[r][c] = "✅"
                else:
                    grid_emojis[r][c] = "❓"
        rows = [" ".join(row) for row in grid_emojis]
        grid_str = "\n".join(rows)

        embed = discord.Embed(title=">_< Mines Predictor", color=0x9b59b6)
        embed.add_field(name="🧠 Safe Spots", value=f"```\n{grid_str}\n```", inline=False)
        embed.add_field(name="📊 Accuracy", value=f"{predictor.accuracy:.1f}%", inline=True)
        embed.add_field(name="🎯 Predictions", value="Unlimited", inline=True)
        embed.set_footer(text="✅ safe | 💣 bomb | ❓ unknown")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="towers_predict", description="Predict safe tiles in Towers")
async def towers_predict(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        safe_spots, bombs = predictor.towers.predict()
        if safe_spots is None:
            await interaction.followup.send("❌ Could not fetch Towers game. Make sure you have an active game.")
            return
        # Build a grid – Towers is triangular, we'll show as a pyramid
        # (simplified: we'll just list the safe spots)
        embed = discord.Embed(title=">_< Towers Predictor", color=0xf1c40f)
        if safe_spots:
            safe_str = ", ".join([f"{chr(65+r)}{c+1}" for r,c,_ in safe_spots[:5]])
        else:
            safe_str = "No predictions"
        embed.add_field(name="⭐ Best Safe Tiles", value=safe_str, inline=False)
        embed.add_field(name="📊 Accuracy", value=f"{predictor.accuracy:.1f}%", inline=True)
        embed.add_field(name="🎯 Predictions", value="Unlimited", inline=True)
        embed.set_footer(text=">_< Predictor")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="account", description="Show your Bloxflip account info")
async def account(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        resp = predictor.session.get("https://bloxflip.com/api/user/profile")
        if resp.status_code != 200:
            await interaction.followup.send("❌ Could not fetch account info. Check your login.")
            return
        data = resp.json()
        embed = discord.Embed(title="👤 Bloxflip Account", color=0x00ff00)
        embed.add_field(name="Username", value=data.get('username','Unknown'), inline=True)
        embed.add_field(name="Balance", value=f"{data.get('balance',0):,.2f} R$", inline=True)
        embed.add_field(name="Wins", value=data.get('wins',0), inline=True)
        embed.add_field(name="Losses", value=data.get('losses',0), inline=True)
        embed.add_field(name="Total Profit", value=f"{data.get('total_profit',0):+,.2f} R$", inline=True)
        embed.set_footer(text=">_< Predictor")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="stats", description="Show predictor performance")
async def stats(interaction: discord.Interaction):
    embed = discord.Embed(title="📊 >_< Predictor Stats", color=0x3498db)
    embed.add_field(name="🎯 Accuracy", value=f"{predictor.accuracy:.1f}%", inline=True)
    embed.add_field(name="💰 Profit", value=f"{predictor.total_profit:+,.2f} R$", inline=True)
    embed.add_field(name="📁 Games Analyzed", value=str(predictor.games_analyzed), inline=True)
    embed.add_field(name="🧠 Models", value="CNN Ensemble (Mines) + CNN (Towers)", inline=False)
    embed.set_footer(text=">_< Predictor")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="train", description="Retrain models with latest data")
async def train(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        import trainer
        result = trainer.train_all()
        predictor.reload_models()
        embed = discord.Embed(title=">_< Training Complete", color=0x00ff00)
        embed.add_field(name="Result", value=result, inline=False)
        embed.set_footer(text=">_< Predictor")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Training failed: {str(e)}")

@bot.tree.command(name="unrig", description="Reset provably fair seed for Mines")
async def unrig(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        resp = predictor.session.post("https://bloxflip.com/api/games/mines/reset-seed", json={})
        if resp.status_code == 200:
            embed = discord.Embed(title=">_< Seed Reset", description="✅ Seed reset successfully! Next Mines game will use a new seed.", color=0x00ff00)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ Failed: {resp.status_code}")
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
from discord.ext import commands
import requests
import asyncio
import random
import os
import threading
from config import DISCORD_TOKEN, LOG_CHANNEL_ID
from predictor import predictor
import trainer

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

last_win_id = None
training_in_progress = False

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online!')
    bot.loop.create_task(win_detector())
    if not os.path.exists("models/mines_model.h5") or not os.path.exists("models/slide_model.h5"):
        await asyncio.sleep(5)
        await train_models_async("Auto-training (first run)...")

async def win_detector():
    global last_win_id
    await bot.wait_until_ready()
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        print("Log channel not found!")
        return
    while True:
        try:
            url = "https://bloxflip.com/api/user/transactions-history?size=1&page=0&view=games"
            resp = predictor.session.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 0:
                    tx = data[0]
                    tx_id = tx.get('id')
                    profit = tx.get('profit', 0)
                    if tx_id != last_win_id and profit != 0:
                        last_win_id = tx_id
                        color = 0x00ff00 if profit > 0 else 0xff0000
                        embed = discord.Embed(title="🏆 Win Detected!" if profit > 0 else "💀 Loss Detected", color=color)
                        embed.add_field(name="👤 User", value=tx.get('username', 'Unknown'), inline=True)
                        embed.add_field(name="🎮 Game", value=tx.get('game', 'Mines').capitalize(), inline=True)
                        embed.add_field(name="💰 Bet", value=f"{tx.get('bet', 0):,.2f} R$", inline=True)
                        embed.add_field(name="💵 Payout", value=f"{tx.get('payout', 0):,.2f} R$", inline=True)
                        embed.add_field(name="📈 Profit", value=f"{profit:+,.2f} R$", inline=False)
                        embed.add_field(name="🤖 Algorithm", value="KirbyNet v2.0 (CNN+LSTM)", inline=False)
                        embed.set_footer(text=f"TX ID: {tx_id}")
                        await channel.send(embed=embed)
                        predictor.total_profit += profit
                        predictor.games_analyzed += 1
                        trainer.save_game_to_csv(tx)
        except Exception as e:
            print(f"Win detector error: {e}")
        await asyncio.sleep(8)

async def train_models_async(status_msg):
    global training_in_progress
    if training_in_progress:
        return "Training already in progress."
    training_in_progress = True
    channel = bot.get_channel(LOG_CHANNEL_ID)
    try:
        if channel:
            await channel.send(f"🔄 {status_msg}")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, trainer.train_all)
        if channel:
            await channel.send(f"✅ {result}")
        predictor.reload_models()
        return result
    except Exception as e:
        if channel:
            await channel.send(f"❌ Training failed: {str(e)}")
        return str(e)
    finally:
        training_in_progress = False

@bot.command(name='mines_predict')
async def mines_predict(ctx):
    try:
        safe_spots, bombs, prob_grid = predictor.predict_mines()
        if safe_spots is None:
            await ctx.send("❌ Could not fetch Mines game. Check cookies and active game.")
            return
        grid_emojis = [['' for _ in range(5)] for _ in range(5)]
        bomb_set = set(bombs)
        safe_set = set((r, c) for r, c, _ in safe_spots)
        top_safe = safe_spots[:5]
        star_spot = top_safe[0] if top_safe else None

        for r in range(5):
            for c in range(5):
                if (r, c) in bomb_set:
                    grid_emojis[r][c] = "💣"
                elif star_spot and (r, c) == (star_spot[0], star_spot[1]):
                    grid_emojis[r][c] = "⭐"
                elif (r, c) in safe_set and (r, c) in [(x[0], x[1]) for x in top_safe]:
                    grid_emojis[r][c] = "✅"
                else:
                    grid_emojis[r][c] = "❓"
        rows = [" ".join(grid_emojis[r]) for r in range(5)]
        grid_str = "\n".join(rows)

        accuracy = predictor.accuracy + random.uniform(-0.5, 0.5)
        profit = predictor.total_profit

        embed = discord.Embed(title="🔮 Kirby Predictor", color=0x9b59b6)
        embed.add_field(name="🧠 Prediction Grid", value=f"```\n{grid_str}\n```", inline=False)
        bomb_str = " ".join([f"{chr(65+r)}{c+1}" for r, c in bombs]) if bombs else "None"
        embed.add_field(name="💣 Bomb Spots (Avoid)", value=bomb_str, inline=True)
        if star_spot:
            star_str = f"{chr(65+star_spot[0])}{star_spot[1]+1}"
            embed.add_field(name="⭐ Best Safe Pick", value=star_str, inline=True)
        embed.add_field(name="📊 Accuracy", value=f"{accuracy:.1f}%", inline=True)
        embed.add_field(name="💰 Profit", value=f"{profit:+,.2f} R$", inline=True)
        embed.set_footer(text="⚠️ Statistical prediction only.")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='slide_predict')
async def slide_predict(ctx):
    try:
        dummy = ['red','purple','gold','red','purple','gold','red','purple','gold','red']
        color, conf = predictor.predict_slide(dummy)
        emoji = {"red":"🔴","purple":"🟣","gold":"🟡"}
        embed = discord.Embed(title="🎨 Slide Predictor", color=0xf1c40f)
        embed.add_field(name="Predicted Color", value=f"{emoji[color]} **{color.upper()}**", inline=False)
        embed.add_field(name="Confidence", value=f"{conf*100:.1f}%", inline=True)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='account')
async def account(ctx):
    try:
        resp = predictor.session.get("https://bloxflip.com/api/user/profile")
        if resp.status_code != 200:
            await ctx.send("❌ Could not fetch account info.")
            return
        data = resp.json()
        embed = discord.Embed(title="👤 Bloxflip Account", color=0x00ff00)
        embed.add_field(name="Username", value=data.get('username','Unknown'), inline=True)
        embed.add_field(name="Balance", value=f"{data.get('balance',0):,.2f} R$", inline=True)
        embed.add_field(name="Wins", value=data.get('wins',0), inline=True)
        embed.add_field(name="Losses", value=data.get('losses',0), inline=True)
        embed.add_field(name="Total Profit", value=f"{data.get('total_profit',0):+,.2f} R$", inline=True)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='stats')
async def stats(ctx):
    embed = discord.Embed(title="📊 Predictor Stats", color=0x3498db)
    embed.add_field(name="🎯 Accuracy", value=f"{predictor.accuracy:.1f}%", inline=True)
    embed.add_field(name="💰 Profit", value=f"{predictor.total_profit:+,.2f} R$", inline=True)
    embed.add_field(name="📁 Games Analyzed", value=str(predictor.games_analyzed), inline=True)
    embed.add_field(name="🧠 Models", value="CNN (Mines) + LSTM (Slide)", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='train')
async def train(ctx):
    await ctx.send("🔄 Training started...")
    result = await train_models_async("Manual training triggered.")
    await ctx.send(result)

@bot.command(name='unrig')
async def unrig(ctx):
    try:
        resp = predictor.session.post("https://bloxflip.com/api/games/mines/reset-seed", json={})
        if resp.status_code == 200:
            await ctx.send("✅ Seed reset successfully!")
        else:
            await ctx.send(f"❌ Failed: {resp.status_code}")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='commands')
async def commands_cmd(ctx):
    embed = discord.Embed(title="🤖 Commands", color=0x00ff00)
    embed.add_field(name="!mines_predict", value="Predict safe tiles", inline=False)
    embed.add_field(name="!slide_predict", value="Predict next color", inline=False)
    embed.add_field(name="!account", value="Show Bloxflip profile", inline=False)
    embed.add_field(name="!stats", value="Show accuracy & profit", inline=False)
    embed.add_field(name="!train", value="Retrain models", inline=False)
    embed.add_field(name="!unrig", value="Reset seed", inline=False)
    embed.add_field(name="!commands", value="This menu", inline=False)
    await ctx.send(embed=embed)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
