import time
import zhinst.core
import zhinst.utils


class MFLIDriver:
    def __init__(self, devID):
        print("MFLI driver initializing...")
        self.DAQ = None
        self.DAQModule = None
        self.isConnected = False
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

            self.DAQModule = self.DAQ.dataAcquisitionModule()

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
