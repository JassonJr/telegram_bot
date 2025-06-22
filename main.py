import logging
import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

# Configuração de Log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Variáveis de Ambiente ---
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("A variável de ambiente 'TELEGRAM_BOT_TOKEN' não está configurada.")
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set.")

# Dicionário de respostas baseado em palavras-chave
respostas_automatica = {
    "olá": "Olá! Como posso ajudar?",
    "oi": "Oi! No que posso ser útil?",
    "ajuda": "Estou aqui para ajudar! Qual sua dúvida?",
    "preço": "Para informações sobre preços, por favor, visite nosso site.",
    "contato": "Você pode nos contatar pelo email ou telefone que estão em nosso perfil.",
    # Adicione mais palavras-chave e suas respostas aqui
}

# --- Funções do Bot ---
async def responder_mensagem(update: Update, context):
    if not update.message:
        logger.warning("Update received without a message.")
        return

    mensagem_recebida = update.message.text
    if not mensagem_recebida:
        logger.warning("Message received without text.")
        return

    mensagem_para_analisar = mensagem_recebida.lower()

    chat_type = update.message.chat.type
    user_info = f"{update.effective_user.full_name} ({update.effective_user.id})"

    logger.info(f"Mensagem recebida em {chat_type} de {user_info}: {mensagem_recebida}")

    resposta_encontrada = False
    for palavra_chave, resposta_fixa in respostas_automatica.items():
        if palavra_chave in mensagem_para_analisar:
            await update.message.reply_text(resposta_fixa)
            resposta_encontrada = True
            break

    if not resposta_encontrada:
        await update.message.reply_text("Desculpe, não entendi. Tente de outra forma ou use uma das palavras-chave: 'olá', 'ajuda', 'preço', 'contato'.")


# --- Configuração da Aplicação python-telegram-bot ---
# A Application do python-telegram-bot será o coração do nosso webhook.
# Não instanciamos Flask ou um router específico aqui.

application = Application.builder().token(TOKEN).build()
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_mensagem))


# --- Função Principal para o Google Cloud Functions ---
# Este é o entry-point para o Google Cloud Function.
# Ele recebe o objeto 'request' do functions-framework (que é um objeto Flask Request).
async def telegram_webhook_entrypoint(request):
    """
    Handles incoming Telegram webhook requests by passing the raw JSON update
    directly to the python-telegram-bot Application.
    """
    logger.info(f"Received {request.method} request to webhook endpoint.")

    # O python-telegram-bot Application tem um método para processar requisições Flask
    # de forma assíncrona. Ele lida com GET (para setWebhook) e POST (para updates).
    return await application.process_webhook_requests(request)