import discord
from discord.ext import commands
from discord import app_commands
import logging
from config import *

logger = logging.getLogger(__name__)


class Anuncios(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="anunciar", description="[ADM] Faz um anúncio no canal de anúncios.")
    @app_commands.describe(
        titulo="Título do anúncio",
        mensagem="Corpo do anúncio",
        imagem_url="URL de uma imagem (opcional)",
        mencionar_todos="Mencionar @everyone? (padrão: sim)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def anunciar(
        self,
        interaction: discord.Interaction,
        titulo: str,
        mensagem: str,
        imagem_url: str = None,
        mencionar_todos: bool = True
    ):
        if interaction.channel_id != CH_CONTROLE:
            await interaction.response.send_message(
                f"❌ Use este comando no canal <#{CH_CONTROLE}>.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        canal = interaction.guild.get_channel(CH_ANUNCIOS)
        if not canal:
            await interaction.followup.send("❌ Canal de anúncios não encontrado.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"📢  {titulo}",
            description=mensagem,
            color=COR_INFO
        )
        embed.set_author(
            name="NatanSites | Serviço de Sites",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )
        embed.set_footer(
            text=f"Anunciado por {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )
        embed.timestamp = discord.utils.utcnow()

        if imagem_url:
            embed.set_image(url=imagem_url)

        conteudo = "@everyone" if mencionar_todos else ""
        await canal.send(content=conteudo, embed=embed)

        # Log
        await self._log(interaction.guild, interaction.user, titulo)
        await interaction.followup.send("✅ Anúncio enviado com sucesso!", ephemeral=True)

    async def _log(self, guild, autor, titulo):
        canal_log = guild.get_channel(CH_LOGS)
        if canal_log:
            embed = discord.Embed(
                title="📋 Log — Anúncio enviado",
                color=COR_INFO,
                description=f"**Título:** {titulo}\n**Por:** {autor.mention}"
            )
            embed.timestamp = discord.utils.utcnow()
            await canal_log.send(embed=embed)

    @anunciar.error
    async def anunciar_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Anuncios(bot))
