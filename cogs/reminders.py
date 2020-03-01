import logging

import discord
from discord.ext import commands
import textwrap

import util
from resources import Timer
import pendulum

from util.converters import HumanTime

logger = logging.getLogger(__name__)


class Reminders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def remind(self, ctx, *, time_and_text: HumanTime(other=True)):
        time, text = time_and_text.time, time_and_text.other

        timer = Timer(
            event='reminder',
            created_at=ctx.message.created_at,
            expires_at=time,
            kwargs={
                'author_id': ctx.author.id,
                'guild_id': ctx.guild.id,
                'channel_id': ctx.channel.id,
                'text': text
            }
        )
        await self.bot.timers.create_timer(timer)
        delta = (pendulum.instance(timer.expires_at) - pendulum.instance(ctx.message.created_at)).in_words()
        await ctx.send(f"{ctx.author.mention} in {delta}:\n{timer.kwargs['text']}")

    @remind.command(name='list', aliases=['get'])
    async def reminders_list(self, ctx):

        fetched = await self.bot.timers.timers_service.get_where(extras={"author_id": ctx.author.id}, limit=10)
        if len(fetched) == 0:
            return await ctx.send('No currently running reminders')

        embed = discord.Embed(
            title='Upcoming reminders',
            color=util.random_discord_color()
        )
        embed.set_author(name=ctx.author, icon_url=ctx.author.avatar_url)

        for timer in fetched:
            text = f"{textwrap.shorten(timer.kwargs['text'], width=512)}"
            embed.add_field(
                name=f'ID: {timer.id}, in {(pendulum.instance(timer.expires_at) - pendulum.now()).in_words()}',
                value=text, inline=False
            )

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_reminder_timer_complete(self, timer):
        channel = self.bot.get_channel(timer.kwargs['channel_id'])
        member = self.bot.get_guild(timer.kwargs['guild_id']).get_member(timer.kwargs['author_id'])
        delta = (pendulum.instance(timer.expires_at) - pendulum.instance(timer.created_at)).in_words()
        await channel.send(f"{member.mention}, {delta} ago:\n{timer.kwargs['text']}")


def setup(bot):
    bot.add_cog(Reminders(bot))
