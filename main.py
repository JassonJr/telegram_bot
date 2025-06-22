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
    # Esta linha vai levantar um erro se o token não for encontrado, o que é bom para depuração.
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set.")

# Dicionário de respostas baseado em palavras-chave
respostas_automatica = {
    "pc": "Vida de pcista",
    "jogo": "zoomer",
    "ps": "console de judeu",
    "playstation": "console de judeu",
    "pincel": "Começou a bajulação",
    "traveco": "amo todos",
    "ocidente": "acabou, judeu venceu",
    "xbox": "só sentar, deitar, jogar e dormir",
    "gamepass": "faz o x",
    "sentiu": "zoomer momento",
    "doutor": "zoomer",
    "goty": "bridget",
    "judeu": "👃🏻",
    "bridget": "é um homi",
    # Adicione mais pares de perguntas e respostas
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
        #await update.message.reply_text("Desculpe, não entendi. Tente de outra forma ou use uma das palavras-chave: 'olá', 'ajuda', 'preço', 'contato'.")
        pass # Não faz nada se não encontrar palavra-chave e não for uma menção direta


# --- Configuração da Aplicação Flask para Webhook ---
app = Flask(__name__)

# O objeto Application do python-telegram-bot é criado globalmente.
application = Application.builder().token(TOKEN).build()
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_mensagem))

# --- Função Principal para o Google Cloud Functions ---
# Esta função será acionada por requisições HTTP (GET para setWebhook, POST para updates)
@app.route('/', methods=['GET', 'POST']) # Define que esta rota aceita GET e POST
async def telegram_webhook_handler(): # Não precisa mais receber 'request' como argumento
    """Handles incoming Telegram webhook requests."""
    
    if request.method == 'GET':
        # Esta é a requisição que você faz no navegador para configurar o webhook.
        # Apenas retornamos um status OK para indicar que o endpoint existe.
        logger.info("Received GET request to webhook endpoint. This is likely a setWebhook call.")
        return jsonify({"status": "ok", "message": "Webhook endpoint is live. Send POST requests for Telegram updates."}), 200
    
    elif request.method == 'POST':
        # Esta é a requisição real do Telegram com as atualizações do bot.
        try:
            req_json = request.get_json(silent=True)
            if not req_json:
                logger.error("No JSON payload received or invalid JSON for POST request.")
                return jsonify({"status": "error", "message": "Invalid JSON"}), 400
            
            update = Update.de_json(req_json, application.bot)
            await application.process_update(update)
            
            return jsonify({"status": "ok"}), 200

        except Exception as e:
            logger.exception(f"Error processing webhook POST request: {e}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    else:
        # Lidar com outros métodos HTTP se necessário
        return jsonify({"status": "error", "message": "Method not allowed"}), 405