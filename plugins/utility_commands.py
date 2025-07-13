# plugins/utility_commands.py

from Ultroid import Ultroid, CMD_HELP
import asyncio
import time

# --- SUAS CONFIGURAÇÕES (para este plugin) ---
DONO_ID = 9312770
GRUPO_LOGS = -4979172772

async def log_ultroid_action(command, user_name, chat_name, client_obj):
    """Registra o uso de comandos no grupo de logs."""
    log_message = f"[LOG] {command} usado por {user_name} no chat '{chat_name}'"
    print(log_message)
    if GRUPO_LOGS:
        try:
            await client_obj.send_message(GRUPO_LOGS, log_message)
        except Exception as e:
            print(f"Erro ao enviar log para o grupo: {e}")

@Ultroid.on_cmd(
    "ping",
    usage="!ping - Mede o tempo de resposta do bot.",
    allow_sudo=True
)
async def ping_ultroid(event):
    if event.sender_id != DONO_ID:
        return await event.edit("🚫 Acesso negado. Apenas o dono pode usar este comando.")
    
    start = time.time()
    # No Ultroid, event.edit() edita a mensagem do comando, servindo como a resposta
    response_msg = await event.edit("Calculando...")
    end = time.time()
    tempo = round((end - start) * 1000)
    await response_msg.edit(f"Pong! Tempo de resposta: {tempo}ms") # Edita a mensagem anterior
    # Ultroid geralmente não precisa de event.delete() para o comando, mas se você quiser apagar, adicione:
    # await event.delete()
    
    sender_user = await event.get_sender()
    chat_obj = await event.get_chat()
    chat_title = getattr(chat_obj, 'title', 'Privado')
    await log_ultroid_action(".ping", sender_user.first_name, chat_title, event.client)

@Ultroid.on_cmd(
    "limpar",
    usage="!limpar <quantidade> - Apaga mensagens do bot no chat.",
    allow_sudo=True
)
async def limpar_ultroid(event):
    if event.sender_id != DONO_ID:
        return await event.edit("🚫 Acesso negado. Apenas o dono pode usar este comando.")
    
    try:
        quantity = int(event.pattern_match.group(1))
    except (ValueError, TypeError):
        return await event.edit("Uso inválido. `.limpar <quantidade>` Ex: `.limpar 5`")
    
    chat_obj = await event.get_chat()
    meu_id = (await event.client.get_me()).id
    
    # Coleta as mensagens para deletar (incluindo o próprio comando do usuário)
    messages_to_delete = []
    messages_to_delete.append(event.id) # Adiciona o comando do usuário
    
    # Itera mensagens para encontrar as do bot
    async for msg in event.client.iter_messages(chat_obj, limit=quantity + 5): # Busca um pouco mais para garantir
        if msg.sender_id == meu_id:
            messages_to_delete.append(msg.id)
            if len(messages_to_delete) >= quantity + 1: # +1 para o próprio comando
                break
    
    # Ultroid tem um método client.delete_messages
    try:
        # Se for um comando editado, event.delete() pode falhar, então use client.delete_messages
        await event.client.delete_messages(chat_obj, messages_to_delete)
        apagadas = len(messages_to_delete)
        response = f"**{apagadas}** mensagens foram apagadas (incluindo o comando)."
    except Exception as e:
        response = f"❌ Erro ao apagar mensagens: {e}"
        if GRUPO_LOGS:
            await event.client.send_message(GRUPO_LOGS, f"[ERRO] Falha no comando .limpar: {e}")

    # Envia uma mensagem de feedback que será auto-apagada
    feedback_msg = await event.client.send_message(chat_obj, response)
    await asyncio.sleep(5)
    await feedback_msg.delete()
    
    sender_user = await event.get_sender()
    chat_title = getattr(chat_obj, 'title', 'Privado')
    await log_ultroid_action(f".limpar {quantity}", sender_user.first_name, chat_title, event.client)

# Adiciona o plugin ao CMD_HELP
CMD_HELP.update(
    {
        "utility_commands": {
            "commands": (
                "ping",
                "limpar"
            ),
            "info": "Comandos de utilidade geral."
        }
    }
)
