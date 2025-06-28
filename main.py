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
# LÓGICA ATUALIZADA: Adiciona memória de curto prazo para evitar repetições
async def responder_mensagem(update: Update, context):
    """
    Lida com as mensagens recebidas, com lógica anti-repetição.
    A prioridade é: Reply Específico > Reply Genérico > Palavra-Chave com Memória.
    """
    if not update.message or not update.message.text:
        return

    mensagem_recebida_texto = update.message.text
    user_info = f"{update.effective_user.full_name} ({update.effective_user.id})"
    
    # --- LÓGICA DE REPLY (permanece a mesma) ---
    if update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id:
        # ... (toda a sua lógica de reply específico e genérico continua aqui, sem alterações)
        # Por uma questão de completude, estou colando ela aqui novamente.
        texto_original_bot = update.message.reply_to_message.text
        logger.info(f"{user_info} respondeu à mensagem: '{texto_original_bot}'")

        # 1. Tenta encontrar uma resposta específica
        for texto_gatilho, lista_de_opcoes in respostas_por_reply.items():
            if texto_gatilho.lower() in texto_original_bot.lower():
                dados_resposta = random.choice(lista_de_opcoes)
                
                texto_resposta = dados_resposta.get("texto")
                if texto_resposta and "{user_input}" in texto_resposta:
                    texto_resposta = texto_resposta.replace("{user_input}", mensagem_recebida_texto)
                
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

    # --- LÓGICA DE PALAVRA-CHAVE COM MEMÓRIA ---
    logger.info(f"Mensagem de {user_info}: '{mensagem_recebida_texto}'")
    mensagem_recebida_lower = mensagem_recebida_texto.lower()
    
    for chaves_agrupadas, lista_de_opcoes in respostas_por_palavra_chave.items():
        lista_palavras_chave = chaves_agrupadas.split(',')
        if any(palavra in mensagem_recebida_lower for palavra in lista_palavras_chave):
            
            # --- INÍCIO DA NOVA LÓGICA ANTI-REPETIÇÃO ---

            # Garante que o dicionário de memória exista para este chat
            chat_data = context.chat_data
            recent_responses = chat_data.setdefault('recent_responses', {})
            
            # Pega os índices das últimas respostas usadas para esta palavra-chave
            last_used_indices = recent_responses.get(chaves_agrupadas, [])
            
            # Cria uma lista de opções disponíveis (cujo índice não está na memória recente)
            opcoes_disponiveis = [
                opcao for i, opcao in enumerate(lista_de_opcoes) if i not in last_used_indices
            ]
            
            # Se todas as opções já foram usadas recentemente, reseta a memória e usa a lista completa
            if not opcoes_disponiveis:
                logger.info(f"Resetando memória para '{chaves_agrupadas}' no chat {update.effective_chat.id}")
                last_used_indices = []
                opcoes_disponiveis = lista_de_opcoes

            # Escolhe aleatoriamente de uma das opções disponíveis ("frescas")
            dados_resposta = random.choice(opcoes_disponiveis)
            
            # Encontra o índice original da resposta escolhida para guardar na memória
            indice_escolhido = lista_de_opcoes.index(dados_resposta)
            last_used_indices.append(indice_escolhido)
            
            # Limita o tamanho da memória. Vamos guardar até N-1 respostas, onde N é o total de opções.
            # Isso garante que sempre haverá pelo menos uma opção "fresca".
            num_total_opcoes = len(lista_de_opcoes)
            max_memoria = max(0, num_total_opcoes - 1)
            recent_responses[chaves_agrupadas] = last_used_indices[-max_memoria:]
            
            # --- FIM DA NOVA LÓGICA ANTI-REPETIÇÃO ---
            
            # A lógica de envio de mensagem permanece a mesma
            texto_resposta = dados_resposta.get("texto")
            sticker_resposta = dados_resposta.get("sticker")
            # ... (e as outras mídias: gif, foto, audio, voz) ...
            
            try:
                # ... (seu bloco 'try/except' com os 'if/elif' para enviar a mídia continua aqui, sem alterações)
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
                
                logger.info(f"Resposta de PALAVRA-CHAVE (com memória) enviada para {user_info}.")
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