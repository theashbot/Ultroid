# plugins/mirar_auto_plugin.py

from Ultroid import Ultroid, CMD_HELP
import asyncio
import re
import unicodedata # Para normalização de texto

# --- SUAS CONFIGURAÇÕES (para este plugin) ---
DONO_ID = 9312770
GRUPO_LOGS = -4979172772 # Copie seu ID de logs

TRICKLAND_BOT_ID = 7312089948
CHAT_ID_TRICKLAND = 7312089948 # ID do chat privado com o bot Trickland

PRIORITY_CATEGORY = "🍿 CINELAND" # Categoria prioritária EXATA com o novo emoji
# Subcategorias prioritárias. A ordem define a prioridade de escolha.
PRIORITY_SUBCATEGORIES = [
    "House of The Dragon",
    "Denied Love",
    "MCU",
    "Lost",
    "Fallout",
    "The Last of Us: Série",
    "Pluto",
    "23.5",
    "Mr. Robot"
]
NUM_TO_EMOJI_MAP = {
    '1': '1️⃣', '2': '2️⃣', '3': '3️⃣', '4': '4️⃣', '5': '5️⃣',
    '6': '6️⃣', '7': '7️⃣', '8': '8️⃣', '9': '9️⃣', '10': '🔟'
}
RESTART_BUTTON_EMOJI = "🔄" # Emoji exato do botão de reiniciar

INTERVALO_MIRAR = 30 # Intervalo em segundos entre cada ciclo completo de mira (ajuste conforme o jogo)

# --- Variáveis de Controle de Estado do Plugin ---
MIRAR_AUTO_ENABLED = False
MIRAR_AUTO_TASK_HANDLE = None

async def log_ultroid_action_mirar(message, client_obj, is_error=False):
    """Registra logs específicos da automação do mirar."""
    prefix = "[MIRAR_AUTO_PLUGIN]"
    log_type = "ERRO" if is_error else "INFO"
    full_message = f"{prefix} [{log_type}] {message}"
    
    print(full_message) # Sempre printa no console do Ultroid
    if GRUPO_LOGS:
        try:
            await client_obj.send_message(GRUPO_LOGS, full_message)
        except Exception as e:
            print(f"Erro ao enviar log para o grupo de logs: {e}")

# --- FUNÇÃO DE NORMALIZAÇÃO DE STRING ---
def normalize_text(text):
    """Normaliza texto para comparação, limpando espaços, convertendo para minúsculas e normalizando Unicode."""
    cleaned_text = text.replace('\u200b', '').replace('\u00a0', ' ').strip().lower()
    normalized_text = unicodedata.normalize('NFC', cleaned_text)
    # Debug print: Remover esta linha após confirmar que está funcionando
    # print(f"[MIRAR_AUTO_PLUGIN] DEBUG: Normalized text '{text}' -> '{normalized_text}' (Codepoints: {[hex(ord(c)) for c in normalized_text]})")
    return normalized_text

