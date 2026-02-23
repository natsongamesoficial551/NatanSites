import discord
from discord.ext import commands
from discord import app_commands
import logging
from config import *
from database import get_conn

logger = logging.getLogger(__name__)


class Compras(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="registrar-compra", description="[ADM] Registra uma compra no canal Compras.")
    @app_commands.describe(
        usuario="Usuário que realizou a compra",
        produto="Nome do produto/serviço",
        valor="Valor pago (ex: 49.90)",
        observacao="Observação adicional (opcional)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def registrar_compra(self, interaction: discord.Interaction, usuario: discord.Member,
                                produto: str, valor: str, observacao: str = None):
        if interaction.channel_id != CH_CONTROLE:
            await interaction.response.send_message(f"❌ Use no canal <#{CH_CONTROLE}>.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        conn = get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE compras_contador SET valor = valor + 1 WHERE id = 1")
                    cur.execute("SELECT valor FROM compras_contador WHERE id = 1")
                    contador = cur.fetchone()["valor"]
                    compra_id = f"NTS-{contador:04d}"
                    cur.execute(
                        "INSERT INTO compras (id, usuario_id, produto, valor, observacao) VALUES (%s, %s, %s, %s, %s)",
                        (compra_id, usuario.id, produto, valor, observacao)
                    )
        finally:
            conn.close()

        canal = interaction.guild.get_channel(CH_COMPRAS)
        if not canal:
            await interaction.followup.send("❌ Canal de compras não encontrado.", ephemeral=True)
            return

        embed = discord.Embed(
            title="✅  Compra Confirmada!",
            description="Uma nova compra foi registrada com sucesso no **NatanSites**.",
            color=COR_SUCESSO
        )
        embed.set_thumbnail(url=usuario.display_avatar.url)
        embed.add_field(name="👤  Comprador", value=usuario.mention, inline=True)
        embed.add_field(name="🆔  Pedido Nº", value=f"`{compra_id}`", inline=True)
        embed.add_field(name="🛍️  Produto/Serviço", value=produto, inline=False)
        embed.add_field(name="💰  Valor Pago", value=f"R$ {valor}", inline=True)
        if observacao:
            embed.add_field(name="📝  Observação", value=observacao, inline=False)
        embed.set_footer(
            text=f"Registrado por {interaction.user.display_name} | NatanSites",
            icon_url=interaction.user.display_avatar.url
        )
        embed.timestamp = discord.utils.utcnow()
        await canal.send(embed=embed)

        canal_log = interaction.guild.get_channel(CH_LOGS)
        if canal_log:
            log = discord.Embed(
                title="📋 Log — Compra registrada",
                description=f"**Pedido:** {compra_id}\n**Comprador:** {usuario.mention}\n**Produto:** {produto}\n**Valor:** R$ {valor}",
                color=COR_SUCESSO
            )
            log.timestamp = discord.utils.utcnow()
            await canal_log.send(embed=log)

        await interaction.followup.send(f"✅ Compra `{compra_id}` registrada!", ephemeral=True)

    @registrar_compra.error
    async def error(self, interaction, error):
        await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Compras(bot))
