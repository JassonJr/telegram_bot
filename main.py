import logging
import os
from flask import Flask, request, jsonify
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


# --- Configuração da Aplicação Flask e python-telegram-bot ---
app = Flask(__name__)

# O objeto Application do python-telegram-bot é criado globalmente.
application = Application.builder().token(TOKEN).build()
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_mensagem))

# Este é o NOVO ponto de entrada para o Google Cloud Functions.
# Usamos a função run_webhook do Application, que já sabe como lidar com o Flask.
async def telegram_webhook_entrypoint(request):
    """
    Handles incoming Telegram webhook requests via Flask's request object.
    This function acts as the entry point for Google Cloud Functions.
    """
    if request.method == "POST":
        return await application.update_queue.put(Update.de_json(request.get_json(force=True), application.bot))
    elif request.method == "GET":
        # Retorna OK para requisições GET (usadas para configurar o webhook)
        logger.info("Received GET request. Returning OK for webhook setup.")
        return jsonify({"status": "ok", "message": "Webhook endpoint is live. Send POST requests for Telegram updates."}), 200
    else:
        return jsonify({"status": "error", "message": "Method not allowed"}), 405

# Em ambientes de produção (como Cloud Functions), você não chama app.run().
# O Flask é executado pelo functions-framework ou um servidor WSGI.
# A função telegram_webhook_entrypoint será o "entry-point" do seu Cloud Function.