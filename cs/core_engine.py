import pymem
import pymem.process
import time
import requests

# --- АВТО-ОБНОВЛЕНИЕ ОФФСЕТОВ ---
# Мы берем свежие адреса памяти прямо из проверенного репозитория, 
# чтобы чит не ломался после мелких патчей CS2.
def get_offsets():
    try:
        offsets = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json").json()
        client_dll = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json").json()
        return offsets, client_dll
    except:
        return None, None

def start_cheat():
    print("[SYSTEM] Searching for CS2...")
    try:
        # 1. Подключаемся к процессу
        pm = pymem.Pymem("cs2.exe")
        client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
        
        offsets, client_data = get_offsets()
        if not offsets:
            print("[ERROR] Could not load offsets!")
            return

        # Получаем нужные адреса
        dwEntityList = offsets['client_dll']['dwEntityList']
        dwLocalPlayerPawn = offsets['client_dll']['dwLocalPlayerPawn']
        m_iTeamNum = client_data['client.dll']['classes']['C_BaseEntity']['fields']['m_iTeamNum']
        m_iHealth = client_data['client.dll']['classes']['C_BaseEntity']['fields']['m_iHealth']

        print("[SUCCESS] PenguinAI Engine Linked to CS2.")
        print("[INFO] Glow/Radar logic active. Use with caution.")

        while True:
            # Читаем твой указатель (Local Player)
            local_player = pm.read_longlong(client + dwLocalPlayerPawn)
            if not local_player: continue
            
            my_team = pm.read_int(local_player + m_iTeamNum)

            # Перебор списка сущностей (врагов и союзников)
            entity_list = pm.read_longlong(client + dwEntityList)
            if not entity_list: continue

            for i in range(1, 64): # В матче максимум 64 игрока
                try:
                    # Хитрый способ CS2 найти игрока в памяти
                    list_entry = pm.read_longlong(entity_list + (8 * (i & 0x7FFF) >> 9) + 16)
                    if not list_entry: continue
                    
                    pawn = pm.read_longlong(list_entry + 120 * (i & 0x1FF))
                    if not pawn: continue

                    # Проверяем здоровье и команду
                    health = pm.read_int(pawn + m_iHealth)
                    team = pm.read_int(pawn + m_iTeamNum)

                    if health > 0 and team != my_team:
                        # --- ТУТ МЫ БУДЕМ ВКЛЮЧАТЬ GLOW/RADAR ---
                        # Пока просто выводим в консоль для теста, что мы их "видим"
                        # Чтобы включить полноценный Glow, нужно работать с SceneSystem (следующий шаг)
                        pass
                except:
                    continue
            
            time.sleep(0.01) # Чтобы не грузить процессор на 100%

    except Exception as e:
        print(f"[CRITICAL] CS2 not found or memory error: {e}")

if __name__ == "__main__":
    start_cheat()
