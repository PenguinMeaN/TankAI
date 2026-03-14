import pymem, pymem.process, requests, time

def start_glow():
    try:
        pm = pymem.Pymem("cs2.exe")
        client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll
        
        # Получаем оффсеты динамически
        offsets = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/offsets.json").json()
        client_dll = requests.get("https://raw.githubusercontent.com/a2x/cs2-dumper/main/output/client_dll.json").json()
        
        dwEntityList = offsets['client_dll']['dwEntityList']
        dwLocalPlayerPawn = offsets['client_dll']['dwLocalPlayerPawn']
        m_iTeamNum = client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_iTeamNum']
        
        print("[PenguinAI] Glow Engine Active. Happy hunting!")

        while True:
            local_player = pm.read_longlong(client + dwLocalPlayerPawn)
            my_team = pm.read_int(local_player + m_iTeamNum)
            
            # Логика отрисовки Glow ESP через SceneSystem (пока просто читаем данные)
            # В v2.1 добавим прямой инжект цвета
            time.sleep(0.01)

    except Exception as e:
        print(f"CS2 Error: {e}")

if __name__ == "__main__":
    start_glow()
