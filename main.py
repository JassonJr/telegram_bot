import logging
import os
import asyncio
import random
import json
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

# --- Carregamento das Respostas ---
def carregar_respostas():
    """Carrega as respostas do arquivo respostas.json."""
    try:
        with open('respostas.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Erro ao carregar 'respostas.json': {e}")
        return {}

respostas_completas = carregar_respostas()
respostas_por_palavra_chave = respostas_completas.get("respostas_por_palavra_chave", {})
respostas_por_reply = respostas_completas.get("respostas_por_reply", {})
# NOVO: Carrega a lista de respostas genéricas
resposta_generica_para_reply = respostas_completas.get("resposta_generica_para_reply", [])


# --- Lógica Principal do Bot ---
async def responder_mensagem(update: Update, context):
    """Lida com as mensagens recebidas, com uma lógica de prioridade:
    1. Reply Específico
    2. Reply Genérico
    3. Palavra-Chave
    """
    if not update.message or not update.message.text:
        return

    mensagem_recebida_texto = update.message.text
    user_info = f"{update.effective_user.full_name} ({update.effective_user.id})"

    # --- LÓGICA DE REPLY (ESPECÍFICO E GENÉRICO) ---
    if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
        texto_original_bot = update.message.reply_to_message.text
        logger.info(f"{user_info} respondeu à mensagem: '{texto_original_bot}'")

        # 1. Tenta encontrar uma resposta específica
        for texto_gatilho, lista_de_opcoes in respostas_por_reply.items():
            if texto_gatilho.lower() in texto_original_bot.lower():
                dados_resposta = random.choice(lista_de_opcoes)
                
                texto_resposta = dados_resposta.get("texto")
                if texto_resposta and "{user_input}" in texto_resposta:
                    texto_resposta = texto_resposta.replace("{user_input}", mensagem_recebida_texto)
                
                # Envia a resposta específica e encerra
                try:
                    if dados_resposta.get("sticker"):
                        await update.message.reply_sticker(sticker=dados_resposta["sticker"])
                    elif texto_resposta:
                        await update.message.reply_text(texto_resposta, parse_mode='HTML')
                    
                    logger.info(f"Resposta de REPLY ESPECÍFICO enviada para {user_info}.")
                    return
                except Exception as e:
                    logger.error(f"Falha ao enviar resposta de REPLY ESPECÍFICO: {e}", exc_info=True)
                    return

        # 2. Se não encontrou resposta específica, tenta a genérica
        if resposta_generica_para_reply:
            dados_resposta = random.choice(resposta_generica_para_reply)
            try:
                if dados_resposta.get("sticker"):
                    await update.message.reply_sticker(sticker=dados_resposta["sticker"])
                elif dados_resposta.get("texto"):
                    await update.message.reply_text(dados_resposta["texto"], parse_mode='HTML')

                logger.info(f"Resposta de REPLY GENÉRICO enviada para {user_info}.")
                return
            except Exception as e:
                logger.error(f"Falha ao enviar resposta de REPLY GENÉRICO: {e}", exc_info=True)
                return

    # --- LÓGICA DE PALAVRA-CHAVE (só executa se não for um reply tratado acima) ---
    logger.info(f"Mensagem de {user_info}: '{mensagem_recebida_texto}'")
    mensagem_recebida_lower = mensagem_recebida_texto.lower()
    
    for chaves_agrupadas, lista_de_opcoes in respostas_por_palavra_chave.items():
        lista_palavras_chave = chaves_agrupadas.split(',')
        if any(palavra in mensagem_recebida_lower for palavra in lista_palavras_chave):
            dados_resposta = random.choice(lista_de_opcoes)
            
            texto_resposta = dados_resposta.get("texto")
            sticker_resposta = dados_resposta.get("sticker")
            gif_resposta = dados_resposta.get("gif")
            foto_resposta = dados_resposta.get("foto")
            audio_resposta = dados_resposta.get("audio")
            voz_resposta = dados_resposta.get("voz")

            try:
                if sticker_resposta: await update.message.reply_sticker(sticker=sticker_resposta)
                elif gif_resposta: await update.message.reply_animation(animation=gif_resposta, caption=texto_resposta, parse_mode='HTML')
                elif foto_resposta: await update.message.reply_photo(photo=foto_resposta, caption=texto_resposta, parse_mode='HTML')
                elif audio_resposta: await update.message.reply_audio(audio=audio_resposta, caption=texto_resposta, parse_mode='HTML')
                elif voz_resposta: await update.message.reply_voice(voice=voz_resposta, caption=texto_resposta, parse_mode='HTML')
                elif texto_resposta: await update.message.reply_text(texto_resposta, parse_mode='HTML')
                
                logger.info(f"Resposta de PALAVRA-CHAVE enviada para {user_info}.")
                return
            except Exception as e:
                logger.error(f"Falha ao enviar resposta de PALAVRA-CHAVE: {e}", exc_info=True)
                return
    pass

# --- O restante do arquivo (application, entrypoint, etc.) permanece O MESMO ---

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