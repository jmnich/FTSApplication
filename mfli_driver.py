import time
import zhinst.core
import zhinst.utils
import logging
from datetime import datetime

class MFLIDriver:

    MFLISamplingRates = (6.0E7, 3.0E7, 1.5E7, 7.5E6,
                         3.75E6, 1.88E6, 9.38E5, 4.69E5,
                         2.34E5, 1.17E5, 5.86E4, 2.93E4,
                         1.46E4, 7.32E3, 3.66E3, 1.83E3)

    def __init__(self, devID):
        print("MFLI driver initializing...")
        self.DAQ = None
        self.Scope = None
        # self.DAQModule = None
        self.isConnected = False
        self.lastInterferogramData = []
        self.lastReferenceData = []
        self.deviceID = devID.replace(' ', '').replace('\t', '').replace('\n', '').replace('\r', '')
        self.currentMeasurementFrequency = None
        self.currentMeasurementPointsCount = None
        # self.tryConnect(self.deviceID)

    def tryConnect(self, deviceID):

        self.deviceID = deviceID.replace(' ', '').replace('\t', '').replace('\n', '').replace('\r', '')
        logging.info(f"MFLI driver trying to connect to: {self.deviceID}")

        try:
            device_id: str = self.deviceID
            server_host: str = "localhost"
            server_port: int = 8004

            (self.DAQ, device, props) = zhinst.utils.create_api_session(
                device_id, 6, server_host=server_host, server_port=server_port
            )

            # restore the base configuration
            zhinst.utils.disable_everything(self.DAQ, self.deviceID)


        except Exception as e:
            print(f"Connection failed to MFLI device")
            print(f"Error message: \n{str(e)}")
            logging.info(f"MFLI driver: connection failed with message: {str(e)}")
            self.isConnected = False
            return False

        print(f"MFLI device connected successfully")
        logging.info(f"MFLI driver: connected")
        self.isConnected = True
        return True

    def configureForMeasurement(self, samplingFreqIndex, sampleLength, triggerEnabled, triggerLevel, triggerHysteresis,
                                triggerDelay):
        logging.info(f"MFLI driver: configuration for measurement. Freq index: {samplingFreqIndex}, "
                     f"sample length: {sampleLength}, triggered acqusition enabled: {triggerEnabled}, "
                     f"trigger level: {triggerLevel} mV, trigger hysteresis: {triggerHysteresis} mV, "
                     f"trigger delay: {triggerDelay} ms")

        self.currentMeasurementFrequency = MFLIDriver.MFLISamplingRates[samplingFreqIndex]
        self.currentMeasurementPointsCount = sampleLength

        zhinst.utils.disable_everything(self.DAQ, self.deviceID)

        self.DAQ.setInt(f'/{self.deviceID}/auxouts/2/demodselect', 0)
        self.DAQ.setInt(f'/{self.deviceID}/auxouts/2/demodselect', 0)
        self.DAQ.setInt(f'/{self.deviceID}/auxouts/3/demodselect', 0)
        self.DAQ.setInt(f'/{self.deviceID}/auxouts/3/demodselect', 0)

        self.Scope = self.DAQ.scopeModule()
        self.Scope.set('lastreplace', 1)
        self.Scope.subscribe(f'/{self.deviceID}/scopes/0/wave')
        self.Scope.set('averager/weight', 1)
        self.Scope.set('averager/restart', 0)
        self.Scope.set('averager/weight', 1)
        self.Scope.set('averager/restart', 0)
        self.Scope.set('fft/power', 0)
        self.Scope.unsubscribe('*')
        self.Scope.set('mode', 1)
        self.Scope.set('fft/spectraldensity', 0)
        self.Scope.set('fft/window', 1)
        # scope.set('save/directory', 'C:\\Users\\JakubMnich\\Documents\\Zurich Instruments\\LabOne\\WebServer')
        self.DAQ.setInt(f'/{self.deviceID}/scopes/0/time', int(samplingFreqIndex))
        self.DAQ.setInt(f'/{self.deviceID}/scopes/0/length', int(sampleLength))
        self.DAQ.setInt(f'/{self.deviceID}/scopes/0/channels/1/inputselect', 8) # '8' - Ref 0
        self.DAQ.setInt(f'/{self.deviceID}/sigins/0/ac', 1)
        self.DAQ.setInt(f'/{self.deviceID}/scopes/0/single', 1)
        self.DAQ.setInt(f'/{self.deviceID}/scopes/0/channel', 3) # '3' - both channels active

        # configure the trigger
        if triggerEnabled:
            self.DAQ.setDouble(f'/{self.deviceID}/scopes/0/trigdelay', triggerDelay / 1000.0) # convert from [ms] to [s]
            self.DAQ.setDouble(f'/{self.deviceID}/scopes/0/triglevel', triggerLevel / 1000.0) # convert from [mV] to [V]
            self.DAQ.setDouble(f'/{self.deviceID}/scopes/0/trighysteresis/absolute', triggerHysteresis / 1000.0) # as above
            self.DAQ.setInt(f'/{self.deviceID}/scopes/0/trigholdoffmode', 0) # holdoff mode: time
            self.DAQ.setDouble(f'/{self.deviceID}/scopes/0/trigholdoff', 0.5) # set holdoff time [s]
            self.DAQ.setInt(f'/{self.deviceID}/scopes/0/trigenable', 1)

        self.Scope.subscribe(f'/{self.deviceID}/scopes/0/wave')

        # force global synchronization between the device and the data server
        self.DAQ.sync()

    def measureData(self):

        startTime = datetime.now()
        expectedMeasDuration = (self.currentMeasurementPointsCount / self.currentMeasurementFrequency) + 1.0
        print(f"Expected measurement duration: {expectedMeasDuration}s")
        status = "ok"

        try:
            self.Scope.execute()
            self.DAQ.setInt(f'/{self.deviceID}/scopes/0/enable', 1)
            self.DAQ.sync()
            result = None
            # perform acquisition and terminate when done or when a timeout occurs
            while  self.Scope.progress() < 1.0 and not self.Scope.finished():
                if (datetime.now() - startTime).total_seconds() > expectedMeasDuration:
                    status = "acquisition timeout"
                    break

                time.sleep(0.5)

            self.DAQ.setInt(f'/{self.deviceID}/scopes/0/enable', 0)
            result = self.Scope.read()

            # dig the data vectors out of the confusing maze dumped by the MFLI
            self.lastInterferogramData = \
                result[f'{self.deviceID}']['scopes']['0']['wave'][0][0]['wave'][0]

            self.lastReferenceData = \
                result[f'{self.deviceID}']['scopes']['0']['wave'][0][0]['wave'][1]

        except:
            self.lastReferenceData = None
            self.lastInterferogramData = None
            print(f"MFLI acquisition failed")
            status = "fail"

        finally:
            # finish gracefully regardless of the measurement results to prevent random crashes
            self.Scope.finish()
            return status




