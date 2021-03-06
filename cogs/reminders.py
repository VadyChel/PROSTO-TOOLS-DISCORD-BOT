import datetime
import discord

from core.utils.time_utils import get_timezone_obj
from core.services.database.models import Reminder
from core.bases.cog_base import BaseCog
from core.converters import Expiry
from core.paginator import Paginator
from discord.ext import commands


class Reminders(BaseCog):
    @commands.group(
        usage="reminder [Команда]",
        description="Категория команд - напоминания",
        help=f"""**Команды групы:** create, delete, list\n\n"""
    )
    @commands.guild_only()
    @commands.cooldown(2, 10, commands.BucketType.member)
    async def reminder(self, ctx):
        if ctx.invoked_subcommand is None:
            PREFIX = str(await self.client.database.get_prefix(ctx.guild))
            commands = "\n".join(
                [f"`{PREFIX}reminder {c.name}`" for c in self.client.get_command("setting").commands]
            )
            emb = discord.Embed(
                title="Команды напоминаний",
                description=commands,
                colour=discord.Color.green(),
            )
            emb.set_author(
                name=self.client.user.name, icon_url=self.client.user.avatar_url
            )
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)

    @reminder.command(
        aliases=["add", "c"],
        description="Создаст напоминания",
        usage="reminder create [Время] [Текст]",
        help="**Полезное:**\nВремя можно указывать в таких форматах: ЧЧ:ММ.ДД.ММ.ГГГГ - 10:30.12.12.2050, кол-воТип - 10m\n\n**Примеры использования:**\n1. {Prefix}reminder create 1h Example reminder text\n2. {Prefix}reminder create 10:30.12.12.2050 Example reminder text\n\n**Пример 1:** Напомнит `Example reminder text` через 1 час\n**Пример 2:** Напомнит `Example reminder text` в 10:30 12.12.2050\n",
    )
    async def create(self, ctx, expiry_at: Expiry, *, text: str):
        if Reminder.objects.filter(user_id=ctx.author.id).count() > 20:
            emb = await self.client.utils.create_error_embed(
                ctx, "**Превишен лимит напоминалок(20)!**",
            )
            await ctx.send(embed=emb)
            return

        reminder_id = await self.client.database.add_reminder(
            member=ctx.author, channel=ctx.channel, time=expiry_at.timestamp(), text=text
        )

        emb = discord.Embed(
            title=f"Создано новое напоминая #{reminder_id}",
            description=f"**Текст напоминания:**\n```{text}```\n**Действует до:**\n`{expiry_at.strftime('%d %B %Y %X')}`",
            colour=discord.Color.green(),
        )
        emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
        await ctx.send(embed=emb)

    @reminder.command(
        aliases=["del", "d"],
        description="Удалит напоминание",
        usage="reminder delete [Id]",
        help="**Примеры использования:**\n1. {Prefix}reminder delete 1\n\n**Пример 1:** Удалит напоминания с id - `1`",
    )
    async def delete(self, ctx, reminder_id: int):
        state = await self.client.database.del_reminder(reminder_id)
        if not state:
            emb = await self.client.utils.create_error_embed(
                ctx, "**Напоминания с таким id не существует!**"
            )
            await ctx.send(embed=emb)
            return

        emb = discord.Embed(
            description=f"Напоминания `#{reminder_id}` было успешно удалено",
            colour=discord.Color.green(),
        )
        emb.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
        await ctx.send(embed=emb)

    @reminder.command(
        aliases=["l"],
        description="Покажет список ваших напоминаний",
        usage="reminder list",
        help="**Примеры использования:**\n1. {Prefix}reminder list\n\n**Пример 1:** Покажет список ваших напоминаний",
    )
    async def list(self, ctx):
        data = await self.client.database.get_reminders(user_id=ctx.author.id, guild_id=ctx.guild.id)
        guild_timezone = get_timezone_obj(await self.client.database.get_guild_timezone(ctx.guild))

        if len(data) > 0:
            embeds = []
            for reminder in data:
                active_to = datetime.datetime.fromtimestamp(reminder.time, tz=guild_timezone).strftime('%d %B %Y %X')
                emb = discord.Embed(
                    title="Список напоминаний",
                    description=f"Id: **{reminder.id}**\nДействует до: `{active_to}`\nТекст:\n>>> {reminder.text[:1024]}",
                    colour=discord.Color.green(),
                )
                emb.set_author(name=self.client.user.name, icon_url=self.client.user.avatar_url)
                emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
                embeds.append(emb)

            message = await ctx.send(embed=embeds[0])
            paginator = Paginator(ctx, message, embeds, footer=True)
            await paginator.start()
        else:
            emb = discord.Embed(
                title="Список напоминаний",
                description="У вас нету напоминаний",
                colour=discord.Color.green(),
            )
            emb.set_author(
                name=self.client.user.name, icon_url=self.client.user.avatar_url
            )
            emb.set_footer(text=self.FOOTER, icon_url=self.client.user.avatar_url)
            await ctx.send(embed=emb)


def setup(client):
    client.add_cog(Reminders(client))