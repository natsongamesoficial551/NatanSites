import discord
from discord.ext import commands
from discord import app_commands
import json, os, logging
from config import *

logger = logging.getLogger(__name__)
DB_PATH = "data/compras.json"


def load_db():
    if not os.path.exists(DB_PATH):
        return {"compras": [], "contador": 0}
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    os.makedirs("data", exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Compras(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="registrar-compra", description="[ADM] Registra uma compra de um usuário no canal Compras.")
    @app_commands.describe(
        usuario="Usuário que realizou a compra",
        produto="Nome do produto/serviço",
        valor="Valor pago (ex: 49.90)",
        observacao="Observação adicional (opcional)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def registrar_compra(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        produto: str,
        valor: str,
        observacao: str = None
    ):
        if interaction.channel_id != CH_CONTROLE:
            await interaction.response.send_message(f"❌ Use este comando no canal <#{CH_CONTROLE}>.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        db = load_db()
        db["contador"] += 1
        compra_id = f"NDB-{db['contador']:04d}"

        db["compras"].append({
            "id": compra_id,
            "usuario_id": usuario.id,
            "produto": produto,
            "valor": valor,
            "observacao": observacao
        })
        save_db(db)

        canal = interaction.guild.get_channel(CH_COMPRAS)
        if not canal:
            await interaction.followup.send("❌ Canal de compras não encontrado.", ephemeral=True)
            return

        embed = discord.Embed(
            title="✅  Compra Confirmada!",
            description=f"Uma nova compra foi registrada com sucesso no **NatanDEV**.",
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
            text=f"Registrado por {interaction.user.display_name} | NatanDEV",
            icon_url=interaction.user.display_avatar.url
        )
        embed.timestamp = discord.utils.utcnow()

        await canal.send(embed=embed)

        # Log
        canal_log = interaction.guild.get_channel(CH_LOGS)
        if canal_log:
            log = discord.Embed(
                title="📋 Log — Compra registrada",
                description=f"**Pedido:** {compra_id}\n**Comprador:** {usuario.mention}\n**Produto:** {produto}\n**Valor:** R$ {valor}",
                color=COR_SUCESSO
            )
            log.timestamp = discord.utils.utcnow()
            await canal_log.send(embed=log)

        await interaction.followup.send(f"✅ Compra `{compra_id}` registrada com sucesso!", ephemeral=True)

    @registrar_compra.error
    async def registrar_compra_error(self, interaction, error):
        await interaction.response.send_message("❌ Sem permissão.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Compras(bot))
