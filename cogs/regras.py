import discord
from discord.ext import commands
from discord import app_commands
import logging, asyncio
from config import *

logger = logging.getLogger(__name__)

REGRAS_EMBED_MARKER = "NATANDEV_REGRAS_EMBED"  # marcador invisível para identificar a mensagem

class Regras(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def build_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="📜  Regras do Servidor NatanSites",
            description=(
                "Leia com atenção e respeite todas as regras para manter um ambiente saudável e profissional."
            ),
            color=COR_PRINCIPAL
        )
        embed.add_field(
            name="🤝  Respeito é fundamental",
            value="Trate todos com cordialidade. Ofensas, xingamentos, preconceito ou discriminação **não serão tolerados**.",
            inline=False
        )
        embed.add_field(
            name="💬  Canais certos para cada assunto",
            value="Use cada canal para o que ele foi criado (ex.: <#1431081928483672216> apenas para solicitar serviços, <#1412979643551711363> para conversar).",
            inline=False
        )
        embed.add_field(
            name="📢  Sem spam ou publicidade",
            value="Mensagens repetitivas, propaganda de outros servidores ou links irrelevantes **não são permitidos**.",
            inline=False
        )
        embed.add_field(
            name="🛠️  Solicitações de serviço",
            value="Pedidos devem ser feitos apenas no canal de pedidos. Mensagens privadas ou em outros canais podem não ser respondidas.",
            inline=False
        )
        embed.add_field(
            name="🔒  Privacidade e segurança",
            value="Não compartilhe dados pessoais de outros membros. Respeite a confidencialidade de projetos e informações técnicas.",
            inline=False
        )
        embed.add_field(
            name="📌  Mantenha o foco técnico",
            value="Evite desviar o assunto dos canais de projetos, dúvidas técnicas ou portfólio. Use os canais de diversão para outros assuntos.",
            inline=False
        )
        embed.add_field(
            name="⚠️  Cumprimento das regras",
            value="O descumprimento pode levar a **aviso**, **mute temporário** ou **banimento**, dependendo da gravidade.",
            inline=False
        )
        embed.add_field(
            name="❓  Dúvidas ou sugestões",
            value="Use os canais corretos para perguntas e sugestões sobre o servidor ou serviços.",
            inline=False
        )
        embed.set_footer(
            text="NatanSites • Serviço de Sites | @everyone @here",
            icon_url="https://cdn.discordapp.com/emojis/1000000000000000000.webp"
        )
        embed.set_thumbnail(url="https://i.imgur.com/your-logo.png")  # troque pela sua logo
        # Marcador invisível no footer para identificar essa mensagem depois
        return embed

    async def enviar_regras(self, guild: discord.Guild):
        """Apaga embed antigo e envia novo embed de regras"""
        canal = guild.get_channel(CH_REGRAS)
        if not canal:
            logger.warning("⚠️ Canal de regras não encontrado.")
            return

        # Apaga mensagens antigas do bot no canal
        try:
            async for msg in canal.history(limit=50):
                if msg.author == self.bot.user:
                    await msg.delete()
                    await asyncio.sleep(0.3)
        except Exception as e:
            logger.error(f"Erro ao limpar canal de regras: {e}")

        embed = self.build_embed()
        try:
            await canal.send(content="@everyone @here", embed=embed)
            logger.info("✅ Embed de regras enviado.")
        except Exception as e:
            logger.error(f"Erro ao enviar embed de regras: {e}")

    async def auto_setup(self, guild: discord.Guild):
        import asyncio
        await self.enviar_regras(guild)

    # ── Slash Command ──────────────────────────────────────────────
    @app_commands.command(name="setup-regras", description="[ADM] Reenvia o embed de regras no canal correto.")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_regras(self, interaction: discord.Interaction):
        # Só pode usar no canal de controle
        if interaction.channel_id != CH_CONTROLE:
            await interaction.response.send_message(
                f"❌ Use este comando no canal <#{CH_CONTROLE}>.", ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)
        await self.enviar_regras(interaction.guild)
        await interaction.followup.send("✅ Embed de regras atualizado com sucesso!", ephemeral=True)

    @setup_regras.error
    async def setup_regras_error(self, interaction: discord.Interaction, error):
        await interaction.response.send_message("❌ Você não tem permissão para usar este comando.", ephemeral=True)


async def setup(bot):
    import asyncio
    await bot.add_cog(Regras(bot))
