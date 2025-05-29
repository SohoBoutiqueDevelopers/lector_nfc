import time
import pyperclip
import pyautogui
from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException, CardConnectionException

COMMON_KEYS = [
    [0xFF]*6,
    [0xA0]*6,
    [0xA1]*6,
    [0x00]*6,
    [0xD3, 0xF7, 0xD3, 0xF7, 0xD3, 0xF7],
    [0x4D, 0x3A, 0x99, 0xC3, 0x51, 0xDD],
    [0x1A, 0x98, 0x2C, 0x7E, 0x45, 0x9A],
    [0xAA]*6,
]

def load_authenticate(connection, key, block, key_type='A'):
    load_key_apdu = [0xFF, 0x82, 0x00, 0x00, 0x06] + key
    response, sw1, sw2 = connection.transmit(load_key_apdu)
    if (sw1, sw2) != (0x90, 0x00):
        return False

    # 2. Autenticar bloque con esa clave
    key_type_flag = 0x60 if key_type.upper() == 'A' else 0x61
    auth_apdu = [0xFF, 0x86, 0x00, 0x00, 0x05,
                 0x01, 0x00, block, key_type_flag, 0x00]  # último byte = slot 0
    response, sw1, sw2 = connection.transmit(auth_apdu)
    return (sw1, sw2) == (0x90, 0x00)

def read_block(connection, block):
    read_apdu = [0xFF, 0xB0, 0x00, block, 0x10]  # Leer 16 bytes
    response, sw1, sw2 = connection.transmit(read_apdu)
    if (sw1, sw2) == (0x90, 0x00):
        return response
    return None

def hex_to_ascii_string(hex_list):
    chars = []
    for byte in hex_list:
        if byte == 0x00:
            break
        chars.append(chr(byte))
    return ''.join(chars)

def wait_for_card(reader):
    while True:
        try:
            connection = reader.createConnection()
            connection.connect()
            return connection
        except NoCardException:
            print("💤 Esperando tarjeta...")
            time.sleep(1)

def main_loop():
    r = readers()
    if not r:
        print("❌ No hay lectores disponibles.")
        return

    reader = r[0]
    print(f"📡 Usando lector: {reader}")

    while True:
        try:
            connection = reader.createConnection()
            connection.connect()
            
            for sector in range(16):
                if sector != 10:
                    continue
                base_block = sector * 4
                trailer_block = base_block + 3

                found_key = None
                for key in COMMON_KEYS:
                    if load_authenticate(connection, key, trailer_block, 'A'):
                        found_key = key
                        break

                if found_key:
                    for i in range(4):
                        block_num = base_block + i
                        data = read_block(connection, block_num)
                        if data:
                            if sector == 10 and block_num == 40:
                                ascii_value = hex_to_ascii_string(data)
                                pyperclip.copy(ascii_value)
                                time.sleep(0.3)
                                pyautogui.hotkey('ctrl', 'v')
                                break
                        else:
                            print(f"⚠️ No se pudo leer bloque {block_num}")
        except NoCardException as e:
            # print(f"⚠️ No hay tarjeta en el lector: {e}")
            continue
        except CardConnectionException:
            # print("⚠️ La tarjeta fue retirada prematuramente.")ç
            continue
        except Exception as e:
            print(f"❌ Error: {e}")

        print("🔁 Esperando próxima tarjeta...\n")
        time.sleep(0.5)

main_loop()
