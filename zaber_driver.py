import serial
from threading import *

class ZaberDriver:

    DelayLineModelNumber = "X-LSQ150D-E01"
    DelayLineResolution = 1.984375  # [um / step]
    DelayLineNominalLength = 150000 # [um]

    def __init__(self):
        self.isReady = False
        self.isConnected = False

        self.serialPort = None

    def tryConnect(self, port):
        print(f"Zaber trying to connect to {port}")

        return False

    def home(self):
        self.sendCommand("/home")

    def sendCommand(self, command):
        return 0

    def waitUntilDone(self):
        return 0