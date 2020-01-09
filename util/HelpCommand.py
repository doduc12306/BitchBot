import discord
from discord.ext import commands
import itertools
from util import funs, paginator

NEW_LINE = '\n'  # working around python's limitation of not allowing `\n` in f-strings


# noinspection PyMethodMayBeStatic,PyShadowingNames,PyBroadException
class BloodyHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()

    async def on_help_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            await ctx.send(str(error.original))
        else:
            # noinspection PyUnresolvedReferences
            raise error.original

    def get_command_signature(self, command):
        parent = command.full_parent_name
        out = command.name

        aliases = ''
        if len(command.aliases) > 0:
            aliases = '|'.join(command.aliases)
            out = f'[{command.qualified_name}, {aliases}]'

        if parent:
            aliases = f" , {aliases}" if (aliases != '') else ""
            out = f'[{parent} {command.name}{aliases}]'

        return f'{out} {command.signature}'

    def add_commands_to_embed(self, commands, cog_name, embed, description=None):
        out = ''
        embed.description = description
        for cmd in commands:
            try:
                out += f"**{cmd.name}**:\t{str(cmd.help).split(NEW_LINE)[0]}\n"
            except:
                continue

        if out:
            embed.add_field(name=f'**{cog_name}**', value=out, inline=False)

        return embed

    def generate_base_help_embed(self):
        embed = discord.Embed(title='**You wanted help? Help is provided**', color=funs.random_discord_color())
        embed.set_footer(text='Do >help command/group name for information about it')
        return embed

    # noinspection SpellCheckingInspection
    async def send_bot_help(self, mapping):
        def key(c):
            return c.cog_name or '\u200bNo Category'

        bot = self.context.bot
        entries = await self.filter_commands(bot.commands, sort=True, key=key)

        data = []

        for cog, cmds in itertools.groupby(entries, key=key):
            cmds = sorted(cmds, key=lambda c: c.name)
            if len(cmds) == 0:
                continue

            actual_cog = bot.get_cog(cog)

            if actual_cog is None:
                continue

            embed = self.generate_base_help_embed()
            embed.title += f'\n{actual_cog.qualified_name} Commands'
            embed.description = actual_cog.description
            for cmd in actual_cog.walk_commands():
                try:
                    if isinstance(cmd, commands.Group) and not cmd.invoke_without_command:
                        continue
                except AttributeError:
                    pass

                help_string = str(cmd.help).strip().split('\n')[0]
                if help_string is not None and len(help_string) > 0:
                    embed.add_field(name=f'**{cmd.qualified_name}**', value=help_string, inline=False)
                else:
                    continue

            data.append(embed)

        pages = paginator.Paginator(self.context, data)
        await pages.paginate()

    async def send_cog_help(self, cog):
        embed = self.generate_base_help_embed()
        embed.title += f'\n {cog.qualified_name} Commands'
        embed = self.add_commands_to_embed(cog.walk_commands(), cog.qualified_name, embed)

        await self.context.send(embed=embed)

    def generate_arg_string_for_embed(self, args):
        out = ''
        keys = list(args.keys())
        values = list(args.values())
        for i in range(len(args)):
            out += f'**{keys[i]}**: {values[i]}\n'

        return out

    def format_command_embed(self, embed, command):
        embed.add_field(name='Format', value=self.get_command_signature(command), inline=False)

        try:
            command_help = funs.parse_docstring(command.help)
            embed.description = command_help[1]
            embed.add_field(name=f'Parameters', value=self.generate_arg_string_for_embed(command_help[0]), inline=False)
        except:
            embed.description = command.help
            embed.add_field(name=f'Parameters', value='The docs are incomplete', inline=False)

        return embed

    async def send_command_help(self, command):
        embed = self.format_command_embed(self.generate_base_help_embed(), command)
        await self.context.send(embed=embed)

    async def send_group_help(self, group):
        subcommands = group.commands

        if len(subcommands) == 0:
            return await self.send_command_help(group)

        subcommands = await self.filter_commands(subcommands, sort=True)

        embed = self.add_commands_to_embed(
            subcommands,
            group.qualified_name,
            self.generate_base_help_embed(),
            group.help
        )

        for subcommand in subcommands:
            if subcommand.invoke_without_command:
                pass

        await self.context.send(embed=embed)
