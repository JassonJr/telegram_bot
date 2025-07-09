import logging
import os
import asyncio
import random
import json
from datetime import datetime, timedelta # NOVO: Imports para lidar com tempo

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

# --- NOVO: Definição do Cooldown ---
COOLDOWN_SECONDS = 600  # O bot só responderá a uma mensagem a cada 10 segundos no mesmo chat

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
resposta_generica_para_reply = respostas_completas.get("resposta_generica_para_reply", [])


# --- Lógica Principal do Bot ---
async def responder_mensagem(update: Update, context):
    """Lida com as mensagens recebidas, aplicando um cooldown por chat."""
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    user_info = f"{update.effective_user.full_name} ({update.effective_user.id})"
    
    # --- INÍCIO DA NOVA LÓGICA DE COOLDOWN ---
    now = datetime.now()
    last_response_time = context.chat_data.get('last_response_timestamp')

    if last_response_time and (now - last_response_time) < timedelta(seconds=COOLDOWN_SECONDS):
        logger.info(f"Cooldown ativo no chat {chat_id}. Ignorando mensagem de {user_info}.")
        return # Para a execução da função se estiver em cooldown
    # --- FIM DA NOVA LÓGICA DE COOLDOWN ---

    mensagem_recebida_texto = update.message.text
    
    # --- LÓGICA DE REPLY ---
    if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
        texto_original_bot = update.message.reply_to_message.text
        logger.info(f"{user_info} respondeu à mensagem: '{texto_original_bot}'")

        # 1. Tenta encontrar uma resposta específica
        for texto_gatilho, lista_de_opcoes in respostas_por_reply.items():
            if texto_gatilho.lower() in texto_original_bot.lower():
                # ... (lógica para escolher e processar a resposta específica)
                dados_resposta = random.choice(lista_de_opcoes)
                texto_resposta = dados_resposta.get("texto")
                if texto_resposta and "{user_input}" in texto_resposta:
                    texto_resposta = texto_resposta.replace("{user_input}", mensagem_recebida_texto)
                
                try:
                    if dados_resposta.get("sticker"):
                        await update.message.reply_sticker(sticker=dados_resposta["sticker"])
                    elif texto_resposta:
                        await update.message.reply_text(texto_resposta, parse_mode='HTML')
                    
                    context.chat_data['last_response_timestamp'] = now # ATUALIZA O HORÁRIO
                    logger.info(f"Resposta de REPLY ESPECÍFICO enviada. Cooldown atualizado para o chat {chat_id}.")
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

                context.chat_data['last_response_timestamp'] = now # ATUALIZA O HORÁRIO
                logger.info(f"Resposta de REPLY GENÉRICO enviada. Cooldown atualizado para o chat {chat_id}.")
                return
            except Exception as e:
                logger.error(f"Falha ao enviar resposta de REPLY GENÉRICO: {e}", exc_info=True)
                return

    # --- LÓGICA DE PALAVRA-CHAVE COM MEMÓRIA ---
    # ... (toda a sua lógica de palavra-chave continua aqui, sem alterações, mas com uma adição)
    logger.info(f"Mensagem de {user_info}: '{mensagem_recebida_texto}'")
    mensagem_recebida_lower = mensagem_recebida_texto.lower()
    
    for chaves_agrupadas, lista_de_opcoes in respostas_por_palavra_chave.items():
        lista_palavras_chave = chaves_agrupadas.split(',')
        if any(palavra in mensagem_recebida_lower for palavra in lista_palavras_chave):
            # ... (lógica anti-repetição)
            chat_data = context.chat_data
            recent_responses = chat_data.setdefault('recent_responses', {})
            last_used_indices = recent_responses.get(chaves_agrupadas, [])
            opcoes_disponiveis = [
                opcao for i, opcao in enumerate(lista_de_opcoes) if i not in last_used_indices
            ]
            if not opcoes_disponiveis:
                last_used_indices = []
                opcoes_disponiveis = lista_de_opcoes
            dados_resposta = random.choice(opcoes_disponiveis)
            indice_escolhido = lista_de_opcoes.index(dados_resposta)
            last_used_indices.append(indice_escolhido)
            num_total_opcoes = len(lista_de_opcoes)
            max_memoria = max(0, num_total_opcoes - 1)
            recent_responses[chaves_agrupadas] = last_used_indices[-max_memoria:]
            
            try:
                # ... (bloco de 'if/elif' para enviar a mídia)
                texto_resposta = dados_resposta.get("texto")
                sticker_resposta = dados_resposta.get("sticker")
                gif_resposta = dados_resposta.get("gif")
                foto_resposta = dados_resposta.get("foto")
                audio_resposta = dados_resposta.get("audio")
                voz_resposta = dados_resposta.get("voz")

                if sticker_resposta: await update.message.reply_sticker(sticker=sticker_resposta)
                elif gif_resposta: await update.message.reply_animation(animation=gif_resposta, caption=texto_resposta, parse_mode='HTML')
                elif foto_resposta: await update.message.reply_photo(photo=foto_resposta, caption=texto_resposta, parse_mode='HTML')
                elif audio_resposta: await update.message.reply_audio(audio=audio_resposta, caption=texto_resposta, parse_mode='HTML')
                elif voz_resposta: await update.message.reply_voice(voice=voz_resposta, caption=texto_resposta, parse_mode='HTML')
                elif texto_resposta: await update.message.reply_text(texto_resposta, parse_mode='HTML')
                
                context.chat_data['last_response_timestamp'] = now # ATUALIZA O HORÁRIO
                logger.info(f"Resposta de PALAVRA-CHAVE enviada. Cooldown atualizado para o chat {chat_id}.")
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