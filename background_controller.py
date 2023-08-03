from threading import *
from mfli_driver import MFLIDriver
from zaber_driver import ZaberDriver

class BackgroundController:

    def __init__(self, mfliDrv, zaberDrv):
        print("Background controller created")

        self.MFLIDriver     = mfliDrv
        self.ZaberDriver    = zaberDrv

        self.SetStatusMessageMethod         = None
        self.SetGeneralReadyFlagMethod      = None
        self.SetDAQReadyFlagMethod          = None
        self.SetDelayLineReadyFlagMethod    = None
        self.UploadNewDataMethod            = None

    def setZaberPort(self, port):
        self.ZaberPort = port

    def setMFLIDeviceName(self, mfliName):
        self.MFLIDeviceName = mfliName

    def initializationWork(self):
        self.SetStatusMessageMethod("Connecting to hardware...")

        if self.MFLIDriver.tryConnect(self.MFLIDriver.deviceID):
            self.SetDAQReadyFlagMethod(True)
        else:
            self.SetDAQReadyFlagMethod(False)

        if self.ZaberDriver.tryConnect(self.ZaberPort):
            self.SetDelayLineReadyFlagMethod(True)
        else:
            self.SetDelayLineReadyFlagMethod(False)

        if self.ZaberDriver.isConnected and self.MFLIDriver.isConnected:
            self.SetStatusMessageMethod("Conneted to hardware")
            self.SetGeneralReadyFlagMethod(True)
        else:
            self.SetStatusMessageMethod("One or more hardware components\nfailed to connect")
            self.SetGeneralReadyFlagMethod(False)

    def performInitialization(self):
        t = Thread(target=self.initializationWork)
        t.start()


