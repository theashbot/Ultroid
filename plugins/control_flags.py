# plugins/control_flags.py

from Ultroid import Ultroid, CMD_HELP
from telethon import events
import asyncio

# --- SUAS CONFIGURAÇÕES (para este plugin) ---
# Copie esses IDs do seu userbot.py original
DONO_ID = 9312770
GRUPO_LOGS = -4979172772

# Flags globais de controle (ativas por padrão ao iniciar o Ultroid)
# Idealmente, estas seriam configuradas via variáveis de ambiente do Ultroid (ex: Config.ATUALIZAR_AUTO = True)
# Mas para adaptar o seu código, vamos mantê-las aqui por enquanto.
ATIVO = True
AUTO_WL = True
AUTO_TROCA = True

async def log_ultroid_action(command, user_name, chat_name, client_obj):
    """Registra o uso de comandos no grupo de logs."""
    log_message = f"[LOG] {command} usado por {user_name} no chat '{chat_name}'"
    print(log_message) # Para ver no terminal do Sevalla/Ultroid
    if GRUPO_LOGS:
        try:
            await client_obj.send_message(GRUPO_LOGS, log_message)
        except Exception as e:
            print(f"Erro ao enviar log para o grupo: {e}")

@Ultroid.on_cmd(
    "bot",
    usage="!bot <on|off> - Ativa/desativa funcionalidades automáticas.",
    allow_sudo=True # Permite que o comando seja usado por Sudo Users do Ultroid
)
async def toggle_bot_ultroid(event):
    global ATIVO
    
    if event.sender_id != DONO_ID:
        # Ultroid Sudo users already checked by allow_sudo. This is a redundant check if you use allow_sudo,
        # but kept to strictly match your original bot's permission logic.
        return await event.edit("🚫 Acesso negado. Apenas o dono pode usar este comando.")

    command_arg = event.pattern_match.group(1).lower()
    
    if command_arg == "on":
        ATIVO = True
        response = "Bot principal **ativado**."
    elif command_arg == "off":
        ATIVO = False
        response = "Bot principal **desativado**."
    else:
        return await event.edit("Uso inválido. Use `.bot on` ou `.bot off`.") # Ultroid uses '.' as prefix by default

    await event.edit(response) # Ultroid geralmente edita a mensagem do comando com a resposta
    
    sender_user = await event.get_sender()
    chat_obj = await event.get_chat()
    chat_title = getattr(chat_obj, 'title', 'Privado')
    
    await log_ultroid_action(f".bot {command_arg}", sender_user.first_name, chat_title, event.client)

@Ultroid.on_cmd(
    "troca",
    usage="!troca <on|off> - Ativa/desativa confirmação automática de trocas.",
    allow_sudo=True
)
async def toggle_troca_ultroid(event):
    global AUTO_TROCA
    if event.sender_id != DONO_ID:
        return await event.edit("🚫 Acesso negado. Apenas o dono pode usar este comando.")

    command_arg = event.pattern_match.group(1).lower()
    
    if command_arg == "on":
        AUTO_TROCA = True
        response = "Troca automática **ativada**."
    elif command_arg == "off":
        AUTO_TROCA = False
        response = "Troca automática **desativada**."
    else:
        return await event.edit("Uso inválido. Use `.troca on` ou `.troca off`.")

    await event.edit(response)
    sender_user = await event.get_sender()
    chat_obj = await event.get_chat()
    chat_title = getattr(chat_obj, 'title', 'Privado')
    await log_ultroid_action(f".troca {command_arg}", sender_user.first_name, chat_title, event.client)

