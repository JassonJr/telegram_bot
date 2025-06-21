import logging
import os
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

# Configuração de Log (para ajudar na depuração no Cloud Functions logs)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Variáveis de Ambiente ---
# É CRÍTICO que você não coloque seu TOKEN diretamente no código em produção.
# O TOKEN será passado como uma variável de ambiente no Google Cloud Functions.
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("A variável de ambiente 'TELEGRAM_BOT_TOKEN' não está configurada.")
    # Em produção, você pode querer levantar uma exceção ou ter um comportamento padrão.
    # Para testes locais, pode-se colocar o token aqui temporariamente:
    # TOKEN = "SEU_TOKEN_AQUI_PARA_TESTES_LOCAIS"

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

    # Convertendo para minúsculas para facilitar a comparação
    mensagem_para_analisar = mensagem_recebida.lower()
    
    chat_type = update.message.chat.type # 'private', 'group', 'supergroup'
    user_info = f"{update.effective_user.full_name} ({update.effective_user.id})"
    
    logger.info(f"Mensagem recebida em {chat_type} de {user_info}: {mensagem_recebida}")

    resposta_encontrada = False
    for palavra_chave, resposta_fixa in respostas_automatica.items():
        if palavra_chave in mensagem_para_analisar:
            await update.message.reply_text(resposta_fixa)
            resposta_encontrada = True
            break
    
    if not resposta_encontrada:
        # Resposta padrão se nenhuma palavra-chave for encontrada
        # Você pode personalizar ou remover esta parte se preferir que o bot não responda
        # a mensagens não reconhecidas.
        #await update.message.reply_text("Desculpe, não entendi. Tente de outra forma ou use uma das palavras-chave: 'olá', 'ajuda', 'preço', 'contato'.")
        pass # Não faz nada se não encontrar palavra-chave e não for uma menção direta


# --- Configuração da Aplicação Flask para Webhook ---
# Criamos uma instância do Flask.
# Esta será a "porta de entrada" para as requisições HTTP do Telegram.
app = Flask(__name__)

# O objeto Application do python-telegram-bot é criado globalmente.
# Ele será usado para processar os updates que o Flask receber.
application = Application.builder().token(TOKEN).build()
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_mensagem))


# --- Função Principal para o Google Cloud Functions ---
# Esta é a função que o Google Cloud Functions vai chamar quando receber uma requisição HTTP.
# O nome desta função é importante e será configurado no Cloud Functions.
async def telegram_webhook_handler(request):
    """Handles incoming Telegram webhook requests."""
    
    # O Google Cloud Functions recebe o request como um objeto Flask.
    # Precisamos extrair o JSON do corpo da requisição, que é a atualização do Telegram.
    try:
        req_json = request.get_json(silent=True)
        if not req_json:
            logger.error("No JSON payload received or invalid JSON.")
            return jsonify({"status": "error", "message": "Invalid JSON"}), 400
        
        # Converte o JSON em um objeto Update do python-telegram-bot
        update = Update.de_json(req_json, application.bot)
        
        # Processa a atualização com os handlers que você configurou
        await application.process_update(update)
        
        # Retorna uma resposta de sucesso para o Telegram
        return jsonify({"status": "ok"}), 200

    except Exception as e:
        logger.exception(f"Erro ao processar webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500