import customtkinter as ctk
from tkinter.filedialog import asksaveasfilename
from tkinter import filedialog
from datetime import datetime
import logging
import numpy as np
import os
import matplotlib as mpl
import matplotlib.pyplot as plt
import scipy
import math

# from serial.serialjava import comm

config_save_raw_data = True
config_save_corrected_interferograms = False
config_save_individual_spectra = False

def find_nearest(array,value):
    idx = np.searchsorted(array, value, side="left")
    if idx > 0 and (idx == len(array) or math.fabs(value - array[idx-1]) < math.fabs(value - array[idx])):
        return array[idx-1]
    else:
        return array[idx]

def save_to_csv_2columns(filePath, column1Header, column2Header, column1Data, column2Data):

    if len(column1Data) != len(column2Data):
        raise ValueError("Data columns have different sizes!")
    else:
        header = f"{column1Header},{column2Header}\n"
        dataLines = [header]

        for i in range(0, len(column1Data)):
            dataLines.append("%f,%f\n" % (column1Data[i], column2Data[i]))

        with open(filePath, 'a') as csvfile:
            csvfile.writelines(dataLines)


def exportAllDataAbsorbance(refX, refY, sampleX, sampleY, absX, absY,
                            absXTitle, absYTitle, absTitle,
                            rngXMin, rngXMax, rngYMin, rngYMax, rngAbsYMin, rngAbsYMax):

    direcotry_selected = filedialog.askdirectory()
    packageNameDialog = ctk.CTkInputDialog(text="Type in a short name for the data package", title="Name your results")
    selectedName = packageNameDialog.get_input().replace(' ', '').replace(
                                    '\t', '').replace('\n', '').replace('\r', '')

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    if len(selectedName) > 0:
        savePackageRootName = timestamp + "_" + selectedName
    else:
        selectedName = "results"
        savePackageRootName = timestamp + "_" + selectedName

    savePackageRootPath = os.path.join(direcotry_selected, savePackageRootName)
    os.mkdir(savePackageRootPath)

    pathToAbsorptionCSV = os.path.join(savePackageRootPath, "absorption.csv")
    pathToReferenceCSV = os.path.join(savePackageRootPath, "reference.csv")
    pathToSampleCSV = os.path.join(savePackageRootPath, "sample.csv")

    pathToAbsorptionPicture = os.path.join(savePackageRootPath, "absorption.png")
    pathToBothPicture = os.path.join(savePackageRootPath, "ref_and_sample.png")

    # save absorption CSV and image
    if (absX is not None and absY is not None and
            len(absX) == len(absY) and len(absX) != 0):

        csvFriendlyXTitle = absXTitle.replace("\u03BC", "u")

        save_to_csv_2columns(pathToAbsorptionCSV,
                             csvFriendlyXTitle, absYTitle,
                             absX, absY)

        mpl.rcParams.update(mpl.rcParamsDefault)
        plt.figure(figsize=(12.5, 7.5))
        plt.tight_layout()
        plt.locator_params(nbins=15)
        plt.rc('xtick', labelsize=18)
        plt.rc('ytick', labelsize=18)
        plt.title(f"{absTitle}", fontsize=20)
        plt.xlabel(f"{absXTitle}", fontsize=20)
        plt.ylabel(f"{absYTitle}", fontsize=20)
        plt.plot(absX, absY)
        plt.xlim((float(rngXMin), float(rngXMax)))
        plt.ylim((float(rngAbsYMin), float(rngAbsYMax)))
        plt.grid(alpha=0.3)
        plt.savefig(pathToAbsorptionPicture)
        plt.close()


    # save reference CSV
    refValid = False

    if (refX is not None and refY is not None and
            len(refX) == len(refY) and len(refX) != 0):

        refValid = True

        save_to_csv_2columns(pathToReferenceCSV,
                             "Wavelength [um]", "Intensity [dBm]",
                             refX, refY)

    # save sample CSV
    sampleValid = False

    if (sampleX is not None and sampleY is not None and
            len(sampleX) == len(sampleY) and len(sampleX) != 0):

        sampleValid = True

        save_to_csv_2columns(pathToSampleCSV,
                             "Wavelength [um]", "Intensity [dBm]",
                             sampleX, sampleY)

    # make a picture for reference and sample
    if sampleValid and refValid:

        mpl.rcParams.update(mpl.rcParamsDefault)
        plt.figure(figsize=(12.5, 7.5))
        plt.tight_layout()
        plt.locator_params(nbins=15)
        plt.rc('xtick', labelsize=18)
        plt.rc('ytick', labelsize=18)
        plt.title(f"Source spectra", fontsize=20)
        plt.xlabel("Wavelength [\u03BCm]", fontsize=20)
        plt.ylabel("Intensity [dBm]", fontsize=20)
        plt.plot(refX, refY, label="Reference")
        plt.plot(sampleX, sampleY, label="Sample")
        plt.legend()
        plt.xlim((float(rngXMin), float(rngXMax)))
        plt.ylim((float(rngYMin), float(rngYMax)))
        plt.grid(alpha=0.3)
        plt.savefig(pathToBothPicture)
        plt.close()

