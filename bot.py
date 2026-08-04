import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
import os
from config import DISCORD_TOKEN, LOG_CHANNEL_ID
from predictor import predictor, BloxflipAuth

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def get_predictor_for_user(user_id):
    user_session = predictor.get_user_session(user_id)
    if user_session:
        from predictor import BloxflipPredictor
        return BloxflipPredictor(session=user_session)
    else:
        return predictor

# ---------- Account Command Group ----------
account_group = app_commands.Group(name="account", description="Manage your Bloxflip account connection")
bot.tree.add_command(account_group)

@account_group.command(name="connect", description="Connect your Bloxflip account")
async def account_connect(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔐 Connect Bloxflip Account",
        description=(
            "Login with Roblox is the easy way: no cookies, just your Roblox username and a quick bio check.\n\n"
            "Prefer the old way? Paste tokens still works."
        ),
        color=0x9b59b6
    )
    view = discord.ui.View()
    roblox_button = discord.ui.Button(label="Login with Roblox", style=discord.ButtonStyle.primary, custom_id="roblox_login")
    tokens_button = discord.ui.Button(label="Paste Tokens", style=discord.ButtonStyle.secondary, custom_id="tokens_login")
    view.add_item(roblox_button)
    view.add_item(tokens_button)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@account_group.command(name="unlink", description="Disconnect your Bloxflip account")
async def account_unlink(interaction: discord.Interaction):
    if interaction.user.id in predictor.user_sessions:
        del predictor.user_sessions[interaction.user.id]
        await interaction.response.send_message("🔓 Account unlinked. You can reconnect with `/account connect`.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ You don't have a linked account.", ephemeral=True)

# ---------- Button & Modal Handlers ----------
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get("custom_id")
        if custom_id == "roblox_login":
            modal = discord.ui.Modal(title="Login with Roblox")
            modal.add_item(discord.ui.TextInput(label=".ROBLOSECURITY Cookie", placeholder="Paste your cookie here", style=discord.TextStyle.paragraph))
            await interaction.response.send_modal(modal)
        elif custom_id == "tokens_login":
            modal = discord.ui.Modal(title="Paste Tokens")
            modal.add_item(discord.ui.TextInput(label="app.rt", placeholder="Enter app.rt value"))
            modal.add_item(discord.ui.TextInput(label="app.at", placeholder="Enter app.at value"))
            await interaction.response.send_modal(modal)

@bot.event
async def on_modal_submit(interaction: discord.Interaction):
    # --- Roblox login ---
    if interaction.data.get("title") == "Login with Roblox":
        cookie = interaction.data["components"][0]["components"][0]["value"]
        try:
            test_auth = BloxflipAuth(roblox_cookie=cookie)
            test_session = test_auth.get_session()
            resp = test_session.get("https://bloxflip.com/api/user/profile", timeout=10)
            if resp.status_code != 200:
                await interaction.response.send_message("❌ Invalid Roblox cookie – could not fetch profile. Check your cookie.", ephemeral=True)
                return
            predictor.set_user_session(interaction.user.id, {"type": "roblox", "cookie": cookie})
            await interaction.response.send_message("✅ Successfully connected with Roblox!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Authentication failed: {str(e)}", ephemeral=True)

    # --- Tokens login ---
    elif interaction.data.get("title") == "Paste Tokens":
        app_rt = interaction.data["components"][0]["components"][0]["value"]
        app_at = interaction.data["components"][1]["components"][0]["value"]
        try:
            test_auth = BloxflipAuth(app_rt=app_rt, app_at=app_at)
            test_session = test_auth.get_session()
            resp = test_session.get("https://bloxflip.com/api/user/profile", timeout=10)
            if resp.status_code != 200:
                await interaction.response.send_message("❌ Invalid tokens – could not fetch profile. Check your app.rt and app.at values.", ephemeral=True)
                return
            predictor.set_user_session(interaction.user.id, {"type": "tokens", "app_rt": app_rt, "app_at": app_at})
            await interaction.response.send_message("✅ Successfully connected with tokens!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Authentication failed: {str(e)}", ephemeral=True)

# ---------- Slash Commands ----------
@bot.tree.command(name="mines_predict", description="Predict safe tiles in Mines")
async def mines_predict(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        local_predictor = get_predictor_for_user(interaction.user.id)
        safe_spots, bombs = local_predictor.mines.predict()
        if safe_spots is None:
            await interaction.followup.send("❌ Could not fetch Mines game. Make sure you have an active game.")
            return
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
        embed.add_field(name="📊 Accuracy", value=f"{local_predictor.accuracy:.1f}%", inline=True)
        embed.add_field(name="🎯 Predictions", value="Unlimited", inline=True)
        embed.set_footer(text="✅ safe | 💣 bomb | ❓ unknown")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="towers_predict", description="Predict safe tiles in Towers")
