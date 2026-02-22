import discord
from discord.ext import commands
from discord import app_commands
import logging
from config import *

logger = logging.getLogger(__name__)


class Apresentacoes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def build_boas_vindas(self, member: discord.Member) -> discord.Embed:
        numero = member.guild.member_count

        embed = discord.Embed(
            title="✨  Bem-vindo(a) ao NatanSites!",
            description=(
                f"Olá, {member.mention}! 🎉\n\n"
                "É um prazer ter você aqui no **NatanSites | Serviço de Sites**.\n"
                "Somos um servidor focado em **desenvolvimento web, projetos digitais e soluções profissionais**.\n\n"
                "Antes de começar, não esqueça de:\n"
                f"📜 Ler as regras em <#{CH_REGRAS}>\n"
                f"❓ Ver as dúvidas frequentes em <#{CH_REGRAS}>\n"
                f"💬 Se apresentar aqui no canal!\n\n"
                "*Seja bem-vindo(a) à nossa comunidade!*"
            ),
            color=COR_BOAS_VINDAS
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_author(
            name=f"{member.display_name} acabou de entrar!",
            icon_url=member.display_avatar.url
        )
        embed.add_field(
            name="👤 Usuário",
            value=f"{member.name}",
            inline=True
        )
        embed.add_field(
            name="🆔 ID",
            value=str(member.id),
            inline=True
        )
        embed.add_field(
            name="👥 Membro Nº",
            value=f"#{numero}",
            inline=True
        )
        embed.set_image(url="https://i.imgur.com/your-banner.png")  # troque pelo seu banner
        embed.set_footer(
            text="NatanSites • Serviço de Sites",
            icon_url=member.guild.icon.url if member.guild.icon else None
        )
        embed.timestamp = discord.utils.utcnow()
        return embed

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        canal = member.guild.get_channel(CH_APRESENTACOES)
        if not canal:
            logger.warning("⚠️ Canal de apresentações não encontrado.")
            return

        embed = self.build_boas_vindas(member)
        try:
            await canal.send(embed=embed)
            logger.info(f"✅ Boas-vindas enviado para {member.display_name}")
        except Exception as e:
            logger.error(f"Erro ao enviar boas-vindas: {e}")

        # Log
        canal_log = member.guild.get_channel(CH_LOGS)
        if canal_log:
            log_embed = discord.Embed(
                title="📋 Log — Novo membro",
                color=COR_SUCESSO,
                description=f"**{member.mention}** entrou no servidor."
            )
            log_embed.timestamp = discord.utils.utcnow()
            await canal_log.send(embed=log_embed)

    async def auto_setup(self, guild: discord.Guild):
        # Apresentações não tem mensagem fixa, só evento — nada a fazer aqui
        logger.info("ℹ️ Apresentações: aguardando membros entrarem.")


async def setup(bot):
    await bot.add_cog(Apresentacoes(bot))
