import os
import customtkinter as ctk
import numpy as np
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

class FTSApp:

    def __init__(self):

        logging.basicConfig(filename='ftsapp.log', format='%(asctime)s %(message)s', level=logging.INFO)
        logging.info('========= Application started =========')

        if SM.isSettingsFileAvailable():
            self.appSettings = SM.readSettingsFromFile()
            SM.validateAndFixSettings(self.appSettings)
        else:
            self.appSettings = SM.getDefaultSettings()

        self.settingsUsedForCurrentMeasurement = self.appSettings.copy()

        # constants
        self.backgroundGray = "#242424"
        self.currentSpectrumX = []
        self.currentSpectrumY = []
        self.currentInterferogramX = []
        self.currentInterferogramY = []

        self.currentlyAvailableCOMPorts = []

        # construct GUI
        ctk.set_appearance_mode("dark")
        self.root = ctk.CTk()
        self.root.geometry("1200x800")
        self.root.minsize(800, 800)
        self.root.title("FTS App")
        self.root.iconbitmap(default='icon.ico')
        # self.root.attributes('-fullscreen',True)

        self.root.resizable(True, True)
        self.root.state('zoomed')

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
        self.frameTopPlot = ctk.CTkFrame(master=self.root,
                                         fg_color="darkblue")

        self.frameTopPlot.grid(row=0, column=1, padx=(5, 5), pady=0)#, sticky="N")

        self.frameBottomPlot = ctk.CTkFrame(master=self.root,
                                            fg_color="darkblue")
        # self.frame.place(relx=0.33, rely=0.025)
        self.frameBottomPlot.grid(row=1, column=1, padx=(5, 5), pady=0)#, sticky="N")

        # buttons
        # create a frame to hold all the buttons related to measurements
        self.frameButtonsTop = ctk.CTkFrame(master=self.root,
                                            height=60,
                                            width=120,
                                            fg_color="dimgrey",
                                            corner_radius=10)
        self.frameButtonsTop.grid(row=0, column=0, sticky="NSEW", padx=5, pady=5)

        self.frameButtonsTop.columnconfigure(0, weight=1)
        self.frameButtonsTop.columnconfigure(1, weight=1)

        self.buttonSingle = ctk.CTkButton(master=self.frameButtonsTop,
                                          text="Single\ncapture",
                                          width=120,
                                          height=80,
                                          corner_radius=10,
                                          command=self.onCmdSingleCapture)
        self.buttonSingle.grid(row=0, column=0, sticky="N", padx=5, pady=5)

        self.buttonArchive = ctk.CTkButton(master=self.frameButtonsTop,
                                           text="Archive\nviewer",
                                           width=120,
                                           height=80,
                                           corner_radius=10,
                                           command=self.onCmdUnusedButton)
        self.buttonArchive.grid(row=0, column=1, sticky="N", padx=5, pady=5)

        self.buttonInterferogram = ctk.CTkButton(master=self.frameButtonsTop,
                                                 text="Open\ninterfer.\nplot",
                                                 width=120,
                                                 height=80,
                                                 corner_radius=10,
                                                 command=self.onCmdOpenInterferogramPlot)
        self.buttonInterferogram.grid(row=1, column=0, sticky="N", padx=5, pady=5)

        self.buttonSpectrum = ctk.CTkButton(master=self.frameButtonsTop,
                                            text="Open\nspectrum\nplot",
                                            width=120,
                                            height=80,
                                            corner_radius=10,
                                            command=self.onCmdOpenSpectrumPlot)
        self.buttonSpectrum.grid(row=1, column=1, sticky="N", padx=5, pady=5)

        # create a frame to hold all the buttons related to settings and configuration
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
        self.settingsTabs.add("Hardware")
        self.settingsTabs.add("Plots")
        self.settingsTabs.add("Export")

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
        self.settingsTabs.tab("Export").columnconfigure(0, weight=1)
        self.settingsTabs.tab("Export").columnconfigure(1, weight=1)

        self.settingsTabs.tab("Export").columnconfigure(0, weight=1)
        self.settingsTabs.tab("Export").columnconfigure(1, weight=1)

        self.buttonSaveNormal = ctk.CTkButton(master=self.settingsTabs.tab("Export"),
                                            text="Save\nresults",
                                            width=120,
                                            height=80,
                                            corner_radius=10,
                                            command=self.onCmdSaveFull)
        self.buttonSaveNormal.grid(row=0, column=0, sticky="N", padx=5, pady=5)

        self.buttonSaveCSV = ctk.CTkButton(master=self.settingsTabs.tab("Export"),
                                            text="Save\nspectrum\nas .csv",
                                            width=120,
                                            height=80,
                                            corner_radius=10,
                                            command=self.onCmdSaveCSVOnly)
        self.buttonSaveCSV.grid(row=0, column=1, sticky="N", padx=5, pady=5)

        # configure settings 'PLOTS' tab
        # ==============================================================================================================
        self.settingsTabs.tab("Plots").columnconfigure(0, weight=1)
        self.settingsTabs.tab("Plots").columnconfigure(1, weight=1)

        self.settingsTabs.tab("Plots").columnconfigure(0, weight=1)
        self.settingsTabs.tab("Plots").columnconfigure(1, weight=1)

        self.spectrumXMinLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Plots"),
                                                    text="Spectrum plot\nrng X MIN [\u03BCm]",
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
                                                    text="Spectrum plot\nrng X MAX [\u03BCm]",
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
                                                    text="Spectrum plot\nrng Y MIN [\u03BCm]",
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
                                                    text="Spectrum plot\nrng Y MAX [\u03BCm]",
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
        self.axBot.set_ylabel('[a.u.]')
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
        self.axBot.set_yscale("log")


        # create a status bar
        self.statusLabel = ctk.CTkLabel(master=self.root,
                                        text="Status bar",
                                        font=ctk.CTkFont(size=12))
        self.statusLabel.grid(row=0, column=1, columnspan=2, sticky="NE", padx=15, pady=5)

        # create drivers
        # self.updateStatusMessage("Connecting to MFLI...")
        self.MFLIDrv = MFLIDriver(self.mfliIDBox.get("0.0", "end"))

        # self.updateStatusMessage("Connecting to Zaber...")
        self.ZaberDrv = ZaberDriver()

        # if self.MFLIDrv.isConnected and self.ZaberDrv.isConnected:
        #     self.updateStatusMessage("Automatic hardware\nconnection successful")
        # else:
        #     self.updateStatusMessage("One or more hardware components\nfailed to connect")

        # set up the background application controller
        self.ApplicationController = BackgroundController(self.MFLIDrv, self.ZaberDrv)
        self.ApplicationController.SetStatusMessageMethod = self.updateStatusMessage
        self.ApplicationController.SetGeneralReadyFlagMethod = self.setGeneralReadyFlag
        self.ApplicationController.SetDAQReadyFlagMethod = self.setDAQReadyFlag
        self.ApplicationController.SetDelayLineReadyFlagMethod = self.setDelayLineReadyFlag
        self.ApplicationController.SendResultsToPlot = self.receiveMeasurementResults

        # try to connect to all the hardware with some default settings
        self.ApplicationController.MFLIDeviceName = self.mfliIDBox.get("0.0", "end")
        self.ApplicationController.ZaberPort = self.zaberPortCombo.get().replace(' ', '').replace(
            '\t', '').replace('\n', '').replace('\r', '')

        # self.ApplicationController.performInitialization()
        # run the app
        self.root.update()
        self.root.mainloop()

    def updateStatusMessage(self, message):
        self.statusLabel.configure(text=message)
        logging.info(f"Status bar message set to: {message}")
        self.root.update()

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

    def receiveMeasurementResults(self, interfX, interfY, spectrumX, spectrumY):
        self.currentSpectrumX = spectrumX
        self.currentSpectrumY = spectrumY
        self.currentInterferogramX = interfX
        self.currentInterferogramY = interfY
        self.updatePlot()

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
        logging.info(f"Single capture started")
        self.settingsUsedForCurrentMeasurement = self.appSettings.copy()
        self.ApplicationController.performMeasurements(measurementsCount=1,
                                                       samplingFrequency=self.MFLIFreqneuenciesAsStrings.
                                                                                index(self.samplingFreqCombo.get()),
                                                       scanStart=int(self.appSettings["delayLineConfiguredScanStart"]),
                                                       scanLength=int(self.appSettings["delayLineConfiguredScanLength"]),
                                                       scanSpeed=float(self.appSettings["delayLineConfiguredScanSpeed"]))

        self.appSettings["mfliSelectedFrequencyIndex"] = str(self.MFLIFreqneuenciesAsStrings.
                                                             index(self.samplingFreqCombo.get()))


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

    def onCmdUnusedButton(self):
        print("Unused button click")

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
        plt.figure()
        plt.title("Spectrum")
        plt.plot(self.currentSpectrumX, self.currentSpectrumY)
        plt.yscale("log")
        plt.ion()
        plt.pause(1.0)
        plt.show()
        plt.pause(1.0)
        plt.ioff()

    def onCmdOpenInterferogramPlot(self):
        logging.info(f"External interferogram plot open")
        plt.figure()
        plt.title("Interferogram")
        plt.plot(self.currentInterferogramX, self.currentInterferogramY)
        plt.ion()
        plt.pause(1.0)
        plt.show()
        plt.pause(1.0)
        plt.ioff()

    def onCmdSaveCSVOnly(self):
        DataExportTool.exportSpectrumAsCSV(self.currentSpectrumX, self.currentSpectrumY)

    def onCmdSaveFull(self):
        self.currentSpectrumX = np.arange(100)
        self.currentSpectrumY = np.sin(self.currentSpectrumX)

        self.currentInterferogramX = np.arange(100)
        self.currentInterferogramY = np.cos(self.currentInterferogramX)

        DataExportTool.exportAllData(
            spectrumX = self.currentSpectrumX,
            spectrumY = self.currentSpectrumY,
            interferogramX = self.currentInterferogramX,
            interferogramY = self.currentInterferogramY,
            interferogramRaw = np.arange(100), #self.MFLIDrv.lastInterferogramData,
            referenceSignalRaw = np.arange(100), #self.MFLIDrv.lastReferenceData,
            settings = self.settingsUsedForCurrentMeasurement
        )
    def onClosing(self):
        SM.saveSettingsToFile(self.appSettings)
        # make sure the application closes properly when the main window is destroyed
        logging.info('========= Application closed =========\n\n\n')
        sys.exit()

    def updatePlot(self):
        self.loadDataToPlots(self.currentInterferogramX, self.currentInterferogramY,
                             self.currentSpectrumX, self.currentSpectrumY)

    def loadDataToPlots(self, interferogramX, interferogramY, spectrumX, spectrumY):

        self.axBot.clear()
        self.axTop.clear()

        if len(spectrumX) == len(spectrumY) and len(spectrumX) > 0:
            self.axBot.grid(color="dimgrey", linestyle='-', linewidth=1, alpha=0.6)
            self.axBot.plot(spectrumX, spectrumY, color="dodgerblue")
            self.axBot.set_xlim(float(self.appSettings["plotSpectrumXRangeMin"]),
                                float(self.appSettings["plotSpectrumXRangeMax"]))
            self.axBot.set_ylim(float(self.appSettings["plotSpectrumYRangeMin"]),
                                float(self.appSettings["plotSpectrumYRangeMax"]))
            self.axBot.set_yscale("log")

            self.axBot.set_xlabel('Wavelength [\u03BCm]')
            self.axBot.set_ylabel('[a.u.]')


        if len(interferogramX) == len(interferogramY) and len(interferogramX) > 0:
            self.axTop.grid(color="dimgrey", linestyle='-', linewidth=1, alpha=0.6)
            self.axTop.plot(interferogramX, interferogramY, color="dodgerblue")
            self.axTop.set_xlim(np.min(interferogramX), np.max(interferogramX))

            self.axTop.set_xlabel('Mirror position [\u03BCm]')
            self.axTop.set_ylabel('Detector voltage [V]')

        self.canvasTopPlot.draw()
        self.canvasBotPlot.draw()
        self.root.update()


# run the app
if __name__ == "__main__":
    CTK_Window = FTSApp()
