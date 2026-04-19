import discord
from discord.ext import commands
import time
import asyncio
import string
import re

from utils import (
    get_quote, fix_quote_casing, countdown_reactions, 
    calculate_accuracy, update_user_stat
)

class Typing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="typespeed", description="Find out your typing speed!")
    async def typespeed(self, ctx: commands.Context, mode: str = "normal"):
        sentence, author = await get_quote()
        
        if mode.lower() == "easy":
            translator = str.maketrans('', '', string.punctuation)
            sentence = sentence.translate(translator).lower()
            
        sentence = fix_quote_casing(sentence)
            
        desc = f"Type the following sentence as fast and accurately as possible:\n\n**`{sentence}`**\n\n"
        if mode.lower() == "easy":
            desc += "*(Easy Mode: Punctuation and casing are ignored)*\n\n"
        desc += "You have 60 seconds."
        
        embed = discord.Embed(
            title="TypeSpeed Test",
            description=desc,
            color=discord.Color.blue()
        )
        prompt_msg = await ctx.send(embed=embed)
        
        start_time = time.time()
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        countdown_task = asyncio.create_task(countdown_reactions(prompt_msg, 60.0))

        try:
            msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            countdown_task.cancel()
            end_time = time.time()
            
            typed_sentence = msg.content
            
            if mode.lower() == "easy":
                translator = str.maketrans('', '', string.punctuation)
                norm_typed = typed_sentence.translate(translator).lower()
                norm_typed = re.sub(r'\s+', ' ', norm_typed).strip()
                accuracy = calculate_accuracy(sentence, norm_typed)
            else:
                accuracy = calculate_accuracy(sentence, typed_sentence)
            time_taken = end_time - start_time
            time_minutes = time_taken / 60
            
            if accuracy < 80.0:
                await ctx.send(f"{ctx.author.mention} Your accuracy was too low ({accuracy:.2f}%). You need at least 80% to qualify.")
                return

            words_typed = len(typed_sentence) / 5
            wpm = words_typed / time_minutes
            
            update_user_stat(ctx.author.id, wpm, accuracy)
            
            result_embed = discord.Embed(title="TypeSpeed Results", color=discord.Color.green())
            result_embed.add_field(name="WPM", value=f"**{wpm:.2f}**", inline=True)
            result_embed.add_field(name="Accuracy", value=f"**{accuracy:.2f}%**", inline=True)
            result_embed.add_field(name="Time", value=f"{time_taken:.2f}s", inline=True)
            if author:
                result_embed.set_footer(text=f"Quote by: {author}")
            
            await ctx.send(f"{ctx.author.mention}", embed=result_embed)
            
        except asyncio.TimeoutError:
            await ctx.send(f"{ctx.author.mention} Time is up! You took too long (DNF).")

    @commands.hybrid_command(name="typerace", description="Race your typing speed against others!")
    async def typerace(self, ctx: commands.Context, mode: str = "normal"):
        invite_embed = discord.Embed(
            title="TypeRace",
            description="A typing race is starting! React with 🏁 within 10 seconds to join the race!",
            color=discord.Color.gold()
        )
        invite_msg = await ctx.send(embed=invite_embed)
        await invite_msg.add_reaction("🏁")
        
        await countdown_reactions(invite_msg, 10.0)
        
        try:
            invite_msg = await ctx.channel.fetch_message(invite_msg.id)
        except Exception:
            await ctx.send("Failed to get race participants. Cancelling.")
            return
            
        participants = []
        
        for reaction in invite_msg.reactions:
            if str(reaction.emoji) == "🏁":
                async for user in reaction.users():
                    if not user.bot:
                        participants.append(user)
                        
        participants = list(set(participants))
        
        if not participants:
            await ctx.send("No one joined the TypeRace. Cancelling.")
            return

        sentence, author = await get_quote()
        if mode.lower() == "easy":
            translator = str.maketrans('', '', string.punctuation)
            sentence = sentence.translate(translator).lower()
            
        sentence = fix_quote_casing(sentence)
        participant_mentions = ", ".join(p.mention for p in participants)
        
        desc = f"Participants: {participant_mentions}\n\nType the following sentence as fast and accurately as possible:\n\n**`{sentence}`**\n\n"
        if mode.lower() == "easy":
            desc += "*(Easy Mode: Punctuation and casing are stripped)*\n\n"
        desc += "You have 60 seconds."
        
        race_embed = discord.Embed(
            title="TypeRace Started!",
            description=desc,
            color=discord.Color.green()
        )
        race_msg = await ctx.send(embed=race_embed)
        
        start_time = time.time()
        results = [] 
        completed_users = set()
        
        def check(m):
            return m.author in participants and m.author not in completed_users and m.channel == ctx.channel
        
        end_time_deadline = start_time + 60.0
        countdown_task = asyncio.create_task(countdown_reactions(race_msg, 60.0))
        
        while len(completed_users) < len(participants):
            remaining_time = end_time_deadline - time.time()
            if remaining_time <= 0:
                break
                
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=remaining_time)
                end_time = time.time()
                
                typed_sentence = msg.content
                
                if mode.lower() == "easy":
                    translator = str.maketrans('', '', string.punctuation)
                    norm_typed = typed_sentence.translate(translator).lower()
                    norm_typed = re.sub(r'\s+', ' ', norm_typed).strip()
                    accuracy = calculate_accuracy(sentence, norm_typed)
                else:
                    accuracy = calculate_accuracy(sentence, typed_sentence)
                
                time_taken = end_time - start_time
                time_minutes = time_taken / 60
                
                completed_users.add(msg.author)
                
                if accuracy < 80.0:
                    await ctx.send(f"{msg.author.mention} Finished, but accuracy was too low ({accuracy:.2f}%).")
                    continue
                    
                words_typed = len(typed_sentence) / 5
                wpm = words_typed / time_minutes
                results.append({
                    "user": msg.author,
                    "wpm": wpm,
                    "accuracy": accuracy,
                    "time": time_taken
                })
                await msg.add_reaction("✅")
                
            except asyncio.TimeoutError:
                break
                
        countdown_task.cancel()
        if not results:
            await ctx.send("The race has ended! Everyone DNF'd (Did Not Finish).")
            return
            
        results.sort(key=lambda x: x['wpm'], reverse=True)
        
        leaderboard_embed = discord.Embed(title="TypeRace Leaderboard 🏆", color=discord.Color.gold())
        if author:
            leaderboard_embed.set_footer(text=f"Quote by: {author}")
        
        for idx, res in enumerate(results):
            rank = idx + 1
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}."
            won = (rank == 1)
            update_user_stat(res['user'].id, res['wpm'], res['accuracy'], won_race=won)
            leaderboard_embed.add_field(
                name=f"{medal} {res['user'].display_name}",
                value=f"**WPM:** {res['wpm']:.2f} | **ACC:** {res['accuracy']:.2f}% | **TIME:** {res['time']:.2f}s",
                inline=False
            )
            
        result_users = [res['user'] for res in results]
        dnf_users = [p for p in participants if p not in result_users]
        if dnf_users:
            dnf_mentions = ", ".join(p.display_name for p in dnf_users)
            leaderboard_embed.add_field(name="DNF ❌", value=dnf_mentions, inline=False)
            
        await ctx.send(embed=leaderboard_embed)

async def setup(bot):
    await bot.add_cog(Typing(bot))
