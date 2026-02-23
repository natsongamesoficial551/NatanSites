import discord
from discord.ext import commands
from discord import app_commands
import logging
from config import *
from database import get_conn

logger = logging.getLogger(__name__)


class Projetos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="projeto-add", description="[ADM] Adiciona um projeto ao canal de projetos.")
    @app_commands.describe(
        nome="Nome do projeto", descricao="Descrição do projeto",
        url="Link do projeto (opcional)", imagem_url="URL da imagem (opcional)",
        cliente="Nome do cliente (opcional)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def projeto_add(self, interaction: discord.Interaction, nome: str, descricao: str,
                          url: str = None, imagem_url: str = None, cliente: str = None):
        if interaction.channel_id != CH_CONTROLE:
            await interaction.response.send_message(f"❌ Use no canal <#{CH_CONTROLE}>.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM projetos")
                count = cur.fetchone()["count"]
                projeto_id = f"proj_{count + 1:04d}"
        finally:
            conn.close()

        canal = interaction.guild.get_channel(CH_PROJETOS)
        if not canal:
            await interaction.followup.send("❌ Canal de projetos não encontrado.", ephemeral=True)
            return

        embed = discord.Embed(title=f"🗂️  {nome}", description=descricao, color=COR_PRINCIPAL)
        if cliente:
            embed.add_field(name="👤  Cliente", value=cliente, inline=True)
        embed.add_field(name="🆔  ID", value=projeto_id, inline=True)
        if url:
            embed.add_field(name="🔗  Link do Projeto", value=f"[Clique aqui para acessar]({url})", inline=False)
        if imagem_url:
            embed.set_image(url=imagem_url)
        embed.set_footer(
            text="NatanSites | Portfólio de Projetos",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )
        embed.timestamp = discord.utils.utcnow()
        msg = await canal.send(embed=embed)

        conn = get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO projetos (id, nome, descricao, url, imagem, cliente, msg_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (projeto_id, nome, descricao, url, imagem_url, cliente, msg.id)
                    )
        finally:
            conn.close()

        await interaction.followup.send(f"✅ Projeto **{nome}** adicionado! (ID: `{projeto_id}`)", ephemeral=True)

    @app_commands.command(name="projeto-remover", description="[ADM] Remove um projeto do canal.")
    @app_commands.describe(projeto_id="ID do projeto (ex: proj_0001)")
    @app_commands.checks.has_permissions(administrator=True)
    async def projeto_remover(self, interaction: discord.Interaction, projeto_id: str):
        if interaction.channel_id != CH_CONTROLE:
            await interaction.response.send_message(f"❌ Use no canal <#{CH_CONTROLE}>.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM projetos WHERE id = %s", (projeto_id,))
                projeto = cur.fetchone()
        finally:
            conn.close()

        if not projeto:
            await interaction.followup.send("❌ Projeto não encontrado.", ephemeral=True)
            return

        canal = interaction.guild.get_channel(CH_PROJETOS)
        if projeto["msg_id"] and canal:
            try:
                msg = await canal.fetch_message(projeto["msg_id"])
                await msg.delete()
            except Exception:
                pass

        conn = get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM projetos WHERE id = %s", (projeto_id,))
        finally:
            conn.close()

        await interaction.followup.send(f"✅ Projeto `{projeto_id}` removido.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Projetos(bot))
