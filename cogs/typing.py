import discord
from discord.ext import commands
import time
import asyncio
import string
import re

from utils import (
    get_quote, fix_quote_casing, countdown_reactions, 
    calculate_accuracy, update_user_stat, load_stats
)

class Typing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_races = set()
        self.active_typespeeds = {}
        self.race_waiting_tasks = {}

    @commands.hybrid_command(name="typespeed", description="Find out your typing speed!")
    async def typespeed(self, ctx: commands.Context, mode: str = "normal"):
        channel_id = ctx.channel.id
        if channel_id in self.active_races:
            await ctx.send(f"{ctx.author.mention} A TypeRace is currently active in this channel. Please wait for it to finish.")
            return
            
        self.active_typespeeds[channel_id] = self.active_typespeeds.get(channel_id, 0) + 1
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
        prompt_msg = await ctx.send(content=f"{ctx.author.mention}, get ready!", embed=embed)
        
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
            
            words_typed = len(typed_sentence) / 5
            wpm = words_typed / time_minutes

            stats = load_stats()
            uid_str = str(ctx.author.id)
            avg_wpm = 0.0
            if uid_str in stats and stats[uid_str].get("tests_completed", 0) > 0:
                avg_wpm = stats[uid_str]["total_wpm"] / stats[uid_str]["tests_completed"]
                
            threshold = max(250.0, avg_wpm + 75.0)

            if wpm > threshold:
                await ctx.send(f"{ctx.author.mention} Copypaste detected. Your typing speed ({wpm:.2f} WPM) is suspiciously high compared to your average. Disqualified.")
                return

            if accuracy < 80.0:
                await ctx.send(f"{ctx.author.mention} Your accuracy was too low ({accuracy:.2f}%). You need at least 80% to qualify.")
                return
            
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
        finally:
            self.active_typespeeds[channel_id] -= 1
            if self.active_typespeeds[channel_id] <= 0:
                del self.active_typespeeds[channel_id]

    @commands.hybrid_command(name="typerace", description="Race your typing speed against others!")
    async def typerace(self, ctx: commands.Context, mode: str = "normal"):
        channel_id = ctx.channel.id
        if channel_id in self.active_races:
            await ctx.send("A TypeRace is already active in this channel.")
            return
        if self.active_typespeeds.get(channel_id, 0) > 0:
            await ctx.send("There are ongoing TypeSpeed tests in this channel. Please wait for them to finish before starting a race.")
            return
            
        self.active_races.add(channel_id)
        
        invite_embed = discord.Embed(
            title="TypeRace",
            description="A typing race is starting! React with 🏁 within 10 seconds to join the race!",
            color=discord.Color.gold()
        )
        invite_msg = await ctx.send(embed=invite_embed)
        await invite_msg.add_reaction("🏁")
        
        waiting_task = asyncio.create_task(countdown_reactions(invite_msg, 10.0))
        self.race_waiting_tasks[channel_id] = waiting_task
        
        await waiting_task
        self.race_waiting_tasks.pop(channel_id, None)
        
        if channel_id not in self.active_races:
            return
        
        try:
            invite_msg = await ctx.channel.fetch_message(invite_msg.id)
        except Exception:
            await ctx.send("Failed to get race participants. Cancelling.")
            self.active_races.discard(channel_id)
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
            self.active_races.discard(channel_id)
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
        
        all_stats = load_stats()
        participant_avg_wpm = {}
        for p in participants:
            p_id = str(p.id)
            if p_id in all_stats and all_stats[p_id].get("tests_completed", 0) > 0:
                participant_avg_wpm[p_id] = all_stats[p_id]["total_wpm"] / all_stats[p_id]["tests_completed"]
        
        end_time_deadline = start_time + 60.0
        countdown_task = asyncio.create_task(countdown_reactions(race_msg, 60.0))
        
        async def handle_participant(user):
            while True:
                remaining_time = end_time_deadline - time.time()
                if remaining_time <= 0:
                    return None
                    
                def check(m):
                    return m.author == user and m.channel == ctx.channel
                    
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
                    
                    words_typed = len(typed_sentence) / 5
                    wpm = words_typed / time_minutes

                    avg_wpm = participant_avg_wpm.get(str(user.id), 0.0)
                    threshold = max(250.0, avg_wpm + 75.0)

                    if wpm > threshold:
                        await ctx.send(f"{user.mention} Copypaste detected. Your typing speed ({wpm:.2f} WPM) is suspiciously high compared to your average. Disqualified.")
                        return None

                    if accuracy < 80.0:
                        await ctx.send(f"{user.mention} Finished, but accuracy was too low ({accuracy:.2f}%).")
                        return None
                        
                    await msg.add_reaction("✅")
                    return {
                        "user": user,
                        "wpm": wpm,
                        "accuracy": accuracy,
                        "time": time_taken
                    }
                    
                except asyncio.TimeoutError:
                    return None

        participant_tasks = [asyncio.create_task(handle_participant(p)) for p in participants]
        all_results = await asyncio.gather(*participant_tasks)
        results = [res for res in all_results if res is not None]
                
        countdown_task.cancel()
        if not results:
            await ctx.send("The race has ended! Everyone DNF'd (Did Not Finish).")
            self.active_races.discard(channel_id)
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
        self.active_races.discard(channel_id)

    @commands.hybrid_command(name="cancel", description="Cancel a pending TypeRace in the current channel.")
    async def cancel(self, ctx: commands.Context):
        channel_id = ctx.channel.id
        if channel_id in self.race_waiting_tasks:
            task = self.race_waiting_tasks.pop(channel_id)
            task.cancel()
            self.active_races.discard(channel_id)
            await ctx.send(f"The pending TypeRace was cancelled by {ctx.author.mention}.")
        else:
            await ctx.send("There is no pending TypeRace in this channel to cancel.")

async def setup(bot):
    await bot.add_cog(Typing(bot))
