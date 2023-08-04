from threading import *
from mfli_driver import MFLIDriver
from zaber_driver import ZaberDriver
import numpy as np

class BackgroundController:

    def __init__(self, mfliDrv, zaberDrv):
        print("Background controller created")

        self.orderedMeasurementsCount = 0
        self.mfliFrequencyIndex = 0
        self.mfliSamplesCount = 0

        self.MFLIDriver     = mfliDrv
        self.ZaberDriver    = zaberDrv

        self.SetStatusMessageMethod         = None
        self.SetGeneralReadyFlagMethod      = None
        self.SetDAQReadyFlagMethod          = None
        self.SetDelayLineReadyFlagMethod    = None
        self.UploadNewDataMethod            = None
        self.SendResultsToPlot              = None

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
            self.SetStatusMessageMethod("Homing...")
            self.ZaberDriver.home()
            self.ZaberDriver.waitUntilIdle()
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
        t = Thread(target=self.initializationWork, daemon=True)
        t.start()

    def performMeasurements(self, measurementsCount, samplesCount, samplingFrequency):
        self.orderedMeasurementsCount = measurementsCount
        self.mfliSamplesCount = samplesCount
        self.mfliFrequencyIndex = samplingFrequency

        t = Thread(target=self.measurementsWork, daemon=True)
        t.start()

    def measurementsWork(self):
        mfliSamplingFrequency = MFLIDriver.MFLISamplingRates[self.mfliFrequencyIndex]

        # TODO
    # - dodać okienko do wpisywania początku skanu
        # - dodać okienko z suwakiem do wybierania długości skanu
        # - dodać suwak do szybkości skanu
        # - liczba sampli obliczy się automatycznie z sample rate MFLI
        #  I to będzie akwizycja

        # self.SetStatusMessageMethod("Homing...")
        # self.ZaberDriver.home()
        # self.ZaberDriver.waitUntilIdle()

        # self.SetStatusMessageMethod("Test...")
        # while True:
        #     self.ZaberDriver.setPosition(position=49000, speed=400000)
        #     self.ZaberDriver.waitUntilIdle()
        #     self.ZaberDriver.setPosition(position=149000, speed=400000)
        #     self.ZaberDriver.waitUntilIdle()
        # self.SetStatusMessageMethod("Configuration...")
        # # configure MFLI
        # self.MFLIDriver.configureForMeasurement(self.mfliFrequencyIndex, self.mfliSamplesCount)
        # # zaber move to beginning of the trajectory
        # # start zaber sweep
        # # start acquisition
        # self.SetStatusMessageMethod("Measurement...")
        # self.MFLIDriver.measureData()
        # # display results
        #
        # interferogramY = self.MFLIDriver.lastInterferogramData
        # interferogramX = np.arange(len(interferogramY))
        #
        # spectrumY = self.MFLIDriver.lastReferenceData
        # spectrumX = np.arange(len(spectrumY))
        #
        # self.SendResultsToPlot(interferogramX, interferogramY, spectrumX, spectrumY)
        # self.SetStatusMessageMethod("Done")






