import discord
from discord.ext import commands
from discord import app_commands
import logging
from config import *
from database import get_conn

logger = logging.getLogger(__name__)


class CarrinhoView(discord.ui.View):
    def __init__(self, produto_id: str):
        super().__init__(timeout=None)
        self.produto_id = produto_id
        self.carrinho_btn.custom_id = f"carrinho_btn_{produto_id}"

    @discord.ui.button(
        label="🛒  Adicionar ao Carrinho",
        style=discord.ButtonStyle.primary,
        custom_id="carrinho_btn_placeholder"
    )
    async def carrinho_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        produto_id = interaction.data["custom_id"].replace("carrinho_btn_", "")

        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM produtos WHERE id = %s", (produto_id,))
                produto = cur.fetchone()
        finally:
            conn.close()

        if not produto:
            await interaction.response.send_message("❌ Produto não encontrado.", ephemeral=True)
            return

        if produto["estoque"] <= 0:
            await interaction.response.send_message("❌ Produto fora de estoque!", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM carrinho WHERE user_id = %s AND produto_id = %s", (user_id, produto_id))
                existente = cur.fetchone()

            if existente:
                await interaction.response.send_message(
                    "⚠️ Este produto já está no seu carrinho! Aguarde o contato do administrador.",
                    ephemeral=True
                )
                return

            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO carrinho (user_id, produto_id, nome, valor) VALUES (%s, %s, %s, %s)",
                        (user_id, produto_id, produto["nome"], produto["valor"])
                    )
        finally:
            conn.close()

        await interaction.response.send_message(
            f"✅ **{produto['nome']}** adicionado ao carrinho!\n"
            f"Aguarde o contato do administrador para finalizar sua compra. 🤝",
            ephemeral=True
        )

        canal_log = interaction.guild.get_channel(CH_LOGS)
        if canal_log:
            embed = discord.Embed(
                title="🛒 Carrinho atualizado",
                description=f"**{interaction.user.mention}** adicionou **{produto['nome']}** ao carrinho.",
                color=COR_LOJA
            )
            embed.timestamp = discord.utils.utcnow()
            await canal_log.send(embed=embed)


