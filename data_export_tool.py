import customtkinter as ctk
from tkinter.filedialog import asksaveasfilename
from tkinter import filedialog
from datetime import datetime
import logging
import numpy as np
import os
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

    if len(selectedName) > 0:
        savePackageRootName = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_") + selectedName
    else:
        savePackageRootName = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_result")

    savePackageRootPath = os.path.join(direcotry_selected, savePackageRootName)

    print(savePackageRootPath)
    # savePackageRootName = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_") + packageNameDialog.get_input()
        # savePackageRoot = os.path.join()
        #