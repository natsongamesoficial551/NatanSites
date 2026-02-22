import discord
from discord.ext import commands
from discord import app_commands
import random, logging, asyncio
from config import *

logger = logging.getLogger(__name__)

FRASES_ZOACAO = [
    "Você programa tão devagar que até o compilador foi tomar café antes de terminar. ☕",
    "Seu código tem mais bug do que um jardim tropical em época de chuva. 🐛",
    "Você demorou tanto pra responder que o Wi-Fi foi e voltou duas vezes. 📡",
    "Você usa o Stack Overflow pra calcular 2+2. 😂",
    "Seu computador trava de vergonha quando você abre o VS Code. 💻",
    "Você digita tão devagar que a barra de rolagem já foi dormir. 😴",
    "Sua lógica é tão confusa que até o GPT ficou com dúvida. 🤖",
    "Você commit tão raramente que o GitHub mandou um 'você ainda está aqui?'. 📦",
    "Seu CSS é tão bagunçado que o designer pediu demissão. 🎨",
    "Você faz deploy às sextas-feira. Diz mais nada. 🚀💥",
    "Você abre o terminal e já o terminal dá um suspiro. 😮‍💨",
    "Seu dark mode é tão escuro que absorbeu a sua criatividade. 🌑",
    "Você escreve comentários mais longos do que o código em si. 📝",
    "Você ainda usa Internet Explorer? Tô achando que sim. 🪦",
    "Sua variável favorita é 'x'. Que originalidade! 🎲",
    "Você acha que recursão é um time de futebol. 🔄",
    "Seu banco de dados tem mais JOIN do que sentido. 🗄️",
    "Você faz push direto na main. Coragem ou descuido? 😬",
    "Seu loop infinito terminou antes da sua reunião de segunda. ♾️",
    "Você usou !important em tudo. E nada funcionou. 🤡",
]


class ZoacaoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="😂  Zoar!",
        style=discord.ButtonStyle.secondary,
        custom_id="zoacao_btn",
        emoji="😂"
    )
    async def zoar(self, interaction: discord.Interaction, button: discord.ui.Button):
        frase = random.choice(FRASES_ZOACAO)
        embed = discord.Embed(
            description=f"😂 **{interaction.user.display_name}** ativou a zoação:\n\n> {frase}",
            color=COR_ZOACAO
        )
        embed.set_footer(text="NatanSites | Modo Zoação 😂")
        await interaction.response.send_message(embed=embed)


class Zoacao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.add_view(ZoacaoView())

    async def enviar_zoacao(self, guild: discord.Guild):
        """Apaga mensagem antiga e envia embed fixo de zoação"""
        canal = guild.get_channel(CH_ZOACAO)
        if not canal:
            return

        try:
            async for msg in canal.history(limit=20):
                if msg.author == self.bot.user:
                    await msg.delete()
                    await asyncio.sleep(0.3)
        except Exception as e:
            logger.error(f"Erro ao limpar canal zoação: {e}")

        embed = discord.Embed(
            title="😂  Modo Zoação Ativado!",
            description=(
                "Bem-vindo ao canal de diversão do **NatanSites**! 🎉\n\n"
                "Clique no botão abaixo para receber uma **frase de zoação** aleatória\n"
                "e alegrar o dia de todos por aqui! 😂\n\n"
                "*Use com responsabilidade... ou não. 🤪*"
            ),
            color=COR_ZOACAO
        )
        embed.set_footer(text="NatanSites | Canal de Diversão")
        embed.timestamp = discord.utils.utcnow()

        view = ZoacaoView()
        await canal.send(embed=embed, view=view)
        logger.info("✅ Embed de zoação enviado.")

    async def auto_setup(self, guild: discord.Guild):
        await self.enviar_zoacao(guild)

    @app_commands.command(name="setup-zoacao", description="[ADM] Reenvia o embed de zoação.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_zoacao(self, interaction: discord.Interaction):
        if interaction.channel_id != CH_CONTROLE:
            await interaction.response.send_message(f"❌ Use no canal <#{CH_CONTROLE}>.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        await self.enviar_zoacao(interaction.guild)
        await interaction.followup.send("✅ Embed de zoação atualizado!", ephemeral=True)

    @app_commands.command(name="zoacao-add", description="[ADM] Adiciona uma nova frase de zoação à lista.")
    @app_commands.describe(frase="A frase de zoação a adicionar")
    @app_commands.checks.has_permissions(administrator=True)
    async def zoacao_add(self, interaction: discord.Interaction, frase: str):
        FRASES_ZOACAO.append(frase)
        await interaction.response.send_message(f"✅ Frase adicionada! Total: **{len(FRASES_ZOACAO)}** frases.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(Zoacao(bot))
