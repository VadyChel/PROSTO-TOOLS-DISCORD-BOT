from core.bases.cog_base import BaseCog
from core.utils.other import process_auto_moderate
from discord.ext import commands


class EventsAntiCaps(BaseCog):
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return

        if message.author.bot:
            return

        if message.author == message.guild.owner:
            return

        data = await self.client.database.sel_guild(guild=message.guild)
        if data.auto_mod["anti_caps"]["state"]:
            if len(message.content) < data.auto_mod["anti_caps"]["min_chars"]:
                return

            content_without_spaces = message.content.replace(" ", "")
            num_upper_chars = 0
            for char in list(content_without_spaces):
                if char.isupper():
                    num_upper_chars += 1

            upper_percent = (num_upper_chars/len(content_without_spaces))*100
            if not upper_percent >= data.auto_mod["anti_caps"]["percent"]:
                return

            await process_auto_moderate(
                await self.client.get_context(message), "anti_caps", data, "Авто-модерация: Капс"
            )


def setup(client):
    client.add_cog(EventsAntiCaps(client))
