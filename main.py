import logging
import os
import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters

# --- Configuração de Log ---
# Essencial para depuração no Cloud Functions
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Variáveis de Ambiente ---
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("A variável de ambiente 'TELEGRAM_BOT_TOKEN' não está configurada.")
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set.")

# --- Lógica do Bot ---
# Dicionário de respostas baseado em palavras-chave
respostas_automatica = {
    "olá": "Olá! Como posso ajudar?",
    "oi": "Oi! No que posso ser útil?",
    "ajuda": "Estou aqui para ajudar! Qual sua dúvida?",
    "preço": "Para informações sobre preços, por favor, visite nosso site.",
    "contato": "Você pode nos contatar pelo email ou telefone que estão em nosso perfil.",
}

async def responder_mensagem(update: Update, context):
    """Lida com as mensagens recebidas e envia uma resposta."""
    if not update.message or not update.message.text:
        logger.warning("Update recebido sem uma mensagem de texto.")
        return

    mensagem_recebida = update.message.text.lower()
    chat_type = update.message.chat.type
    user_info = f"{update.effective_user.full_name} ({update.effective_user.id})"

    logger.info(f"Mensagem recebida em '{chat_type}' de {user_info}: '{update.message.text}'")

    resposta_encontrada = False
    for palavra_chave, resposta_fixa in respostas_automatica.items():
        if palavra_chave in mensagem_recebida:
            await update.message.reply_text(resposta_fixa)
            resposta_encontrada = True
            logger.info(f"Resposta enviada para {user_info} com base na palavra-chave '{palavra_chave}'.")
            break

    if not resposta_encontrada:
        await update.message.reply_text("Desculpe, não entendi. Tente de outra forma ou use uma das palavras-chave: 'olá', 'ajuda', 'preço', 'contato'.")
        logger.info(f"Nenhuma palavra-chave encontrada. Enviada resposta padrão para {user_info}.")


# --- Inicialização da Aplicação PTB ---
# É importante instanciar a aplicação fora do handler para reutilização
# entre invocações da Cloud Function (otimização de "cold start").
application = Application.builder().token(TOKEN).build()
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_mensagem))


# --- Entry Point para o Google Cloud Functions ---
def telegram_webhook_entrypoint(request):
    """
    Entrypoint HTTP síncrono que o GCF irá chamar.
    Esta função faz a "ponte" para o código assíncrono.
    """
    logger.info("Entrypoint da função foi acionado.")
    
    # MUDANÇA CRÍTICA 1: Usar asyncio.run() para executar a função async
    # de dentro do nosso entrypoint síncrono.
    asyncio.run(main_async(request))
    
    # MUDANÇA CRÍTICA 2: Retornar uma resposta HTTP 200 OK para o Telegram.
    # Isso confirma o recebimento do webhook. Se não fizermos isso, o Telegram
    # continuará reenviando a mesma atualização, causando execuções repetidas.
    return 'OK', 200

async def main_async(request):
    """Função assíncrona que processa a requisição do webhook."""
    try:
        # Pega o corpo da requisição JSON
        json_data = request.get_json(force=True)
        logger.info(f"Request JSON data: {json_data}")
        
        # Cria um objeto Update a partir do JSON recebido
        update = Update.de_json(json_data, application.bot)
        
        # Processa o update. Isso irá disparar o 'responder_mensagem' se o filtro corresponder.
        await application.process_update(update)
        
    except Exception as e:
        logger.error(f"Erro ao processar a requisição: {e}")