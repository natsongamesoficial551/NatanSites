# 🤖 NatanDEV Bot — Guia de Instalação e Uso

## 📁 Estrutura do Projeto
```
natandev-bot/
├── main.py              ← Arquivo principal (execute este)
├── config.py            ← IDs dos canais, token, cores
├── requirements.txt     ← Dependências Python
├── data/                ← Banco de dados JSON (criado automaticamente)
│   ├── loja.json
│   ├── compras.json
│   ├── projetos.json
│   └── free.json
└── cogs/                ← Módulos do bot
    ├── regras.py
    ├── anuncios.py
    ├── apresentacoes.py
    ├── loja.py
    ├── compras.py
    ├── projetos.py
    ├── suporte.py
    ├── zoacao.py
    ├── free.py
    └── logs.py
```

---

## ⚙️ Instalação

### 1. Instalar Python 3.11+
Baixe em https://www.python.org/downloads/

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar o bot
Abra o arquivo `config.py` e preencha:
```python
BOT_TOKEN = "SEU_TOKEN_AQUI"    # Token do Developer Portal
GUILD_ID  = 000000000000000000  # ID do seu servidor Discord
ROLE_ADMIN   = 000000000000000000  # ID do cargo Administrador
ROLE_FUNDADOR = 000000000000000000  # ID do cargo Fundador
```

### 4. Criar o bot no Discord Developer Portal
1. Acesse https://discord.com/developers/applications
2. Crie um novo aplicativo
3. Vá em **Bot** → Ative **"Message Content Intent"** e **"Server Members Intent"**
4. Copie o token e cole no `config.py`
5. Em **OAuth2 > URL Generator**: marque `bot` + `applications.commands`
6. Permissões: Administrator (ou ajuste conforme preferir)
7. Convide o bot com o link gerado

### 5. Iniciar o bot
```bash
python main.py
```

---

## 🎮 Comandos por Canal

### 📍 Canal: Controle do Bot (todos os comandos ADM ficam aqui)

| Comando | Descrição |
|---------|-----------|
| `/setup-regras` | Reenvia embed de regras |
| `/setup-suporte` | Reenvia embed de suporte com botão |
| `/setup-zoacao` | Reenvia embed de zoação com botão |
| `/anunciar` | Faz um anúncio no canal de anúncios |
| `/registrar-compra` | Registra uma compra no canal Compras |
| `/loja-add` | Adiciona produto na loja |
| `/loja-remover` | Remove produto da loja |
| `/ver-carrinho` | Vê quem tem itens no carrinho |
| `/limpar-carrinho` | Limpa carrinho após venda |
| `/projeto-add` | Adiciona projeto ao canal Projetos |
| `/projeto-remover` | Remove projeto |
| `/free-add` | Adiciona item gratuito no canal Free |
| `/free-remover` | Remove item do canal Free |
| `/zoacao-add` | Adiciona frase de zoação à lista |

---

## 🔄 Comportamento ao Iniciar

Ao ligar o bot, ele automaticamente:
1. ✅ Apaga mensagens antigas dele no canal **Regras** e reenvia o embed
2. ✅ Apaga mensagens antigas dele no canal **Suporte** e reenvia o embed com botão
3. ✅ Apaga mensagens antigas dele no canal **Zoação** e reenvia o embed com botão
4. ✅ Sincroniza todos os slash commands (aparecem com `/` no Discord)

---

## 🎫 Sistema de Suporte (Tickets)
- Usuário clica em **📩 Chamar Suporte** no canal suporte
- Bot cria canal privado `ticket-[username]` visível apenas para o usuário e ADMs
- Canal tem botão **🔒 Fechar Ticket** — somente administradores conseguem usar
- Ao fechar: canal é deletado e ação é registrada nos logs

## 🛒 Sistema de Loja
1. ADM usa `/loja-add` → produto aparece na loja com botão
2. Usuário clica em **🛒 Adicionar ao Carrinho**
3. ADM usa `/ver-carrinho` para ver quem tem interesse
4. ADM chama o usuário no PV para finalizar
5. ADM usa `/registrar-compra` → aparece no canal Compras
6. ADM usa `/limpar-carrinho` para limpar após venda

---

## ❓ Problemas Comuns

**Bot não aparece os comandos `/`:**
- Aguarde até 1 hora após o primeiro start (Discord pode demorar para sincronizar)
- Verifique se a permissão `applications.commands` está no link de convite

**Erro de permissão ao criar canal de ticket:**
- O bot precisa da permissão `Manage Channels` no servidor

**Bot não apaga mensagens antigas:**
- O bot precisa da permissão `Manage Messages` nos canais fixos