def exportAbsorbanceAsCSV(absorbanceX, absorbanceY, axisNameX, axisNameY):
    if len(absorbanceX) == len(absorbanceY) and len(absorbanceX) != 0:
        initial_file_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_absorption.csv")

        f = asksaveasfilename(initialfile=initial_file_name,
                              defaultextension=".csv", filetypes=[("CSV", "*.csv"), ("CSV Files", "*.csv")])

        save_to_csv_2columns(f,
                             axisNameX, axisNameY,
                             absorbanceX, absorbanceY)

        logging.info(f"Absorption plot saved as a .CSV file: " + str(f))

    else:
        logging.info(f"Failed to save absorption plot as a .CSV file")

def exportSpectrumAsCSV(spectrumX, spectrumY):

    if len(spectrumX) == len(spectrumY) and len(spectrumX) != 0:
        initial_file_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_spectrum.csv")

        f = asksaveasfilename(initialfile=initial_file_name,
                              defaultextension=".csv", filetypes=[("CSV", "*.csv"), ("CSV Files", "*.csv")])

        # save to .csv
        save_to_csv_2columns(f,
                             "Wavelength [um]", "Intensity [dBm]",
                             spectrumX, spectrumY)

        logging.info(f"Spectrum saved as a .CSV file: " + str(f))

    else:
        logging.info(f"Failed to save spectrum as a .CSV file")

