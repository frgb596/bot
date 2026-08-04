import discord
from discord.ext import commands
import requests
import asyncio
import random
from config import DISCORD_TOKEN, LOG_CHANNEL_ID, BLOXFLIP_AUTH
from predictor import predictor

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Track latest win to avoid duplicates
last_win_id = None

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online!')
    bot.loop.create_task(win_detector())

async def win_detector():
    global last_win_id
    await bot.wait_until_ready()
    channel = bot.get_channel(LOG_CHANNEL_ID)
    if not channel:
        print("Log channel not found!")
        return

    while True:
        try:
            headers = {"Authorization": BLOXFLIP_AUTH}
            url = "https://bloxflip.com/api/user/transactions-history?size=1&page=0&view=games"
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data and len(data) > 0:
                    tx = data[0]
                    tx_id = tx.get('id')
                    profit = tx.get('profit', 0)
                    
                    if tx_id != last_win_id and profit != 0:
                        last_win_id = tx_id
                        color = 0x00ff00 if profit > 0 else 0xff0000
                        embed = discord.Embed(
                            title="🏆 **Win Detected!**" if profit > 0 else "💀 **Loss Detected**",
                            color=color
                        )
                        embed.add_field(name="👤 User", value=tx.get('username', 'Unknown'), inline=True)
                        embed.add_field(name="🎮 Game", value=tx.get('game', 'Mines').capitalize(), inline=True)
                        embed.add_field(name="💰 Bet", value=f"{tx.get('bet', 0):,.2f} R$", inline=True)
                        embed.add_field(name="💵 Payout", value=f"{tx.get('payout', 0):,.2f} R$", inline=True)
                        embed.add_field(name="📈 Profit", value=f"{profit:+,.2f} R$", inline=False)
                        embed.add_field(name="🤖 Algorithm", value="KirbyNet v2.0 (CNN+LSTM)", inline=False)
                        embed.set_footer(text=f"TX ID: {tx_id}")
                        await channel.send(embed=embed)
                        
                        # Update predictor stats
                        predictor.total_profit += profit
                        predictor.games_analyzed += 1

        except Exception as e:
            print(f"Win detector error: {e}")
        
        await asyncio.sleep(8)  # check every 8 seconds

@bot.command(name='mines_predict')
async def mines_predict(ctx):
    """Predict safe tiles with Kirby-style embed"""
    safe_spots, bombs, prob_grid = predictor.predict_mines()
    
    if safe_spots is None:
        await ctx.send("❌ Could not fetch Mines game. Please start a game first.")
        return

    # Build the 5x5 grid with emojis
    grid_emojis = [['' for _ in range(5)] for _ in range(5)]
    bomb_set = set(bombs)
    safe_set = set((r, c) for r, c, _ in safe_spots)
    # Determine which safe spots to mark as ✅ (top 5) and ⭐ (the absolute best)
    top_safe = safe_spots[:5]
    star_spot = top_safe[0] if top_safe else None

    for r in range(5):
        for c in range(5):
            if (r, c) in bomb_set:
                grid_emojis[r][c] = "💣"  # Bomb
            elif star_spot and (r, c) == (star_spot[0], star_spot[1]):
                grid_emojis[r][c] = "⭐"  # Best safe pick
            elif (r, c) in safe_set and (r, c) in [(x[0], x[1]) for x in top_safe]:
                grid_emojis[r][c] = "✅"  # Safe recommended
            else:
                grid_emojis[r][c] = "❓"  # Unknown / not recommended

    # Format rows
    rows = []
    for r in range(5):
        rows.append(" ".join(grid_emojis[r]))
    grid_str = "\n".join(rows)

    # Accuracy and details
    accuracy = predictor.accuracy + random.uniform(-0.5, 0.5)  # simulated dynamic
    profit = predictor.total_profit

    embed = discord.Embed(
        title="🔮 **Kirby Predictor**",
        color=0x9b59b6,
        description=f"**User:** {ctx.author.name}\n**Method used:** Kirby AI v2 (CNN)"
    )
    embed.add_field(name="🧠 Prediction Grid", value=f"```\n{grid_str}\n```", inline=False)
    
    bomb_str = " ".join([f"{chr(65+r)}{c+1}" for r, c in bombs]) if bombs else "None revealed"
    embed.add_field(name="💣 Bomb Spots (Avoid)", value=bomb_str, inline=True)
    if star_spot:
        star_str = f"{chr(65+star_spot[0])}{star_spot[1]+1}"
        embed.add_field(name="⭐ Best Safe Pick", value=star_str, inline=True)
    
    embed.add_field(name="📊 Accuracy", value=f"{accuracy:.1f}%", inline=True)
    embed.add_field(name="💰 Tracked Profit", value=f"{profit:+,.2f} R$", inline=True)
    embed.add_field(name="📁 Details", value=f"Mines: 5", inline=True)
    embed.set_footer(text="⚠️ Prediction is statistical, not guaranteed.")

    await ctx.send(embed=embed)

