import logging
import os
import asyncio
import random
import json  # NOVO: Importa a biblioteca para trabalhar com JSON

from telegram import Update
from telegram.ext import Application, MessageHandler, filters

# --- Configuração de Log ---
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

# ALTERADO: Carrega as respostas de um arquivo JSON externo.
def carregar_respostas():
    """Carrega as respostas do arquivo respostas.json."""
    try:
        # 'encoding="utf-8"' é crucial para ler acentos e caracteres especiais.
        with open('respostas.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Arquivo 'respostas.json' não encontrado! O bot não terá respostas.")
        return {}
    except json.JSONDecodeError:
        logger.error("Erro ao decodificar 'respostas.json'! Verifique a sintaxe do arquivo.")
        return {}

respostas_automatica = carregar_respostas()

# A função 'responder_mensagem' e todo o resto do código permanecem EXATAMENTE IGUAIS.
# Isso mostra a beleza de separar os dados da lógica!
# LÓGICA ATUALIZADA: Entende chaves agrupadas com vírgulas.
async def responder_mensagem(update: Update, context):
    """Lida com as mensagens recebidas, sorteia uma resposta e a envia."""
    if not update.message or not update.message.text:
        return

    mensagem_recebida = update.message.text.lower()
    user_info = f"{update.effective_user.full_name} ({update.effective_user.id})"
    logger.info(f"Mensagem de {user_info}: '{update.message.text}'")

    resposta_encontrada = False
    # A variável 'chaves_agrupadas' agora representa strings como "oi,olá"
    for chaves_agrupadas, lista_de_opcoes in respostas_automatica.items():
        
        # Transforma a string "oi,olá" em uma lista de palavras ['oi', 'olá']
        lista_palavras_chave = chaves_agrupadas.split(',')
        
        # Verifica se ALGUMA das palavras da lista está na mensagem do usuário
        if any(palavra in mensagem_recebida for palavra in lista_palavras_chave):
            
            dados_resposta = random.choice(lista_de_opcoes)
            
            texto_resposta = dados_resposta.get("texto")
            sticker_resposta = dados_resposta.get("sticker")
            gif_resposta = dados_resposta.get("gif")
            foto_resposta = dados_resposta.get("foto")
            audio_resposta = dados_resposta.get("audio")
            voz_resposta = dados_resposta.get("voz")

            try:
                if sticker_resposta: await update.message.reply_sticker(sticker=sticker_resposta)
                elif gif_resposta: await update.message.reply_animation(animation=gif_resposta, caption=texto_resposta)
                elif foto_resposta: await update.message.reply_photo(photo=foto_resposta, caption=texto_resposta)
                elif audio_resposta: await update.message.reply_audio(audio=audio_resposta, caption=texto_resposta)
                elif voz_resposta: await update.message.reply_voice(voice=voz_resposta, caption=texto_resposta)
                elif texto_resposta: await update.message.reply_text(texto_resposta)
            except Exception as e:
                logger.error(f"Falha ao enviar resposta para '{chaves_agrupadas}': {e}", exc_info=True)

            resposta_encontrada = True
            break

    if not resposta_encontrada:
        # A mensagem padrão continua a mesma, pois o bot não precisa expor suas palavras-chave.
        #await update.message.reply_text("Desculpe, não entendi o que você quis dizer.")
        pass #pula caso não encontrar resposta


# --- O restante do arquivo permanece O MESMO ---

application = Application.builder().token(TOKEN).build()
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_mensagem))

def telegram_webhook_entrypoint(request):
    asyncio.run(main_async(request))
    return 'OK', 200

async def main_async(request):
    try:
        await application.initialize()
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, application.bot)
        await application.process_update(update)
    except Exception as e:
        logger.error(f"Erro no processamento assíncrono: {e}", exc_info=True)
    finally:
        await application.shutdown()