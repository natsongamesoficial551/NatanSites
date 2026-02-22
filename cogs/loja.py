import discord
from discord.ext import commands
from discord import app_commands
import json, os, logging
from config import *

logger = logging.getLogger(__name__)
DB_PATH = "data/loja.json"


def load_db():
    if not os.path.exists(DB_PATH):
        return {"produtos": {}, "carrinho": {}}
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(data):
    os.makedirs("data", exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Views ───────────────────────────────────────────────────────────

class CarrinhoView(discord.ui.View):
    def __init__(self, produto_id: str):
        super().__init__(timeout=None)
        self.produto_id = produto_id

    @discord.ui.button(label="🛒  Adicionar ao Carrinho", style=discord.ButtonStyle.primary, custom_id="carrinho_btn")
    async def adicionar(self, interaction: discord.Interaction, button: discord.ui.Button):
        db = load_db()
        produto = db["produtos"].get(self.produto_id)

        if not produto:
            await interaction.response.send_message("❌ Produto não encontrado.", ephemeral=True)
            return

        if produto["estoque"] <= 0:
            await interaction.response.send_message("❌ Produto fora de estoque!", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        if user_id not in db["carrinho"]:
            db["carrinho"][user_id] = []

        # Verifica se já está no carrinho
        for item in db["carrinho"][user_id]:
            if item["id"] == self.produto_id:
                await interaction.response.send_message(
                    "⚠️ Este produto já está no seu carrinho! Aguarde o contato do administrador.", ephemeral=True
                )
                return

        db["carrinho"][user_id].append({
            "id": self.produto_id,
            "nome": produto["nome"],
            "valor": produto["valor"]
        })
        save_db(db)

        await interaction.response.send_message(
            f"✅ **{produto['nome']}** adicionado ao carrinho!\n"
            f"Aguarde o contato do administrador para finalizar sua compra. 🤝",
            ephemeral=True
        )

        # Notifica logs
        canal_log = interaction.guild.get_channel(CH_LOGS)
        if canal_log:
            embed = discord.Embed(
                title="🛒 Carrinho atualizado",
                description=f"**{interaction.user.mention}** adicionou **{produto['nome']}** ao carrinho.",
                color=COR_LOJA
            )
            embed.timestamp = discord.utils.utcnow()
            await canal_log.send(embed=embed)


# ── Cog ─────────────────────────────────────────────────────────────

class Loja(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Registra views persistentes
        bot.add_view(CarrinhoView("placeholder"))

    @app_commands.command(name="loja-add", description="[ADM] Adiciona um produto à loja.")
    @app_commands.describe(
        nome="Nome do produto",
        descricao="Descrição do produto",
        valor="Valor do produto (ex: 29.90)",
        estoque="Quantidade em estoque",
        imagem_url="URL da imagem do produto (opcional)"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def loja_add(
        self,
        interaction: discord.Interaction,
        nome: str,
        descricao: str,
        valor: str,
        estoque: int,
        imagem_url: str = None
    ):
        if interaction.channel_id != CH_CONTROLE:
            await interaction.response.send_message(f"❌ Use este comando no canal <#{CH_CONTROLE}>.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        db = load_db()
        produto_id = f"prod_{len(db['produtos']) + 1:04d}"
        db["produtos"][produto_id] = {
            "nome": nome,
            "descricao": descricao,
            "valor": valor,
            "estoque": estoque,
            "imagem": imagem_url,
            "msg_id": None
        }
        save_db(db)

        canal = interaction.guild.get_channel(CH_LOJA)
        embed = self._build_produto_embed(produto_id, db["produtos"][produto_id])
        view = CarrinhoView(produto_id)
        msg = await canal.send(embed=embed, view=view)

        db["produtos"][produto_id]["msg_id"] = msg.id
        save_db(db)

        await interaction.followup.send(f"✅ Produto **{nome}** adicionado à loja! (ID: `{produto_id}`)", ephemeral=True)

    @app_commands.command(name="loja-remover", description="[ADM] Remove um produto da loja.")
    @app_commands.describe(produto_id="ID do produto (ex: prod_0001)")
    @app_commands.checks.has_permissions(administrator=True)
    async def loja_remover(self, interaction: discord.Interaction, produto_id: str):
        if interaction.channel_id != CH_CONTROLE:
            await interaction.response.send_message(f"❌ Use este comando no canal <#{CH_CONTROLE}>.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        db = load_db()

        if produto_id not in db["produtos"]:
            await interaction.followup.send("❌ Produto não encontrado.", ephemeral=True)
            return

        produto = db["produtos"][produto_id]
        # Tenta deletar a mensagem da loja
        canal = interaction.guild.get_channel(CH_LOJA)
        if produto.get("msg_id") and canal:
            try:
                msg = await canal.fetch_message(produto["msg_id"])
                await msg.delete()
            except Exception:
                pass

        del db["produtos"][produto_id]
        save_db(db)
        await interaction.followup.send(f"✅ Produto `{produto_id}` removido.", ephemeral=True)

    @app_commands.command(name="ver-carrinho", description="[ADM] Vê todos os usuários com itens no carrinho.")
    @app_commands.checks.has_permissions(administrator=True)
    async def ver_carrinho(self, interaction: discord.Interaction):
        if interaction.channel_id != CH_CONTROLE:
            await interaction.response.send_message(f"❌ Use este comando no canal <#{CH_CONTROLE}>.", ephemeral=True)
            return

        db = load_db()
        if not db["carrinho"]:
            await interaction.response.send_message("🛒 Nenhum item nos carrinhos no momento.", ephemeral=True)
            return

        embed = discord.Embed(title="🛒  Carrinhos Ativos", color=COR_LOJA)
        for user_id, itens in db["carrinho"].items():
            if not itens:
                continue
            user = interaction.guild.get_member(int(user_id))
            nome = user.display_name if user else f"ID: {user_id}"
            lista = "\n".join([f"• {i['nome']} — R$ {i['valor']}" for i in itens])
            embed.add_field(name=f"👤 {nome}", value=lista, inline=False)

        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="limpar-carrinho", description="[ADM] Limpa o carrinho de um usuário após venda.")
    @app_commands.describe(usuario="Usuário para limpar o carrinho")
    @app_commands.checks.has_permissions(administrator=True)
    async def limpar_carrinho(self, interaction: discord.Interaction, usuario: discord.Member):
        if interaction.channel_id != CH_CONTROLE:
            await interaction.response.send_message(f"❌ Use este comando no canal <#{CH_CONTROLE}>.", ephemeral=True)
            return

        db = load_db()
        db["carrinho"][str(usuario.id)] = []
        save_db(db)
        await interaction.response.send_message(f"✅ Carrinho de {usuario.mention} limpo.", ephemeral=True)

    def _build_produto_embed(self, produto_id: str, produto: dict) -> discord.Embed:
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
        embed.set_footer(text="NatanDEV | Clique no botão abaixo para adicionar ao carrinho")
        embed.timestamp = discord.utils.utcnow()
        return embed


async def setup(bot):
    await bot.add_cog(Loja(bot))
