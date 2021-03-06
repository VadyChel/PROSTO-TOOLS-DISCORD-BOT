import uuid
import datetime
import typing
import discord

from django.db.models import Max
from django.forms.models import model_to_dict
from .models import (
    User,
    Warn,
    Giveaway,
    Guild,
    StatusReminder,
    Reminder,
    Mute,
    Punishment,
    Error,
    BotStat,
    Blacklist,
    AuditLogs
)


TABLES_TO_MODELS = {
    "warns": Warn,
    "users": User,
    "guilds": Guild,
    "reminders": Reminder,
    "status_reminders": StatusReminder,
    "blacklist": Blacklist,
    "giveaways": Giveaway,
    "errors": Error,
    "bot_stats": BotStat,
    "punishments": Punishment,
    "mutes": Mute
}


class Database:
    def __init__(self, client):
        self.client = client
        self.cache = self.client.cache

    async def add_giveaway(
            self,
            channel_id: int,
            message_id: int,
            creator: discord.Member,
            num_winners: int,
            time: int,
            name: str,
            prize: int
    ) -> int:
        new_giveaway = Giveaway(
            guild_id=creator.guild.id,
            channel_id=channel_id,
            message_id=message_id,
            creator_id=creator.id,
            num_winners=num_winners,
            time=time,
            name=name,
            prize=prize
        )
        new_giveaway.save()

        self.cache.giveaways.add(model_to_dict(new_giveaway))
        return new_giveaway.id

    async def del_giveaway(self, giveaway_id: int) -> Giveaway:
        delete_giveaway = Giveaway.objects.get(id=giveaway_id)
        delete_giveaway.delete()

        self.cache.giveaways.remove(id=giveaway_id)
        return delete_giveaway

    async def get_giveaways(self, **kwargs) -> typing.List[Giveaway]:
        cached_giveaways = self.cache.giveaways.find(**kwargs)
        if len(cached_giveaways) > 0:
            return cached_giveaways

        return Giveaway.objects.filter(**kwargs)

    async def get_giveaway(self, giveaway_id: int) -> Giveaway:
        cached_giveaway = self.cache.giveaways.get(id=giveaway_id)
        if cached_giveaway is not None:
            return cached_giveaway

        return Giveaway.objects.get(id=giveaway_id)

    async def add_status_reminder(self, target_id: int, user_id: int, wait_for: str, type_reminder: str) -> int:
        new_reminder = StatusReminder(
            target_id=target_id,
            user_id=user_id,
            wait_for=wait_for,
            type=type_reminder
        )
        new_reminder.save()

        self.cache.status_reminders.add(model_to_dict(new_reminder))
        return new_reminder.id

    async def get_status_reminders(self, **kwargs) -> typing.List[StatusReminder]:
        cached_reminders = self.cache.status_reminders.find(**kwargs)
        if len(cached_reminders) > 0:
            return cached_reminders

        return StatusReminder.objects.filter(**kwargs)

    async def get_status_reminder(self, **kwargs) -> StatusReminder:
        cached_reminder = self.cache.status_reminders.get(**kwargs)
        if cached_reminder is not None:
            return cached_reminder

        return StatusReminder.objects.get(**kwargs)

    async def del_status_reminder(self, status_reminder_id: int) -> bool:
        db_reminder = StatusReminder.objects.get(id=status_reminder_id)
        if db_reminder is None:
            return False

        db_reminder.delete()
        self.cache.status_reminders.remove(id=status_reminder_id)
        return True

    async def add_reminder(
            self,
            member: discord.Member,
            channel: discord.TextChannel,
            time: int,
            text: str,
    ) -> int:
        new_reminder = Reminder(
            user_id=member.id,
            guild_id=member.guild.id,
            text=text,
            time=time,
            channel_id=channel.id
        )
        new_reminder.save()

        self.cache.reminders.add(model_to_dict(new_reminder))
        return new_reminder.id

    async def get_reminders(self, **kwargs) -> typing.List[Reminder]:
        cached_reminders = self.cache.reminders.find(**kwargs)
        if len(cached_reminders) > 0:
            return cached_reminders

        return Reminder.objects.filter(**kwargs)

    async def del_reminder(self, reminder_id: int) -> bool:
        db_reminder = Reminder.objects.get(id=reminder_id)
        if db_reminder is None:
            return False

        db_reminder.delete()
        self.cache.reminders.remove(id=reminder_id)
        return True

    async def add_warn(self, user_id: int, guild_id: int, reason: str, author: int) -> int:
        warns_count = Warn.objects.filter(user_id=user_id, guild_id=guild_id).count()+1
        new_warn = Warn(
            user_id=user_id,
            guild_id=guild_id,
            reason=reason,
            state=True,
            time=datetime.datetime.utcnow().timestamp(),
            author=author,
            num=warns_count
        )
        new_warn.save()

        return new_warn.id

    async def del_warn(self, warn_id: int) -> typing.Optional[Warn]:
        db_warn = Warn.objects.get(id=warn_id)
        if db_warn is None:
            return None

        db_warn.update(state=False)
        return db_warn

    async def del_warns(self, **kwargs) -> None:
        Warn.objects.filter(**kwargs).update(state=False)

    async def get_warns(self, **kwargs) -> typing.List[Warn]:
        return Warn.objects.filter(**kwargs)

    async def add_mute(self, member: discord.Member, reason: str, active_to: int, author: int) -> int:
        new_mute = Mute(
            user_id=member.id,
            guild_id=member.guild.id,
            reason=reason,
            active_to=active_to,
            time=(await self.client.utils.get_guild_time(member.guild)).timestamp(),
            author=author
        )
        new_mute.save()

        return new_mute.id

    async def del_mute(self, user_id: int, guild_id: int) -> None:
        db_mute = Mute.objects.get(user_id=user_id, guild_id=guild_id)
        if db_mute is None:
            return

        db_mute.delete()

    async def get_mutes(self, guild_id: int) -> typing.List[Mute]:
        return Mute.objects.filter(guild_id=guild_id)

    async def get_mute(self, guild_id: int, member_id: int) -> Mute:
        return Mute.objects.get(guild_id=guild_id, member_id=member_id)

    async def add_punishment(
            self,
            type_punishment: str,
            time: int,
            member: discord.Member,
            role_id: int = 0,
            **kwargs,
    ) -> int:
        new_punishment = Punishment(
            user_id=member.id,
            guild_id=member.guild.id,
            type=type_punishment,
            time=time,
            role_id=role_id
        )
        new_punishment.save()

        self.cache.punishments.add(model_to_dict(new_punishment))
        if type_punishment == "mute":
            await self.add_mute(
                active_to=time,
                member=member,
                reason=kwargs.pop("reason"),
                author=kwargs.pop("author"),
            )

        return new_punishment.id

    async def get_punishments(self) -> typing.List[Punishment]:
        cached_punishments = self.cache.punishments.all()
        if len(cached_punishments) > 0:
            return cached_punishments

        return Punishment.objects.all()

    async def del_punishment(self, **kwargs) -> None:
        db_punishment = Punishment.objects.get(**kwargs)
        if db_punishment is None:
            return

        db_punishment.delete()
        self.cache.punishments.remove(**kwargs)

    async def sel_user(self, target: discord.Member) -> User:
        cached_user = self.cache.users.get(guild_id=target.guild.id, user_id=target.id)
        if cached_user is not None:
            return cached_user

        db_user = User.objects.get(user_id=target.id, guild_id=target.guild.id)
        if db_user is None:
            new_user = User(
                user_id=target.id,
                guild_id=target.guild.id,
                level=1,
                exp=0,
                money=0,
                coins=0,
                reputation=0,
                prison=False,
                profile="default",
                bio="",
                clan="",
                items=[],
                pets=[],
                transactions=[],
                bonuses=[]
            )
            new_user.save()
            self.cache.users.add(model_to_dict(new_user))
            return new_user

        self.cache.users.add(model_to_dict(db_user))
        return db_user

    async def sel_guild(self, guild: discord.Guild) -> Guild:
        cached_guild = self.cache.guilds.get(guild_id=guild.id)
        if cached_guild is not None:
            return cached_guild

        db_guild = Guild.objects.get(guild_id=guild.id)
        if db_guild is None:
            new_guild = Guild(
                guild_id=guild.id,
                exp_multi=100,
                donate=False,
                prefix="p.",
                api_key=str(uuid.uuid4()),
                timezone="utc",
                server_stats={},
                voice_channel={},
                shop_list=[],
                ignored_channels=[],
                auto_mod={
                    "anti_flud": {
                        "state": False,
                        "delete_message": False,
                        "punishment": {
                            "state": False,
                            "type": "mute",
                            "time": None
                        },
                        "message": {
                            "state": False,
                            "type": "channel",
                            "content": {
                                "code": None,
                                "text": None
                            }
                        },
                        "target_roles": [],
                        "target_channels": [],
                        "ignore_roles": [],
                        "ignore_channels": [],
                    },
                    "anti_invite": {
                        "state": False,
                        "delete_message": False,
                        "punishment": {
                            "state": False,
                            "type": "mute",
                            "time": None
                        },
                        "message": {
                            "state": False,
                            "type": "channel",
                            "content": {
                                "code": None,
                                "text": None
                            }
                        },
                        "target_roles": [],
                        "target_channels": [],
                        "ignore_roles": [],
                        "ignore_channels": [],
                    },
                    "anti_caps": {
                        "state": False,
                        "delete_message": False,
                        "punishment": {
                            "state": False,
                            "type": "mute",
                            "time": None
                        },
                        "message": {
                            "state": False,
                            "type": "channel",
                            "content": {
                                "code": None,
                                "text": None
                            }
                        },
                        "percent": 40,
                        "min_chars": 10,
                        "target_roles": [],
                        "target_channels": [],
                        "ignore_roles": [],
                        "ignore_channels": [],
                    },
                    "anti_mentions": {
                        "state": False,
                        "delete_message": False,
                        "punishment": {
                            "state": False,
                            "type": "mute",
                            "time": None
                        },
                        "message": {
                            "state": False,
                            "type": "channel",
                            "content": {
                                "code": None,
                                "text": None
                            }
                        },
                        "max_mentions": 4,
                        "target_roles": [],
                        "target_channels": [],
                        "ignore_roles": [],
                        "ignore_channels": [],
                    },
                    "anti_link": {
                        "state": False,
                        "delete_message": False,
                        "punishment": {
                            "state": False,
                            "type": "mute",
                            "time": None
                        },
                        "message": {
                            "state": False,
                            "type": "channel",
                            "content": {
                                "code": None,
                                "text": None
                            }
                        },
                        "domains": [],
                        "target_roles": [],
                        "target_channels": [],
                        "ignore_roles": [],
                        "ignore_channels": [],
                    },
                    "auto_nick_corrector": {
                        "state": False,
                        "target_roles": [],
                        "ignore_roles": [],
                        "replace_with": "New nick",
                        "percent": 60
                    },
                    "captcha": {"state": False}
                },
                clans=[],
                moderators=[],
                auto_reactions={},
                welcomer={
                    "join": {
                        "state": False,
                        "type": "channel",
                        "channel_id": None,
                        "message": {
                            "text": None,
                            "code": None
                        }
                    },
                    "leave": {
                        "state": False,
                        "type": "channel",
                        "channel_id": None,
                        "message": {
                            "text": None,
                            "code": None
                        }
                    }
                },
                auto_roles={},
                custom_commands=[],
                autoresponders={},
                audit={
                    'message_edit': {"state": False, "channel_id": None},
                    'message_delete': {"state": False, "channel_id": None},
                    'member_nick_update': {"state": False, "channel_id": None},
                    'member_roles_update': {"state": False, "channel_id": None},
                    'member_mute': {'state': False, "channel_id": None},
                    'member_unmute': {'state': False, "channel_id": None},
                    'member_ban': {'state': False, "channel_id": None},
                    'member_unban': {'state': False, "channel_id": None},
                    'clan_delete': {'state': False, "channel_id": None},
                    'clan_create': {'state': False, "channel_id": None},
                    'money_remove': {'state': False, "channel_id": None},
                    'money_add': {'state': False, "channel_id": None},
                    'channel_create': {'state': False, "channel_id": None},
                    'channel_delete': {'state': False, "channel_id": None},
                    'role_create': {'state': False, "channel_id": None},
                    'role_delete': {'state': False, "channel_id": None},
                    'member_voice_move': {'state': False, "channel_id": None},
                    'member_voice_connect': {'state': False, "channel_id": None},
                    'member_voice_disconnect': {'state': False, "channel_id": None},
                    'member_join': {'state': False, "channel_id": None},
                    'member_leave': {'state': False, "channel_id": None},
                    'bot_join': {'state': False, "channel_id": None},
                    'bot_leave': {'state': False, "channel_id": None},
                    'member_kick': {'state': False, "channel_id": None},
                    'new_warn': {'state': False, "channel_id": None},
                    'warns_reset': {'state': False, "channel_id": None},
                },
                rank_message={
                    "state": False,
                    "type": "channel",
                    "channel_id": None,
                    "not_sending_channels": [],
                    "message": {
                        "text": None,
                        "code": None
                    }
                },
                commands_settings={},
                warns_settings={
                    "max": 3,
                    "punishment": {
                        "state": False,
                        "type": "mute",
                        "time": None
                    },
                    "role": {
                        "state": False,
                        "type": "add",
                        "role_id": None,
                        "time": None
                    }
                },
            )
            new_guild.save()
            self.cache.guilds.add(model_to_dict(new_guild))
            return new_guild

        self.cache.guilds.add(model_to_dict(db_guild))
        return db_guild

    async def get_prefix(self, guild: discord.Guild):
        if guild is None:
            return self.client.config.DEFAULT_PREFIX

        cached_guild = self.cache.guilds.get(guild_id=guild.id)
        if cached_guild is not None:
            return cached_guild.prefix

        db_guild = Guild.objects.get(guild_id=guild.id)
        if db_guild is not None:
            return db_guild.prefix
        else:
            return (await self.sel_guild(guild)).prefix

    async def get_moder_roles(self, guild: discord.Guild):
        cached_guild = self.cache.guilds.get(guild_id=guild.id)
        if cached_guild is not None:
            return cached_guild.moderators

        db_guild = Guild.objects.get(guild_id=guild.id)
        if db_guild is not None:
            return db_guild.moderators
        else:
            return (await self.sel_guild(guild)).moderators

    async def get_guild_timezone(self, guild: discord.Guild):
        cached_guild = self.cache.guilds.get(guild_id=guild.id)
        if cached_guild is not None:
            return cached_guild.timezone

        db_guild = Guild.objects.get(guild_id=guild.id)
        if db_guild is not None:
            return db_guild.timezone
        else:
            return (await self.sel_guild(guild)).timezone

    async def update(self, table: str, **kwargs):
        where = kwargs.pop("where")
        self.cache.__getattribute__(table).update(kwargs, **where)
        TABLES_TO_MODELS[table].objects.filter(**where).update(**kwargs)

    async def add_stat_counter(
            self, entity: str = "all commands", add_counter: int = None
    ) -> None:
        if add_counter is None:
            BotStat.objects.create(
                count=BotStat.objects.filter(
                    entity='all commands'
                ).aggregate(Max('count')).get('count__max', 0)+1,
                timestamp=datetime.datetime.utcnow(),
                entity="all commands"
            )

        BotStat.objects.create(
            count=add_counter if add_counter is not None else BotStat.objects.filter(
                entity=entity
            ).aggregate(Max('count')).get('count__max', 0)+1,
            timestamp=datetime.datetime.utcnow(),
            entity=entity
        )

    async def add_error(self, error_id: str, traceback: str, command: str, guild_id: int, user_id: int) -> None:
        Error.objects.create(
            error_id=error_id,
            guild_id=guild_id,
            user_id=user_id,
            time=datetime.datetime.utcnow(),
            traceback=traceback,
            command=command
        )

    async def add_blacklist_entity(self, entity_id: int, type_entity: str, reason: str) -> int:
        new_blacklist_entity = Blacklist(
            time=datetime.datetime.utcnow().timestamp(),
            entity_id=entity_id,
            type=type_entity,
            reason=reason
        )
        new_blacklist_entity.save()

        self.cache.blacklist.add(model_to_dict(new_blacklist_entity))
        return new_blacklist_entity.id

    async def get_blacklist_entities(self, **kwargs) -> typing.List[Blacklist]:
        cached_blacklist_entities = self.cache.blacklist.find(**kwargs)
        if len(cached_blacklist_entities) > 0:
            return cached_blacklist_entities

        return Blacklist.objects.filter(**kwargs)

    async def get_blacklist_entity(self, **kwargs) -> Blacklist:
        cached_blacklist_entity = self.cache.status_reminders.get(**kwargs)
        if cached_blacklist_entity is not None:
            return cached_blacklist_entity

        return Blacklist.objects.get(**kwargs)

    async def del_blacklist_entity(self, **kwargs) -> bool:
        db_blacklist_entity = Blacklist.objects.get(**kwargs)
        if db_blacklist_entity is None:
            return False

        db_blacklist_entity.delete()
        self.cache.blacklist.remove(**kwargs)
        return True

    async def add_audit_log(
            self, user: discord.User, channel: discord.TextChannel, guild_id: int, action_type: str, **kwargs
    ) -> int:
        new_log = AuditLogs(
            guild_id=guild_id,
            time=datetime.datetime.utcnow(),
            type=action_type,
            channel={
                "id": channel.id,
                "name": channel.name,
            },
            user={
                "id": user.id,
                "username": user.name,
                "discriminator": user.discriminator,
                "avatar_url": user.avatar_url_as(
                    format="gif" if user.is_avatar_animated() else "png", size=1024
                )
            },
            options=kwargs
        )
        new_log.save()
        return new_log.id