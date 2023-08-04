import time
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
        self.scanStartPosition = 0
        self.scanLength = 0
        self.scanSpeed = 0

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

    def performMeasurements(self, measurementsCount, samplingFrequency, scanStart, scanLength, scanSpeed):
        self.orderedMeasurementsCount = measurementsCount
        self.mfliFrequencyIndex = samplingFrequency
        self.scanStartPosition = scanStart
        self.scanLength = scanLength
        self.scanSpeed = scanSpeed

        t = Thread(target=self.measurementsWork, daemon=True)
        t.start()

    def measurementsWork(self):
        self.SetStatusMessageMethod("Preparing...")
        mfliSamplingFrequency = MFLIDriver.MFLISamplingRates[self.mfliFrequencyIndex]
        self.mfliSamplesCount = (self.scanLength / (self.scanSpeed * 1000)) * mfliSamplingFrequency

        # send the delay line to the starting position
        self.ZaberDriver.setPosition(position=self.scanStartPosition, speed=ZaberDriver.MaxSpeed)

        # configure MFLI
        self.MFLIDriver.configureForMeasurement(self.mfliFrequencyIndex, self.mfliSamplesCount)

        # wait until the mirror is in position
        self.ZaberDriver.waitUntilIdle()

        # acquire data (note: zaber uses us/s, interface uses mm/s)
        self.SetStatusMessageMethod("Acquisition...")
        self.MFLIDriver.measureData()
        self.ZaberDriver.setPosition(position=self.scanStartPosition-self.scanLength, speed=self.scanSpeed * 1000)
        self.ZaberDriver.waitUntilIdle()

        # synchronization delay
        time.sleep(0.1)

        # display results
        interferogramY = self.MFLIDriver.lastInterferogramData
        interferogramX = np.arange(len(interferogramY))

        spectrumY = self.MFLIDriver.lastReferenceData
        spectrumX = np.arange(len(spectrumY))

        self.SendResultsToPlot(interferogramX, interferogramY, spectrumX, spectrumY)
        self.SetStatusMessageMethod("Done")


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






