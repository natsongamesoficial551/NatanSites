import discord
from discord.ext import commands
import logging
from config import *

logger = logging.getLogger(__name__)


class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    async def registrar(guild: discord.Guild, titulo: str, descricao: str, cor: int = COR_INFO):
        """Método estático para outros cogs registrarem logs facilmente."""
        canal = guild.get_channel(CH_LOGS)
        if not canal:
            return
        embed = discord.Embed(title=f"📋 {titulo}", description=descricao, color=cor)
        embed.timestamp = discord.utils.utcnow()
        try:
            await canal.send(embed=embed)
        except Exception as e:
            logger.error(f"Erro ao registrar log: {e}")

    async def auto_setup(self, guild: discord.Guild):
        logger.info("ℹ️ Logs: pronto para registrar ações.")


async def setup(bot):
    await bot.add_cog(Logs(bot))