async def towers_predict(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        local_predictor = get_predictor_for_user(interaction.user.id)
        safe_spots, bombs = local_predictor.towers.predict()
        if safe_spots is None:
            await interaction.followup.send("❌ Could not fetch Towers game. Make sure you have an active game.")
            return
        embed = discord.Embed(title=">_< Towers Predictor", color=0xf1c40f)
        if safe_spots:
            safe_str = ", ".join([f"{chr(65+r)}{c+1}" for r,c,_ in safe_spots[:5]])
        else:
            safe_str = "No predictions"
        embed.add_field(name="⭐ Best Safe Tiles", value=safe_str, inline=False)
        embed.add_field(name="📊 Accuracy", value=f"{local_predictor.accuracy:.1f}%", inline=True)
        embed.add_field(name="🎯 Predictions", value="Unlimited", inline=True)
        embed.set_footer(text=">_< Predictor")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="account_info", description="Show your Bloxflip account info")
async def account_info(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        local_predictor = get_predictor_for_user(interaction.user.id)
        resp = local_predictor.session.get("https://bloxflip.com/api/user/profile")
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
        local_predictor = get_predictor_for_user(interaction.user.id)
        resp = local_predictor.session.post("https://bloxflip.com/api/games/mines/reset-seed", json={})
        if resp.status_code == 200:
            embed = discord.Embed(title=">_< Seed Reset", description="✅ Seed reset successfully! Next Mines game will use a new seed.", color=0x00ff00)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ Failed: {resp.status_code}")
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

# ---------- Sync command ----------
@bot.command(name='sync')
async def sync_commands(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ You need administrator permissions.")
        return
    try:
        await bot.tree.sync(guild=ctx.guild)
        await ctx.send("✅ Slash commands synced to this server! You can now use `/` commands.")
    except Exception as e:
        await ctx.send(f"❌ Sync failed: {e}")

# ---------- Win detector ----------
@bot.event
async def on_ready():
    print(f'✅ >_< Predictor is online as {bot.user}')
    await bot.tree.sync()
    bot.loop.create_task(win_detector())

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
                        embed.set_footer(text=">_< Predictor")
                        await channel.send(embed=embed)
        except Exception as e:
            print(f"Win detector error: {e}")
        await asyncio.sleep(8)

# ===== THIS IS THE ONLY LINE AT THE BOTTOM =====
bot.run(DISCORD_TOKEN)import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import random
import os
from config import DISCORD_TOKEN, LOG_CHANNEL_ID
from predictor import predictor, BloxflipAuth

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def get_predictor_for_user(user_id):
    user_session = predictor.get_user_session(user_id)
    if user_session:
        from predictor import BloxflipPredictor
        return BloxflipPredictor(session=user_session)
    else:
        return predictor

# ---------- Account Command Group ----------
account_group = app_commands.Group(name="account", description="Manage your Bloxflip account connection")
bot.tree.add_command(account_group)

@account_group.command(name="connect", description="Connect your Bloxflip account")
async def account_connect(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔐 Connect Bloxflip Account",
        description=(
            "Login with Roblox is the easy way: no cookies, just your Roblox username and a quick bio check.\n\n"
            "Prefer the old way? Paste tokens still works."
        ),
        color=0x9b59b6
    )
    view = discord.ui.View()
    roblox_button = discord.ui.Button(label="Login with Roblox", style=discord.ButtonStyle.primary, custom_id="roblox_login")
    tokens_button = discord.ui.Button(label="Paste Tokens", style=discord.ButtonStyle.secondary, custom_id="tokens_login")
    view.add_item(roblox_button)
    view.add_item(tokens_button)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@account_group.command(name="unlink", description="Disconnect your Bloxflip account")
async def account_unlink(interaction: discord.Interaction):
    if interaction.user.id in predictor.user_sessions:
        del predictor.user_sessions[interaction.user.id]
        await interaction.response.send_message("🔓 Account unlinked. You can reconnect with `/account connect`.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ You don't have a linked account.", ephemeral=True)

# ---------- Button & Modal Handlers ----------
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get("custom_id")
        if custom_id == "roblox_login":
            modal = discord.ui.Modal(title="Login with Roblox")
            modal.add_item(discord.ui.TextInput(label=".ROBLOSECURITY Cookie", placeholder="Paste your cookie here", style=discord.TextStyle.paragraph))
            await interaction.response.send_modal(modal)
        elif custom_id == "tokens_login":
            modal = discord.ui.Modal(title="Paste Tokens")
            modal.add_item(discord.ui.TextInput(label="app.rt", placeholder="Enter app.rt value"))
            modal.add_item(discord.ui.TextInput(label="app.at", placeholder="Enter app.at value"))
            await interaction.response.send_modal(modal)

@bot.event
async def on_modal_submit(interaction: discord.Interaction):
    # --- Roblox login ---
    if interaction.data.get("title") == "Login with Roblox":
        cookie = interaction.data["components"][0]["components"][0]["value"]
        try:
            test_auth = BloxflipAuth(roblox_cookie=cookie)
            test_session = test_auth.get_session()
            resp = test_session.get("https://bloxflip.com/api/user/profile", timeout=10)
            if resp.status_code != 200:
                await interaction.response.send_message("❌ Invalid Roblox cookie – could not fetch profile. Check your cookie.", ephemeral=True)
                return
            predictor.set_user_session(interaction.user.id, {"type": "roblox", "cookie": cookie})
            await interaction.response.send_message("✅ Successfully connected with Roblox!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Authentication failed: {str(e)}", ephemeral=True)

    # --- Tokens login ---
    elif interaction.data.get("title") == "Paste Tokens":
        app_rt = interaction.data["components"][0]["components"][0]["value"]
        app_at = interaction.data["components"][1]["components"][0]["value"]
        try:
            test_auth = BloxflipAuth(app_rt=app_rt, app_at=app_at)
            test_session = test_auth.get_session()
            resp = test_session.get("https://bloxflip.com/api/user/profile", timeout=10)
            if resp.status_code != 200:
                await interaction.response.send_message("❌ Invalid tokens – could not fetch profile. Check your app.rt and app.at values.", ephemeral=True)
                return
            predictor.set_user_session(interaction.user.id, {"type": "tokens", "app_rt": app_rt, "app_at": app_at})
            await interaction.response.send_message("✅ Successfully connected with tokens!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Authentication failed: {str(e)}", ephemeral=True)

# ---------- Slash Commands ----------
@bot.tree.command(name="mines_predict", description="Predict safe tiles in Mines")
async def mines_predict(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        local_predictor = get_predictor_for_user(interaction.user.id)
        safe_spots, bombs = local_predictor.mines.predict()
        if safe_spots is None:
            await interaction.followup.send("❌ Could not fetch Mines game. Make sure you have an active game.")
            return
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
        embed.add_field(name="📊 Accuracy", value=f"{local_predictor.accuracy:.1f}%", inline=True)
        embed.add_field(name="🎯 Predictions", value="Unlimited", inline=True)
        embed.set_footer(text="✅ safe | 💣 bomb | ❓ unknown")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="towers_predict", description="Predict safe tiles in Towers")
async def towers_predict(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        local_predictor = get_predictor_for_user(interaction.user.id)
        safe_spots, bombs = local_predictor.towers.predict()
        if safe_spots is None:
            await interaction.followup.send("❌ Could not fetch Towers game. Make sure you have an active game.")
            return
        embed = discord.Embed(title=">_< Towers Predictor", color=0xf1c40f)
        if safe_spots:
            safe_str = ", ".join([f"{chr(65+r)}{c+1}" for r,c,_ in safe_spots[:5]])
        else:
            safe_str = "No predictions"
        embed.add_field(name="⭐ Best Safe Tiles", value=safe_str, inline=False)
        embed.add_field(name="📊 Accuracy", value=f"{local_predictor.accuracy:.1f}%", inline=True)
        embed.add_field(name="🎯 Predictions", value="Unlimited", inline=True)
        embed.set_footer(text=">_< Predictor")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="account_info", description="Show your Bloxflip account info")
async def account_info(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        local_predictor = get_predictor_for_user(interaction.user.id)
        resp = local_predictor.session.get("https://bloxflip.com/api/user/profile")
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
        local_predictor = get_predictor_for_user(interaction.user.id)
        resp = local_predictor.session.post("https://bloxflip.com/api/games/mines/reset-seed", json={})
        if resp.status_code == 200:
            embed = discord.Embed(title=">_< Seed Reset", description="✅ Seed reset successfully! Next Mines game will use a new seed.", color=0x00ff00)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ Failed: {resp.status_code}")
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

# ---------- Sync command ----------
@bot.command(name='sync')
async def sync_commands(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ You need administrator permissions.")
        return
    try:
        await bot.tree.sync(guild=ctx.guild)
        await ctx.send("✅ Slash commands synced to this server! You can now use `/` commands.")
    except Exception as e:
        await ctx.send(f"❌ Sync failed: {e}")

# ---------- Win detector ----------
@bot.event
async def on_ready():
    print(f'✅ >_< Predictor is online as {bot.user}')
    await bot.tree.sync()
    bot.loop.create_task(win_detector())

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
                        embed.set_footer(text=">_< Predictor")
                        await channel.send(embed=embed)
        except Exception as e:
            print(f"Win detector error: {e}")
        await asyncio.sleep(8)

# ===== THIS IS THE ONLY LINE AT THE BOTTOM =====
bot.run(DISCORD_TOKEN)
from discord import app_commands
from discord.ext import commands
import asyncio
import random
import os
from config import DISCORD_TOKEN, LOG_CHANNEL_ID
from predictor import predictor, BloxflipAuth

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

def get_predictor_for_user(user_id):
    user_session = predictor.get_user_session(user_id)
    if user_session:
        from predictor import BloxflipPredictor
        return BloxflipPredictor(session=user_session)
    else:
        return predictor

# ---------- Account Command Group ----------
account_group = app_commands.Group(name="account", description="Manage your Bloxflip account connection")
bot.tree.add_command(account_group)

@account_group.command(name="connect", description="Connect your Bloxflip account")
async def account_connect(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🔐 Connect Bloxflip Account",
        description=(
            "Login with Roblox is the easy way: no cookies, just your Roblox username and a quick bio check.\n\n"
            "Prefer the old way? Paste tokens still works."
        ),
        color=0x9b59b6
    )
    view = discord.ui.View()
    roblox_button = discord.ui.Button(label="Login with Roblox", style=discord.ButtonStyle.primary, custom_id="roblox_login")
    tokens_button = discord.ui.Button(label="Paste Tokens", style=discord.ButtonStyle.secondary, custom_id="tokens_login")
    view.add_item(roblox_button)
    view.add_item(tokens_button)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@account_group.command(name="unlink", description="Disconnect your Bloxflip account")
async def account_unlink(interaction: discord.Interaction):
    if interaction.user.id in predictor.user_sessions:
        del predictor.user_sessions[interaction.user.id]
        await interaction.response.send_message("🔓 Account unlinked. You can reconnect with `/account connect`.", ephemeral=True)
    else:
        await interaction.response.send_message("❌ You don't have a linked account.", ephemeral=True)

# ---------- Button & Modal Handlers ----------
@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get("custom_id")
        if custom_id == "roblox_login":
            modal = discord.ui.Modal(title="Login with Roblox")
            modal.add_item(discord.ui.TextInput(label=".ROBLOSECURITY Cookie", placeholder="Paste your cookie here", style=discord.TextStyle.paragraph))
            await interaction.response.send_modal(modal)
        elif custom_id == "tokens_login":
            modal = discord.ui.Modal(title="Paste Tokens")
            modal.add_item(discord.ui.TextInput(label="app.rt", placeholder="Enter app.rt value"))
            modal.add_item(discord.ui.TextInput(label="app.at", placeholder="Enter app.at value"))
            await interaction.response.send_modal(modal)

@bot.event
async def on_modal_submit(interaction: discord.Interaction):
    # --- Roblox login ---
    if interaction.data.get("title") == "Login with Roblox":
        cookie = interaction.data["components"][0]["components"][0]["value"]
        try:
            # Test the cookie by creating a temporary auth
            test_auth = BloxflipAuth(roblox_cookie=cookie)
            test_session = test_auth.get_session()
            resp = test_session.get("https://bloxflip.com/api/user/profile", timeout=10)
            if resp.status_code != 200:
                await interaction.response.send_message("❌ Invalid Roblox cookie – could not fetch profile. Check your cookie.", ephemeral=True)
                return
            # Store the session
            predictor.set_user_session(interaction.user.id, {"type": "roblox", "cookie": cookie})
            await interaction.response.send_message("✅ Successfully connected with Roblox!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Authentication failed: {str(e)}", ephemeral=True)

    # --- Tokens login ---
    elif interaction.data.get("title") == "Paste Tokens":
        app_rt = interaction.data["components"][0]["components"][0]["value"]
        app_at = interaction.data["components"][1]["components"][0]["value"]
        try:
            # Test the tokens by creating a temporary auth
            test_auth = BloxflipAuth(app_rt=app_rt, app_at=app_at)
            test_session = test_auth.get_session()
            resp = test_session.get("https://bloxflip.com/api/user/profile", timeout=10)
            if resp.status_code != 200:
                await interaction.response.send_message("❌ Invalid tokens – could not fetch profile. Check your app.rt and app.at values.", ephemeral=True)
                return
            # Store the session
            predictor.set_user_session(interaction.user.id, {"type": "tokens", "app_rt": app_rt, "app_at": app_at})
            await interaction.response.send_message("✅ Successfully connected with tokens!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Authentication failed: {str(e)}", ephemeral=True)

# ---------- Slash Commands ----------
@bot.tree.command(name="mines_predict", description="Predict safe tiles in Mines")
async def mines_predict(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        local_predictor = get_predictor_for_user(interaction.user.id)
        safe_spots, bombs = local_predictor.mines.predict()
        if safe_spots is None:
            await interaction.followup.send("❌ Could not fetch Mines game. Make sure you have an active game.")
            return
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
        embed.add_field(name="📊 Accuracy", value=f"{local_predictor.accuracy:.1f}%", inline=True)
        embed.add_field(name="🎯 Predictions", value="Unlimited", inline=True)
        embed.set_footer(text="✅ safe | 💣 bomb | ❓ unknown")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="towers_predict", description="Predict safe tiles in Towers")
async def towers_predict(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        local_predictor = get_predictor_for_user(interaction.user.id)
        safe_spots, bombs = local_predictor.towers.predict()
        if safe_spots is None:
            await interaction.followup.send("❌ Could not fetch Towers game. Make sure you have an active game.")
            return
        embed = discord.Embed(title=">_< Towers Predictor", color=0xf1c40f)
        if safe_spots:
            safe_str = ", ".join([f"{chr(65+r)}{c+1}" for r,c,_ in safe_spots[:5]])
        else:
            safe_str = "No predictions"
        embed.add_field(name="⭐ Best Safe Tiles", value=safe_str, inline=False)
        embed.add_field(name="📊 Accuracy", value=f"{local_predictor.accuracy:.1f}%", inline=True)
        embed.add_field(name="🎯 Predictions", value="Unlimited", inline=True)
        embed.set_footer(text=">_< Predictor")
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

@bot.tree.command(name="account_info", description="Show your Bloxflip account info")
async def account_info(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        local_predictor = get_predictor_for_user(interaction.user.id)
        resp = local_predictor.session.get("https://bloxflip.com/api/user/profile")
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
        local_predictor = get_predictor_for_user(interaction.user.id)
        resp = local_predictor.session.post("https://bloxflip.com/api/games/mines/reset-seed", json={})
        if resp.status_code == 200:
            embed = discord.Embed(title=">_< Seed Reset", description="✅ Seed reset successfully! Next Mines game will use a new seed.", color=0x00ff00)
            await interaction.followup.send(embed=embed)
        else:
            await interaction.followup.send(f"❌ Failed: {resp.status_code}")
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}")

# ---------- Sync command ----------
@bot.command(name='sync')
async def sync_commands(ctx):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ You need administrator permissions.")
        return
    try:
        await bot.tree.sync(guild=ctx.guild)
        await ctx.send("✅ Slash commands synced to this server! You can now use `/` commands.")
    except Exception as e:
        await ctx.send(f"❌ Sync failed: {e}")

# ---------- Win detector ----------
@bot.event
async def on_ready():
    print(f'✅ >_< Predictor is online as {bot.user}')
    await bot.tree.sync()
    bot.loop.create_task(win_detector())

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
                        embed.set_footer(text=">_< Predictor")
                        await channel.send(embed=embed)
        except Exception as e:
            print(f"Win detector error: {e}")
        await asyncio.sleep(8)

# ===== THIS IS THE ONLY LINE AT THE BOTTOM =====
bot.run(DISCORD_TOKEN)# 在 on_modal_submit 事件中

# --- Tokens login ---
elif interaction.data.get("title") == "Paste Tokens":
    app_rt = interaction.data["components"][0]["components"][0]["value"]
    app_at = interaction.data["components"][1]["components"][0]["value"]
    try:
        # 使用新的认证类进行验证
        test_auth = BloxflipAuth(app_rt=app_rt, app_at=app_at)
        test_session = test_auth.get_session()
        # 发送一个测试请求
        resp = test_session.get("https://bloxflip.com/api/user/profile")
        if resp.status_code != 200:
            await interaction.response.send_message("❌ Invalid tokens – could not fetch profile. Check your app.rt and app.at values.", ephemeral=True)
            return
        # 验证通过，存储会话
        predictor.set_user_session(interaction.user.id, {"type": "tokens", "app_rt": app_rt, "app_at": app_at})
        await interaction.response.send_message("✅ Successfully connected with tokens!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Authentication failed: {str(e)}", ephemeral=True)