async def mirar_automation_loop(client_obj):
    """
    Loop principal da automação do /mirar.
    """
    global MIRAR_AUTO_ENABLED # Acessa a flag global do plugin

    await log_ultroid_action_mirar("Tarefa de automação do /mirar iniciada.", client_obj)

    while MIRAR_AUTO_ENABLED:
        try:
            await log_ultroid_action_mirar(f"Enviando /mirar para o chat {CHAT_ID_TRICKLAND}...", client_obj)
            # Envia o comando /mirar e obtém a referência da mensagem enviada
            sent_mirar_command_message = await client_obj.send_message(CHAT_ID_TRICKLAND, '/mirar')
            
            current_game_message = None # Para armazenar a mensagem que Trickland bot edita
            
            # --- Etapa 1: Esperar e selecionar Categoria ---
            category_selected = False
            for _ in range(5): 
                await asyncio.sleep(2) 
                messages = await client_obj.get_messages(CHAT_ID_TRICKLAND, limit=2) 
                for message in messages:
                    if message.sender_id == TRICKLAND_BOT_ID and \
                       "Aponte, mire e acerte uma opção:" in message.raw_text and \
                       message.buttons and \
                       message.reply_to_msg_id == sent_mirar_command_message.id:
                        
                        current_game_message = message
                        await log_ultroid_action_mirar(f"Mensagem de seleção de categoria recebida (ID: {current_game_message.id}).", client_obj)
                        
                        found_button_in_message = False
                        for row in current_game_message.buttons: 
                            for button in row: 
                                if normalize_text(PRIORITY_CATEGORY) in normalize_text(button.text): # Normaliza para comparação
                                    await log_ultroid_action_mirar(f"Clicando na categoria: {button.text}", client_obj)
                                    try:
                                        await button.click()
                                        category_selected = True
                                        found_button_in_message = True
                                        break
                                    except Exception as e:
                                        await log_ultroid_action_mirar(f"Erro ao clicar no botão de categoria '{button.text}': {e}", client_obj, is_error=True)
                            if found_button_in_message:
                                break
                        if category_selected:
                            break 
                if category_selected:
                    break 
            
            if not category_selected:
                await log_ultroid_action_mirar(f"ATENÇÃO: Categoria '{PRIORITY_CATEGORY}' não encontrada ou bot não respondeu a tempo para a seleção de categoria.", client_obj, is_error=True)
                await asyncio.sleep(INTERVALO_MIRAR) 
                continue 

            # --- Etapa 2: Esperar pela EDIÇÃO da mensagem com Subcategoria (ou Reiniciar) ---
            subcategory_chosen = False
            for _ in range(5): 
                await asyncio.sleep(3) 
                
                if current_game_message: 
                    try:
                        # Recarrega a versão mais recente da mensagem pelo seu ID
                        edited_message = await client_obj.get_messages(CHAT_ID_TRICKLAND, ids=current_game_message.id)
                        
                        if edited_message and \
                           edited_message.sender_id == TRICKLAND_BOT_ID and \
                           "Escolha uma subcategoria:" in edited_message.raw_text and \
                           edited_message.buttons: 
                            
                            await log_ultroid_action_mirar(f"Mensagem de subcategoria EDITADA encontrada (ID: {edited_message.id}).", client_obj)
                            
                            # --- INÍCIO DA DEPURACAO (Remover após confirmar que está funcionando) ---
                            # print(f"[MIRAR_AUTO_PLUGIN] DEBUG: Texto BRUTO da mensagem de subcategoria (PROCESSANDO EDIÇÃO): {repr(edited_message.raw_text)}")
                            # series_listings = re.findall(r'(\d+)\s*-\s*(.+)', edited_message.raw_text)
                            # print(f"[MIRAR_AUTO_PLUGIN] DEBUG: series_listings (repr): {repr(series_listings)}") 
                            # series_to_num_map = {normalize_text(name): num.strip() for num, name in series_listings}
                            # print(f"[MIRAR_AUTO_PLUGIN] DEBUG: series_to_num_map (repr): {repr(series_to_num_map)}")
                            # print(f"[MIRAR_AUTO_PLUGIN] DEBUG: Mapeamento NUM_TO_EMOJI_MAP: {repr(NUM_TO_EMOJI_MAP)}")
                            # actual_buttons_found = []
                            # for r in edited_message.buttons:
                            #     for b in r:
                            #         actual_buttons_found.append(repr(b.text))
                            # print(f"[MIRAR_AUTO_PLUGIN] DEBUG: Textos de botões ATUAIS (repr): {actual_buttons_found}")
                            # --- FIM DA DEPURACAO ---

                            # Para evitar que o re.findall falhe se não houver subcategorias listadas corretamente
                            series_listings = re.findall(r'(\d+)\s*-\s*(.+)', edited_message.raw_text)
                            if not series_listings:
                                await log_ultroid_action_mirar("ERRO: Nenhuma subcategoria encontrada no texto da mensagem editada.", client_obj, is_error=True)
                                break # Sai do loop de tentativas de edição

                            series_to_num_map = {
                                normalize_text(name): num.strip() 
                                for num, name in series_listings
                            }
                            
                            chosen_button_object = None 
                            
                            for priority_series in PRIORITY_SUBCATEGORIES:
                                lookup_key = normalize_text(priority_series)
                                # print(f"[MIRAR_AUTO_PLUGIN] DEBUG: Tentando encontrar prioridade: '{priority_series}' (lookup_key: {repr(lookup_key)}) (Codepoints: {[hex(ord(c)) for c in lookup_key]})")
                                
                                found_in_map_explicitly = False
                                actual_matched_map_key = None
                                
                                # --- BUSCA EXPLÍCITA NO MAPA ---
                                for map_key_candidate in series_to_num_map.keys():
                                    # print(f"  [MIRAR_AUTO_PLUGIN] DEBUG: Comparando {repr(lookup_key)} com chave do mapa {repr(map_key_candidate)} (Codepoints: {[hex(ord(c)) for c in map_key_candidate]})")
                                    if lookup_key == map_key_candidate:
                                        found_in_map_explicitly = True
                                        actual_matched_map_key = map_key_candidate
                                        # print(f"  [MIRAR_AUTO_PLUGIN] DEBUG: CORRESPONDÊNCIA ENCONTRADA EXPLICITAMENTE: {repr(lookup_key)} == {repr(map_key_candidate)}")
                                        break 
                                
                                if found_in_map_explicitly: 
                                    num_str_for_priority = series_to_num_map[actual_matched_map_key]
                                    emoji_button_text = NUM_TO_EMOJI_MAP.get(num_str_for_priority)
                                    
                                    await log_ultroid_action_mirar(f"Prioridade encontrada: '{priority_series}' (Número: '{num_str_for_priority}', Emoji esperado: '{emoji_button_text}')", client_obj)
                                    if emoji_button_text: 
                                        for row in edited_message.buttons:
                                            for button in row:
                                                if button.text == emoji_button_text: 
                                                    chosen_button_object = button
                                                    await log_ultroid_action_mirar(f"Botão de prioridade ENCONTRADO: {repr(button.text)}", client_obj)
                                                    break
                                            if chosen_button_object:
                                                break
                                    if chosen_button_object:
                                        break # Sai do loop de prioridades
                                    else:
                                        await log_ultroid_action_mirar(f"Emoji esperado '{emoji_button_text}' para prioridade '{priority_series}' NÃO encontrado entre os botões reais.", client_obj, is_error=True)
                                else:
                                    # print(f"[MIRAR_AUTO_PLUGIN] DEBUG: Chave '{lookup_key}' NÃO encontrada em series_to_num_map (após busca explícita).")
                                    pass # Continue to next priority if not found

                            if chosen_button_object:
                                try:
                                    await chosen_button_object.click()
                                    await log_ultroid_action_mirar(f"Subcategoria clicada com sucesso: {chosen_button_object.text}", client_obj)
                                    subcategory_chosen = True
                                    break 
                                except Exception as e:
                                    await log_ultroid_action_mirar(f"Erro ao clicar na subcategoria: {e}", client_obj, is_error=True)
                                break 
                            else:
                                await log_ultroid_action_mirar(f"Nenhuma subcategoria prioritária encontrada na lista da mensagem. Procurando botão de reinício '{RESTART_BUTTON_EMOJI}'.", client_obj)
                                
                                found_restart_button_object = None
                                for row in edited_message.buttons: 
                                    for button in row:
                                        if RESTART_BUTTON_EMOJI in button.text: 
                                            found_restart_button_object = button
                                            await log_ultroid_action_mirar(f"Clicando no botão de reinício: {button.text}", client_obj)
                                            break
                                    if found_restart_button_object:
                                        break
                                
                                if found_restart_button_object:
                                    try:
                                        await found_restart_button_object.click() 
                                        await log_ultroid_action_mirar(f"Botão de reinício clicado com sucesso: {found_restart_button_object.text}", client_obj)
                                        subcategory_chosen = True
                                        break
                                    except Exception as e:
                                        await log_ultroid_action_mirar(f"Erro ao clicar no botão de reinício '{found_restart_button_object.text}': {e}", client_obj, is_error=True)
                                else: 
                                    await log_ultroid_action_mirar(f"Botão de reinício '{RESTART_BUTTON_EMOJI}' não encontrado na mensagem.", client_obj, is_error=True)
                                
                                break 
                        
                        else: # A mensagem não é a esperada de subcategoria editada
                            await log_ultroid_action_mirar(f"DEBUG: Mensagem {edited_message.id} não é a esperada de subcategoria após edição. Texto: {repr(edited_message.raw_text)}", client_obj)
                            pass 
                    except Exception as e:
                        await log_ultroid_action_mirar(f"ERRO ao recarregar ou processar mensagem editada (ID: {current_game_message.id}): {e}", client_obj, is_error=True)
                        
                else: # current_game_message é None (significa que falhou na Etapa 1)
                    await log_ultroid_action_mirar(f"DEBUG: current_game_message é None, não pode buscar edição. Pode ter falhado na etapa anterior.", client_obj)
                    break 

            if not subcategory_chosen:
                await log_ultroid_action_mirar(f"ATENÇÃO: Falha em escolher subcategoria ou reiniciar APÓS EDIÇÃO. Bot não respondeu a tempo.", client_obj, is_error=True)

        except asyncio.CancelledError:
            await log_ultroid_action_mirar("Tarefa de automação do /mirar cancelada.", client_obj)
            break 
        except Exception as e:
            await log_ultroid_action_mirar(f"ERRO na tarefa de automação do /mirar: {e}", client_obj, is_error=True)

        if MIRAR_AUTO_ENABLED: # Só espera se ainda estiver ativado
            await log_ultroid_action_mirar(f"Aguardando {INTERVALO_MIRAR} segundos para a próxima execução...", client_obj)
            await asyncio.sleep(INTERVALO_MIRAR)
    
    await log_ultroid_action_mirar("Tarefa de automação do /mirar finalizada.", client_obj)


