from collections import Counter

from motor import version as motorversion
from PIL import features as pilfeatures
from pymongo import version as pymongoversion
from redbot.core import commands
from redbot.core.utils import chat_formatting as chat
from tabulate import tabulate

from leveler.abc import MixinMeta

from .basecmd import LevelAdminBaseCMD


class Debugging(MixinMeta):
    """Debug commands"""

    lvladmin = getattr(LevelAdminBaseCMD, "lvladmin")

    @lvladmin.group(hidden=True, name="debug")
    @commands.is_owner()
    async def debug_commands(self, ctx):
        """Debug commands.

        Dont use it until you know what you doing."""

    @debug_commands.command(name="info")
    async def debug_info(self, ctx):
        await ctx.send(
            chat.box(
                tabulate(
                    {
                        "pymongo version": pymongoversion,
                        "motor version": motorversion,
                        "PIL version": pilfeatures.version("pil"),
                        "PIL features": tabulate(
                            {
                                feature: pilfeatures.version(feature) or "N/A"
                                for feature in pilfeatures.get_supported()
                            },
                            tablefmt="psql",
                        ),
                    },
                    tablefmt="psql",
                )
            )
        )

    @debug_commands.group(name="integrity")
    async def db_integrity(self, ctx):
        """Database integrity commands."""

    @db_integrity.command(name="check")
    async def db_integrity_check(self, ctx):
        """Check Database integrity.

        Everything should be True. Otherwise there is malfunction somewhere in XP handling."""
        c = Counter()
        async with ctx.typing():
            async for user in self.db.users.find({}):
                total_xp = 0
                for server in user["servers"]:
                    xp = await self._level_exp(user["servers"][server]["level"])
                    total_xp += xp
                    total_xp += user["servers"][server]["current_exp"]
                c[total_xp == user["total_exp"]] += 1
        await ctx.send(chat.box(tabulate(c.most_common())))

    @db_integrity.command(name="fix")
    async def db_integrity_fix(self, ctx):
        """Artificially fix Database integrity."""
        async with ctx.typing():
            async for user in self.db.users.find({}):
                total_xp = 0
                for server in user["servers"]:
                    xp = await self._level_exp(user["servers"][server]["level"])
                    total_xp += xp
                    total_xp += user["servers"][server]["current_exp"]
                if total_xp != user["total_exp"]:
                    await self.db.users.update_one(
                        {"user_id": user["user_id"]}, {"$set": {"total_exp": total_xp}}
                    )
        await ctx.tick()
