import typing
import discord
import jinja2

from core.services.cache.cache_manager import CacheItem
from core.converters import Expiry
from discord.ext import commands


def model_to_dict(model: CacheItem) -> dict:
    return model._dict


def check_filters(entity: typing.Union[discord.Message, discord.Member], filters: typing.Iterable, predicates: dict) -> bool:
    if not filters:
        return True

    return all([predicates[i](entity) for i in filters])


async def process_converters(
        ctx: commands.Context,
        converters: typing.Iterable,
        argument: typing.Any,
        return_exception: bool = False
) -> typing.Any:
    error = None
    for conv in converters:
        try:
            result = await conv().convert(
                ctx, argument
            )
        except commands.CommandError as e:
            error = e
        else:
            return result

    if return_exception and error is not None:
        raise error


async def is_moderator(ctx):
    data = []
    if ctx.guild is not None:
        data = await ctx.bot.database.get_moder_roles(guild=ctx.guild)
        roles = ctx.guild.roles[::-1]
        data.append(roles[0].id)

    if data and ctx.guild is not None:
        for role_id in data:
            role = ctx.guild.get_role(role_id)
            if role in ctx.author.roles:
                return True
        return ctx.author.guild_permissions.administrator
    else:
        return ctx.author.guild_permissions.administrator if ctx.guild is not None else False


def is_guild_owner(ctx):
    if ctx.guild is None:
        return False

    return ctx.author == ctx.guild.owner


async def get_prefix(client, message):
    if message.guild is None:
        return client.config.DEFAULT_PREFIX

    prefix = await client.database.get_prefix(guild=message.guild)
    return commands.when_mentioned_or(*(str(prefix),))(client, message)


async def process_auto_moderate(ctx: commands.Context, auto_moderate: str, data, reason: str):
    if "target_channels" in data.auto_mod[auto_moderate].keys():
        if data.auto_mod[auto_moderate]["target_channels"]:
            if ctx.channel.id not in data.auto_mod[auto_moderate]["target_channels"]:
                return

    if data.auto_mod[auto_moderate]["target_roles"]:
        if not any([
            role.id in data.auto_mod[auto_moderate]["target_roles"]
            for role in ctx.author.roles
        ]):
            return

    if ctx.channel.id in data.auto_mod[auto_moderate]["ignore_channels"]:
        return

    if not any([
        role.id in data.auto_mod[auto_moderate]["ignore_roles"]
        for role in ctx.author.roles
    ]):
        return

    if data.auto_mod[auto_moderate]["punishment"]["state"]:
        type_punishment = data.auto_mod[auto_moderate]["punishment"]["type"]
        expiry_at = None
        if data.auto_mod[auto_moderate]["punishment"]["time"] is not None:
            expiry_at = await process_converters(
                ctx, Expiry.__args__, data.auto_mod[auto_moderate]["punishment"]["time"]
            )

        if type_punishment == "mute":
            await ctx.bot.support_commands.mute(
                ctx=ctx,
                member=ctx.author,
                author=ctx.guild.me,
                expiry_at=expiry_at,
                reason=reason,
            )
        elif type_punishment == "warn":
            await ctx.bot.support_commands.warn(
                ctx=ctx,
                member=ctx.author,
                author=ctx.guild.me,
                reason=reason,
            )
        elif type_punishment == "kick":
            await ctx.bot.support_commands.kick(
                ctx=ctx,
                member=ctx.author,
                author=ctx.guild.me,
                reason=reason
            )
        elif type_punishment == "ban":
            await ctx.bot.support_commands.ban(
                ctx=ctx,
                member=ctx.author,
                author=ctx.guild.me,
                expiry_at=expiry_at,
                reason=reason,
            )

    if data.auto_mod[auto_moderate]["delete_message"]:
        await ctx.message.delete()

    if data.auto_mod[auto_moderate]["message"]["state"]:
        try:
            try:
                text = await ctx.bot.template_engine.render(
                    ctx.message, ctx.author, data.auto_mod[auto_moderate]["message"]["content"]
                )
            except discord.errors.HTTPException:
                emb = await ctx.bot.utils.create_error_embed(
                    ctx, "**Во время выполнения кастомной команды пройзошла неизвестная ошибка!**"
                )
                await ctx.send(embed=emb)
                return
        except jinja2.exceptions.TemplateSyntaxError as e:
            emb = await ctx.bot.utils.create_error_embed(
                ctx, f"Во время выполнения кастомной команды пройзошла ошибка:\n```{repr(e)}```"
            )
            await ctx.send(embed=emb)
            return

        if data.auto_mod[auto_moderate]["message"]["type"] == "channel":
            await ctx.send(text)
        elif data.auto_mod[auto_moderate]["message"]["type"] == "dm":
            try:
                await ctx.author.send(text)
            except discord.errors.Forbidden:
                pass
