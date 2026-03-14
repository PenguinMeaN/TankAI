import sys

# Проверяем, передал ли лаунчер логин пользователя
if len(sys.argv) > 1:
    username = sys.argv[1]
else:
    username = "Guest"

print("========================================")
print(f"Welcome, {username}!")
print("========================================")
print("Tactical Core is active and running.")
print("Waiting for game process...")
input("\nPress Enter to close this core window...")
