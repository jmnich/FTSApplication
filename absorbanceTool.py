import os
import customtkinter as ctk
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sys
from tkinter.filedialog import asksaveasfilename
from tkinter import filedialog

class AbsorbanceTool:

    def __init__(self, root):
        # important fields
        self.referenceSpectrumAxisNameX = None
        self.referenceSpectrumAxisNameY = None
        self.referenceSpectrumAxisX = None
        self.referenceSpectrumAxisY = None

        self.sampleSpectrumAxisNameX = None
        self.sampleSpectrumAxisNameY = None
        self.sampleSpectrumAxisX = None
        self.sampleSpectrumAxisY = None

        self.absorbanceSpectrumAxisNameX = None
        self.absorbanceSpectrumAxisNameY = None
        self.absorbanceSpectrumAxisX = None
        self.absorbanceSpectrumAxisY = None

        # build GUI
        ctk.set_appearance_mode("dark")
        self.absorbanceRoot = ctk.CTkToplevel(root)
        self.absorbanceRoot.geometry("1200x800")
        self.absorbanceRoot.minsize(width=1200, height=800)
        self.absorbanceRoot.title("Absorbance tool")
        self.absorbanceRoot.iconbitmap(default='icon.ico')
        self.absorbanceRoot.resizable(True, True)

        self.backgroundGray = "#242424"

        self.referenceSpectrumX = None
        self.referenceSpectrumY = None
        self.sampleSpectrumX = None
        self.sampleSpectrumY = None
        self.absorbanceSpectrumX = None
        self.absorbanceSpectrumY = None


        # build GUI
        self.screen_geometry = self.absorbanceRoot.winfo_geometry()
        scr_width = int(self.screen_geometry.split('x')[0])

        if scr_width > 1920:
            menu_col_width = 250
        else:
            menu_col_width = 200

        self.absorbanceRoot.columnconfigure(0, weight=1, minsize=menu_col_width)
        self.absorbanceRoot.columnconfigure(1, weight=4)

        self.absorbanceRoot.rowconfigure(0, weight=1)
        self.absorbanceRoot.rowconfigure(1, weight=1)
        self.absorbanceRoot.rowconfigure(2, weight=1)

        # create plot frames
        self.frameReferencePlot = ctk.CTkFrame(master=self.absorbanceRoot,
                                         fg_color="darkblue")

        self.frameReferencePlot.grid(row=0, column=1, padx=(5, 5), pady=0)#, sticky="N")

        self.frameSamplePlot = ctk.CTkFrame(master=self.absorbanceRoot,
                                            fg_color="darkblue")
        # self.frame.place(relx=0.33, rely=0.025)
        self.frameSamplePlot.grid(row=1, column=1, padx=(5, 5), pady=0)#, sticky="N")

        self.frameAbsorbancePlot = ctk.CTkFrame(master=self.absorbanceRoot,
                                            fg_color="darkblue")
        # self.frame.place(relx=0.33, rely=0.025)
        self.frameAbsorbancePlot.grid(row=2, column=1, padx=(5, 5), pady=0)#, sticky="N")


        # create button frames
        self.frameButtonsReference = ctk.CTkFrame(master=self.absorbanceRoot,
                                               height=60,
                                               width=120,
                                               fg_color="dimgrey",
                                               corner_radius=10)
        self.frameButtonsReference.grid(row=0, column=0, sticky="NSEW", padx=5, pady=5)

        self.frameButtonsSample = ctk.CTkFrame(master=self.absorbanceRoot,
                                               height=60,
                                               width=120,
                                               fg_color="dimgrey",
                                               corner_radius=10)
        self.frameButtonsSample.grid(row=1, column=0, sticky="NSEW", padx=5, pady=5)

        self.frameButtonsAbsorbance = ctk.CTkFrame(master=self.absorbanceRoot,
                                               height=60,
                                               width=120,
                                               fg_color="dimgrey",
                                               corner_radius=10)
        self.frameButtonsAbsorbance.grid(row=2, column=0, sticky="NSEW", padx=5, pady=5)

        # reference spectrum interface
        # ==============================================================================================================
        self.frameButtonsReference.columnconfigure(0, weight=1)
        self.frameButtonsReference.rowconfigure(0, weight=1)
        self.frameButtonsReference.rowconfigure(1, weight=1)
        self.frameButtonsReference.rowconfigure(2, weight=1)
        self.frameButtonsReference.rowconfigure(3, weight=1)

        self.referenceLabel = ctk.CTkLabel(master=self.frameButtonsReference,
                                        text="Reference",
                                        font=ctk.CTkFont(size=16, weight="bold"))
        self.referenceLabel.grid(row=0, column=0, sticky="NSEW", padx=5, pady=5)

        self.buttonLoadRefLast = ctk.CTkButton(master=self.frameButtonsReference,
                                            text="Last\nspectrum",
                                            width=120,
                                            height=80,
                                            corner_radius=10,
                                            command=self.onCmdLoadReferenceSpectrumLast)
        self.buttonLoadRefLast.grid(row=1, column=0, sticky="N", padx=5, pady=5)

        self.buttonLoadRefAvg = ctk.CTkButton(master=self.frameButtonsReference,
                                            text="Average\nspectrum",
                                            width=120,
                                            height=80,
                                            corner_radius=10,
                                            command=self.onCmdLoadReferenceSpectrumAverage)
        self.buttonLoadRefAvg.grid(row=2, column=0, sticky="N", padx=5, pady=5)

        self.buttonLoadRefFile = ctk.CTkButton(master=self.frameButtonsReference,
                                            text="Spectrum\nfrom file",
                                            width=120,
                                            height=80,
                                            corner_radius=10,
                                            command=self.onCmdLoadReferenceSpectrumFromFile)
        self.buttonLoadRefFile.grid(row=3, column=0, sticky="N", padx=5, pady=5)

        # sample spectrum interface
        # ==============================================================================================================
        self.frameButtonsSample.columnconfigure(0, weight=1)
        self.frameButtonsSample.rowconfigure(0, weight=1)
        self.frameButtonsSample.rowconfigure(1, weight=1)
        self.frameButtonsSample.rowconfigure(2, weight=1)
        self.frameButtonsSample.rowconfigure(3, weight=1)

        self.sampleLabel = ctk.CTkLabel(master=self.frameButtonsSample,
                                        text="Sample",
                                        font=ctk.CTkFont(size=16, weight="bold"))
        self.sampleLabel.grid(row=0, column=0, sticky="NSEW", padx=5, pady=5)

        self.buttonLoadSmpLast = ctk.CTkButton(master=self.frameButtonsSample,
                                            text="Last\nspectrum",
                                            width=120,
                                            height=80,
                                            corner_radius=10,
                                            command=self.onCmdLoadSampleSpectrumLast)
        self.buttonLoadSmpLast.grid(row=1, column=0, sticky="N", padx=5, pady=5)

        self.buttonLoadSmpAvg = ctk.CTkButton(master=self.frameButtonsSample,
                                            text="Average\nspectrum",
                                            width=120,
                                            height=80,
                                            corner_radius=10,
                                            command=self.onCmdLoadSampleSpectrumAverage)
        self.buttonLoadSmpAvg.grid(row=2, column=0, sticky="N", padx=5, pady=5)

        self.buttonLoadSmpFile = ctk.CTkButton(master=self.frameButtonsSample,
                                            text="Spectrum\nfrom file",
                                            width=120,
                                            height=80,
                                            corner_radius=10,
                                            command=self.onCmdLoadSampleSpectrumFromFile)
        self.buttonLoadSmpFile.grid(row=3, column=0, sticky="N", padx=5, pady=5)

        # absorbance spectrum interface
        self.frameButtonsAbsorbance.columnconfigure(0, weight=1)
        self.frameButtonsAbsorbance.rowconfigure(0, weight=1)

        self.settingsTabs = ctk.CTkTabview(master=self.frameButtonsAbsorbance)
        self.settingsTabs.grid(column=0, row=0, padx=3)
        self.settingsTabs.add("Settings")
        self.settingsTabs.add("Export")

        # configure settings 'SETTINGS' tab
        # ==============================================================================================================
        self.settingsTabs.tab("Settings").rowconfigure(0, weight=1)
        self.settingsTabs.tab("Settings").rowconfigure(1, weight=1)

        # configure settings 'EXPORT' tab
        # ==============================================================================================================
        self.settingsTabs.tab("Export").rowconfigure(0, weight=1)
        self.settingsTabs.tab("Export").rowconfigure(1, weight=1)
        self.settingsTabs.tab("Export").rowconfigure(2, weight=1)
        self.settingsTabs.tab("Export").rowconfigure(3, weight=1)

        self.saveAbsorbanceToCSVButton = ctk.CTkButton(master=self.settingsTabs.tab("Export"),
                                            text="Save absorbance\nto .CSV",
                                            width=120,
                                            height=80,
                                            corner_radius=10,
                                            command=None)
        self.saveAbsorbanceToCSVButton.grid(row=1, column=0, sticky="N", padx=5, pady=5)

        # create plots
        # ==============================================================================================================
        plt.style.use('dark_background')
        self.figRef, self.axRef = plt.subplots()
        self.figRef.suptitle("Reference spectrum")
        self.axRef.set_xlabel('Wavelength [\u03BCm]')
        self.axRef.set_ylabel('[a.u.]')
        self.figRef.set_facecolor(self.backgroundGray)
        self.figRef.set_size_inches(100, 100)
        self.figRef.subplots_adjust(left=0.1, right=0.99, bottom=0.1, top=0.97, wspace=0, hspace=0)
        self.figRef.set_tight_layout(True)
        self.axRef.set_yscale("log")
        self.canvasRefPlot = FigureCanvasTkAgg(self.figRef, master=self.frameReferencePlot)
        self.canvasRefPlot.get_tk_widget().pack(side='right', fill='both', expand=True)
        self.canvasRefPlot.draw()

        self.figSmp, self.axSmp = plt.subplots()
        self.figSmp.suptitle("Sample spectrum")
        self.axSmp.set_xlabel('Wavelength [\u03BCm]')
        self.axSmp.set_ylabel('[a.u.]')
        self.figSmp.set_facecolor(self.backgroundGray)
        self.figSmp.set_size_inches(100, 100)
        self.figSmp.subplots_adjust(left=0.1, right=0.99, bottom=0.1, top=0.97, wspace=0, hspace=0)
        self.figSmp.set_tight_layout(True)
        self.axSmp.set_yscale("log")
        self.canvasSmpPlot = FigureCanvasTkAgg(self.figSmp, master=self.frameSamplePlot)
        self.canvasSmpPlot.get_tk_widget().pack(side='right', fill='both', expand=True)
        self.canvasSmpPlot.draw()

        self.figAbs, self.axAbs = plt.subplots()
        self.figAbs.suptitle("Absorbance spectrum")
        self.axAbs.set_xlabel('Wavelength [\u03BCm]')
        self.axAbs.set_ylabel('[a.u.]')
        self.figAbs.set_facecolor(self.backgroundGray)
        self.figAbs.set_size_inches(100, 100)
        self.figAbs.subplots_adjust(left=0.1, right=0.99, bottom=0.1, top=0.97, wspace=0, hspace=0)
        self.figAbs.set_tight_layout(True)
        self.axAbs.set_yscale("log")
        self.canvasAbsPlot = FigureCanvasTkAgg(self.figAbs, master=self.frameAbsorbancePlot)
        self.canvasAbsPlot.get_tk_widget().pack(side='right', fill='both', expand=True)
        self.canvasAbsPlot.draw()

        self.absorbanceRoot.update()
        self.absorbanceRoot.after(1, lambda: self.absorbanceRoot.focus_force())
        self.absorbanceRoot.update()


    def onCmdLoadReferenceSpectrumFromFile(self):

        (self.referenceSpectrumAxisNameX, self.referenceSpectrumAxisNameY,
         self.referenceSpectrumAxisX, self.referenceSpectrumAxisY) = self.loadSpectrumFromCSV()

        self.updatePlots()

    def onCmdLoadReferenceSpectrumLast(self):
        print("TODO")

    def onCmdLoadReferenceSpectrumAverage(self):
        print("TODO")

    def onCmdLoadSampleSpectrumFromFile(self):

        (self.sampleSpectrumAxisNameX, self.sampleSpectrumAxisNameY,
         self.sampleSpectrumAxisX, self.sampleSpectrumAxisY) = self.loadSpectrumFromCSV()

        self.updatePlots()

    def onCmdLoadSampleSpectrumLast(self):
        print("TODO")

    def onCmdLoadSampleSpectrumAverage(self):
        print("TODO")

    def updatePlots(self):
        print("TODO")


    def loadSpectrumFromCSV(self):
        types = [(
        ('.CSV spectrum', '*.csv')
        )]

        filename = filedialog.askopenfilename(title="Open .CSV spectrum file", filetypes=types)

        data = np.genfromtxt(filename, delimiter=",", dtype=float, names=True)

        axisNameX = data.dtype.names[0].split('_')[0] + " [" + data.dtype.names[0].split('_')[1] + "]"
        axisNameY = data.dtype.names[1].split('_')[0] + " [" + data.dtype.names[1].split('_')[1] + "]"

        npAxisX = np.zeros(len(data))
        npAxisY = np.zeros(len(data))

        for i in range(0, len(data)):
            npAxisX[i] = data[i][0]
            npAxisY[i] = data[i][1]

        return axisNameX, axisNameY, npAxisX, npAxisY
