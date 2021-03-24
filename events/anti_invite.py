import re
import discord
import jinja2
from core.utils.other import process_converters
from core.converters import Expiry
from discord.ext import commands


class EventsAntiInvite(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.SOFTBAN_ROLE = self.client.config.SOFTBAN_ROLE
        self.FOOTER = self.client.config.FOOTER_TEXT
        self.pattern = re.compile(
            "discord\s?(?:(?:.|dot|(.)|(dot))\s?gg|(?:app)?\s?.\s?com\s?/\s?invite)\s?/\s?([A-Z0-9-]{2,18})", re.I
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return

        if message.author.bot:
            return

        data = await self.client.database.sel_guild(guild=message.guild)
        if data["auto_mod"]["anti_invite"]["state"]:
            finded_codes = re.findall(self.pattern, message.content)
            try:
                guild_invites_codes = [invite.code for invite in await message.guild.invites()]
            except discord.errors.Forbidden:
                return

            invites = [
                invite
                for item in finded_codes
                for invite in item
                if invite
                if invite not in guild_invites_codes
            ]
            if invites == []:
                return

            if "target_channels" in data["auto_mod"]["anti_invite"].keys():
                if data["auto_mod"]["anti_invite"]["target_channels"]:
                    if message.channel.id not in data["auto_mod"]["anti_invite"]["target_channels"]:
                        return

            if "target_roles" in data["auto_mod"]["anti_invite"].keys():
                if data["auto_mod"]["anti_invite"]["target_roles"]:
                    state = False
                    for role in message.author.roles:
                        if role.id in data["auto_mod"]["anti_invite"]["target_roles"]:
                            state = True

                    if not state:
                        return

            if "ignore_channels" in data["auto_mod"]["anti_invite"].keys():
                if message.channel.id in data["auto_mod"]["anti_invite"]["ignore_channels"]:
                    return

            if "ignore_roles" in data["auto_mod"]["anti_invite"].keys():
                for role in message.author.roles:
                    if role.id in data["auto_mod"]["anti_invite"]["ignore_roles"]:
                        return

            if "punishment" in data["auto_mod"]["anti_invite"].keys():
                reason = "Авто-модерация: Приглашения"
                type_punishment = data["auto_mod"]["anti_invite"]["punishment"]["type"]
                ctx = await self.client.get_context(message)
                expiry_at = None
                if data["auto_mod"]["anti_invite"]["punishment"]["time"] is not None:
                    expiry_at = await process_converters(
                        ctx, Expiry.__args__, data["auto_mod"]["anti_invite"]["punishment"]["time"]
                    )

                if type_punishment == "mute":
                    await self.client.support_commands.mute(
                        ctx=ctx,
                        member=message.author,
                        author=message.guild.me,
                        expiry_at=expiry_at,
                        reason=reason,
                    )
                elif type_punishment == "warn":
                    await self.client.support_commands.warn(
                        ctx=ctx,
                        member=message.author,
                        author=message.guild.me,
                        reason=reason,
                    )
                elif type_punishment == "kick":
                    await self.client.support_commands.kick(
                        ctx=ctx,
                        member=message.author,
                        author=message.guild.me,
                        reason=reason
                    )
                elif type_punishment == "ban":
                    await self.client.support_commands.ban(
                        ctx=ctx,
                        member=message.author,
                        author=message.guild.me,
                        expiry_at=expiry_at,
                        reason=reason,
                    )
                elif type_punishment == "soft-ban":
                    await self.client.support_commands.soft_ban(
                        ctx=ctx,
                        member=message.author,
                        author=message.guild.me,
                        expiry_at=expiry_at,
                        reason=reason,
                    )

            if "delete_message" in data["auto_mod"]["anti_invite"].keys():
                await message.delete()

            if "message" in data["auto_mod"]["anti_invite"].keys():
                member_data = await self.client.database.sel_user(target=message.author)
                member_data.update({"multi": data["exp_multi"]})
                ctx = await self.client.get_context(message)
                try:
                    try:
                        text = await self.client.template_engine.render(
                            message,
                            message.author,
                            member_data,
                            data["auto_mod"]["anti_invite"]["message"]["text"]
                        )
                    except discord.errors.HTTPException:
                        emb = await self.client.utils.create_error_embed(
                            ctx, "**Во время выполнения кастомной команды пройзошла неизвестная ошибка!**"
                        )
                        await message.channel.send(embed=emb)
                        return
                except jinja2.exceptions.TemplateSyntaxError as e:
                    emb = await self.client.utils.create_error_embed(
                        ctx, f"Во время выполнения кастомной команды пройзошла ошибка:\n```{repr(e)}```"
                    )
                    await message.channel.send(embed=emb)
                    return

                if data["auto_mod"]["anti_invite"]["message"]["type"] == "channel":
                    await message.channel.send(text)
                elif data["auto_mod"]["anti_invite"]["message"]["type"] == "dm":
                    try:
                        await message.author.send(text)
                    except discord.errors.Forbidden:
                        pass


def setup(client):
    client.add_cog(EventsAntiInvite(client))
