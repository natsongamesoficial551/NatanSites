import discord
from discord.ext import commands
from discord import app_commands
import logging
from config import *
from database import get_conn

logger = logging.getLogger(__name__)


class FreeView(discord.ui.View):
    def __init__(self, item_id: str):
        super().__init__(timeout=None)
        self.item_id = item_id
        self.adquirir_btn.custom_id = f"free_btn_{item_id}"

    @discord.ui.button(
        label="⬇️  Adquirir Gratuitamente",
        style=discord.ButtonStyle.success,
        custom_id="free_btn_placeholder"
    )
    async def adquirir_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        item_id = interaction.data["custom_id"].replace("free_btn_", "")

        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM free_itens WHERE id = %s", (item_id,))
                item = cur.fetchone()
        finally:
            conn.close()

        if not item:
            await interaction.response.send_message("❌ Item não encontrado.", ephemeral=True)
            return

        if item["estoque"] is not None and item["estoque"] <= 0:
            await interaction.response.send_message("❌ Item esgotado no momento.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"⬇️  Download: {item['nome']}",
            description=f"{item['descricao']}\n\n**Clique no link abaixo para baixar:**\n🔗 [Acessar Download]({item['link']})",
            color=COR_FREE
        )
        embed.set_footer(text="NatanSites | Downloads Gratuitos")
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed, ephemeral=True)

        if item["estoque"] is not None:
            conn = get_conn()
            try:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute("UPDATE free_itens SET estoque = estoque - 1 WHERE id = %s", (item_id,))
            finally:
                conn.close()

        canal_log = interaction.guild.get_channel(CH_LOGS)
        if canal_log:
            log = discord.Embed(
                title="📋 Log — Download Free",
                description=f"**{interaction.user.mention}** baixou **{item['nome']}**.",
                color=COR_FREE
            )
            log.timestamp = discord.utils.utcnow()
            await canal_log.send(embed=log)


class Free(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._register_views()

    def _register_views(self):
        try:
            conn = get_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM free_itens")
                    itens = cur.fetchall()
            finally:
                conn.close()
            for item in itens:
                self.bot.add_view(FreeView(item["id"]))
            logger.info(f"✅ Free: {len(itens)} view(s) registrada(s).")
        except Exception as e:
            logger.error(f"Erro ao registrar views free: {e}")

    @app_commands.command(name="free-add", description="[ADM] Adiciona um item gratuito ao canal Free.")
    @app_commands.describe(
        nome="Nome do item", descricao="Descrição do item",
        link_download="Link direto de download",
        estoque="Quantidade disponível (deixe vazio para ilimitado)",
        imagem_url="URL de imagem do item (opcional)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def free_add(self, interaction: discord.Interaction, nome: str, descricao: str,
                       link_download: str, estoque: int = None, imagem_url: str = None):
        if interaction.channel_id != CH_CONTROLE:
            await interaction.response.send_message(f"❌ Use no canal <#{CH_CONTROLE}>.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        conn = get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM free_itens")
                    count = cur.fetchone()["count"]
                    item_id = f"free_{count + 1:04d}"
                    cur.execute(
                        "INSERT INTO free_itens (id, nome, descricao, link, estoque, imagem) VALUES (%s, %s, %s, %s, %s, %s)",
                        (item_id, nome, descricao, link_download, estoque, imagem_url)
                    )
        finally:
            conn.close()

        canal = interaction.guild.get_channel(CH_FREE)
        item = {"nome": nome, "descricao": descricao, "link": link_download,
                "estoque": estoque, "imagem": imagem_url}
        embed = self._build_embed(item_id, item)
        view = FreeView(item_id)
        self.bot.add_view(view)
        msg = await canal.send(embed=embed, view=view)

        conn = get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE free_itens SET msg_id = %s WHERE id = %s", (msg.id, item_id))
        finally:
            conn.close()

        await interaction.followup.send(f"✅ Item **{nome}** adicionado! (ID: `{item_id}`)", ephemeral=True)

    @app_commands.command(name="free-remover", description="[ADM] Remove um item do canal Free.")
    @app_commands.describe(item_id="ID do item (ex: free_0001)")
    @app_commands.checks.has_permissions(administrator=True)
    async def free_remover(self, interaction: discord.Interaction, item_id: str):
        if interaction.channel_id != CH_CONTROLE:
            await interaction.response.send_message(f"❌ Use no canal <#{CH_CONTROLE}>.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM free_itens WHERE id = %s", (item_id,))
                item = cur.fetchone()
        finally:
            conn.close()

        if not item:
            await interaction.followup.send("❌ Item não encontrado.", ephemeral=True)
            return

        canal = interaction.guild.get_channel(CH_FREE)
        if item["msg_id"] and canal:
            try:
                msg = await canal.fetch_message(item["msg_id"])
                await msg.delete()
            except Exception:
                pass

        conn = get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM free_itens WHERE id = %s", (item_id,))
        finally:
            conn.close()

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
        embed.set_footer(text="NatanSites | Downloads Gratuitos — Clique em Adquirir!")
        embed.timestamp = discord.utils.utcnow()
        return embed

    async def auto_setup(self, guild: discord.Guild):
        logger.info("ℹ️ Free: views já registradas via _register_views.")


async def setup(bot):
    await bot.add_cog(Free(bot))
