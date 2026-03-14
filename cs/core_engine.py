import pymem
import pymem.process
import requests
import time

# --- АВТО-ОФФСЕТЫ ---
OFFSETS = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json").json()
CLIENT_DLL = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json").json()

# Адреса
dwEntityList = OFFSETS['client_dll']['dwEntityList']
dwLocalPlayerPawn = OFFSETS['client_dll']['dwLocalPlayerPawn']
# Поля (Offsets)
m_iTeamNum = CLIENT_DLL['client.dll']['classes']['C_BaseEntity']['fields']['m_iTeamNum']
m_iHealth = CLIENT_DLL['client.dll']['classes']['C_BaseEntity']['fields']['m_iHealth']
m_entitySpottedState = CLIENT_DLL['client.dll']['classes']['C_CSPlayerPawnBase']['fields']['m_entitySpottedState']
m_bSpotted = 0x8 # Обычно это смещение внутри spottedState

def start_cheat():
    try:
        pm = pymem.Pymem("cs2.exe")
        client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
        print("[PenguinAI] Engine Connected. Radar Hack: ON")

        while True:
            # Находим себя
            local_player = pm.read_longlong(client + dwLocalPlayerPawn)
            if not local_player: continue
            my_team = pm.read_int(local_player + m_iTeamNum)

            # Список сущностей
            entity_list = pm.read_longlong(client + dwEntityList)
            
            for i in range(1, 64):
                try:
                    # Поиск Pawn игрока
                    entry_ptr = pm.read_longlong(entity_list + (8 * (i & 0x7FFF) >> 9) + 16)
                    controller_ptr = pm.read_longlong(entry_ptr + 120 * (i & 0x1FF))
                    
                    # Получаем Pawn через Handle
                    pawn_handle = pm.read_long(controller_ptr + 0x7FC) # m_hPawn
                    pawn_ptr = pm.read_longlong(entry_ptr + 120 * (pawn_handle & 0x1FF))
                    
                    if not pawn_ptr: continue

                    # Данные врага
                    health = pm.read_int(pawn_ptr + m_iHealth)
                    team = pm.read_int(pawn_ptr + m_iTeamNum)

                    if health > 0 and team != my_team:
                        # --- RADAR HACK ---
                        # Заставляем игру думать, что мы видим врага
                        pm.write_bool(pawn_ptr + m_entitySpottedState + m_bSpotted, True)
                        
                except: continue
            
            time.sleep(0.5) # Для радара большая частота не нужна

    except Exception as e:
        print(f"Waiting for CS2... {e}")
        time.sleep(2)

if __name__ == "__main__":
    start_glow()
