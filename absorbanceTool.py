import os
import time

import customtkinter as ctk
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sys
from tkinter.filedialog import asksaveasfilename
from tkinter import filedialog
from tkinter import messagebox
import data_export_tool as DET

class AbsorbanceTool:

    def __init__(self, root, initialSettings):
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

        self.reference_loaded = False
        self.sample_loaded = False
        self.spectra_valid_for_absorbance_calculation = False

        # external methods for uploading data
        self.grabReferenceSpectrumDataLast = None
        self.grabReferenceSpectrumDataAverage = None
        self.grabSampleSpectrumDataLast = None
        self.grabSampleSpectrumDataAverage = None

        # external methods for handling settings
        self.grabApplicationSettings = None
        self.setApplicationSettings = None

        # plots' ranges
        self.plotsXMin = float(initialSettings["absorbanceToolRangeXMin"])
        self.plotsXMax = float(initialSettings["absorbanceToolRangeXMax"])
        self.plotsYMin = float(initialSettings["absorbanceToolRangeYMin"])
        self.plotsYMax = float(initialSettings["absorbanceToolRangeYMax"])
        self.plotsAbsYMin = float(initialSettings["absorbanceToolAbsRangeYMin"])
        self.plotsAbsYMax = float(initialSettings["absorbanceToolAbsRangeYMax"])

        # build GUI
        ctk.set_appearance_mode("dark")
        self.absorbanceRoot = ctk.CTk()
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
        self.settingsTabs.tab("Settings").rowconfigure(2, weight=1)
        self.settingsTabs.tab("Settings").rowconfigure(3, weight=1)
        self.settingsTabs.tab("Settings").rowconfigure(4, weight=1)
        self.settingsTabs.tab("Settings").rowconfigure(5, weight=1)

        self.settingsTabs.tab("Settings").columnconfigure(0, weight=1)
        self.settingsTabs.tab("Settings").columnconfigure(1, weight=1)

        self.xMinLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Settings"),
                                                    text="X\nmin [\u03BCm]",
                                                    font=ctk.CTkFont(size=12))
        self.xMinLabel.grid(row=0, column=0, sticky="E", padx=5, pady=1)

        self.xMinBox = ctk.CTkEntry(master=self.settingsTabs.tab("Settings"),
                                        width=80, height=30)
        self.xMinBox.insert(0, initialSettings["absorbanceToolRangeXMin"])
        self.xMinBox.grid(row=0, column=1, sticky="E", padx=5, pady=1)
        self.xMinBox.bind("<FocusOut>", self.onCmdUpdatePlotRanges)
        self.xMinBox.bind("<Return>", self.onCmdUpdatePlotRanges)

        self.xMaxLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Settings"),
                                                    text="X\nmax [\u03BCm]",
                                                    font=ctk.CTkFont(size=12))
        self.xMaxLabel.grid(row=1, column=0, sticky="E", padx=5, pady=1)

        self.xMaxBox = ctk.CTkEntry(master=self.settingsTabs.tab("Settings"),
                                        width=80, height=30)
        self.xMaxBox.insert(0, initialSettings["absorbanceToolRangeXMax"])
        self.xMaxBox.grid(row=1, column=1, sticky="E", padx=5, pady=1)
        self.xMaxBox.bind("<FocusOut>", self.onCmdUpdatePlotRanges)
        self.xMaxBox.bind("<Return>", self.onCmdUpdatePlotRanges)

        self.yMinLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Settings"),
                                                    text="Y\nmin",
                                                    font=ctk.CTkFont(size=12))
        self.yMinLabel.grid(row=2, column=0, sticky="E", padx=5, pady=1)

        self.yMinBox = ctk.CTkEntry(master=self.settingsTabs.tab("Settings"),
                                        width=80, height=30)
        self.yMinBox.insert(0, initialSettings["absorbanceToolRangeYMin"])
        self.yMinBox.grid(row=2, column=1, sticky="E", padx=5, pady=1)
        self.yMinBox.bind("<FocusOut>", self.onCmdUpdatePlotRanges)
        self.yMinBox.bind("<Return>", self.onCmdUpdatePlotRanges)

        self.yMaxLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Settings"),
                                                    text="Y\nmax",
                                                    font=ctk.CTkFont(size=12))
        self.yMaxLabel.grid(row=3, column=0, sticky="E", padx=5, pady=1)

        self.yMaxBox = ctk.CTkEntry(master=self.settingsTabs.tab("Settings"),
                                        width=80, height=30)
        self.yMaxBox.insert(0, initialSettings["absorbanceToolRangeYMax"])
        self.yMaxBox.grid(row=3, column=1, sticky="E", padx=5, pady=1)
        self.yMaxBox.bind("<FocusOut>", self.onCmdUpdatePlotRanges)
        self.yMaxBox.bind("<Return>", self.onCmdUpdatePlotRanges)

        self.yAbsMinLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Settings"),
                                                    text="Y abs\nmin",
                                                    font=ctk.CTkFont(size=12))
        self.yAbsMinLabel.grid(row=4, column=0, sticky="E", padx=5, pady=1)

        self.yAbsMinBox = ctk.CTkEntry(master=self.settingsTabs.tab("Settings"),
                                        width=80, height=30)
        self.yAbsMinBox.insert(0, initialSettings["absorbanceToolAbsRangeYMin"])
        self.yAbsMinBox.grid(row=4, column=1, sticky="E", padx=5, pady=1)
        self.yAbsMinBox.bind("<FocusOut>", self.onCmdUpdatePlotRanges)
        self.yAbsMinBox.bind("<Return>", self.onCmdUpdatePlotRanges)

        self.yAbsMaxLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Settings"),
                                                    text="Y abs\nmax",
                                                    font=ctk.CTkFont(size=12))
        self.yAbsMaxLabel.grid(row=5, column=0, sticky="E", padx=5, pady=1)

        self.yAbsMaxBox = ctk.CTkEntry(master=self.settingsTabs.tab("Settings"),
                                        width=80, height=30)
        self.yAbsMaxBox.insert(0, initialSettings["absorbanceToolAbsRangeYMax"])
        self.yAbsMaxBox.grid(row=5, column=1, sticky="E", padx=5, pady=1)
        self.yAbsMaxBox.bind("<FocusOut>", self.onCmdUpdatePlotRanges)
        self.yAbsMaxBox.bind("<Return>", self.onCmdUpdatePlotRanges)

        # configure settings 'EXPORT' tab
        # ==============================================================================================================
        self.settingsTabs.tab("Export").rowconfigure(0, weight=1)
        self.settingsTabs.tab("Export").rowconfigure(1, weight=1)
        self.settingsTabs.tab("Export").rowconfigure(2, weight=1)
        self.settingsTabs.tab("Export").rowconfigure(3, weight=1)

        self.settingsTabs.tab("Export").columnconfigure(0, weight=1)
        self.settingsTabs.tab("Export").columnconfigure(1, weight=1)

        self.saveAbsorbanceToCSVButton = ctk.CTkButton(master=self.settingsTabs.tab("Export"),
                                            text="Save\nabsorb.\nas .CSV",
                                            width=100,
                                            height=80,
                                            corner_radius=10,
                                            command=self.onCmdSaveAbsorptionToCSV)
        self.saveAbsorbanceToCSVButton.grid(row=0, column=1, sticky="N", padx=5, pady=5)

        self.saveResultsButton = ctk.CTkButton(master=self.settingsTabs.tab("Export"),
                                            text="Save\nresults",
                                            width=100,
                                            height=80,
                                            corner_radius=10,
                                            command=self.onCmdSaveAll)
        self.saveResultsButton.grid(row=0, column=0, sticky="N", padx=5, pady=5)

        self.inspectAbsorbanceButton = ctk.CTkButton(master=self.settingsTabs.tab("Export"),
                                            text="Inspect\nabsorb.",
                                            width=100,
                                            height=80,
                                            corner_radius=10,
                                            fg_color="darkgreen",
                                            command=self.onCmdInspectAbsorbance)
        self.inspectAbsorbanceButton.grid(row=1, column=0, sticky="N", padx=5, pady=5)
        self.inspectAbsorbanceButton.configure(state="disabled")

        self.inspectRefButton = ctk.CTkButton(master=self.settingsTabs.tab("Export"),
                                            text="Inspect\nreference",
                                            width=100,
                                            height=80,
                                            corner_radius=10,
                                            fg_color="darkgreen",
                                            command=self.onCmdInspectReference)
        self.inspectRefButton.grid(row=2, column=0, sticky="N", padx=5, pady=5)
        self.inspectRefButton.configure(state="disabled")

        self.inspectSampleButton = ctk.CTkButton(master=self.settingsTabs.tab("Export"),
                                            text="Inspect\nsample",
                                            width=100,
                                            height=80,
                                            corner_radius=10,
                                            fg_color="darkgreen",
                                            command=self.onCmdInspectSample)
        self.inspectSampleButton.grid(row=2, column=1, sticky="N", padx=5, pady=5)
        self.inspectSampleButton.configure(state="disabled")

        # create plots
        # ==============================================================================================================
        plt.style.use('dark_background')
        self.figRef, self.axRef = plt.subplots()
        self.figRef.suptitle("Reference spectrum")
        self.axRef.set_xlabel('Wavelength [\u03BCm]')
        self.axRef.set_ylabel('[dBm]')
        self.figRef.set_facecolor(self.backgroundGray)
        self.figRef.set_size_inches(100, 100)
        self.figRef.subplots_adjust(left=0.1, right=0.99, bottom=0.1, top=0.97, wspace=0, hspace=0)
        self.figRef.set_tight_layout(True)
        # self.axRef.set_yscale("log")
        self.canvasRefPlot = FigureCanvasTkAgg(self.figRef, master=self.frameReferencePlot)
        self.canvasRefPlot.get_tk_widget().pack(side='right', fill='both', expand=True)
        self.canvasRefPlot.draw()

        self.figSmp, self.axSmp = plt.subplots()
        self.figSmp.suptitle("Sample spectrum")
        self.axSmp.set_xlabel('Wavelength [\u03BCm]')
        self.axSmp.set_ylabel('[dBm]')
        self.figSmp.set_facecolor(self.backgroundGray)
        self.figSmp.set_size_inches(100, 100)
        self.figSmp.subplots_adjust(left=0.1, right=0.99, bottom=0.1, top=0.97, wspace=0, hspace=0)
        self.figSmp.set_tight_layout(True)
        # self.axSmp.set_yscale("log")
        self.canvasSmpPlot = FigureCanvasTkAgg(self.figSmp, master=self.frameSamplePlot)
        self.canvasSmpPlot.get_tk_widget().pack(side='right', fill='both', expand=True)
        self.canvasSmpPlot.draw()

        self.figAbs, self.axAbs = plt.subplots()
        self.figAbs.suptitle("Absorption spectrum")
        self.axAbs.set_xlabel('Wavelength [\u03BCm]')
        self.axAbs.set_ylabel('Absorbance')
        self.figAbs.set_facecolor(self.backgroundGray)
        self.figAbs.set_size_inches(100, 100)
        self.figAbs.subplots_adjust(left=0.1, right=0.99, bottom=0.1, top=0.97, wspace=0, hspace=0)
        self.figAbs.set_tight_layout(True)
        # self.axAbs.set_yscale("log")
        self.canvasAbsPlot = FigureCanvasTkAgg(self.figAbs, master=self.frameAbsorbancePlot)
        self.canvasAbsPlot.get_tk_widget().pack(side='right', fill='both', expand=True)
        self.canvasAbsPlot.draw()

        plt.close()
        plt.close()
        plt.close()

        self.absorbanceRoot.update()
        # self.absorbanceRoot.grab_set()
        # # self.absorbanceRoot.attributes('-topmost', 'true')
        # # self.absorbanceRoot.after(1, lambda: self.absorbanceRoot.focus_force())
        # self.absorbanceRoot.update()
        # time.sleep(1)
        #
        # self.absorbanceRoot.grab_release()

    def onCmdLoadReferenceSpectrumFromFile(self):
        (self.referenceSpectrumAxisNameX, self.referenceSpectrumAxisNameY,
         self.referenceSpectrumAxisX, self.referenceSpectrumAxisY) = self.loadSpectrumFromCSV()

        self.updatePlots()

    def onCmdLoadReferenceSpectrumLast(self):
        (self.referenceSpectrumAxisNameX, self.referenceSpectrumAxisNameY,
         self.referenceSpectrumAxisX, self.referenceSpectrumAxisY) = self.grabReferenceSpectrumDataLast()

        self.updatePlots()

    def onCmdLoadReferenceSpectrumAverage(self):
        (self.referenceSpectrumAxisNameX, self.referenceSpectrumAxisNameY,
         self.referenceSpectrumAxisX, self.referenceSpectrumAxisY) = self.grabReferenceSpectrumDataAverage()

        self.updatePlots()

    def onCmdLoadSampleSpectrumFromFile(self):
        (self.sampleSpectrumAxisNameX, self.sampleSpectrumAxisNameY,
         self.sampleSpectrumAxisX, self.sampleSpectrumAxisY) = self.loadSpectrumFromCSV()

        self.updatePlots()

    def onCmdLoadSampleSpectrumLast(self):
        (self.sampleSpectrumAxisNameX, self.sampleSpectrumAxisNameY,
         self.sampleSpectrumAxisX, self.sampleSpectrumAxisY) = self.grabSampleSpectrumDataLast()

        self.updatePlots()

    def onCmdLoadSampleSpectrumAverage(self):
        (self.sampleSpectrumAxisNameX, self.sampleSpectrumAxisNameY,
         self.sampleSpectrumAxisX, self.sampleSpectrumAxisY) = self.grabSampleSpectrumDataAverage()

        self.updatePlots()

    def onCmdUpdatePlotRanges(self, other):
        settings = self.grabApplicationSettings()

        # read and sanitize all range settings for plots
        # X MIN
        try:
            self.plotsXMin = float(self.xMinBox.get())
            settings["absorbanceToolRangeXMin"] = self.xMinBox.get()
        except:
            self.plotsXMin = float(settings["absorbanceToolRangeXMin"])
            self.xMinBox.delete(0, "end")
            self.xMinBox.insert(0, settings["absorbanceToolRangeXMin"])

        # X MAX
        try:
            self.plotsXMax = float(self.xMaxBox.get())
            settings["absorbanceToolRangeXMax"] = self.xMaxBox.get()
        except:
            self.plotsXMax = float(settings["absorbanceToolRangeXMax"])
            self.xMaxBox.delete(0, "end")
            self.xMaxBox.insert(0, settings["absorbanceToolRangeXMax"])

        # Y MIN
        try:
            self.plotsYMin = float(self.yMinBox.get())
            settings["absorbanceToolRangeYMin"] = self.yMinBox.get()
        except:
            self.plotsYMin = float(settings["absorbanceToolRangeYMin"])
            self.yMinBox.delete(0, "end")
            self.yMinBox.insert(0, settings["absorbanceToolRangeYMin"])

        # Y MAX
        try:
            self.plotsYMax = float(self.yMaxBox.get())
            settings["absorbanceToolRangeYMax"] = self.yMaxBox.get()
        except:
            self.plotsYMax = float(settings["absorbanceToolRangeYMax"])
            self.yMaxBox.delete(0, "end")
            self.yMaxBox.insert(0, settings["absorbanceToolRangeYMax"])

        # Y ABS MIN
        try:
            self.plotsAbsYMin = float(self.yAbsMinBox.get())
            settings["absorbanceToolAbsRangeYMin"] = self.yAbsMinBox.get()
        except:
            self.plotsAbsYMin = float(settings["absorbanceToolAbsRangeYMin"])
            self.yAbsMinBox.delete(0, "end")
            self.yAbsMinBox.insert(0, settings["absorbanceToolAbsRangeYMin"])

        # Y ABS MAX
        try:
            self.plotsAbsYMax = float(self.yAbsMaxBox.get())
            settings["absorbanceToolAbsRangeYMax"] = self.yAbsMaxBox.get()
        except:
            self.plotsAbsYMax= float(settings["absorbanceToolAbsRangeYMax"])
            self.yAbsMaxBox.delete(0, "end")
            self.yAbsMaxBox.insert(0, settings["absorbanceToolAbsRangeYMax"])

        # save new settings
        self.setApplicationSettings(settings)

        # update plot settings
        self.updatePlots()

    def updatePlots(self):
        plt.style.use('dark_background')
        # clear old data
        self.axRef.clear()
        self.axSmp.clear()
        self.axAbs.clear()

        # set ranges and plot new data

        # reference spectrum
        if (self.referenceSpectrumAxisX is not None) and (self.referenceSpectrumAxisY is not None) and \
                (len(self.referenceSpectrumAxisY) == len(self.referenceSpectrumAxisX)) and \
                (len(self.referenceSpectrumAxisY) != 0):

            self.reference_loaded = True
            self.inspectRefButton.configure(state="enabled")

            self.axRef.grid(color="dimgrey", linestyle='-', linewidth=1, alpha=0.6)
            self.axRef.plot(self.referenceSpectrumAxisX, self.referenceSpectrumAxisY, color="dodgerblue")

            self.axRef.set_xlim(self.plotsXMin, self.plotsXMax)
            self.axRef.set_ylim(self.plotsYMin, self.plotsYMax)
            # self.axRef.set_yscale("log")

            self.axRef.set_xlabel(self.referenceSpectrumAxisNameX)
            self.axRef.set_ylabel(self.referenceSpectrumAxisNameY)

        # sample spectrum
        if (self.sampleSpectrumAxisX is not None) and (self.sampleSpectrumAxisY is not None) and \
                (len(self.sampleSpectrumAxisY) == len(self.sampleSpectrumAxisX)) and \
                (len(self.sampleSpectrumAxisY) != 0):

            self.sample_loaded = True
            self.inspectSampleButton.configure(state="enabled")

            self.axSmp.grid(color="dimgrey", linestyle='-', linewidth=1, alpha=0.6)
            self.axSmp.plot(self.sampleSpectrumAxisX, self.sampleSpectrumAxisY, color="dodgerblue")

            self.axSmp.set_xlim(self.plotsXMin, self.plotsXMax)
            self.axSmp.set_ylim(self.plotsYMin, self.plotsYMax)
            # self.axSmp.set_yscale("log")

            self.axSmp.set_xlabel(self.sampleSpectrumAxisNameX)
            self.axSmp.set_ylabel(self.sampleSpectrumAxisNameY)

        if self.sample_loaded and self.reference_loaded:
            validation_result = self.validateSpectraForAbsorbanceCalculation()

            if validation_result == "OK":
                self.spectra_valid_for_absorbance_calculation = True
            else:
                self.spectra_valid_for_absorbance_calculation = False
                messagebox.showwarning(title="Error - can't calculate absorbance", message=validation_result)

        if self.sample_loaded and self.reference_loaded and self.spectra_valid_for_absorbance_calculation:
            self.calculateAbsorbance()

            self.axAbs.grid(color="dimgrey", linestyle='-', linewidth=1, alpha=0.6)
            self.axAbs.plot(self.absorbanceSpectrumAxisX, self.absorbanceSpectrumAxisY, color="dodgerblue")

            self.axAbs.set_xlim(self.plotsXMin, self.plotsXMax)
            self.axAbs.set_ylim(self.plotsAbsYMin, self.plotsAbsYMax)
            # self.axAbs.set_yscale("log")

            self.axAbs.set_xlabel(self.absorbanceSpectrumAxisNameX)
            self.axAbs.set_ylabel(self.absorbanceSpectrumAxisNameY)

            self.inspectAbsorbanceButton.configure(state="enabled")

        # force redraw and refresh
        self.canvasRefPlot.draw()
        self.canvasSmpPlot.draw()
        self.canvasAbsPlot.draw()
        self.absorbanceRoot.update()

    def calculateAbsorbance(self):
        # in order to calculate absorbance, spectra must be first converted from [dBm] to [W]
        refInWatts = np.power(10, (self.referenceSpectrumAxisY - 30) / 10)
        sampleInWatts = np.power(10, (self.sampleSpectrumAxisY - 30) / 10)

        self.absorbanceSpectrumAxisX = self.referenceSpectrumAxisX
        # self.absorbanceSpectrumAxisY = self.referenceSpectrumAxisY - self.sampleSpectrumAxisY
        self.absorbanceSpectrumAxisY = np.log10(refInWatts / sampleInWatts)
        self.absorbanceSpectrumAxisNameX = self.referenceSpectrumAxisNameX
        self.absorbanceSpectrumAxisNameY = "Absorbance"

    def validateSpectraForAbsorbanceCalculation(self):
        msg = ""

        if self.referenceSpectrumAxisY is None or self.referenceSpectrumAxisX is None:
            return "Error - reference spectrum uninitialized"

        if self.sampleSpectrumAxisY is None or self.sampleSpectrumAxisX is None:
            return "Error - sample spectrum uninitialized"

        if len(self.sampleSpectrumAxisX) != len(self.referenceSpectrumAxisX) != len(self.sampleSpectrumAxisY) != len(self.referenceSpectrumAxisY):
            return (f"Error - axes lengths not equal.\n"
                    f"Ref X = {len(self.referenceSpectrumAxisX)} Ref Y = {len(self.referenceSpectrumAxisY)}\n"
                    f"Sample X = {len(self.sampleSpectrumAxisX)} Sample Y = {len(self.sampleSpectrumAxisY)}")

        return "OK"

    def loadSpectrumFromCSV(self):
        types = [(
        ('.CSV spectrum', '*.csv')
        )]

        try:
            filename = filedialog.askopenfilename(title="Open .CSV spectrum file", filetypes=types)
            data = np.genfromtxt(filename, delimiter=",", dtype=float, names=True)
        except:
            messagebox.showwarning(title="Error - can't load spectrum file", message="Invalid spectrum file format")
            return None,None,None,None

        axisNameX = data.dtype.names[0].split('_')[0] + " [" + data.dtype.names[0].split('_')[1] + "]"
        axisNameY = data.dtype.names[1].split('_')[0] + " [" + data.dtype.names[1].split('_')[1] + "]"

        npAxisX = np.zeros(len(data))
        npAxisY = np.zeros(len(data))

        for i in range(0, len(data)):
            npAxisX[i] = data[i][0]
            npAxisY[i] = data[i][1]

        return axisNameX, axisNameY, npAxisX, npAxisY

    def onCmdInspectReference(self):

        if not self.reference_loaded:
            return

        try:
            mpl.rcParams.update(mpl.rcParamsDefault)
            plt.figure()
            plt.locator_params(nbins=15)
            plt.rc('xtick', labelsize=18)
            plt.rc('ytick', labelsize=18)
            plt.title("Reference spectrum", fontsize=20)
            plt.xlabel("Wavelength [\u03BCm]", fontsize=20)
            plt.ylabel("Intensity [dBm]", fontsize=20)
            plt.plot(self.referenceSpectrumAxisX, self.referenceSpectrumAxisY, color="dodgerblue")
            plt.xlim((float(self.plotsXMin), float(self.plotsXMax)))
            plt.ylim((float(self.plotsYMin), float(self.plotsYMax)))
            plt.grid(alpha=0.3)
            plt.ion()
            plt.pause(1.0)
            plt.show()
            plt.pause(1.0)
            plt.ioff()
        except:
            messagebox.showwarning(title="Error - can't inspect spectrum", message="Can't plot the data")

    def onCmdInspectSample(self):

        if not self.sample_loaded:
            return

        try:
            mpl.rcParams.update(mpl.rcParamsDefault)
            plt.figure()
            plt.locator_params(nbins=15)
            plt.rc('xtick', labelsize=18)
            plt.rc('ytick', labelsize=18)
            plt.title("Sample spectrum", fontsize=20)
            plt.xlabel("Wavelength [\u03BCm]", fontsize=20)
            plt.ylabel("Intensity [dBm]", fontsize=20)
            plt.plot(self.sampleSpectrumAxisX, self.sampleSpectrumAxisY, color="dodgerblue")
            plt.xlim((float(self.plotsXMin), float(self.plotsXMax)))
            plt.ylim((float(self.plotsYMin), float(self.plotsYMax)))
            plt.grid(alpha=0.3)
            plt.ion()
            plt.pause(1.0)
            plt.show()
            plt.pause(1.0)
            plt.ioff()
        except:
            messagebox.showwarning(title="Error - can't inspect spectrum", message="Can't plot the data")

    def onCmdInspectAbsorbance(self):

        if not self.spectra_valid_for_absorbance_calculation:
            return

        try:
            mpl.rcParams.update(mpl.rcParamsDefault)
            plt.figure()
            plt.locator_params(nbins=15)
            plt.rc('xtick', labelsize=18)
            plt.rc('ytick', labelsize=18)
            plt.title("Absorption spectrum", fontsize=20)
            plt.xlabel("Wavelength [\u03BCm]", fontsize=20)
            plt.ylabel("Absorbance", fontsize=20)
            plt.plot(self.absorbanceSpectrumAxisX, self.absorbanceSpectrumAxisY, color="dodgerblue")
            plt.xlim((float(self.plotsXMin), float(self.plotsXMax)))
            plt.ylim((float(self.plotsAbsYMin), float(self.plotsAbsYMax)))
            plt.grid(alpha=0.3)
            plt.ion()
            plt.pause(1.0)
            plt.show()
            plt.pause(1.0)
            plt.ioff()
        except:
            messagebox.showwarning(title="Error - can't inspect spectrum", message="Can't plot the data")

    def onCmdSaveAbsorptionToCSV(self):
        DET.exportAbsorbanceAsCSV(absorbanceX=self.absorbanceSpectrumAxisX, absorbanceY=self.absorbanceSpectrumAxisY,
                                  axisNameX="Wavelength_um", axisNameY="Absorbance")

    def onCmdSaveAll(self):
        DET.exportAllDataAbsorbance(refX=self.referenceSpectrumAxisX,   refY=self.referenceSpectrumAxisY,
                                    sampleX=self.sampleSpectrumAxisX,   sampleY=self.sampleSpectrumAxisY,
                                    absX=self.absorbanceSpectrumAxisX,  absY=self.absorbanceSpectrumAxisY,
                                    absXTitle="Wavelength [\u03BCm]",   absYTitle="Absorbance", absTitle="Absorption",
                                    rngXMin=self.plotsXMin,             rngXMax=self.plotsXMax,
                                    rngYMin=self.plotsYMin,             rngYMax=self.plotsYMax,
                                    rngAbsYMin=self.plotsAbsYMin,       rngAbsYMax=self.plotsAbsYMax)