class Loja(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._register_views()

    def _register_views(self):
        try:
            conn = get_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT id FROM produtos")
                    produtos = cur.fetchall()
            finally:
                conn.close()
            for p in produtos:
                self.bot.add_view(CarrinhoView(p["id"]))
            logger.info(f"✅ Loja: {len(produtos)} view(s) registrada(s).")
        except Exception as e:
            logger.error(f"Erro ao registrar views loja: {e}")

    @app_commands.command(name="loja-add", description="[ADM] Adiciona um produto à loja.")
    @app_commands.describe(
        nome="Nome do produto", descricao="Descrição do produto",
        valor="Valor do produto (ex: 29.90)", estoque="Quantidade em estoque",
        imagem_url="URL da imagem do produto (opcional)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def loja_add(self, interaction: discord.Interaction, nome: str, descricao: str,
                       valor: str, estoque: int, imagem_url: str = None):
        if interaction.channel_id != CH_CONTROLE:
            await interaction.response.send_message(f"❌ Use no canal <#{CH_CONTROLE}>.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        conn = get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM produtos")
                    count = cur.fetchone()["count"]
                    produto_id = f"prod_{count + 1:04d}"
                    cur.execute(
                        "INSERT INTO produtos (id, nome, descricao, valor, estoque, imagem) VALUES (%s, %s, %s, %s, %s, %s)",
                        (produto_id, nome, descricao, valor, estoque, imagem_url)
                    )
        finally:
            conn.close()

        canal = interaction.guild.get_channel(CH_LOJA)
        produto = {"nome": nome, "descricao": descricao, "valor": valor, "estoque": estoque, "imagem": imagem_url}
        embed = self._build_embed(produto_id, produto)
        view = CarrinhoView(produto_id)
        self.bot.add_view(view)
        msg = await canal.send(embed=embed, view=view)

        conn = get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE produtos SET msg_id = %s WHERE id = %s", (msg.id, produto_id))
        finally:
            conn.close()

        await interaction.followup.send(f"✅ Produto **{nome}** adicionado! (ID: `{produto_id}`)", ephemeral=True)

    @app_commands.command(name="loja-remover", description="[ADM] Remove um produto da loja.")
    @app_commands.describe(produto_id="ID do produto (ex: prod_0001)")
    @app_commands.checks.has_permissions(administrator=True)
    async def loja_remover(self, interaction: discord.Interaction, produto_id: str):
        if interaction.channel_id != CH_CONTROLE:
            await interaction.response.send_message(f"❌ Use no canal <#{CH_CONTROLE}>.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM produtos WHERE id = %s", (produto_id,))
                produto = cur.fetchone()
        finally:
            conn.close()

        if not produto:
            await interaction.followup.send("❌ Produto não encontrado.", ephemeral=True)
            return

        canal = interaction.guild.get_channel(CH_LOJA)
        if produto["msg_id"] and canal:
            try:
                msg = await canal.fetch_message(produto["msg_id"])
                await msg.delete()
            except Exception:
                pass

        conn = get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM produtos WHERE id = %s", (produto_id,))
        finally:
            conn.close()

        await interaction.followup.send(f"✅ Produto `{produto_id}` removido.", ephemeral=True)

    @app_commands.command(name="ver-carrinho", description="[ADM] Vê todos os usuários com itens no carrinho.")
    @app_commands.checks.has_permissions(administrator=True)
    async def ver_carrinho(self, interaction: discord.Interaction):
        if interaction.channel_id != CH_CONTROLE:
            await interaction.response.send_message(f"❌ Use no canal <#{CH_CONTROLE}>.", ephemeral=True)
            return

        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM carrinho ORDER BY user_id")
                itens = cur.fetchall()
        finally:
            conn.close()

        if not itens:
            await interaction.response.send_message("🛒 Nenhum item nos carrinhos no momento.", ephemeral=True)
            return

        embed = discord.Embed(title="🛒  Carrinhos Ativos", color=COR_LOJA)
        agrupado = {}
        for item in itens:
            agrupado.setdefault(item["user_id"], []).append(item)

        for uid, lista in agrupado.items():
            member = interaction.guild.get_member(int(uid))
            nome = member.display_name if member else f"ID: {uid}"
            valor_lista = "\n".join([f"• {i['nome']} — R$ {i['valor']}" for i in lista])
            embed.add_field(name=f"👤 {nome}", value=valor_lista, inline=False)

        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="limpar-carrinho", description="[ADM] Limpa o carrinho de um usuário após venda.")
    @app_commands.describe(usuario="Usuário para limpar o carrinho")
    @app_commands.checks.has_permissions(administrator=True)
    async def limpar_carrinho(self, interaction: discord.Interaction, usuario: discord.Member):
        if interaction.channel_id != CH_CONTROLE:
            await interaction.response.send_message(f"❌ Use no canal <#{CH_CONTROLE}>.", ephemeral=True)
            return

        conn = get_conn()
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM carrinho WHERE user_id = %s", (str(usuario.id),))
        finally:
            conn.close()

        await interaction.response.send_message(f"✅ Carrinho de {usuario.mention} limpo.", ephemeral=True)

    def _build_embed(self, produto_id: str, produto: dict) -> discord.Embed:
        embed = discord.Embed(
            title=f"🛍️  {produto['nome']}",
            description=produto["descricao"],
            color=COR_LOJA
        )
        embed.add_field(name="💰  Valor", value=f"R$ {produto['valor']}", inline=True)
        embed.add_field(name="📦  Estoque", value=str(produto["estoque"]), inline=True)
        embed.add_field(name="🆔  ID", value=produto_id, inline=True)
        if produto.get("imagem"):
            embed.set_image(url=produto["imagem"])
        embed.set_footer(text="NatanSites | Clique no botão abaixo para adicionar ao carrinho")
        embed.timestamp = discord.utils.utcnow()
        return embed


async def setup(bot):
    await bot.add_cog(Loja(bot))
