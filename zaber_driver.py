import time

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

        self.serialPort = serial.Serial()
        self.serialPort.port = port
        self.serialPort.baudrate = 115200

        try:
            self.serialPort.open()
        except:
            pass

        if self.serialPort.isOpen():
            print("Zaber connected")
            return True
        else:
            print("Zaber disconnected")
            return False

    def home(self):
        self.sendCommand("/home")

    def sendCommand(self, command):
        dummy = command + "\r\n"
        if self.serialPort.isOpen():
            self.serialPort.write(bytes(dummy, 'ascii'))

    def waitUntilIdle(self):

        if not self.serialPort.isOpen():
            return

        while True:
            self.sendCommand("/")
            response = self.serialPort.readline()

            if response.contains("IDLE"):
                break
            else:
                time.sleep(0.01)

    def setPosition(self, position):
        calculated_steps = round(position / self.DelayLineResolution)
        self.sendCommand(f"/move abs {calculated_steps}")
