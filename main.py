import os
import customtkinter as ctk
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sys
from mfli_driver import MFLIDriver
from zaber_driver import ZaberDriver
import time
import si_prefix as si
from background_controller import BackgroundController
import serial.tools.list_ports
import settings_manager as SM
import logging
from tkinter.filedialog import asksaveasfilename
from tkinter import filedialog
from datetime import datetime
import data_export_tool as DataExportTool
import absorbanceTool as AbsorbanceTool

class FTSApp:

    def __init__(self):
        logging.basicConfig(filename='ftsapp.log', format='%(asctime)s %(message)s', level=logging.INFO)
        logging.info('========= Application started =========')

        self.absorbanceToolWindow = None

        if SM.isSettingsFileAvailable():
            self.appSettings = SM.readSettingsFromFile()
            SM.validateAndFixSettings(self.appSettings)
        else:
            self.appSettings = SM.getDefaultSettings()

        self.settingsUsedForCurrentMeasurement = self.appSettings.copy()

        # constants
        self.backgroundGray = "#242424"
        self.plotLineColor = "gold" # dodgerblue
        self.currentSpectrumX = []
        self.currentSpectrumY = []
        self.currentInterferogramX = []
        self.currentInterferogramY = []
        self.currentAverageSpectrumX = []
        self.currentAverageSpectrumY = []

        self.currentlyAvailableCOMPorts = []

        # construct GUI
        ctk.set_appearance_mode("dark")
        self.root = ctk.CTk()
        self.root.geometry("1200x800")
        self.root.minsize(800, 800)
        self.root.title("FTS App")
        self.root.iconbitmap(default='icon.ico')
        self.root.resizable(True, True)
        self.root.state('zoomed')
        self.root.withdraw()

        self.screen_geometry = self.root.winfo_geometry()
        scr_width = int(self.screen_geometry.split('x')[0])

        if scr_width > 1920:
            menu_col_width = 350
        else:
            menu_col_width = 250

        self.root.columnconfigure(0, weight=1, minsize=menu_col_width)
        self.root.columnconfigure(1, weight=3)

        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self.root.protocol("WM_DELETE_WINDOW", self.onClosing)

        # build GUI elements
        self.frameTopPlot = ctk.CTkFrame(master=self.root, fg_color="darkblue")

        self.frameTopPlot.grid(row=0, column=1, padx=(5, 5), pady=0)#, sticky="N")

        self.frameBottomPlot = ctk.CTkFrame(master=self.root, fg_color="darkblue")
        # self.frame.place(relx=0.33, rely=0.025)
        self.frameBottomPlot.grid(row=1, column=1, padx=(5, 5), pady=0)#, sticky="N")

        # buttons
        # create a frame to hold all the controls related to measurements
        # ==============================================================================================================
        self.frameButtonsTop = ctk.CTkFrame(master=self.root,
                                            height=60,
                                            width=120,
                                            fg_color="dimgrey",
                                            corner_radius=10)
        self.frameButtonsTop.grid(row=0, column=0, sticky="NSEW", padx=5, pady=5)

        self.frameButtonsTop.columnconfigure(0, weight=1)
        self.frameButtonsTop.columnconfigure(1, weight=1)

        self.frameButtonsTop.rowconfigure(0, weight=1)
        self.frameButtonsTop.rowconfigure(1, weight=1)
        self.frameButtonsTop.rowconfigure(2, weight=1, minsize=40)
        self.frameButtonsTop.rowconfigure(3, weight=1)
        self.frameButtonsTop.rowconfigure(4, weight=1)
        self.frameButtonsTop.rowconfigure(5, weight=1)

        self.buttonSingle = ctk.CTkButton(master=self.frameButtonsTop,
                                          text="Single\ncapture",
                                          width=120,
                                          height=75,
                                          corner_radius=10,
                                          command=self.onCmdSingleCapture)
        self.buttonSingle.grid(row=0, column=0, sticky="N", padx=5, pady=5)

        self.multipleMeasStartButton = ctk.CTkButton(master=self.frameButtonsTop,
                                            text="Capture\nmultiple",
                                            width=120,
                                            height=75,
                                            corner_radius=10,
                                            command=self.onCmdMultipleCapture)
        self.multipleMeasStartButton.grid(row=1, column=0, sticky="N", padx=5, pady=5)

        self.multipleMeasStopButton = ctk.CTkButton(master=self.frameButtonsTop,
                                            text="Stop",
                                            width=120,
                                            height=75,
                                            corner_radius=10,
                                            fg_color="darkred",
                                            command=self.onCmdStopMeasurement)
        self.multipleMeasStopButton.grid(row=1, column=1, sticky="N", padx=5, pady=5)

        self.multipleMeasLabel = ctk.CTkLabel(master=self.frameButtonsTop,
                                                    text="Number of\naverages",
                                                    font=ctk.CTkFont(size=12))
        self.multipleMeasLabel.grid(row=2, column=0, sticky="N", padx=5, pady=5)

        self.multipleMeasBox = ctk.CTkEntry(master=self.frameButtonsTop,
                                        width=120, height=30)
        self.multipleMeasBox.insert(0, self.appSettings["averagingCount"])
        self.multipleMeasBox.grid(row=2, column=1, sticky="N", padx=5, pady=5)
        self.multipleMeasBox.bind("<FocusOut>", self.onCmdUpdateAveragingCount)
        self.multipleMeasBox.bind("<Return>", self.onCmdUpdateAveragingCount)

        self.buttonInterferogram = ctk.CTkButton(master=self.frameButtonsTop,
                                                 text="Inspect\ninterferogram",
                                                 width=120,
                                                 height=75,
                                                 corner_radius=10,
                                                 fg_color="darkgreen",
                                                 command=self.onCmdOpenInterferogramPlot)
        self.buttonInterferogram.grid(row=3, column=0, sticky="N", padx=5, pady=5)

        self.buttonSpectrum = ctk.CTkButton(master=self.frameButtonsTop,
                                            text="Inspect\nspectrum",
                                            width=120,
                                            height=75,
                                            corner_radius=10,
                                            fg_color="darkgreen",
                                            command=self.onCmdOpenSpectrumPlot)
        self.buttonSpectrum.grid(row=3, column=1, sticky="N", padx=5, pady=5)

        self.referenceSignalButton = ctk.CTkButton(master=self.frameButtonsTop,
                                            text="Inspect\nref. signal",
                                            width=120,
                                            height=75,
                                            corner_radius=10,
                                            fg_color="darkgreen",
                                            command=self.onCmdReferencePlot)
        self.referenceSignalButton.grid(row=4, column=0, sticky="N", padx=5, pady=5)

        self.absorbanceToolButton = ctk.CTkButton(master=self.frameButtonsTop,
                                            text="Absorbance\ntool",
                                            width=120,
                                            height=75,
                                            corner_radius=10,
                                            command=self.onCmdOpenAbsorbanceTool)
        self.absorbanceToolButton.grid(row=5, column=0, sticky="N", padx=5, pady=5)

        self.buttonArchive = ctk.CTkButton(master=self.frameButtonsTop,
                                           text="Archive\nviewer",
                                           width=120,
                                           height=75,
                                           corner_radius=10,
                                           command=self.onCmdUnusedButton)
        self.buttonArchive.grid(row=5, column=1, sticky="N", padx=5, pady=5)
        self.buttonArchive.configure(state="disabled")

        # create a frame to hold all the controls related to settings and configuration
        # ==============================================================================================================
        self.frameButtonsBottom = ctk.CTkFrame(master=self.root,
                                               height=60,
                                               width=5000,
                                               fg_color="dimgrey",
                                               corner_radius=10)
        self.frameButtonsBottom.grid(row=1, column=0, sticky="NSEW", padx=5, pady=5)

        self.frameButtonsBottom.columnconfigure(0, weight=1)
        self.frameButtonsBottom.columnconfigure(1, weight=1)

        # self.frameButtonsBottom.rowconfigure(0, weight=1)
        # self.frameButtonsBottom.rowconfigure(1, weight=1)
        # self.frameButtonsBottom.rowconfigure(2, weight=1)
        # self.frameButtonsBottom.rowconfigure(3, weight=1)
        # self.frameButtonsBottom.rowconfigure(4, weight=1)

        self.configLabel = ctk.CTkLabel(master=self.frameButtonsBottom,
                                        text="Settings",
                                        font=ctk.CTkFont(size=16, weight="bold"))
        self.configLabel.grid(row=0, column=0, columnspan=2, sticky="NSEW", padx=5, pady=5)

        # create settings tabs
        self.settingsTabs = ctk.CTkTabview(master=self.frameButtonsBottom)
        self.settingsTabs.grid(row=4, column=0, columnspan=2, sticky="NSEW", padx=2, pady=2)
        self.settingsTabs.add("Scan")
        self.settingsTabs.add("Trig")
        self.settingsTabs.add("Hardware")
        self.settingsTabs.add("Plots")
        self.settingsTabs.add("Save")

        # configure settings 'SCAN' tab
        # ==============================================================================================================
        self.settingsTabs.tab("Scan").columnconfigure(0, weight=1)
        self.settingsTabs.tab("Scan").columnconfigure(1, weight=1)

        self.samplingFreqLabelHeader = ctk.CTkLabel(master=self.settingsTabs.tab("Scan"),
                                                    text="Sampling\nfreqency",
                                                    font=ctk.CTkFont(size=12))
        self.samplingFreqLabelHeader.grid(row=0, column=0, sticky="E", padx=5, pady=5)

        self.MFLIFreqneuenciesAsStrings = []

        for f in MFLIDriver.MFLISamplingRates:
            self.MFLIFreqneuenciesAsStrings.append(si.si_format(f, precision=2) + "Hz")

        self.samplingFreqCombo = ctk.CTkComboBox(master=self.settingsTabs.tab("Scan"),
                                                 values=self.MFLIFreqneuenciesAsStrings,
                                                 state="readonly",
                                                 width=120)
        self.samplingFreqCombo.grid(row=0, column=1, sticky="E", padx=5, pady=5)
        self.samplingFreqCombo.set(self.MFLIFreqneuenciesAsStrings[int(self.appSettings["mfliSelectedFrequencyIndex"])])

        self.startingPosLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Scan"),
                                                    text="Start\nposition [\u03BCm]",
                                                    font=ctk.CTkFont(size=12))
        self.startingPosLabel.grid(row=1, column=0, sticky="E", padx=5, pady=5)

        self.startingPosBox = ctk.CTkEntry(master=self.settingsTabs.tab("Scan"),
                                        width=120, height=30)
        self.startingPosBox.insert(0, self.appSettings["delayLineConfiguredScanStart"])
        self.startingPosBox.grid(row=1, column=1, sticky="E", padx=5, pady=5)
        self.startingPosBox.bind("<FocusOut>", self.onCmdUpdateStartingPositionFromBox)
        self.startingPosBox.bind("<Return>", self.onCmdUpdateStartingPositionFromBox)

        self.scanLengthLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Scan"),
                                                    text="Scan\nlength [\u03BCm]",
                                                    font=ctk.CTkFont(size=12))
        self.scanLengthLabel.grid(row=2, column=0, sticky="E", padx=5, pady=5)

        self.scanLengthBox = ctk.CTkEntry(master=self.settingsTabs.tab("Scan"),
                                        width=120, height=30)
        # self.scanLengthBox.configure(wrap='none')
        self.scanLengthBox.insert(0, self.appSettings["delayLineConfiguredScanLength"])
        self.scanLengthBox.grid(row=2, column=1, sticky="E", padx=5, pady=5)
        self.scanLengthBox.bind("<FocusOut>", self.onCmdUpdateScanLengthFromBox)
        self.scanLengthBox.bind("<Return>", self.onCmdUpdateScanLengthFromBox)

        self.scanLengthSlider = ctk.CTkSlider(master = self.settingsTabs.tab("Scan"),
                                              width = 250,
                                              height = 20,
                                              from_ = int(self.appSettings["delayLineMinimalScanLength"]),
                                              to = ZaberDriver.DelayLineNominalLength -
                                                 (ZaberDriver.DelayLineNominalLength -
                                                  int(self.appSettings["delayLineConfiguredScanStart"])),
                                              number_of_steps=(ZaberDriver.DelayLineNominalLength -
                                                             (ZaberDriver.DelayLineNominalLength -
                                                             int(self.appSettings["delayLineConfiguredScanStart"])) -
                                                             int(self.appSettings["delayLineMinimalScanLength"])) / 100,
                                              command=self.onCmdUpdateScanLengthFromSlider)
        self.scanLengthSlider.grid(row=3, column=0, columnspan=2, sticky="N", padx=5, pady=5)
        self.scanLengthSlider.set(float(self.appSettings["delayLineConfiguredScanLength"]))

        self.scanSpeedLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Scan"),
                                                    text="Scan speed\n[mm/s]",
                                                    font=ctk.CTkFont(size=12))
        self.scanSpeedLabel.grid(row=4, column=0, sticky="E", padx=5, pady=5)

        self.scanSpeedValueLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Scan"),
                                                    text=self.appSettings["delayLineConfiguredScanSpeed"],
                                                    font=ctk.CTkFont(size=12))
        self.scanSpeedValueLabel.grid(row=4, column=1, sticky="W", padx=5, pady=5)

        self.scanSpeedSlider = ctk.CTkSlider(master = self.settingsTabs.tab("Scan"),
                                              width = 250,
                                              height = 20,
                                              from_ = int(self.appSettings["delayLineMinimumSpeed"]),
                                              to = int(self.appSettings["delayLineMaximumSpeed"]),
                                              number_of_steps = int(self.appSettings["delayLineSpeedSliderTicks"]),
                                              command=self.onCmdScanSpeedUpdateFromSlider)
        self.scanSpeedSlider.grid(row=5, column=0, columnspan=2, sticky="N", padx=5, pady=5)
        self.scanSpeedSlider.set(float(self.appSettings["delayLineConfiguredScanSpeed"]))

        # configure settings 'TRIG' tab
        # ==============================================================================================================
        self.settingsTabs.tab("Trig").columnconfigure(0, weight=1)
        self.settingsTabs.tab("Trig").columnconfigure(1, weight=1)

        self.settingsTabs.tab("Trig").rowconfigure(0, weight=1)
        self.settingsTabs.tab("Trig").rowconfigure(1, weight=1)
        self.settingsTabs.tab("Trig").rowconfigure(2, weight=1)
        self.settingsTabs.tab("Trig").rowconfigure(3, weight=1)

        self.triggerEnableSwitch = ctk.CTkSwitch(master=self.settingsTabs.tab("Trig"),
                                                    text="Triggered acquisition mode",
                                                    command=self.onCmdTriggerSwitchModified,
                                                    onvalue="True", offvalue="False")
        self.triggerEnableSwitch.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="W")

        if self.appSettings["triggerModeEnabled"] == "True":
            self.triggerEnableSwitch.select()
        else:
            self.triggerEnableSwitch.deselect()

        self.triggerLevelLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Trig"),
                                                    text="Trigger\nlevel [mV]",
                                                    font=ctk.CTkFont(size=12))
        self.triggerLevelLabel.grid(row=1, column=0, sticky="E", padx=5, pady=5)

        self.triggerLevelBox = ctk.CTkEntry(master=self.settingsTabs.tab("Trig"),
                                        width=120, height=30)
        self.triggerLevelBox.insert(0, self.appSettings["triggerLevel"])
        self.triggerLevelBox.grid(row=1, column=1, sticky="E", padx=5, pady=5)
        self.triggerLevelBox.bind("<FocusOut>", self.onCmdRefreshTriggerSettings)
        self.triggerLevelBox.bind("<Return>", self.onCmdRefreshTriggerSettings)

        self.triggerHysteresisLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Trig"),
                                                    text="Trigger\nhysteresis [mV]",
                                                    font=ctk.CTkFont(size=12))
        self.triggerHysteresisLabel.grid(row=2, column=0, sticky="E", padx=5, pady=5)

        self.triggerHysteresisBox = ctk.CTkEntry(master=self.settingsTabs.tab("Trig"),
                                        width=120, height=30)
        self.triggerHysteresisBox.insert(0, self.appSettings["triggerHysteresis"])
        self.triggerHysteresisBox.grid(row=2, column=1, sticky="E", padx=5, pady=5)
        self.triggerHysteresisBox.bind("<FocusOut>", self.onCmdRefreshTriggerSettings)
        self.triggerHysteresisBox.bind("<Return>", self.onCmdRefreshTriggerSettings)

        self.triggerDelayLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Trig"),
                                                    text="Trigger\ndelay [ms]",
                                                    font=ctk.CTkFont(size=12))
        self.triggerDelayLabel.grid(row=3, column=0, sticky="E", padx=5, pady=5)

        self.triggerDelayBox = ctk.CTkEntry(master=self.settingsTabs.tab("Trig"),
                                        width=120, height=30)
        self.triggerDelayBox.insert(0, self.appSettings["triggerDelay"])
        self.triggerDelayBox.grid(row=3, column=1, sticky="E", padx=5, pady=5)
        self.triggerDelayBox.bind("<FocusOut>", self.onCmdRefreshTriggerSettings)
        self.triggerDelayBox.bind("<Return>", self.onCmdRefreshTriggerSettings)

        # configure settings 'HARDWARE' tab
        # ==============================================================================================================
        self.settingsTabs.tab("Hardware").columnconfigure(0, weight=1)
        self.settingsTabs.tab("Hardware").columnconfigure(1, weight=1)

        self.hardwareStatusLabelHeader = ctk.CTkLabel(master=self.settingsTabs.tab("Hardware"),
                                                      text="General\nstatus",
                                                      font=ctk.CTkFont(size=12))
        self.hardwareStatusLabelHeader.grid(row=0, column=0, sticky="E", padx=5, pady=5)

        self.hardwareStatusLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Hardware"),
                                                text="NOT\nREADY",
                                                text_color="red",
                                                font=ctk.CTkFont(size=14, weight="bold"))
        self.hardwareStatusLabel.grid(row=0, column=1, sticky="W", padx=5, pady=5)

        self.mfliStatusLabelHeader = ctk.CTkLabel(master=self.settingsTabs.tab("Hardware"),
                                                  text="DAQ\nsystem",
                                                  font=ctk.CTkFont(size=12))
        self.mfliStatusLabelHeader.grid(row=1, column=0, sticky="E", padx=5, pady=5)

        self.mfliStatusLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Hardware"),
                                            text="NOT\nREADY",
                                            text_color="red",
                                            font=ctk.CTkFont(size=14, weight="bold"))
        self.mfliStatusLabel.grid(row=1, column=1, sticky="W", padx=5, pady=5)

        self.zaberStatusLabelHeader = ctk.CTkLabel(master=self.settingsTabs.tab("Hardware"),
                                                   text="Delay\nline",
                                                   font=ctk.CTkFont(size=12))
        self.zaberStatusLabelHeader.grid(row=2, column=0, sticky="E", padx=5, pady=5)

        self.zaberStatusLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Hardware"),
                                             text="NOT\nREADY",
                                             text_color="red",
                                             font=ctk.CTkFont(size=14, weight="bold"))
        self.zaberStatusLabel.grid(row=2, column=1, sticky="W", padx=5, pady=5)

        self.zaberCOMLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Hardware"),
                                          text="Zaber port",
                                          font=ctk.CTkFont(size=12))
        self.zaberCOMLabel.grid(row=3, column=0, sticky="W", padx=5, pady=5)

        self.zaberPortCombo = ctk.CTkComboBox(master=self.settingsTabs.tab("Hardware"),
                                              values=[],
                                              state="readonly",
                                              width=140)
        self.zaberPortCombo.grid(row=3, column=1, sticky="E", padx=5, pady=5)
        self.onCmdRefreshCOMPorts()

        # set the last used Zaber COM port if it is currently available
        if self.currentlyAvailableCOMPorts.__contains__(self.appSettings["delayLineCOMPort"]):
            self.zaberPortCombo.set(self.appSettings["delayLineCOMPort"])

        self.zaberPortRefreshButton = ctk.CTkButton(master=self.settingsTabs.tab("Hardware"),
                                            text="",
                                            width=20,
                                            height=20,
                                            corner_radius=4,
                                            command=self.onCmdRefreshCOMPorts)
        self.zaberPortRefreshButton.grid(row=3, column=0, sticky="E", padx=5, pady=5)

        self.mfliIDLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Hardware"),
                                        text="MFLI ID",
                                        font=ctk.CTkFont(size=12))
        self.mfliIDLabel.grid(row=4, column=0, sticky="W", padx=5, pady=5)

        self.mfliIDBox = ctk.CTkTextbox(master=self.settingsTabs.tab("Hardware"),
                                        width=140, height=30)
        self.mfliIDBox.configure(wrap='none')
        self.mfliIDBox.insert("0.0", self.appSettings["mfliDeviceID"])
        self.mfliIDBox.grid(row=4, column=1, sticky="E", padx=5, pady=5)

        self.buttonHardware = ctk.CTkButton(master=self.settingsTabs.tab("Hardware"),
                                            text="Connect\nall",
                                            width=120,
                                            height=80,
                                            corner_radius=10,
                                            command=self.onCmdConnectHardware)
        self.buttonHardware.grid(row=6, column=0, sticky="N", padx=5, pady=5)

        self.buttonHardware = ctk.CTkButton(master=self.settingsTabs.tab("Hardware"),
                                            text="Home\nmirror",
                                            width=120,
                                            height=80,
                                            corner_radius=10,
                                            command=self.onCmdUnusedButton)
        self.buttonHardware.grid(row=6, column=1, sticky="N", padx=5, pady=5)

        # configure settings 'EXPORT' tab
        # ==============================================================================================================
        self.settingsTabs.tab("Save").columnconfigure(0, weight=1)
        self.settingsTabs.tab("Save").columnconfigure(1, weight=1)

        self.settingsTabs.tab("Save").columnconfigure(0, weight=1)
        self.settingsTabs.tab("Save").columnconfigure(1, weight=1)

        self.buttonSaveNormal = ctk.CTkButton(master=self.settingsTabs.tab("Save"),
                                            text="Save\nresults",
                                            width=120,
                                            height=80,
                                            corner_radius=10,
                                            command=self.onCmdSaveFull)
        self.buttonSaveNormal.grid(row=0, column=0, sticky="N", padx=5, pady=5)

        self.buttonSaveCSV = ctk.CTkButton(master=self.settingsTabs.tab("Save"),
                                            text="Save\nspectrum\nas .csv",
                                            width=120,
                                            height=80,
                                            corner_radius=10,
                                            command=self.onCmdSaveCSVOnly)
        self.buttonSaveCSV.grid(row=0, column=1, sticky="N", padx=5, pady=5)

        self.exportRawDataSwitch = ctk.CTkSwitch(master=self.settingsTabs.tab("Save"),
                                                    text="Export raw data", command=self.onExportSwitchModified,
                                                    onvalue="True", offvalue="False")
        self.exportRawDataSwitch.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="W")

        if self.appSettings["saveRawData"] == "True":
            self.exportRawDataSwitch.select()
        else:
            self.exportRawDataSwitch.deselect()

        self.exportToMatSwitch = ctk.CTkSwitch(master=self.settingsTabs.tab("Save"),
                                                    text="Export to .MAT", command=self.onExportSwitchModified,
                                                    onvalue="True", offvalue="False")
        self.exportToMatSwitch.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="W")

        if self.appSettings["saveDataToMAT"] == "True":
            self.exportToMatSwitch.select()
        else:
            self.exportToMatSwitch.deselect()
        # configure settings 'PLOTS' tab
        # ==============================================================================================================
        self.settingsTabs.tab("Plots").columnconfigure(0, weight=1)
        self.settingsTabs.tab("Plots").columnconfigure(1, weight=1)

        self.settingsTabs.tab("Plots").columnconfigure(0, weight=1)
        self.settingsTabs.tab("Plots").columnconfigure(1, weight=1)

        self.spectrumXMinLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Plots"),
                                                    text="Spectrum plot\nX MIN [\u03BCm]",
                                                    font=ctk.CTkFont(size=12))
        self.spectrumXMinLabel.grid(row=0, column=0, sticky="E", padx=5, pady=5)

        self.spectrumXMinBox = ctk.CTkEntry(master=self.settingsTabs.tab("Plots"),
                                        width=120, height=30)
        # self.scanLengthBox.configure(wrap='none')
        self.spectrumXMinBox.insert(0, self.appSettings["plotSpectrumXRangeMin"])
        self.spectrumXMinBox.grid(row=0, column=1, sticky="E", padx=5, pady=5)
        self.spectrumXMinBox.bind("<FocusOut>", self.onCmdUpdateSpectrumPlotRanges)
        self.spectrumXMinBox.bind("<Return>", self.onCmdUpdateSpectrumPlotRanges)

        self.spectrumXMaxLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Plots"),
                                                    text="Spectrum plot\nX MAX [\u03BCm]",
                                                    font=ctk.CTkFont(size=12))
        self.spectrumXMaxLabel.grid(row=1, column=0, sticky="E", padx=5, pady=5)

        self.spectrumXMaxBox = ctk.CTkEntry(master=self.settingsTabs.tab("Plots"),
                                        width=120, height=30)
        # self.scanLengthBox.configure(wrap='none')
        self.spectrumXMaxBox.insert(0, self.appSettings["plotSpectrumXRangeMax"])
        self.spectrumXMaxBox.grid(row=1, column=1, sticky="E", padx=5, pady=5)
        self.spectrumXMaxBox.bind("<FocusOut>", self.onCmdUpdateSpectrumPlotRanges)
        self.spectrumXMaxBox.bind("<Return>", self.onCmdUpdateSpectrumPlotRanges)

        self.spectrumYMinLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Plots"),
                                                    text="Spectrum plot\nY MIN [dBm]",
                                                    font=ctk.CTkFont(size=12))
        self.spectrumYMinLabel.grid(row=2, column=0, sticky="E", padx=5, pady=5)

        self.spectrumYMinBox = ctk.CTkEntry(master=self.settingsTabs.tab("Plots"),
                                        width=120, height=30)
        # self.scanLengthBox.configure(wrap='none')
        self.spectrumYMinBox.insert(0, self.appSettings["plotSpectrumYRangeMin"])
        self.spectrumYMinBox.grid(row=2, column=1, sticky="E", padx=5, pady=5)
        self.spectrumYMinBox.bind("<FocusOut>", self.onCmdUpdateSpectrumPlotRanges)
        self.spectrumYMinBox.bind("<Return>", self.onCmdUpdateSpectrumPlotRanges)

        self.spectrumYMaxLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Plots"),
                                                    text="Spectrum plot\nY MAX [dBm]",
                                                    font=ctk.CTkFont(size=12))
        self.spectrumYMaxLabel.grid(row=3, column=0, sticky="E", padx=5, pady=5)

        self.spectrumYMaxBox = ctk.CTkEntry(master=self.settingsTabs.tab("Plots"),
                                        width=120, height=30)
        # self.scanLengthBox.configure(wrap='none')
        self.spectrumYMaxBox.insert(0, self.appSettings["plotSpectrumYRangeMax"])
        self.spectrumYMaxBox.grid(row=3, column=1, sticky="E", padx=5, pady=5)
        self.spectrumYMaxBox.bind("<FocusOut>", self.onCmdUpdateSpectrumPlotRanges)
        self.spectrumYMaxBox.bind("<Return>", self.onCmdUpdateSpectrumPlotRanges)

        # Create plots
        # ==============================================================================================================
        plt.style.use('dark_background')
        self.figTop, self.axTop = plt.subplots()
        self.figTop.suptitle("Interferogram")
        self.axTop.set_xlabel('Mirror position [\u03BCm]')
        self.axTop.set_ylabel('Detector voltage [V]')
        self.figTop.set_facecolor(self.backgroundGray)
        self.figTop.set_size_inches(100, 100)
        self.figTop.subplots_adjust(left=0.1, right=0.99, bottom=0.1, top=0.97, wspace=0, hspace=0)
        self.figTop.set_tight_layout(True)
        self.canvasTopPlot = FigureCanvasTkAgg(self.figTop, master=self.frameTopPlot)
        self.canvasTopPlot.get_tk_widget().pack(side='right', fill='both', expand=True)
        self.canvasTopPlot.draw()

        self.figBot, self.axBot = plt.subplots()
        self.figBot.suptitle("Spectrum")
        self.axBot.set_xlabel('Wavelength [\u03BCm]')
        self.axBot.set_ylabel('[dBm]')
        self.figBot.set_facecolor(self.backgroundGray)
        self.figBot.set_size_inches(100, 100)
        self.figBot.subplots_adjust(left=0.1, right=0.99, bottom=0.1, top=0.97, wspace=0, hspace=0)
        self.figBot.set_tight_layout(True)
        self.canvasBotPlot = FigureCanvasTkAgg(self.figBot, master=self.frameBottomPlot)
        self.canvasBotPlot.get_tk_widget().pack(side='right', fill='both', expand=True)
        self.canvasBotPlot.draw()

        self.updatePlot()
        plt.close()
        plt.close()

        self.axBot.set_xlim(float(self.appSettings["plotSpectrumXRangeMin"]),
                            float(self.appSettings["plotSpectrumXRangeMax"]))
        self.axBot.set_ylim(float(self.appSettings["plotSpectrumYRangeMin"]),
                            float(self.appSettings["plotSpectrumYRangeMax"]))
        # self.axBot.set_yscale("log")

        self.settingsTabs.set("Hardware")

        # create a status bar
        self.statusLabel = ctk.CTkLabel(master=self.root,
                                        text="",
                                        font=ctk.CTkFont(size=12))
        self.statusLabel.grid(row=0, column=1, columnspan=2, sticky="NE", padx=15, pady=5)

        # create drivers
        self.MFLIDrv = MFLIDriver(self.mfliIDBox.get("0.0", "end"))
        self.ZaberDrv = ZaberDriver()

        # set up the background application controller
        self.ApplicationController = BackgroundController(self.MFLIDrv, self.ZaberDrv)
        self.ApplicationController.SetStatusMessageMethod = self.updateStatusMessage
        self.ApplicationController.SetGeneralReadyFlagMethod = self.setGeneralReadyFlag
        self.ApplicationController.SetDAQReadyFlagMethod = self.setDAQReadyFlag
        self.ApplicationController.SetDelayLineReadyFlagMethod = self.setDelayLineReadyFlag
        self.ApplicationController.SendResultsToPlot = self.receiveMeasurementResults
        self.ApplicationController.NotifyAllMeasurementsDone = self.receiveNotificationAllMeasurementsDone

        # try to connect to all the hardware with some default settings
        self.ApplicationController.MFLIDeviceName = self.mfliIDBox.get("0.0", "end")
        self.ApplicationController.ZaberPort = self.zaberPortCombo.get().replace(' ', '').replace(
            '\t', '').replace('\n', '').replace('\r', '')

        # self.ApplicationController.performInitialization()
        # run the app
        self.root.update()
        self.root.deiconify()   # show the window after it's loaded
        self.root.mainloop()

    def updateStatusMessage(self, message):
        self.statusLabel.configure(text=message)
        logging.info(f"Status bar message set to: {message}")
        self.root.update()

    def getApplicationSettings(self):
        return self.appSettings

    def setApplicationSettings(self, settings):
        self.appSettings = settings

    def setGeneralReadyFlag(self, isReady):
        if isReady:
            self.hardwareStatusLabel.configure(text="READY", text_color="lightgreen")
            logging.info(f"General status: ready")
        else:
            self.hardwareStatusLabel.configure(text="NOT\nREADY", text_color="red")
            logging.info(f"General status: not ready")

    def setDAQReadyFlag(self, isReady):
        if isReady:
            self.mfliStatusLabel.configure(text="READY", text_color="lightgreen")
            self.appSettings["mfliDeviceID"] = self.MFLIDrv.deviceID
            logging.info(f"DAQ status: ready")
        else:
            self.mfliStatusLabel.configure(text="NOT\nREADY", text_color="red")
            logging.info(f"DAQ status: not ready")

    def setDelayLineReadyFlag(self, isReady):
        if isReady:
            self.zaberStatusLabel.configure(text="READY", text_color="lightgreen")
            self.appSettings["delayLineCOMPort"] = self.zaberPortCombo.get()
            logging.info(f"Delay line status: ready")
        else:
            self.zaberStatusLabel.configure(text="NOT\nREADY", text_color="red")
            logging.info(f"Delay line status: not ready")

    def receiveMeasurementResults(self, interfX, interfY, spectrumX, spectrumY, averageSpectrumX, averageSpectrumY,
        completedMeasurements):

        self.currentInterferogramX = interfX
        self.currentInterferogramY = interfY
        self.currentSpectrumX = spectrumX
        self.currentSpectrumY = spectrumY
        self.currentAverageSpectrumX = averageSpectrumX
        self.currentAverageSpectrumY = averageSpectrumY

        self.multipleMeasBox.delete(0, "end")

        if completedMeasurements == self.ApplicationController.orderedMeasurementsCount:
            self.multipleMeasBox.insert(0,f"{self.ApplicationController.orderedMeasurementsCount}")
        else:
            self.multipleMeasBox.insert(0,
                                        f"{completedMeasurements}/{self.ApplicationController.orderedMeasurementsCount}")
        self.updatePlot()

    def receiveNotificationAllMeasurementsDone(self):
        logging.info("All ordered measurements done")
        self.updateStatusMessage("Done")

    def onCmdTriggerSwitchModified(self):
        self.onCmdRefreshTriggerSettings(None)

    def onCmdRefreshTriggerSettings(self, other):
        # trigger switch
        self.appSettings["triggerModeEnabled"] = self.triggerEnableSwitch.get()

        # handle trigger delay setting
        try:
            newDelaySetting = float(self.triggerDelayBox.get())
            self.appSettings["triggerDelay"] = str(newDelaySetting)
        except:
            newDelaySetting = float(self.appSettings["triggerDelay"])
            self.triggerDelayBox.delete(0, "end")
            self.triggerDelayBox.insert(0, str(newDelaySetting))

        # handle trigger level setting
        try:
            newLevelSetting = float(self.triggerLevelBox.get())
            self.appSettings["triggerLevel"] = str(newLevelSetting)
        except:
            newLevelSetting = float(self.appSettings["triggerLevel"])
            self.triggerLevelBox.delete(0, "end")
            self.triggerLevelBox.insert(0, str(newLevelSetting))

        # handle trigger hysteresis setting
        try:
            newHysteresisSetting = float(self.triggerHysteresisBox.get())
            self.appSettings["triggerHysteresis"] = str(newHysteresisSetting)
        except:
            newHysteresisSetting = float(self.appSettings["triggerHysteresis"])
            self.triggerHysteresisBox.delete(0, "end")
            self.triggerHysteresisBox.insert(0, str(newHysteresisSetting))

        self.updatePlot() # update plots to redraw the trigger cursor

    def onCmdRefreshCOMPorts(self):
        ports = serial.tools.list_ports.comports()
        self.currentlyAvailableCOMPorts.clear()
        for port, desc, hwid in sorted(ports):
            self.currentlyAvailableCOMPorts.append("{}".format(port))

        if len(self.currentlyAvailableCOMPorts) == 0:
            self.currentlyAvailableCOMPorts.append("NONE")

        self.zaberPortCombo.configure(values=self.currentlyAvailableCOMPorts)
        self.zaberPortCombo.set(self.currentlyAvailableCOMPorts[0])

        logging.info(f"COM ports refresh. Found: {self.currentlyAvailableCOMPorts}")

    def onCmdSingleCapture(self):
        self.appSettings["mfliSelectedFrequencyIndex"] = str(self.MFLIFreqneuenciesAsStrings.
                                                             index(self.samplingFreqCombo.get()))

        logging.info(f"Single capture started")
        self.settingsUsedForCurrentMeasurement = self.appSettings.copy()
        self.settingsUsedForCurrentMeasurement["averagingCount"] = 1

        if self.appSettings["triggerModeEnabled"] == "True":
            trgMode = True
        else:
            trgMode = False

        self.ApplicationController.performMeasurements(measurementsCount=1,
                                                    samplingFrequency=self.MFLIFreqneuenciesAsStrings.
                                                                            index(self.samplingFreqCombo.get()),
                                                    scanStart=int(self.appSettings["delayLineConfiguredScanStart"]),
                                                    scanLength=int(self.appSettings["delayLineConfiguredScanLength"]),
                                                    scanSpeed=float(self.appSettings["delayLineConfiguredScanSpeed"]),
                                                    trigModeEnabled=trgMode,
                                                    trigLevel=float(self.appSettings["triggerLevel"]),
                                                    trigHysteresis=float(self.appSettings["triggerHysteresis"]),
                                                    trigDelay=float(self.appSettings["triggerDelay"]))

    def onCmdMultipleCapture(self):

        try:
            measCount = int(self.appSettings["averagingCount"])
        except:
            logging.info(f"Multiple captures failed due to incorrect data in the measurement count setting")
            self.updateStatusMessage("Incorrect data in the\nmeasurement count setting")
            return

        self.appSettings["mfliSelectedFrequencyIndex"] = str(self.MFLIFreqneuenciesAsStrings.
                                                             index(self.samplingFreqCombo.get()))

        logging.info(f"Multiple captures with averaging started. Count = {measCount}")
        self.settingsUsedForCurrentMeasurement = self.appSettings.copy()

        if self.appSettings["triggerModeEnabled"] == "True":
            trgMode = True
        else:
            trgMode = False

        self.ApplicationController.performMeasurements(measurementsCount=measCount,
                                                    samplingFrequency=self.MFLIFreqneuenciesAsStrings.
                                                                                index(self.samplingFreqCombo.get()),
                                                    scanStart=int(self.appSettings["delayLineConfiguredScanStart"]),
                                                    scanLength=int(self.appSettings["delayLineConfiguredScanLength"]),
                                                    scanSpeed=float(self.appSettings["delayLineConfiguredScanSpeed"]),
                                                    trigModeEnabled=trgMode,
                                                    trigLevel=float(self.appSettings["triggerLevel"]),
                                                    trigHysteresis=float(self.appSettings["triggerHysteresis"]),
                                                    trigDelay=float(self.appSettings["triggerDelay"]))
    def onCmdStopMeasurement(self):
        self.ApplicationController.requestStop()

    def onCmdUpdateScanLengthFromSlider(self, other):
        sliderSetting = self.scanLengthSlider.get()
        self.scanLengthBox.delete(0, "end")
        self.scanLengthBox.insert(0, str(int(sliderSetting)))
        self.appSettings["delayLineConfiguredScanLength"] = str(sliderSetting)

    def onCmdUpdateScanLengthFromBox(self, other):
        minSetting = int(self.appSettings["delayLineMinimalScanLength"])
        maxSetting =  (ZaberDriver.DelayLineNominalLength -
                       (ZaberDriver.DelayLineNominalLength - int(self.appSettings["delayLineConfiguredScanStart"])))

        try:
            newSetting = int(self.scanLengthBox.get())
        except:
            newSetting = (maxSetting - minSetting) / 2

        if newSetting > maxSetting:
            newSetting = maxSetting
        elif newSetting < minSetting:
            newSetting = minSetting

        self.scanLengthBox.delete(0, "end")
        self.scanLengthBox.insert(0, str(newSetting))
        self.scanLengthSlider.set(newSetting)
        self.appSettings["delayLineConfiguredScanLength"] = str(newSetting)

    def onExportSwitchModified(self):
        self.appSettings["saveDataToMAT"] = self.exportToMatSwitch.get()
        self.appSettings["saveRawData"] = self.exportRawDataSwitch.get()

        print(self.appSettings["saveDataToMAT"])
        print(self.appSettings["saveRawData"])

    def onCmdUpdateStartingPositionFromBox(self, other):
        minSetting = 2000
        maxSetting = ZaberDriver.DelayLineNominalLength

        try:
            newSetting = int(self.startingPosBox.get())
        except:
            newSetting = 149000

        if newSetting > maxSetting:
            newSetting = maxSetting
        elif newSetting < minSetting:
            newSetting = minSetting

        self.startingPosBox.delete(0, "end")
        self.startingPosBox.insert(0, str(newSetting))

        self.appSettings["delayLineConfiguredScanStart"] = str(newSetting)
        configuredStartingPosition = int(self.appSettings["delayLineConfiguredScanStart"])
        minimalScanLength = int(self.appSettings["delayLineMinimalScanLength"])

        logging.info(f"Scan starting position set to: {configuredStartingPosition}")

        # make sure scan length settings are valid and slider is configured correctly
        self.scanLengthSlider.configure(to=ZaberDriver.DelayLineNominalLength -
                                           (ZaberDriver.DelayLineNominalLength -
                                           configuredStartingPosition))
        self.scanLengthSlider.configure(number_of_steps=(ZaberDriver.DelayLineNominalLength -
                                                    (ZaberDriver.DelayLineNominalLength -
                                                    configuredStartingPosition) -
                                                    minimalScanLength) / 100)
        # use this command to make sure settings are ok
        self.onCmdUpdateScanLengthFromBox(None)

    def onCmdScanSpeedUpdateFromSlider(self, other):
        configuredScanSpeed = self.scanSpeedSlider.get()
        self.scanSpeedValueLabel.configure(text=str(int(configuredScanSpeed)))
        self.appSettings["delayLineConfiguredScanSpeed"] = str(configuredScanSpeed)

    def onCmdUpdateAveragingCount(self, other):

        try:
            newSetting = int(self.multipleMeasBox.get().replace(' ', '').replace('\t', '').replace('\n', '').replace(
            '\r', ''))

            if 1 < newSetting <= 10000:
                self.appSettings["averagingCount"] = str(newSetting)
                self.multipleMeasBox.delete(0, "end")
                self.multipleMeasBox.insert(0, self.appSettings["averagingCount"])
            else:
                self.multipleMeasBox.delete(0, "end")
                self.multipleMeasBox.insert(0, self.appSettings["averagingCount"])

        except:
            self.multipleMeasBox.delete(0, "end")
            self.multipleMeasBox.insert(0, self.appSettings["averagingCount"])

    def onCmdUnusedButton(self):
        print("Unused button click")


    def onCmdOpenAbsorbanceTool(self):
        self.absorbanceToolWindow = AbsorbanceTool.AbsorbanceTool(self.root, self.appSettings, self.plotLineColor)

        self.absorbanceToolWindow.grabSampleSpectrumDataAverage = self.giveSpectrumForAbsorbanceAverage
        self.absorbanceToolWindow.grabReferenceSpectrumDataAverage = self.giveSpectrumForAbsorbanceAverage
        self.absorbanceToolWindow.grabSampleSpectrumDataLast = self.giveSpectrumForAbsorbanceLast
        self.absorbanceToolWindow.grabReferenceSpectrumDataLast = self.giveSpectrumForAbsorbanceLast
        self.absorbanceToolWindow.grabApplicationSettings = self.getApplicationSettings
        self.absorbanceToolWindow.setApplicationSettings = self.setApplicationSettings

    def onCmdUpdateSpectrumPlotRanges(self, other):
        self.appSettings["plotSpectrumXRangeMin"] = self.spectrumXMinBox.get()
        self.appSettings["plotSpectrumXRangeMax"] = self.spectrumXMaxBox.get()
        self.appSettings["plotSpectrumYRangeMin"] = self.spectrumYMinBox.get()
        self.appSettings["plotSpectrumYRangeMax"] = self.spectrumYMaxBox.get()

        ymin = float(self.appSettings["plotSpectrumYRangeMin"])
        ymax = float(self.appSettings["plotSpectrumYRangeMax"])
        xmin = float(self.appSettings["plotSpectrumXRangeMin"])
        xmax = float(self.appSettings["plotSpectrumXRangeMax"])

        self.axBot.set_xlim(xmin, xmax)
        self.axBot.set_ylim(ymin, ymax)

        logging.info(f"Spectrum plot ranges updated to: X({xmin},{xmax}) Y({ymin},{ymax})")

        self.canvasBotPlot.draw()
        self.root.update()

    def onCmdConnectHardware(self):
        strippedMFLIID = self.mfliIDBox.get("0.0", "end").replace(' ', '').replace('\t', '').replace('\n', '').replace(
            '\r', '')

        strippedZaberPort = self.zaberPortCombo.get().replace(' ', '').replace('\t', '').replace('\n', '').replace(
            '\r', '')

        logging.info(f"Attempting to connect to hardware. Zaber port: {strippedZaberPort} and MFLI devID: {strippedMFLIID}")
        self.ApplicationController.setZaberPort(strippedZaberPort)
        self.ApplicationController.setMFLIDeviceName(strippedMFLIID)
        self.ApplicationController.performInitialization()

    def onCmdOpenSpectrumPlot(self):
        logging.info(f"External spectrum plot open")

        mpl.rcParams.update(mpl.rcParamsDefault)
        plt.figure()
        plt.locator_params(nbins=15)
        plt.rc('xtick', labelsize=18)
        plt.rc('ytick', labelsize=18)
        plt.title("Spectrum", fontsize=20)
        plt.xlabel("Wavelength [\u03BCm]", fontsize=20)
        plt.ylabel("Intensity [dBm]", fontsize=20)
        plt.plot(self.currentAverageSpectrumX, self.currentAverageSpectrumY, color="dodgerblue")
        plt.xlim((float(self.appSettings["plotSpectrumXRangeMin"]), float(self.appSettings["plotSpectrumXRangeMax"])))
        plt.ylim((float(self.appSettings["plotSpectrumYRangeMin"]), float(self.appSettings["plotSpectrumYRangeMax"])))
        plt.grid(alpha=0.3)
        plt.ion()
        plt.pause(1.0)
        plt.show()
        plt.pause(1.0)
        plt.ioff()

    def onCmdOpenInterferogramPlot(self):
        logging.info(f"External interferogram plot open")

        mpl.rcParams.update(mpl.rcParamsDefault)
        plt.figure()
        plt.locator_params(nbins=15)
        plt.rc('xtick', labelsize=18)
        plt.rc('ytick', labelsize=18)
        plt.title("Interferogram", fontsize=20)
        plt.xlabel("Position [\u03BCm]", fontsize=20)
        plt.ylabel("Detector voltage [V]", fontsize=20)
        plt.plot(self.currentInterferogramX, self.currentInterferogramY)
        plt.xlim((min(self.currentInterferogramX), max(self.currentInterferogramX)))
        plt.grid(alpha=0.3)
        plt.ion()
        plt.pause(1.0)
        plt.show()
        plt.pause(1.0)
        plt.ioff()

    def onCmdReferencePlot(self):
        logging.info(f"Reference signal plot open")

        mpl.rcParams.update(mpl.rcParamsDefault)
        plt.figure()
        plt.locator_params(nbins=15)
        plt.rc('xtick', labelsize=18)
        plt.rc('ytick', labelsize=18)
        plt.title("Raw data with reference signal", fontsize=20)
        plt.xlabel("Sample num", fontsize=20)
        plt.ylabel("Detector voltage [V]", fontsize=20)
        plt.plot(self.MFLIDrv.lastReferenceData, alpha=0.75)
        plt.plot(self.MFLIDrv.lastInterferogramData)
        plt.grid(alpha=0.3)
        plt.ion()
        plt.pause(1.0)
        plt.show()
        plt.pause(1.0)
        plt.ioff()

    def onCmdSaveCSVOnly(self):
        DataExportTool.exportSpectrumAsCSV(self.currentSpectrumX, self.currentSpectrumY)

    def onCmdSaveFull(self):

        self.settingsUsedForCurrentMeasurement["saveDataToMAT"] = self.appSettings["saveDataToMAT"]
        self.settingsUsedForCurrentMeasurement["saveRawData"] = self.appSettings["saveRawData"]

        DataExportTool.exportAllDataMultipleMeasurements(
            averageSpectrumX            = self.currentAverageSpectrumX,
            averageSpectrumY            = self.currentAverageSpectrumY,
            rawSpectraX                 = self.ApplicationController.spectraX,
            rawSpectraY                 = self.ApplicationController.spectraY,
            correctedInterferogramsX    = self.ApplicationController.processedInterferogramsX,
            correctedInterferogramsY    = self.ApplicationController.processedInterferogramsY,
            interferogramsRaw           = self.ApplicationController.rawInterferograms,
            referenceSignalsRaw         = self.ApplicationController.rawReferenceSignals,
            settings                    = self.settingsUsedForCurrentMeasurement
        )

    def onClosing(self):
        SM.saveSettingsToFile(self.appSettings)
        # make sure the application closes properly when the main window is destroyed
        logging.info('========= Application closed =========\n\n\n')
        sys.exit()

    def updatePlot(self):
        self.loadDataToPlots(self.currentInterferogramX, self.currentInterferogramY,
                             self.currentSpectrumX, self.currentSpectrumY,
                             self.currentAverageSpectrumX, self.currentAverageSpectrumY, 0)

    def giveSpectrumForAbsorbanceLast(self):
        return ('Wavelength [\u03BCm]', 'Intensity [dBm]',
                self.currentSpectrumX.copy(), self.currentSpectrumY.copy())

    def giveSpectrumForAbsorbanceAverage(self):
        return ('Wavelength [\u03BCm]', 'Intensity [dBm]',
                self.currentAverageSpectrumX.copy(), self.currentAverageSpectrumY.copy())
    def loadDataToPlots(self, interferogramX, interferogramY, spectrumX, spectrumY, averageSpectrumX, averageSpectrumY,
                        completedMeasurements):

        # self.currentInterferogramX = interferogramX
        # self.currentInterferogramY = interferogramY
        # self.currentSpectrumX = spectrumX
        # self.currentSpectrumY = spectrumY
        # self.currentAverageSpectrumX = averageSpectrumX
        # self.currentAverageSpectrumY = averageSpectrumY

        if completedMeasurements != 0:
            self.multipleMeasBox.delete(0, "end")
            self.multipleMeasBox.insert(0,
                                    f"{completedMeasurements}/{self.ApplicationController.orderedMeasurementsCount}")

        plt.style.use('dark_background')
        self.axBot.clear()
        self.axTop.clear()

        # plot spectrum
        self.axBot.grid(color="dimgrey", linestyle='-', linewidth=1, alpha=0.6)

        if ((spectrumX is not None) and (spectrumY is not None) and
                (len(spectrumX) == len(spectrumY)) and (len(spectrumX) > 0)):

            self.axBot.plot(spectrumX, spectrumY, color="grey", alpha=0.7)

        if ((averageSpectrumX is not None) and (averageSpectrumY is not None) and
                (len(averageSpectrumX) == len(averageSpectrumY)) and (len(averageSpectrumX) > 0)):

            self.axBot.plot(averageSpectrumX, averageSpectrumY, color=self.plotLineColor)


        self.axBot.set_xlim(float(self.appSettings["plotSpectrumXRangeMin"]),
                            float(self.appSettings["plotSpectrumXRangeMax"]))
        self.axBot.set_ylim(float(self.appSettings["plotSpectrumYRangeMin"]),
                            float(self.appSettings["plotSpectrumYRangeMax"]))

        self.axBot.set_xlabel('Wavelength [\u03BCm]')
        self.axBot.set_ylabel('[dBm]')

        # plot interferogram
        self.axTop.grid(color="dimgrey", linestyle='-', linewidth=1, alpha=0.6)

        interferogramValidForDisplay = False
        if (interferogramX is not None and interferogramY is not None and
                len(interferogramX) == len(interferogramY) and len(interferogramX) > 0):

            interferogramValidForDisplay = True

        # draw trigger and hysteresis cursors
        if self.appSettings["triggerModeEnabled"] == 'True':
            # make sure the markers will be displayed correctly even if there is no interferogram loaded
            if interferogramValidForDisplay:
                triggerMarkerX = [np.min(interferogramX), np.max(interferogramX)]
                hysteresisMarkerX = [np.min(interferogramX), np.max(interferogramX)]
            else:
                triggerMarkerX = [0.0, 1.0]
                hysteresisMarkerX = [0.0, 1.0]
                self.axTop.set_xlim(0.0, 1.0)
                self.axTop.set_ylim(- float(self.appSettings["triggerLevel"]) / 1000.0 - 0.1,
                                    float(self.appSettings["triggerLevel"]) / 1000.0 + 0.1)

            triggerMarkerY = [float(self.appSettings["triggerLevel"]) / 1000.0,
                       float(self.appSettings["triggerLevel"]) / 1000.0]

            self.axTop.plot(triggerMarkerX, triggerMarkerY, color="red", alpha=0.75,
                            label="Trigger", linestyle="dashed")

            hysteresisMarkerYVal = ((float(self.appSettings["triggerLevel"]) / 1000.0) -
                                    (float(self.appSettings["triggerHysteresis"]) / 1000.0))

            hysteresisMarkerY = [hysteresisMarkerYVal, hysteresisMarkerYVal]

            self.axTop.plot(hysteresisMarkerX, hysteresisMarkerY, color="lime", alpha=0.75,
                            label="Hysteresis", linestyle="dashed")

            self.axTop.set_xlabel('Mirror position [\u03BCm]')
            self.axTop.set_ylabel('Detector voltage [V]')

        # plot the interferogram itself
        if interferogramValidForDisplay:
            self.axTop.plot(interferogramX, interferogramY, color=self.plotLineColor, label="Signal")
            self.axTop.set_xlim(np.min(interferogramX), np.max(interferogramX))

        if self.appSettings["triggerModeEnabled"] == 'True':
            self.axTop.legend()

        self.canvasTopPlot.draw()
        self.canvasBotPlot.draw()
        self.root.update()


# run the app
if __name__ == "__main__":
    CTK_Window = FTSApp()
