import time
import logging
import sys
import numpy as np
from ctypes import c_int, c_double, c_bool, c_byte, byref, cdll, create_string_buffer
from datetime import datetime

from daq_base import DAQDriver

# DWF constants (defined inline to avoid path issues with dwfconstants.py)
trigsrcNone = 0
trigsrcPC = 1
trigsrcDetectorAnalogIn = 2
trigsrcDetectorDigitalIn = 3

trigtypeEdge = 0
trigtypePulse = 1

trigcondRisingPositive = 0
trigcondFallingNegative = 1

DwfStateDone = 2


class DigilentDriver(DAQDriver):

    # Same rates as MFLI (max 60 MHz, well within ADP2230's 125 MS/s capability)
    SamplingRates = (6.0E7, 3.0E7, 1.5E7, 7.5E6,
                     3.75E6, 1.88E6, 9.38E5, 4.69E5,
                     2.34E5, 1.17E5, 5.86E4, 2.93E4,
                     1.46E4, 7.32E3, 3.66E3, 1.83E3)

    def __init__(self):
        print("Digilent driver initializing...")
        super().__init__()

        self.dwf = None
        self.hdwf = c_int(0)
        self.channelRange = 5.0

    def setChannelRange(self, rangeVolts):
        self.channelRange = float(rangeVolts)

    def _loadLibrary(self):
        if sys.platform.startswith("win"):
            return cdll.dwf
        elif sys.platform.startswith("darwin"):
            return cdll.LoadLibrary("/Library/Frameworks/dwf.framework/dwf")
        else:
            return cdll.LoadLibrary("libdwf.so")

    def tryConnect(self, *args, **kwargs) -> bool:
        logging.info("Digilent driver: trying to connect to ADP2230 via USB")

        try:
            self.dwf = self._loadLibrary()

            self.hdwf = c_int(0)
            self.dwf.FDwfDeviceOpen(c_int(-1), byref(self.hdwf))

            if self.hdwf.value == 0:
                szError = create_string_buffer(512)
                self.dwf.FDwfGetLastErrorMsg(szError)
                errMsg = szError.value.decode()
                print(f"Digilent ADP2230 connection failed: {errMsg}")
                logging.info(f"Digilent driver: connection failed: {errMsg}")
                self.isConnected = False
                return False

        except Exception as e:
            print(f"Digilent ADP2230 connection failed: {str(e)}")
            logging.info(f"Digilent driver: connection failed: {str(e)}")
            self.isConnected = False
            return False

        print("Digilent ADP2230 connected successfully")
        logging.info("Digilent driver: connected")
        self.isConnected = True
        return True

    def configureForMeasurement(self, samplingFreqIndex, sampleLength, triggerEnabled, triggerLevel,
                                triggerReference, triggerHysteresis):
        logging.info(f"Digilent driver: configuration for measurement. Freq index: {samplingFreqIndex}, "
                     f"sample length: {sampleLength}, triggered: {triggerEnabled}, "
                     f"trigger level: {triggerLevel} mV, trigger hysteresis: {triggerHysteresis} mV, "
                     f"trigger reference: {triggerReference} %")

        self.triggerEnabled = triggerEnabled
        self.currentMeasurementFrequency = DigilentDriver.SamplingRates[samplingFreqIndex]
        self.currentMeasurementPointsCount = int(sampleLength)

        dwf = self.dwf
        hdwf = self.hdwf

        # enable both channels
        dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(0), c_bool(True))
        dwf.FDwfAnalogInChannelEnableSet(hdwf, c_int(1), c_bool(True))

        # set range for both channels
        dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(0), c_double(self.channelRange))
        dwf.FDwfAnalogInChannelRangeSet(hdwf, c_int(1), c_double(self.channelRange))

        # set acquisition frequency and buffer size
        dwf.FDwfAnalogInFrequencySet(hdwf, c_double(self.currentMeasurementFrequency))
        dwf.FDwfAnalogInBufferSizeSet(hdwf, c_int(int(sampleLength)))

        # configure trigger
        if self.triggerEnabled:
            dwf.FDwfAnalogInTriggerSourceSet(hdwf, c_byte(trigsrcDetectorAnalogIn))
            dwf.FDwfAnalogInTriggerTypeSet(hdwf, c_int(trigtypeEdge))
            dwf.FDwfAnalogInTriggerChannelSet(hdwf, c_int(0))
            triglev = triggerLevel / 1000.0
            dwf.FDwfAnalogInTriggerLevelSet(hdwf, c_double(triglev))
            dwf.FDwfAnalogInTriggerConditionSet(hdwf, c_int(trigcondRisingPositive))
            dwf.FDwfAnalogInTriggerAutoTimeoutSet(hdwf, c_double(0))
        else:
            dwf.FDwfAnalogInTriggerSourceSet(hdwf, c_byte(trigsrcNone))

    def armTrigger(self):
        print("Digilent: trigger prearm")
        try:
            dwf = self.dwf
            hdwf = self.hdwf
            dwf.FDwfAnalogInConfigure(hdwf, c_bool(True), c_bool(True))
        except Exception as err:
            self.lastReferenceData = None
            self.lastInterferogramData = None
            print(f"Digilent trigger prearm failed: {err}")

    def measureDataWithPrearmedTrigger(self) -> str:
        return self._acquireData(triggered=True)

    def measureDataStandaloneMethod(self) -> str:
        return self._acquireData(triggered=False)

    def _acquireData(self, triggered: bool) -> str:
        startTime = datetime.now()
        expectedMeasDuration = (self.currentMeasurementPointsCount / self.currentMeasurementFrequency) + 2.0
        print(f"Digilent: max allowed measurement duration: {expectedMeasDuration}s")
        status = "ok"

        try:
            dwf = self.dwf
            hdwf = self.hdwf
            nSamples = int(self.currentMeasurementPointsCount)

            if not triggered:
                dwf.FDwfAnalogInConfigure(hdwf, c_bool(True), c_bool(True))

            sts = c_byte(0)
            while True:
                dwf.FDwfAnalogInStatus(hdwf, c_int(1), byref(sts))
                if sts.value == DwfStateDone:
                    break
                if (datetime.now() - startTime).total_seconds() > expectedMeasDuration:
                    status = "acquisition timeout"
                    print("Digilent: timeout")
                    break
                time.sleep(0.05)

            if status == "ok":
                channel0Data = (c_double * nSamples)()
                channel1Data = (c_double * nSamples)()

                dwf.FDwfAnalogInStatusData(hdwf, c_int(0), channel0Data, c_int(nSamples))
                dwf.FDwfAnalogInStatusData(hdwf, c_int(1), channel1Data, c_int(nSamples))

                self.lastReferenceData = np.array(channel0Data, dtype=np.float32)
                self.lastInterferogramData = np.array(channel1Data, dtype=np.float32)

                print(f"Digilent: data acquired, {nSamples} samples per channel")

        except Exception as err:
            self.lastReferenceData = None
            self.lastInterferogramData = None
            print(f"Digilent acquisition failed: {err}")
            status = "acquisition failed"

        finally:
            return status
