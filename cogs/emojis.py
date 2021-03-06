import random

import discord
from discord.ext import commands as dpy_commands

import keys
from services import EmojiService
from util import funs, BloodyMenuPages, EmbedPagesData, commands


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def arg_or_1(arg: str):
    return int(arg) if arg.isdigit() else 1


# noinspection PyIncorrectDocstring
class Emojis(dpy_commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.safe_emojis = []

        self.bot.loop.create_task(self.fetch_safe_emojis())

    async def fetch_safe_emojis(self):
        async with self.bot.db.acquire() as db:
            self.safe_emojis = await EmojiService.fetch_all_safe_emojis(db)

    def safety_check(self, ctx: commands.Context):
        if ctx.author.id == self.bot.owner_id:
            return True

        if ctx.channel.is_nsfw():
            return True

        if ctx.guild is None:
            return True

        if ctx.guild.id in keys.trusted_guilds:
            return True

    def ensure_safe_emojis(self, ctx: commands.Context, emojis):
        if self.safety_check(ctx):
            return True

        for emoji in emojis:
            if emoji.id not in self.safe_emojis:
                raise dpy_commands.CheckFailure(
                    f"Channel '{ctx.channel}' needs to be NSFW in order to use emoji '{emoji.name}'.")

    # For some reason, greedy fucks up
    # noinspection PyUnresolvedReferences
    @commands.group(aliases=["e"], invoke_without_command=True)
    async def emoji(self, ctx: commands.Context, emojis: dpy_commands.Greedy[discord.Emoji], amount: arg_or_1 = 1):
        """Send any number of the emoji given by 'emojis'

        Only emojis that has been marked safe by bot admins can be used in non-NSFW channels.
        This is a safety feature so that the bot does not send any NSFW content on non-NSFW channels

        Args:
            emojis: The name of the emojis to send.
            amount: The number of times to repeat
        """
        self.ensure_safe_emojis(ctx, emojis)

        horny = 697884245183430867
        if any([e.id == horny for e in emojis]) and ctx.guild.id in keys.trusted_guilds and \
                ctx.author.id != self.bot.owner_id:

            messages = [m for m in self.bot.cached_messages if m.channel == ctx.channel][-10:]
            if any([m.author.id == self.bot.owner_id for m in messages]):
                no = self.bot.get_emoji(random.choice((597591030807920660, 610785266231279630)))
                return await ctx.send(random.choice(('nope, not gonna do that', 'no u', str(no))))

        to_be_sent = ' '.join([f'{emoji} ' * amount for emoji in emojis])
        if to_be_sent == '':
            return await ctx.send('No emojis of that name found', delete_after=2)
        await ctx.send(to_be_sent, embed=discord.Embed(color=0x00000F).set_author(name=f"- {ctx.author.display_name}"))
        await ctx.message.delete(delay=2)

    @emoji.command(aliases=["emojiurl", "l"])
    async def link(self, ctx: commands.Context, emoji: discord.Emoji):
        """Send link of any one of the emoji given by 'emojis' command

        Only emojis that has been marked safe by bot admins can be used in non-NSFW channels.
        This is a safety feature so that the bot does not send any NSFW content on non-NSFW channels

        Args:
            emoji: The emoji's name to link
        """
        self.ensure_safe_emojis(ctx, [emoji])
        await ctx.send(str(emoji.url))
        await ctx.message.delete(delay=2)

    @emoji.command()
    async def list(self, ctx: commands.Context):
        """
        Shows the emojis that can be sent by 'emoji' command

        Only emojis that has been marked safe by bot admins are shown in non-NSFW channels.
        This is a safety feature so that the bot does not send any NSFW content on non-NSFW channels
        """

        def pred(e):
            if self.safety_check(ctx):
                return True

            if e.id in self.safe_emojis:
                return True

            return False

        all_emojis = [e for e in self.bot.emojis if (e.available and pred(e))]
        chunked_emojis = list(chunks(all_emojis, 20))
        count = 1
        data = []
        for emojis in chunked_emojis:
            embed = discord.Embed(title='Available emojis', color=funs.random_discord_color())
            embed.set_footer(text=f'Total: {len(all_emojis)}')
            out = []
            for emoji in emojis:
                out.append(f'{count}. {emoji.name} \t{emoji}')
                count += 1

            embed.description = '\n'.join(out)
            data.append(embed)

        pages = BloodyMenuPages(EmbedPagesData(data))
        await pages.start(ctx)

    @emoji.command(aliases=['em'])
    async def embed(self, ctx: commands.Context, emoji: discord.Emoji):
        """
        Send embed of any one of the emoji given by 'emojis' command

        Only emojis that has been marked safe by bot admins can be used in non-NSFW channels.
        This is a safety feature so that the bot does not send any NSFW content on non-NSFW channels

        Args:
            emoji: The name of emoji to send in an the embed
        """
        self.ensure_safe_emojis(ctx, [emoji])
        embed = discord.Embed()
        embed.set_image(url=str(emoji.url))
        await ctx.send(embed=embed)
        await ctx.message.delete(delay=2)

    @emoji.command()
    async def react(self, ctx: commands.Context, message: discord.Message, emoji: discord.Emoji):
        """Make the bot react to a message with the given emoji

        Only emojis that has been marked safe by bot admins can be used in non-NSFW channels.
        This is a safety feature so that the bot does not send any NSFW content on non-NSFW channels

        Arg:
            message: The message to react to
            emoji: The name of emoji to react with
        """
        self.ensure_safe_emojis(ctx, [emoji])
        await message.add_reaction(emoji)

    @emoji.command(aliases=['marksafe', 'ms'], hidden=True, wants_db=True)
    @dpy_commands.check(lambda ctx: ctx.author.id in keys.can_use_private_commands)
    async def mark_safe(self, ctx, emoji: discord.Emoji):
        await EmojiService.mark_safe(ctx.db, emoji.id, ctx.author.id)
        await self.fetch_safe_emojis()
        await ctx.send(f'\N{WHITE HEAVY CHECK MARK}')


def setup(bot):
    bot.add_cog(Emojis(bot))
