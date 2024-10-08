import json
import os.path

def isSettingsFileAvailable():
    path = './app_settings.txt'
    return os.path.isfile(path)

def saveSettingsToFile(settings):
    # settings
    with open('./app_settings.txt', "w") as fp:
        json.dump(settings, fp)  # encode dict into JSON

def readSettingsFromFile():
    with open('./app_settings.txt', "r") as fp:
        # Load the dictionary from the file
        settings_dict = json.load(fp)
    return settings_dict

def validateAndFixSettings(settings):

    if len(getDefaultSettings().keys()) > len(settings.keys()):

        for key in getDefaultSettings().keys():
            if not (key in settings):
                settings[key] = getDefaultSettings()[key]

    elif len(getDefaultSettings().keys()) > len(settings.keys()):
        settings = getDefaultSettings()

def getDefaultSettings():

    defaultSettings = {
        "delayLineMinimumSpeed":"1",
        "delayLineMaximumSpeed":"50",
        "delayLineSpeedSliderTicks":"49",
        "delayLineConfiguredScanSpeed": "5",

        "delayLineCOMPort": "COM4",

        "delayLineConfiguredScanStart":"149000",
        "delayLineConfiguredScanLength": "5000",
        "delayLineMinimalScanLength":"1000",

        "mfliSelectedFrequencyIndex":"7",
        "mfliDeviceID":"dev6285",

        "plotSpectrumXRangeMin":"1",
        "plotSpectrumXRangeMax": "30",
        "plotSpectrumYRangeMin": "-80",
        "plotSpectrumYRangeMax": "-30",

        "plotEngine":"matplotlib",

        "averagingCount":"5",
        
        "saveRawData":"False",
        "saveDataToMAT":"False",

        "absorbanceToolRangeXMin":"1.0",
        "absorbanceToolRangeXMax": "30.0",
        "absorbanceToolRangeYMin": "-80",
        "absorbanceToolRangeYMax": "-30",
        "absorbanceToolAbsRangeYMin": "0",
        "absorbanceToolAbsRangeYMax": "2.0",

        "triggerModeEnabled": "False",
        "triggerLevel": "100.0",
        "triggerReference": "50.0",
        "triggerHysteresis": "10.0",

        "adjustmentCenterPoint" : "75000.0",
        "adjustmentAmplitude" : "5000.0",
        "adjustmentPeriod" : "2000.0",

        "apodizationWindow" : "boxcar"
    }

    return  defaultSettings