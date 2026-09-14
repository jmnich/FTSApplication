import logging


class DAQDriver:
    """Base class for all DAQ drivers (MFLI, Digilent ADP2230, Simulated)."""

    SamplingRates = ()

    def __init__(self):
        self.isConnected = False
        self.lastInterferogramData = []
        self.lastReferenceData = []
        self.currentMeasurementFrequency = None
        self.currentMeasurementPointsCount = None
        self.triggerEnabled = False

    def tryConnect(self, *args, **kwargs) -> bool:
        raise NotImplementedError

    def configureForMeasurement(self, samplingFreqIndex, sampleLength, triggerEnabled, triggerLevel,
                                triggerReference, triggerHysteresis):
        raise NotImplementedError

    def armTrigger(self):
        raise NotImplementedError

    def measureDataWithPrearmedTrigger(self) -> str:
        raise NotImplementedError

    def measureDataStandaloneMethod(self) -> str:
        raise NotImplementedError
