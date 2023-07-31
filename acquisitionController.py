class AcquisitionController:
    def __init__(self):
        print("Acquisition controller initializing...")

    def isReadyToMeasure(self):
        return False

    def startAcquisition(self, spectraCount):
        print("Starting acquisition...")
