import sys

# Получаем логин от лаунчера
user = sys.argv[1] if len(sys.argv) > 1 else "Unknown"

print("========================================")
print(f"  PENGUIN AI | COUNTER-STRIKE PROJECT")
print("========================================")
print(f"Status: Authenticated as {user}")
print("Searching for CS process...")

# Здесь в будущем будет твой код для CS
import time
time.sleep(5)
