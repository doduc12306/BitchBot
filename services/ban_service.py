from database import database
from database.sql import SQL
from resources import Ban


class BanService:
    @classmethod
    async def insert(cls, ban):
        fetched = await database.connection.fetchrow('''
        insert into Bans (reason, banned_by_id, banned_user_id, guild_id)
        values ($1, $2, $3, $4)
        returning *;
        ''', ban.reason, ban.banned_by_id, ban.banned_user_id, ban.guild_id)

        return Ban.convert(fetched)

    @classmethod
    def sql(cls):
        return SQL(
            createTable='''
                create table if not exists Bans
                (
                    id             serial primary key,
                    reason         text,
                    banned_at      timestamp default now(),
                    banned_by_id   bigint not null,
                    banned_user_id bigint not null,
                    unban_time     timestamp,
                    guild_id       bigint not null
                );
            '''
        )