@Ultroid.on_cmd(
    "wlauto",
    usage="!wlauto <on|off> - Ativa/desativa resposta automática de wishlist.",
    allow_sudo=True
)
async def toggle_wlauto_ultroid(event):
    global AUTO_WL
    if event.sender_id != DONO_ID:
        return await event.edit("🚫 Acesso negado. Apenas o dono pode usar este comando.")

    command_arg = event.pattern_match.group(1).lower()
    
    if command_arg == "on":
        AUTO_WL = True
        response = "Resposta automática de wishlist **ativada**."
    elif command_arg == "off":
        AUTO_WL = False
        response = "Resposta automática de wishlist **desativada**."
    else:
        return await event.edit("Uso inválido. Use `.wlauto on` ou `.wlauto off`.")

    await event.edit(response)
    sender_user = await event.get_sender()
    chat_obj = await event.get_chat()
    chat_title = getattr(chat_obj, 'title', 'Privado')
    await log_ultroid_action(f".wlauto {command_arg}", sender_user.first_name, chat_title, event.client)


# Handler geral de mensagens (Auto WL e Auto Troca) - Este será um Listener de eventos
# Ultroid tem um sistema para eventos que não são comandos, mas são mensagens.
# Isso se assemelha ao seu `@bot.on(events.NewMessage(incoming=True))`
# A lógica de permissão GRUPOS_AUTORIZADOS deve ser adaptada aqui.
# Ultroid tem um config.ALLOW_CHATS ou similar. Por simplicidade, vou usar a sua lista.
GRUPOS_AUTORIZADOS = [ # Copie sua lista de grupos_autorizados
    -4697979383, -1002203987354, -1002466128307, -1002287872172,
    -1002378474759, -1002436424424, -1002242021038, -1002260423742,
    -1002333343993, -1002430200771
]

@Ultroid.on_message(
    incoming=True,
    # Você pode querer adicionar um filtro para apenas chats permitidos aqui,
    # mas a lógica interna já faz a checagem.
    # Ex: from_users=False, func=lambda e: e.is_group # Filtra apenas grupos
)
async def handle_messages_ultroid(event):
    if not ATIVO or event.is_private:
        return

    # No Ultroid, o cliente atual é event.client
    eu = await event.client.get_me()
    meu_username = eu.username.lower() if eu.username else ""

    # Lógica de Auto WL
    if event.is_reply:
        msg_respondida = await event.get_reply_message()
        # No Ultroid, event.client.id é o ID do userbot
        if msg_respondida and msg_respondida.sender_id == eu.id and event.sender_id != eu.id:
            if re.fullmatch(r'[\/\.\!]wl', event.raw_text.strip().lower()):
                if AUTO_WL and event.chat_id in GRUPOS_AUTORIZADOS:
                    await asyncio.sleep(2)
                    await event.reply("/wl")

    sender = await event.get_sender()
    if sender and hasattr(sender, 'bot') and sender.bot:
        texto = event.raw_text.lower()
        # Lógica de Auto Troca
        if (
            "fez uma proposta de troca" in texto or
            "deseja trocar" in texto or
            "está fazendo uma troca mágica com" in texto
        ):
            if meu_username not in texto:
                return
            if not AUTO_TROCA:
                return
            await asyncio.sleep(1)
            try:
                buttons = await event.get_buttons()
                for row in buttons:
                    for button in row:
                        if 'confirmar' in button.text.lower() or '✅' in button.text:
                            await button.click()
                            chat_obj = await event.get_chat()
                            chat_title = getattr(chat_obj, 'title', 'Chat')
                            sender_name = sender.first_name if sender else "Alguém"
                            # Usar o log do Ultroid ou enviar para o GRUPO_LOGS
                            if GRUPO_LOGS:
                                await event.client.send_message(GRUPO_LOGS, f"[LOG] Troca confirmada automaticamente no grupo '{chat_title}' por {sender_name}.")
                            return
            except Exception as e:
                if GRUPO_LOGS:
                    await event.client.send_message(GRUPO_LOGS, f"[ERRO] Falha ao tentar confirmar troca: {str(e)}")

# Adiciona o plugin ao CMD_HELP
CMD_HELP.update(
    {
        "control_flags": {
            "commands": (
                "bot",
                "troca",
                "wlauto"
            ),
            "info": "Gerencia as funcionalidades automáticas do bot."
        }
    }
)
