import discord
from discord.ext import commands
from discord import app_commands
import json, os, logging
from config import *

logger = logging.getLogger(__name__)
DB_PATH = "data/free.json"


def load_db():
    if not os.path.exists(DB_PATH):
        return {"itens": {}}
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    os.makedirs("data", exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── View com botão Adquirir ──────────────────────────────────────────

class FreeView(discord.ui.View):
    def __init__(self, item_id: str, link: str):
        super().__init__(timeout=None)
        self.item_id = item_id
        self.link = link

    @discord.ui.button(
        label="⬇️  Adquirir Gratuitamente",
        style=discord.ButtonStyle.success,
        custom_id="free_btn"
    )
    async def adquirir(self, interaction: discord.Interaction, button: discord.ui.Button):
        db = load_db()
        item = db["itens"].get(self.item_id)

        if not item:
            await interaction.response.send_message("❌ Item não encontrado.", ephemeral=True)
            return

        if item.get("estoque") is not None and item["estoque"] <= 0:
            await interaction.response.send_message("❌ Item esgotado no momento.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"⬇️  Download: {item['nome']}",
            description=(
                f"{item['descricao']}\n\n"
                f"**Clique no link abaixo para baixar:**\n"
                f"🔗 [Acessar Download]({item['link']})"
            ),
            color=COR_FREE
        )
        embed.set_footer(text="NatanDEV | Downloads Gratuitos")
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=embed, ephemeral=True)

        # Reduz estoque se configurado
        if item.get("estoque") is not None:
            db["itens"][self.item_id]["estoque"] -= 1
            save_db(db)

        # Log
        canal_log = interaction.guild.get_channel(CH_LOGS)
        if canal_log:
            log = discord.Embed(
                title="📋 Log — Download Free",
                description=f"**{interaction.user.mention}** baixou **{item['nome']}**.",
                color=COR_FREE
            )
            log.timestamp = discord.utils.utcnow()
            await canal_log.send(embed=log)


# ── Cog ─────────────────────────────────────────────────────────────

class Free(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Registra views persistentes com placeholder
        bot.add_view(FreeView("placeholder", "https://example.com"))

    @app_commands.command(name="free-add", description="[ADM] Adiciona um item gratuito ao canal Free.")
    @app_commands.describe(
        nome="Nome do item",
        descricao="Descrição do item",
        link_download="Link direto de download",
        estoque="Quantidade disponível (deixe vazio para ilimitado)",
        imagem_url="URL de imagem do item (opcional)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def free_add(
        self,
        interaction: discord.Interaction,
        nome: str,
        descricao: str,
        link_download: str,
        estoque: int = None,
        imagem_url: str = None
    ):
        if interaction.channel_id != CH_CONTROLE:
            await interaction.response.send_message(f"❌ Use no canal <#{CH_CONTROLE}>.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        db = load_db()
        item_id = f"free_{len(db['itens']) + 1:04d}"
        db["itens"][item_id] = {
            "nome": nome,
            "descricao": descricao,
            "link": link_download,
            "estoque": estoque,
            "imagem": imagem_url,
            "msg_id": None
        }
        save_db(db)

        canal = interaction.guild.get_channel(CH_FREE)
        embed = self._build_embed(item_id, db["itens"][item_id])
        view = FreeView(item_id, link_download)
        msg = await canal.send(embed=embed, view=view)

        db["itens"][item_id]["msg_id"] = msg.id
        save_db(db)

        await interaction.followup.send(f"✅ Item **{nome}** adicionado! (ID: `{item_id}`)", ephemeral=True)

    @app_commands.command(name="free-remover", description="[ADM] Remove um item do canal Free.")
    @app_commands.describe(item_id="ID do item (ex: free_0001)")
    @app_commands.checks.has_permissions(administrator=True)
    async def free_remover(self, interaction: discord.Interaction, item_id: str):
        if interaction.channel_id != CH_CONTROLE:
            await interaction.response.send_message(f"❌ Use no canal <#{CH_CONTROLE}>.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        db = load_db()

        if item_id not in db["itens"]:
            await interaction.followup.send("❌ Item não encontrado.", ephemeral=True)
            return

        item = db["itens"][item_id]
        canal = interaction.guild.get_channel(CH_FREE)
        if item.get("msg_id") and canal:
            try:
                msg = await canal.fetch_message(item["msg_id"])
                await msg.delete()
            except Exception:
                pass

        del db["itens"][item_id]
        save_db(db)
        await interaction.followup.send(f"✅ Item `{item_id}` removido.", ephemeral=True)

    def _build_embed(self, item_id: str, item: dict) -> discord.Embed:
        estoque_txt = "♾️ Ilimitado" if item.get("estoque") is None else str(item["estoque"])
        embed = discord.Embed(
            title=f"🎁  {item['nome']}",
            description=item["descricao"],
            color=COR_FREE
        )
        embed.add_field(name="💰  Preço", value="**GRÁTIS** 🎉", inline=True)
        embed.add_field(name="📦  Disponível", value=estoque_txt, inline=True)
        embed.add_field(name="🆔  ID", value=item_id, inline=True)
        if item.get("imagem"):
            embed.set_image(url=item["imagem"])
        embed.set_footer(text="NatanDEV | Downloads Gratuitos — Clique em Adquirir!")
        embed.timestamp = discord.utils.utcnow()
        return embed

    async def auto_setup(self, guild: discord.Guild):
        logger.info("ℹ️ Free: sem embed fixo inicial — itens são adicionados por comando.")


async def setup(bot):
    await bot.add_cog(Free(bot))
