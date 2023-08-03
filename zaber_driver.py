import serial

class ZaberDriver:

    def __init__(self):
        self.isConnected = False
        print("Zaber driver initializing...")

    def tryConnect(self, port):
        print(f"Zaber trying to connect to {port}")

        return False