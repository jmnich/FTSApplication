import time
import zhinst.core
import zhinst.utils


class MFLIDriver:
    def __init__(self, devID):
        print("MFLI driver initializing...")
        self.DAQ = None
        self.Scope = None
        # self.DAQModule = None
        self.isConnected = False
        self.lastData = []
        self.deviceID = devID.replace(' ', '').replace('\t', '').replace('\n', '').replace('\r', '')
        self.tryConnect(self.deviceID)

    def tryConnect(self, deviceID):

        try:
            device_id: str = deviceID
            server_host: str = "localhost"
            server_port: int = 8004

            (self.DAQ, device, props) = zhinst.utils.create_api_session(
                device_id, 6, server_host=server_host, server_port=server_port
            )

            # restore the base configuration
            zhinst.utils.disable_everything(self.DAQ, self.deviceID)

            # self.DAQModule = self.DAQ.dataAcquisitionModule()

            # self.DAQ = zhinst.core.ziDAQServer('localhost', 8004, 6)
            # self.DAQModule = self.DAQ.dataAcquisitionModule()

        except Exception as e:
            print(f"Connection failed to MFLI device")
            print(f"Error message: \n{str(e)}")
            self.isConnected = False
            return False

        print(f"MFLI device connected successfully")
        self.isConnected = True
        return True

    def configureForMeasurement(self):
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
        self.DAQ.setInt(f'/{self.deviceID}/scopes/0/time', 9)
        self.DAQ.setInt(f'/{self.deviceID}/scopes/0/length', 1000)
        self.DAQ.setInt(f'/{self.deviceID}/scopes/0/channels/1/inputselect', 8)
        self.DAQ.setInt(f'/{self.deviceID}/sigins/0/ac', 1)
        self.DAQ.setInt(f'/{self.deviceID}/scopes/0/single', 1)
        self.Scope.subscribe(f'/{self.deviceID}/scopes/0/wave')

        # force global synchronization between the device and the data server
        self.DAQ.sync()

    def measureData(self):
        self.Scope.execute()
        self.DAQ.setInt(f'/{self.deviceID}/scopes/0/enable', 1)
        result = 0
        while self.Scope.progress() < 1.0 and not self.Scope.finished():
            time.sleep(0.1)
            print(f"Progress {float(self.Scope.progress()) * 100:.2f} %\r")

        result = self.Scope.read()
        waveCh0 = result[f'{self.deviceID}']['scopes']['0']['wave'][0][0]['wave'][0]
        self.lastData = waveCh0
        self.Scope.finish()
