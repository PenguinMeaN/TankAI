import pymem
import pymem.process
import requests
import time
import ctypes

# Свежие оффсеты берем из проверенного источника (a2x)
OFFSETS_URL = "https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json"
CLIENT_URL = "https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json"

def start_glow():
    try:
        # Подключаемся к CS2
        pm = pymem.Pymem("cs2.exe")
        client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
        
        # Тянем актуальные адреса
        offsets = requests.get(OFFSETS_URL).json()
        client_data = requests.get(CLIENT_URL).json()

        dwEntityList = offsets['client_dll']['dwEntityList']
        dwLocalPlayerPawn = offsets['client_dll']['dwLocalPlayerPawn']
        m_iTeamNum = client_data['client.dll']['classes']['C_BaseEntity']['fields']['m_iTeamNum']
        m_iHealth = client_data['client.dll']['classes']['C_BaseEntity']['fields']['m_iHealth']

        print("[PenguinAI] Engine Connected. Glow is Warming Up...")

        while True:
            # Находим тебя
            local_player = pm.read_longlong(client + dwLocalPlayerPawn)
            if not local_player: continue
            my_team = pm.read_int(local_player + m_iTeamNum)

            # Ищем врагов
            entity_list = pm.read_longlong(client + dwEntityList)
            if not entity_list: continue

            for i in range(1, 64):
                try:
                    # Магия поиска сущностей в CS2
                    list_entry = pm.read_longlong(entity_list + (8 * (i & 0x7FFF) >> 9) + 16)
                    if not list_entry: continue
                    
                    pawn = pm.read_longlong(list_entry + 120 * (i & 0x1FF))
                    if not pawn: continue

                    # Проверяем: жив ли и не в нашей ли команде
                    health = pm.read_int(pawn + m_iHealth)
                    team = pm.read_int(pawn + m_iTeamNum)

                    if health > 0 and team != my_team:
                        # --- ТУТ БУДЕТ ОТРИСОВКА (v2.1) ---
                        # В CS2 Glow работает через SceneSystem или перепись материалов.
                        # На этом этапе мы убеждаемся, что база видит врагов.
                        pass
                except: continue
            
            time.sleep(0.01)

    except Exception as e:
        print(f"[SYSTEM] Waiting for CS2... ({e})")
        time.sleep(3)

if __name__ == "__main__":
    start_glow()