@Ultroid.on_cmd(
    "mirarauto",
    usage="!mirarauto <on|off> - Ativa/desativa a automação do comando /mirar.",
    allow_sudo=True
)
async def toggle_mirar_auto_ultroid(event):
    global MIRAR_AUTO_ENABLED, MIRAR_AUTO_TASK_HANDLE
    
    if event.sender_id != DONO_ID:
        return await event.edit("🚫 Acesso negado. Apenas o dono pode usar este comando.")
    
    command_arg = event.pattern_match.group(1).lower()
    
    if command_arg == "on":
        if not MIRAR_AUTO_ENABLED:
            MIRAR_AUTO_ENABLED = True
            # Inicia a tarefa de automação, passando o objeto cliente do Ultroid
            MIRAR_AUTO_TASK_HANDLE = asyncio.create_task(mirar_automation_loop(event.client))
            response_msg = "Automação do `/mirar` **ativada**."
            await log_ultroid_action_mirar("Automação do /mirar ATIVADA via comando.", event.client)
        else:
            response_msg = "Automação do `/mirar` já está ativa."
    else: # command_arg == "off"
        if MIRAR_AUTO_ENABLED:
            MIRAR_AUTO_ENABLED = False
            if MIRAR_AUTO_TASK_HANDLE and not MIRAR_AUTO_TASK_HANDLE.done():
                MIRAR_AUTO_TASK_HANDLE.cancel() # Tenta cancelar a tarefa
                try:
                    await MIRAR_AUTO_TASK_HANDLE # Aguarda o cancelamento (ou erro)
                except asyncio.CancelledError:
                    pass # É esperado que um CancelledError ocorra
            MIRAR_AUTO_TASK_HANDLE = None # Limpa a referência da tarefa
            response_msg = "Automação do `/mirar` **desativada**."
            await log_ultroid_action_mirar("Automação do /mirar DESATIVADA via comando.", event.client)
        else:
            response_msg = "Automação do `/mirar` já está desativada."
            
    await event.edit(response_msg) # Edita a mensagem do comando com a resposta

# Adiciona o plugin ao CMD_HELP
CMD_HELP.update(
    {
        "mirar_auto": {
            "commands": ("mirarauto",),
            "info": "Ativa/desativa a automação do comando /mirar no Trickland."
        }
    }
)
