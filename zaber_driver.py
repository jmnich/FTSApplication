import serial
from threading import *

class ZaberDriver:

    def __init__(self):
        self.isReady = False
        self.isConnected = False
        print("Zaber driver initializing...")

    def tryConnect(self, port):
        print(f"Zaber trying to connect to {port}")

        return False

    def home(self):
        self.sendCommand("/home")

    def sendCommand(self, command):
        return 0

    def waitUntilDone(self):
        return 0