import pyperclip
from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.util import toHexString
from smartcard.Exceptions import CardConnectionException

class UIDObserver(CardObserver):
    def update(self, observable, actions):
        added_cards, removed_cards = actions
        for card in added_cards:
            try:
                connection = card.createConnection()
                connection.connect()

                # Comando para obtener UID (lector compatible con APDU extendido)
                GET_UID = [0xFF, 0xCA, 0x00, 0x00, 0x00]
                response, sw1, sw2 = connection.transmit(GET_UID)

                if (sw1, sw2) == (0x90, 0x00):
                    uid = toHexString(response)
                    pyperclip.copy(uid)
                    print(f"UID leído: {uid} (copiado al portapapeles)")
                else:
                    print(f"Error al leer UID: SW1={hex(sw1)} SW2={hex(sw2)}")
            except CardConnectionException as e:
                print("Error al conectar con tarjeta:", e)

print("Monitoreando tarjetas... (Ctrl+C para salir)")

monitor = CardMonitor()
observer = UIDObserver()
monitor.addObserver(observer)

try:
    while True:
        pass  # Loop principal en background
except KeyboardInterrupt:
    print("Finalizando...")
    monitor.deleteObserver(observer)
