import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Habilita o log
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

TOKEN = '7657219327:AAH5UUcmwvUbeep1Da8DHdFiXerCH8Qq1ng'

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
    "pergunta": "Resposta",
    # Adicione mais pares de perguntas e respostas
}

async def responder_mensagem(update: Update, context):
    mensagem_recebida = update.message.text
    chat_id = update.message.chat_id
    chat_type = update.message.chat.type # 'private', 'group', 'supergroup'

    # Log para depuração
    logging.info(f"Mensagem recebida em {chat_type} de {update.effective_user.full_name} ({chat_id}): {mensagem_recebida}")

    # Processa a mensagem apenas se for um grupo ou supergrupo
    if chat_type in ['group', 'supergroup']:
        # Verifica se o bot foi mencionado (se a privacidade estiver ativada ou para ter certeza)
        # update.message.parse_entities() pode ser usado para analisar menções, mas uma verificação simples de string também funciona.
        # Por exemplo: if f"@{context.bot.username.lower()}" in mensagem_recebida.lower():

        # Lógica de resposta baseada em palavras-chave para grupos
        mensagem_para_analisar = mensagem_recebida.lower()
        resposta_encontrada = False

        for palavra_chave, resposta_fixa in respostas_automatica.items():
            if palavra_chave in mensagem_para_analisar:
                await update.message.reply_text(resposta_fixa)
                resposta_encontrada = True
                break
        
        # Resposta padrão se nenhuma palavra-chave for encontrada e o bot foi mencionado
        # Ou se o bot deve sempre responder
        if not resposta_encontrada:
             # Você pode adicionar uma condição aqui, como:
             # if f"@{context.bot.username.lower()}" in mensagem_para_analisar:
             # await update.message.reply_text("Desculpe, não entendi. Por favor, seja mais específico ou mencione-me com uma pergunta direta.")
             pass # Não faz nada se não encontrar palavra-chave e não for uma menção direta

    elif chat_type == 'private':
        # Comportamento do bot em conversas privadas (DM)
        mensagem_para_analisar = mensagem_recebida.lower()
        resposta_encontrada = False

        for palavra_chave, resposta_fixa in respostas_automatica.items():
            if palavra_chave in mensagem_para_analisar:
                await update.message.reply_text(resposta_fixa)
                resposta_encontrada = True
                break
        
        if not resposta_encontrada:
            #await update.message.reply_text("Não entendi a sua mensagem. Tente algo como 'olá' ou 'ajuda'.")
            pass # Não faz nada se não encontrar palavra-chave

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_mensagem))

    logging.info("Bot rodando...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()