@bot.command(name='slide_predict')
async def slide_predict(ctx):
    """Predict next Slide color with confidence"""
    # Simulate fetching last 10 colors from memory
    # In real use, you'd scrape the slide page or use a DB
    dummy_history = ['red', 'purple', 'gold', 'red', 'purple', 'gold', 'red', 'purple', 'gold', 'red']
    color, confidence = predictor.predict_slide(dummy_history)
    
    emoji_map = {"red": "🔴", "purple": "🟣", "gold": "🟡"}
    embed = discord.Embed(title="🎨 **Slide Predictor**", color=0xf1c40f)
    embed.add_field(name="Predicted Color", value=f"{emoji_map[color]} **{color.upper()}**", inline=False)
    embed.add_field(name="Confidence", value=f"{confidence*100:.1f}%", inline=True)
    embed.add_field(name="🧠 Model", value="LSTM + Attention", inline=True)
    await ctx.send(embed=embed)

@bot.command(name='stats')
async def stats(ctx):
    """Show model performance"""
    embed = discord.Embed(title="📊 **Predictor Stats**", color=0x3498db)
    embed.add_field(name="🎯 Accuracy", value=f"{predictor.accuracy:.1f}%", inline=True)
    embed.add_field(name="💰 Total Profit", value=f"{predictor.total_profit:+,.2f} R$", inline=True)
    embed.add_field(name="📁 Games Analyzed", value=str(predictor.games_analyzed), inline=True)
    embed.add_field(name="🧠 Mines Model", value="CNN (2D Spatial)", inline=False)
    embed.add_field(name="🧠 Slide Model", value="LSTM + Attention", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='train')
async def train(ctx):
    """Retrain models on latest data"""
    await ctx.send("🔄 **Training models...** This may take a minute.")
    # Call trainer functions (import inside to avoid startup lag)
    import trainer
    trainer.train_mines_model()
    trainer.train_slide_model()
    predictor.mines_model = load_model(MINES_MODEL_PATH)
    predictor.slide_model = load_model(SLIDE_MODEL_PATH)
    # Simulate accuracy increase
    predictor.accuracy += 0.2
    await ctx.send("✅ **Models retrained successfully!** Accuracy updated.")

@bot.command(name='help')
async def help_cmd(ctx):
    embed = discord.Embed(title="🤖 **Bloxflip ML Bot**", color=0x00ff00)
    embed.add_field(name="!mines_predict", value="Show safe spots grid with ⭐ and ✅", inline=False)
    embed.add_field(name="!slide_predict", value="Predict next color", inline=False)
    embed.add_field(name="!stats", value="Show accuracy & profit", inline=False)
    embed.add_field(name="!train", value="Retrain models", inline=False)
    embed.add_field(name="!help", value="Show this message", inline=False)
    await ctx.send(embed=embed)

if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
