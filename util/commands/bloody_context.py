from discord.ext import commands as dpy_commands
import typing
import asyncpg

__all__ = ('Context',)


class Context(dpy_commands.Context):
    def __init__(self, **attrs):
        super().__init__(**attrs)
        self.db: typing.Optional[asyncpg.Connection] = None