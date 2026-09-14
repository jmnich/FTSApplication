import time
import logging
import os
import numpy as np

from daq_base import DAQDriver


class SimulatedDAQ(DAQDriver):

    SamplingRates = (6.0E7, 3.0E7, 1.5E7, 7.5E6,
                     3.75E6, 1.88E6, 9.38E5, 4.69E5,
                     2.34E5, 1.17E5, 5.86E4, 2.93E4,
                     1.46E4, 7.32E3, 3.66E3, 1.83E3)

    def __init__(self):
        print("Simulated DAQ initializing...")
        super().__init__()

        self.noiseLevel = 0.0

        dataPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "simulated_raw_0_ds4.npz")
        loaded = np.load(dataPath)
        self._embeddedData = loaded["data"]
        self._embeddedReference = self._embeddedData[:, 0].copy()
        self._embeddedInterferogram = self._embeddedData[:, 1].copy()

    def setNoiseLevel(self, level):
        self.noiseLevel = float(level)

    def tryConnect(self, *args, **kwargs) -> bool:
        print("Simulated DAQ connected")
        logging.info("Simulated DAQ: connected")
        self.isConnected = True
        return True

    def configureForMeasurement(self, samplingFreqIndex, sampleLength, triggerEnabled, triggerLevel,
                                triggerReference, triggerHysteresis):
        logging.info(f"Simulated DAQ: configuration (no-op). Freq index: {samplingFreqIndex}, "
                     f"sample length: {sampleLength}, triggered: {triggerEnabled}")

        self.triggerEnabled = triggerEnabled
        self.currentMeasurementFrequency = SimulatedDAQ.SamplingRates[samplingFreqIndex]
        self.currentMeasurementPointsCount = sampleLength

    def armTrigger(self):
        print("Simulated DAQ: trigger armed (no-op)")

    def measureDataWithPrearmedTrigger(self) -> str:
        return self._measure()

    def measureDataStandaloneMethod(self) -> str:
        return self._measure()

    def _measure(self) -> str:
        print("Simulated DAQ: generating measurement data")

        ref = self._embeddedReference.copy().astype(np.float64)
        meas = self._embeddedInterferogram.copy().astype(np.float64)

        if self.noiseLevel > 0:
            refNoiseAmp = self.noiseLevel * 0.01 * np.max(np.abs(ref))
            measNoiseAmp = self.noiseLevel * 0.01 * np.max(np.abs(meas))
            ref = ref + refNoiseAmp * np.random.randn(len(ref))
            meas = meas + measNoiseAmp * np.random.randn(len(meas))

        self.lastReferenceData = ref.astype(np.float32)
        self.lastInterferogramData = meas.astype(np.float32)

        simulatedDuration = min(self.currentMeasurementPointsCount / self.currentMeasurementFrequency, 5.0)
        time.sleep(simulatedDuration)

        return "ok"