def exportAllDataMultipleMeasurements(averageSpectrumX, averageSpectrumY,
                                      rawSpectraX, rawSpectraY,
                                      correctedInterferogramsX, correctedInterferogramsY,
                                      interferogramsRaw, referenceSignalsRaw, settings, comments):

    direcotry_selected = filedialog.askdirectory()
    packageNameDialog = ctk.CTkInputDialog(text="Type in a short name for the data package", title="Name your results")
    selectedName = packageNameDialog.get_input().replace(' ', '').replace(
                                    '\t', '').replace('\n', '').replace('\r', '')

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    if len(selectedName) > 0:
        savePackageRootName = timestamp + "_" + selectedName
    else:
        selectedName = "results"
        savePackageRootName = timestamp + "_" + selectedName

    savePackageRootPath = os.path.join(direcotry_selected, savePackageRootName)
    os.mkdir(savePackageRootPath)

    pathToSpectrumCSV = os.path.join(savePackageRootPath, "spectrum.csv")
    pathToInterferogramCSV = os.path.join(savePackageRootPath, "interferogram.csv")
    pathToSpectrumPicture = os.path.join(savePackageRootPath, "spectrum.png")
    pathToInterferogramPicture = os.path.join(savePackageRootPath, "interferogram.png")
    pathToComments = os.path.join(savePackageRootPath, "comments.txt")

    pathToMatlabSubDirectory = os.path.join(savePackageRootPath, "matlab")

    if settings["saveDataToMAT"] == 'True':
        saveToMATFlag = True
    else:
        saveToMATFlag = False

    if settings["saveRawData"] == 'True':
        saveRawData = True
    else:
        saveRawData = False

    if saveToMATFlag:
        os.mkdir(pathToMatlabSubDirectory)

    pathToMeasurementInfo = os.path.join(savePackageRootPath, "measurementInfo.txt")
    pathToRawSpectraDirectory = os.path.join(savePackageRootPath, "raw_spectra")
    pathToCorrectedInterferogramsDirectory = os.path.join(savePackageRootPath, "corrected_interferograms")
    pathToRawDataDirectory = os.path.join(savePackageRootPath, "raw_data")

    if saveRawData:
        if config_save_individual_spectra:
            os.mkdir(pathToRawSpectraDirectory)

        if config_save_corrected_interferograms:
            os.mkdir(pathToCorrectedInterferogramsDirectory)

        if config_save_raw_data:
            os.mkdir(pathToRawDataDirectory)

    averageSpectrumDataValid = False
    rawSpectraDataValid = False
    interferogramDataValid = False
    rawDataValid = False

    # save average spectrum .CSV and image
    if (averageSpectrumX is not None and averageSpectrumY is not None and
            len(averageSpectrumX) == len(averageSpectrumY) and len(averageSpectrumX) != 0):

        averageSpectrumDataValid = True

        # save to .csv
        save_to_csv_2columns(pathToSpectrumCSV,
                             "Wavelength [um]", "Intensity [dBm]",
                             averageSpectrumX, averageSpectrumY)

        mpl.rcParams.update(mpl.rcParamsDefault)
        plt.figure(figsize=(12.5, 7.5))
        plt.tight_layout()
        plt.locator_params(nbins=15)
        plt.rc('xtick', labelsize=18)
        plt.rc('ytick', labelsize=18)
        plt.title("Spectrum", fontsize=20)
        plt.xlabel("Wavelength [\u03BCm]", fontsize=20)
        plt.ylabel("Intensity [dBm]", fontsize=20)
        plt.plot(averageSpectrumX, averageSpectrumY)
        # plt.yscale('log')
        plt.xlim((float(settings["plotSpectrumXRangeMin"]), float(settings["plotSpectrumXRangeMax"])))
        plt.ylim((float(settings["plotSpectrumYRangeMin"]), float(settings["plotSpectrumYRangeMax"])))
        plt.grid(alpha=0.3)
        plt.savefig(pathToSpectrumPicture)
        plt.close()

    # save example interferogram .CSV and image
    if (correctedInterferogramsX[0] is not None and correctedInterferogramsY[0] is not None and
            len(correctedInterferogramsX[0]) == len(correctedInterferogramsY[0]) and
            len(correctedInterferogramsX[0]) != 0):

        # save to .csv
        save_to_csv_2columns(pathToInterferogramCSV,
                             "Position [um]", "Voltage [V]",
                             correctedInterferogramsX[0], correctedInterferogramsY[0])

        mpl.rcParams.update(mpl.rcParamsDefault)
        plt.figure(figsize=(12.5, 7.5))
        plt.tight_layout()
        plt.locator_params(nbins=15)
        plt.rc('xtick', labelsize=18)
        plt.rc('ytick', labelsize=18)
        plt.title("Interferogram no. 0", fontsize=20)
        plt.xlabel("Position [\u03BCm]", fontsize=20)
        plt.ylabel("Detector voltage [V]", fontsize=20)
        plt.plot(correctedInterferogramsX[0], correctedInterferogramsY[0])
        plt.xlim((min(correctedInterferogramsX[0]), max(correctedInterferogramsX[0])))
        plt.grid(alpha=0.3)
        plt.savefig(pathToInterferogramPicture)
        plt.close()

    # save raw spectra to .CSV files
    if (config_save_individual_spectra and
            saveRawData and
            len(rawSpectraX) == len(rawSpectraY) and
            len(rawSpectraX) != 0):

        rawSpectraDataValid = True

        for i in range(0, len(rawSpectraX)):
            pathToRawSpectrum = os.path.join(pathToRawSpectraDirectory, f"spectrum_{i}.csv")

            # save to .csv
            save_to_csv_2columns(pathToRawSpectrum,
                                 "Wavelength [um]", "Intensity [dBm]",
                                 rawSpectraX[i], rawSpectraY[i])

    # save corrected interferograms to .CSV files
    if (config_save_corrected_interferograms and
        saveRawData and
        len(correctedInterferogramsX) == len(correctedInterferogramsY) and
        len(correctedInterferogramsX) != 0):

        interferogramDataValid = True

        for i in range(0, len(correctedInterferogramsX)):
            pathToRawInterferogram = os.path.join(pathToCorrectedInterferogramsDirectory, f"interferogram_{i}.csv")

            # save to .csv
            save_to_csv_2columns(pathToRawInterferogram,
                                 "Position [um]", "Voltage [V]",
                                 correctedInterferogramsX[i], correctedInterferogramsY[i])

    # save raw data to .CSV files
    if (config_save_raw_data and
        saveRawData and
        len(referenceSignalsRaw) == len(interferogramsRaw) and
        len(referenceSignalsRaw) != 0):

        rawDataValid = True

        for i in range(0, len(referenceSignalsRaw)):
            pathToRaw = os.path.join(pathToRawDataDirectory, f"raw_{i}.csv")

            # save to .csv
            save_to_csv_2columns(pathToRaw,
                                 "Reference detector [V]", "Primary detector [V]",
                                 referenceSignalsRaw[i], interferogramsRaw[i])

    # export everything as .mat files
    # .mat average spectrum
    if averageSpectrumDataValid and saveToMATFlag:
        pathToAverageSpectrumMat = os.path.join(pathToMatlabSubDirectory, f"spectrumAverage.mat")
        spectrum_structure = np.array([averageSpectrumX, averageSpectrumY], dtype=[('Wavelength', 'f'), ('Intensity', 'f')])
        scipy.io.savemat(pathToAverageSpectrumMat, {"Average spectrum":spectrum_structure})

    # .mat corrected interferograms
    if interferogramDataValid and saveRawData and saveToMATFlag:
        pathToCorrectedInterferogramsMat = os.path.join(pathToMatlabSubDirectory, f"correctedInterferograms.mat")
        mdic = {}

        for i in range(0, len(correctedInterferogramsX)):
            interferogram_struct = np.array([correctedInterferogramsX[i], correctedInterferogramsY[i]],
                                            dtype=[('Position', 'f'), ('Voltage', 'f')])

            mdic[f"interferogram_{i}"] = interferogram_struct

        scipy.io.savemat(pathToCorrectedInterferogramsMat, mdic)

    # .mat raw spectra
    if rawSpectraDataValid and saveRawData and saveToMATFlag:
        pathToRawSpectraMat = os.path.join(pathToMatlabSubDirectory, f"rawSpectra.mat")
        mdic = {}

        for i in range(0, len(rawSpectraX)):
            spectrum_struct = np.array([rawSpectraX[i], rawSpectraY[i]],
                                            dtype=[('Wavelength', 'f'), ('Intensity', 'f')])

            mdic[f"spectrum_{i}"] = spectrum_struct

        scipy.io.savemat(pathToRawSpectraMat, mdic)

    # .mat raw data
    if rawDataValid and saveRawData and saveToMATFlag:
        pathToRawDataMat = os.path.join(pathToMatlabSubDirectory, f"rawData.mat")
        mdic = {}

        for i in range(0, len(referenceSignalsRaw)):
            spectrum_struct = np.array([referenceSignalsRaw[i], interferogramsRaw[i]],
                                            dtype=[('Reference detector', 'f'), ('Primary detector', 'f')])

            mdic[f"raw_{i}"] = spectrum_struct

        scipy.io.savemat(pathToRawDataMat, mdic)

    # save measurement info and settings
    if settings is not None:
        with open(pathToMeasurementInfo, 'w') as f:

            f.write(f"instrument:Experimental THz FTS\n")
            f.write(f"data_type:Basic FTS spectrum\n")
            f.write(f"average_spectrum_data_included:{averageSpectrumDataValid}\n")
            f.write(f"raw_spectra_data_included:{rawSpectraDataValid}\n")
            f.write(f"interferogram_data_included:{interferogramDataValid}\n")
            f.write(f"raw_data_included:{rawDataValid}\n")
            f.write(f"name:{selectedName}\n")
            f.write(f"timestamp:{timestamp}\n")

            for key in settings.keys():
                f.write(f"{key}:{settings[key]}\n")

    if comments is not None:
        with open(pathToComments, 'w') as f:
            f.write(f"NAME: {selectedName}\n")
            f.write(f"TIMESTAMP: {timestamp}\n\n")
            f.write(comments)

    logging.info(f"Data export finished. Location: {savePackageRootPath}")


