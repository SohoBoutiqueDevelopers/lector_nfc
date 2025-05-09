import time
from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException, CardConnectionException

# Claves comunes a probar
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
    # 1. Cargar clave en slot 0 del lector
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

def main():
    r = readers()
    if not r:
        print("❌ No hay lectores disponibles.")
        return

    reader = r[0]
    print(f"📡 Usando lector: {reader}")

    connection = reader.createConnection()
    connection.connect()
    print("🆔 Tarjeta conectada.")

    # Obtener UID (opcional)
    uid_apdu = [0xFF, 0xCA, 0x00, 0x00, 0x00]
    response, sw1, sw2 = connection.transmit(uid_apdu)
    if (sw1, sw2) == (0x90, 0x00):
        print(f"🔍 UID: {toHexString(response)}")
    else:
        print("⚠️ No se pudo leer el UID.")

    print("\n📖 Iniciando lectura de sectores...")

    for sector in range(16):  # 16 sectores (0 a 15)
        print(f"\n📁 Sector {sector}")
        base_block = sector * 4
        trailer_block = base_block + 3

        found_key = None
        for key in COMMON_KEYS:
            if load_authenticate(connection, key, trailer_block, 'A'):
                found_key = key
                break

        if found_key:
            print(f"✅ Autenticado con clave: {toHexString(found_key)}")
            for i in range(4):
                block_num = base_block + i
                data = read_block(connection, block_num)
                if data:
                    print(f"📦 Bloque {block_num:02}: {toHexString(data)}")
                else:
                    print(f"⚠️ No se pudo leer bloque {block_num}")
        else:
            print("❌ No se pudo autenticar con claves conocidas.")

    print("\n✅ Lectura finalizada.")

main()
