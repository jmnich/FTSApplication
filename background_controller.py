import time
from threading import *

import numpy

from mfli_driver import MFLIDriver
from zaber_driver import ZaberDriver
from data_processor import DataProcessor
import logging
import numpy as np
import math

from tkinter import messagebox

class BackgroundController:

    def __init__(self, mfliDrv, zaberDrv):
        print("Background controller created")
        self.stopRequestFlag = False

        self.DataAnalyzer = DataProcessor()
        self.orderedMeasurementsCount = 0
        self.mfliFrequencyIndex = 0
        self.mfliSamplesCount = 0
        self.scanStartPosition = 0
        self.scanLength = 0
        self.scanSpeed = 0
        self.triggerModeEnabled = False
        self.triggerLevel = None
        self.triggerHysteresis = None
        self.triggerReference = None
        self.selectedApodizationWindowType = None

        self.MFLIDriver     = mfliDrv
        self.ZaberDriver    = zaberDrv

        # external methods used for communication between the background controller and the GUI
        self.SetStatusMessageMethod         = None
        self.SetGeneralReadyFlagMethod      = None
        self.SetDAQReadyFlagMethod          = None
        self.SetDelayLineReadyFlagMethod    = None
        self.UploadNewDataMethod            = None
        self.SendResultsToPlot              = None
        self.NotifyAllMeasurementsDone      = None

        self.ZaberPort                      = None
        self.MFLIDeviceName                 = None

        self.rawInterferograms = []
        self.rawReferenceSignals = []
        self.processedInterferogramsX = []
        self.processedInterferogramsY = []
        self.spectraX = []
        self.spectraY = []
        self.averageSpectrumX = None
        self.averageSpectrumY = None

    def setZaberPort(self, port):
        self.ZaberPort = port

    def requestStop(self):
        self.stopRequestFlag = True

    def setMFLIDeviceName(self, mfliName):
        self.MFLIDeviceName = mfliName

    def initializationWork(self):

        if self.ZaberPort is None or self.MFLIDeviceName is None:
            self.SetStatusMessageMethod("Select ports and IDs\nfor hardware modules")
            return

        self.SetStatusMessageMethod("Connecting to hardware...")

        if self.MFLIDriver.tryConnect(self.MFLIDeviceName):
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
        logging.info(f"Application controller: hardware initialization starting")
        t = Thread(target=self.initializationWork, daemon=True)
        t.start()


    def performMeasurements(self, measurementsCount, samplingFrequency, scanStart, scanLength, scanSpeed,
                            trigModeEnabled, trigLevel, trigHysteresis, trigReference, apodizationWindow):
        logging.info(f"Application controller: measurement starting")

        # reset and configure the backgroung controller
        self.rawInterferograms.clear()
        self.rawReferenceSignals.clear()
        self.processedInterferogramsX.clear()
        self.processedInterferogramsY.clear()
        self.spectraX.clear()
        self.spectraY.clear()
        self.averageSpectrumX = None
        self.averageSpectrumY = None

        self.orderedMeasurementsCount   = measurementsCount
        self.mfliFrequencyIndex         = samplingFrequency
        self.scanStartPosition          = scanStart
        self.scanLength                 = scanLength
        self.scanSpeed                  = scanSpeed
        self.selectedApodizationWindowType = apodizationWindow

        self.triggerModeEnabled         = trigModeEnabled
        self.triggerLevel               = trigLevel
        self.triggerHysteresis          = trigHysteresis
        self.triggerReference           = trigReference

        self.stopRequestFlag            = False

        # start the actual measurement thread
        t = Thread(target=self.measurementsWork, daemon=True)
        t.start()


    def measurementsWork(self):
        self.SetStatusMessageMethod("Preparing...")

        if self.stopRequestFlag:
            self.stopRequestFlag = False
            self.SetStatusMessageMethod("Measurement stopped")
            return

        status = self.performAcqusition()

        if status == "ok":
            self.allMeasurementsDone()  # all ordered measurements are completed, terminate gracefully
        elif status == "stop":
            self.SetStatusMessageMethod("Measurement stopped")
        else:
            self.SetStatusMessageMethod("Measurement failed")
            messagebox.showerror('Measurement failed', status)


    def performAcqusition(self):
        self.ZaberDriver.waitUntilIdle()
        mfliSamplingFrequency = MFLIDriver.MFLISamplingRates[self.mfliFrequencyIndex]
        self.mfliSamplesCount = (self.scanLength / (self.scanSpeed * 1000)) * mfliSamplingFrequency

        # configure MFLI
        self.MFLIDriver.configureForMeasurement(samplingFreqIndex=self.mfliFrequencyIndex,
                                                sampleLength=self.mfliSamplesCount,
                                                triggerEnabled=self.triggerModeEnabled,
                                                triggerLevel=self.triggerLevel,
                                                triggerReference=self.triggerReference,
                                                triggerHysteresis=self.triggerHysteresis)

        time.sleep(1)

        failedAcquisitionsCount = 0
        failMessages = []

        # acquire all data
        i = 0
        while i < self.orderedMeasurementsCount:
            i += 1
        # for i in range(0, self.orderedMeasurementsCount):
            if failedAcquisitionsCount >= math.ceil(self.orderedMeasurementsCount * 0.2):

                if self.orderedMeasurementsCount == 1:
                    errstatus = "Single measurement failed"
                else:
                    errstatus = "More than 20% of the ordered measurements failed"

                return errstatus

            self.ZaberDriver.waitUntilIdle()
            time.sleep(0.25)  # wait to let the mirror settle

            if self.stopRequestFlag:
                self.stopRequestFlag = False
                self.SetStatusMessageMethod("Measurement stopped")
                return "stop"

            # calculate start and stop positions for the delay line
            # note: direction of scan from zaber motor to the other end
            preferred_margin = self.scanSpeed * 1000 * 0.5
            startPosition = self.scanStartPosition + preferred_margin
            endPosition = self.scanStartPosition - self.scanLength - preferred_margin

            # clamp the values
            if endPosition < 0:
                endPosition = 0

            if startPosition > self.ZaberDriver.DelayLineNominalLength:
                startPosition = self.ZaberDriver.DelayLineNominalLength

            # send the delay line to the starting position
            self.ZaberDriver.setPosition(position=startPosition, speed=ZaberDriver.MaxSpeed)

            # if trigger mode is enabled arm the trigger and wait for a moment until it takes effect
            if self.triggerModeEnabled:
                self.MFLIDriver.armTrigger()
                # time.sleep(1.0)

            # wait until the mirror is in position
            self.ZaberDriver.waitUntilIdle()
            time.sleep(1.0)  # wait to let the mirror settle

            self.SetStatusMessageMethod("Acquisition...")
            # acquire data (note: zaber uses us/s, interface uses mm/s)
            # prepare scanning trajectory with a 0.1 sec marging if possible

            self.ZaberDriver.setPosition(endPosition, speed=self.scanSpeed * 1000)

            # if self.scanStartPosition-self.scanLength > preferred_margin:
            #     self.ZaberDriver.setPosition(position=self.scanStartPosition - self.scanLength - preferred_margin,
            #                                  speed=self.scanSpeed * 1000)
            # else:
            #     self.ZaberDriver.setPosition(position=self.scanStartPosition - self.scanLength,
            #                                  speed=self.scanSpeed * 1000)

            if self.triggerModeEnabled:
                measStatus = self.MFLIDriver.measureDataWithPrearmedTrigger()
            else:
                measStatus = self.MFLIDriver.measureDataStandaloneMethod()

            self.ZaberDriver.waitUntilIdle()

            # try to complete the measurement even if acquisition fails a few times
            if measStatus != "ok":
                failedAcquisitionsCount += 1
                i -= 1
                print("Measurement cycle skipped due to error: " + measStatus)
                continue

            # send the delay line to the starting position while the calculations are running
            self.ZaberDriver.setPosition(position=startPosition, speed=ZaberDriver.MaxSpeed)

            self.SetStatusMessageMethod("Calculations...")
            # synchronization delay
            # time.sleep(0.1)

            try:
                # results = self.DataAnalyzer.analyzeData(rawReferenceSignal=self.MFLIDriver.lastReferenceData,
                #                                         rawInterferogram=self.MFLIDriver.lastInterferogramData)
                results = self.DataAnalyzer.analyzeDataHilbertInterpolation(rawReferenceSignal=self.MFLIDriver.lastReferenceData,
                                                        rawInterferogram=self.MFLIDriver.lastInterferogramData,
                                                        apodizationWindowType=self.selectedApodizationWindowType)
            except:
                self.SetStatusMessageMethod("Data acquisition or analysis failed")
                failedAcquisitionsCount += 1
                i -= 1
                print("Data acquisition or analysis failed due to exception")
                continue

            self.rawInterferograms.append(np.copy(self.MFLIDriver.lastInterferogramData))
            self.rawReferenceSignals.append(np.copy(self.MFLIDriver.lastReferenceData))
            self.spectraX.append(np.copy(results["spectrumX"]))
            self.spectraY.append(np.copy(results["spectrumY"]))
            self.processedInterferogramsX.append(np.copy(results["interferogramX"]))
            self.processedInterferogramsY.append(np.copy(results["interferogramY"]))

            # equalize lengths of all spectra before averaging
            minimalSpectrumLength = len(self.spectraX[0])

            for s in self.spectraX:
                if len(s) < minimalSpectrumLength:
                    minimalSpectrumLength = len(s)

            for z in range(0, len(self.spectraX)):
                if len(self.spectraX[z]) > minimalSpectrumLength:
                    self.spectraX[z] = self.spectraX[z][:minimalSpectrumLength - 1]
                    self.spectraY[z] = self.spectraY[z][:minimalSpectrumLength - 1]

            # calculate an average spectrum
            sumArr = numpy.zeros(len(self.spectraY[0]))
            for s in self.spectraY:
                sumArr += s

            sumArr /= len(self.spectraY)

            self.averageSpectrumX = self.spectraX[0]
            self.averageSpectrumY = sumArr

            self.SendResultsToPlot(results["interferogramX"], results["rawInterferogramY"],
                                   results["spectrumX"], results["spectrumY"],
                                   self.averageSpectrumX, self.averageSpectrumY, i,
                                   results["apodizationWindow"])

        return "ok"


    def allMeasurementsDone(self):
        self.NotifyAllMeasurementsDone()
        # self.SetStatusMessageMethod("Done")