def exportAllData(spectrumX, spectrumY, interferogramX, interferogramY, interferogramRaw, referenceSignalRaw, settings):

    direcotry_selected = filedialog.askdirectory()
    packageNameDialog = ctk.CTkInputDialog(text="Type in a short name for the data package", title="Name your results")
    selectedName = packageNameDialog.get_input().replace(' ', '').replace(
                                    '\t', '').replace('\n', '').replace('\r', '')

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    if len(selectedName) > 0:
        savePackageRootName = timestamp + "_" + selectedName
    else:
        selectedName = "results"
        savePackageRootName = timestamp + "_" + selectedName

    savePackageRootPath = os.path.join(direcotry_selected, savePackageRootName)
    os.mkdir(savePackageRootPath)

    pathToSpectrumCSV = os.path.join(savePackageRootPath, "spectrum.csv")
    pathToInterferogramCSV = os.path.join(savePackageRootPath, "interferogram.csv")
    pathToRawData = os.path.join(savePackageRootPath, "raw_data.csv")
    pathToSpectrumPicture = os.path.join(savePackageRootPath, "spectrum.png")
    pathToInterferogramPicture = os.path.join(savePackageRootPath, "interferogram.png")
    pathToMatlabData = os.path.join(savePackageRootPath, "matlabData.mat")
    pathToMeasurementInfo = os.path.join(savePackageRootPath, "measurementInfo.txt")

    spectrumDataValid = False
    interferogramDataValid = False
    rawDataValid = False

    if (spectrumX is not None and spectrumY is not None and
            len(spectrumX) == len(spectrumY) and len(spectrumX) != 0):

        spectrumDataValid = True

        save_to_csv_2columns(pathToSpectrumCSV,
                             "Wavelength [um]", "Intensity [dBm]",
                             spectrumX, spectrumY)

        mpl.rcParams.update(mpl.rcParamsDefault)
        plt.figure(figsize=(12.5, 7.5))
        plt.tight_layout()
        plt.locator_params(nbins=15)
        plt.rc('xtick', labelsize=18)
        plt.rc('ytick', labelsize=18)
        plt.title("Spectrum", fontsize=20)
        plt.xlabel("Wavelength [\u03BCm]", fontsize=20)
        plt.ylabel("Intensity [dBm]", fontsize=20)
        plt.plot(spectrumX, spectrumY)
        # plt.yscale('log')
        plt.xlim((float(settings["plotSpectrumXRangeMin"]), float(settings["plotSpectrumXRangeMax"])))
        plt.ylim((float(settings["plotSpectrumYRangeMin"]), float(settings["plotSpectrumYRangeMax"])))
        plt.grid(alpha=0.3)
        plt.savefig(pathToSpectrumPicture)
        plt.close()

    if (interferogramX is not None and interferogramY is not None and
            len(interferogramX) == len(interferogramY) and len(interferogramX) != 0):

        interferogramDataValid = True

        save_to_csv_2columns(pathToInterferogramCSV,
                             "Position [um]", "Voltage [V]",
                             interferogramX, interferogramY)

        mpl.rcParams.update(mpl.rcParamsDefault)
        plt.figure(figsize=(12.5, 7.5))
        plt.tight_layout()
        plt.locator_params(nbins=15)
        plt.rc('xtick', labelsize=18)
        plt.rc('ytick', labelsize=18)
        plt.title("Interferogram", fontsize=20)
        plt.xlabel("Position [\u03BCm]", fontsize=20)
        plt.ylabel("Detector voltage [V]", fontsize=20)
        plt.plot(interferogramX, interferogramY)
        plt.xlim((min(interferogramX), max(interferogramX)))
        plt.grid(alpha=0.3)
        plt.savefig(pathToInterferogramPicture)
        plt.close()

    if (referenceSignalRaw is not None and interferogramRaw is not None and
            len(referenceSignalRaw) == len(interferogramRaw) and len(interferogramRaw) != 0):

        rawDataValid = True

        save_to_csv_2columns(pathToRawData,
                             "Reference detector signal [V]", "Main detector signal [V]",
                              referenceSignalRaw, interferogramRaw)

    if spectrumDataValid and interferogramDataValid and rawDataValid:
            spectrum_structure = np.array([spectrumX, spectrumY], dtype=[('Wavelength', 'f'), ('Intensity', 'f')])
            interferogramStructure = np.array([interferogramX, interferogramY], dtype=[('Position', 'f'), ('Voltage', 'f')])
            rawDataStructure = np.array([referenceSignalRaw, interferogramRaw], dtype=[('Reference detector', 'f'), ('Main detector', 'f')])

            scipy.io.savemat(pathToMatlabData, {'Spectrum' : spectrum_structure,
                                                'Interferogram' : interferogramStructure,
                                                'Raw' : rawDataStructure})

    if settings is not None:
        with open(pathToMeasurementInfo, 'w') as f:

            f.write(f"instrument:Experimental THz FTS\n")
            f.write(f"data_type:Basic FTS spectrum\n")
            f.write(f"spectrum_data_included:{spectrumDataValid}\n")
            f.write(f"interferogram_data_included:{interferogramDataValid}\n")
            f.write(f"raw_data_included:{rawDataValid}\n")
            f.write(f"name:{selectedName}\n")
            f.write(f"timestamp:{timestamp}\n")

            for key in settings.keys():
                f.write(f"{key}:{settings[key]}\n")

    logging.info(f"Data export finished. Location: {savePackageRootPath}")
