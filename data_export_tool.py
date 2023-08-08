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
def exportSpectrumAsCSV(spectrumX, spectrumY):

    if len(spectrumX) == len(spectrumY) and len(spectrumX) != 0:
        initial_file_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_spectrum.csv")

        f = asksaveasfilename(initialfile=initial_file_name,
                              defaultextension=".csv", filetypes=[("CSV", "*.csv"), ("CSV Files", "*.csv")])

        np.savetxt(f, np.column_stack((spectrumX, spectrumY)),
                   fmt='%.6e', delimiter=',', newline='\n', header='Wavelength [um],Intensity [a.u.]',
                   footer='', comments='', encoding=None)

        logging.info(f"Spectrum saved as a .CSV file: " + str(f))

    else:
        logging.info(f"Failed to save spectrum as a .CSV file")

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

        np.savetxt(pathToSpectrumCSV, np.column_stack((spectrumX, spectrumY)),
                   fmt='%.6e', delimiter=',', newline='\n', header='Wavelength [um],Intensity [a.u.]',
                   footer='', comments='', encoding=None)

        mpl.rcParams.update(mpl.rcParamsDefault)
        plt.figure(figsize=(12.5, 7.5))
        plt.tight_layout()
        plt.locator_params(nbins=15)
        plt.rc('xtick', labelsize=18)
        plt.rc('ytick', labelsize=18)
        plt.title("Spectrum", fontsize=20)
        plt.xlabel("Wavelength [\u03BCm]", fontsize=20)
        plt.ylabel("Intensity [a.u.]", fontsize=20)
        plt.plot(spectrumX, spectrumY)
        plt.yscale('log')
        plt.xlim((float(settings["plotSpectrumXRangeMin"]), float(settings["plotSpectrumXRangeMax"])))
        plt.ylim((float(settings["plotSpectrumYRangeMin"]), float(settings["plotSpectrumYRangeMax"])))
        plt.grid(alpha=0.3)
        plt.savefig(pathToSpectrumPicture)

    if (interferogramX is not None and interferogramY is not None and
            len(interferogramX) == len(interferogramY) and len(interferogramX) != 0):

        interferogramDataValid = True

        np.savetxt(pathToInterferogramCSV, np.column_stack((interferogramX, interferogramY)),
                   fmt='%.6e', delimiter=',', newline='\n', header='Position [um],Voltage [V]',
                   footer='', comments='', encoding=None)

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

    if (referenceSignalRaw is not None and interferogramRaw is not None and
            len(referenceSignalRaw) == len(interferogramRaw) and len(interferogramRaw) != 0):

        rawDataValid = True

        np.savetxt(pathToRawData, np.column_stack((referenceSignalRaw, interferogramRaw)),
                   fmt='%.6e', delimiter=',', newline='\n', header='Reference detector signal [V],Main detector signal [V]',
                   footer='', comments='', encoding=None)


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