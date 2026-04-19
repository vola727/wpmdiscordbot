import discord
from discord.ext import commands
from utils import load_stats

class Profile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="profile", description="Check your typing profile and stats!")
    async def profile(self, ctx: commands.Context, user: discord.Member = None):
        target_user = user or ctx.author
        stats = load_stats()
        uid = str(target_user.id)
        
        if uid not in stats or stats[uid]["tests_completed"] == 0:
            await ctx.send(f"{target_user.mention} has not completed any typing tests yet!")
            return
            
        user_data = stats[uid]
        tests = user_data["tests_completed"]
        avg_wpm = user_data["total_wpm"] / tests
        avg_acc = user_data["total_accuracy"] / tests
        highest_wpm = user_data.get("highest_wpm", 0.0)
        races_won = user_data.get("races_won", 0)
        
        embed = discord.Embed(title=f"📊 {target_user.display_name}'s Profile", color=discord.Color.purple())
        embed.add_field(name="Tests Completed", value=str(tests), inline=True)
        embed.add_field(name="Races Won", value=str(races_won), inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True)
        embed.add_field(name="Average WPM", value=f"**{avg_wpm:.2f}**", inline=True)
        embed.add_field(name="Highest WPM", value=f"**{highest_wpm:.2f}**", inline=True)
        embed.add_field(name="Average Accuracy", value=f"{avg_acc:.2f}%", inline=True)
        
        if target_user.display_avatar:
            embed.set_thumbnail(url=target_user.display_avatar.url)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Profile(bot))
