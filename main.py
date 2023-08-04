import customtkinter as ctk
from PIL import Image, ImageOps
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

class FTSApp:

    def __init__(self):
        # constants
        self.backgroundGray = "#242424"
        self.configuredStartingPosition = 149000
        self.configuredScanLength = 50000
        self.minimalScanLength = 1000
        self.minSpeed = 1   # mm/s
        self.maxSpeed = 50  # mm/s
        self.configuredScanSpeed = 5 # mm/s

        self.currentSpectrumX = []
        self.currentSpectrumY = []
        self.currentInterferogramX = []
        self.currentInterferogramY = []

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
                                         height=60,
                                         width=120,
                                         fg_color="darkblue")

        self.frameTopPlot.grid(row=0, column=1, padx=(15, 5), pady=0, sticky="NE")

        self.frameBottomPlot = ctk.CTkFrame(master=self.root,
                                            height=60,
                                            width=120,
                                            fg_color="darkblue")
        # self.frame.place(relx=0.33, rely=0.025)
        self.frameBottomPlot.grid(row=1, column=1, padx=(15, 5), pady=0, sticky="NE")

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

        # create a frame to hold all the buttons related to measurements
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
        self.samplingFreqCombo.set(self.MFLIFreqneuenciesAsStrings[9])

        self.startingPosLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Scan"),
                                                    text="Start\nposition [\u03BCm]",
                                                    font=ctk.CTkFont(size=12))
        self.startingPosLabel.grid(row=1, column=0, sticky="E", padx=5, pady=5)

        self.startingPosBox = ctk.CTkEntry(master=self.settingsTabs.tab("Scan"),
                                        width=120, height=30)
        self.startingPosBox.insert(0, str(self.configuredStartingPosition))
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
        self.scanLengthBox.insert(0, str(self.configuredScanLength))
        self.scanLengthBox.grid(row=2, column=1, sticky="E", padx=5, pady=5)
        self.scanLengthBox.bind("<FocusOut>", self.onCmdUpdateScanLengthFromBox)
        self.scanLengthBox.bind("<Return>", self.onCmdUpdateScanLengthFromBox)

        self.scanLengthSlider = ctk.CTkSlider(master=self.settingsTabs.tab("Scan"),
                                              width=250,
                                              height=20,
                                              from_=self.minimalScanLength,
                                              to=ZaberDriver.DelayLineNominalLength -
                                                 (ZaberDriver.DelayLineNominalLength - self.configuredStartingPosition),
                                              number_of_steps=(ZaberDriver.DelayLineNominalLength -
                                                             (ZaberDriver.DelayLineNominalLength -
                                                             self.configuredStartingPosition) -
                                                             self.minimalScanLength) / 100,
                                              command=self.onCmdUpdateScanLengthFromSlider)
        self.scanLengthSlider.grid(row=3, column=0, columnspan=2, sticky="N", padx=5, pady=5)
        self.scanLengthSlider.set(self.configuredScanLength)

        self.scanSpeedLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Scan"),
                                                    text="Scan speed\n[mm/s]",
                                                    font=ctk.CTkFont(size=12))
        self.scanSpeedLabel.grid(row=4, column=0, sticky="E", padx=5, pady=5)

        self.scanSpeedValueLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Scan"),
                                                    text=str(self.configuredScanSpeed),
                                                    font=ctk.CTkFont(size=12))
        self.scanSpeedValueLabel.grid(row=4, column=1, sticky="W", padx=5, pady=5)

        self.scanSpeedSlider = ctk.CTkSlider(master=self.settingsTabs.tab("Scan"),
                                              width=250,
                                              height=20,
                                              from_=self.minSpeed,
                                              to=self.maxSpeed,
                                              number_of_steps=49,
                                              command=self.onCmdScanSpeedUpdateFromSlider)
        self.scanSpeedSlider.grid(row=5, column=0, columnspan=2, sticky="N", padx=5, pady=5)
        self.scanSpeedSlider.set(self.configuredScanSpeed)


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
        self.mfliIDBox.insert("0.0", "dev6285")
        self.mfliIDBox.grid(row=4, column=1, sticky="E", padx=5, pady=5)

        self.buttonHardware = ctk.CTkButton(master=self.settingsTabs.tab("Hardware"),
                                            text="Reconnect\nall",
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

        # configure settings 'SAVE' tab
        # ==============================================================================================================
        self.settingsTabs.tab("Save").columnconfigure(0, weight=1)
        self.settingsTabs.tab("Save").columnconfigure(1, weight=1)


        # Create plots
        # ==============================================================================================================
        plt.style.use('dark_background')
        self.figTop, self.axTop = plt.subplots()
        self.figTop.suptitle("Interferogram")
        self.figTop.set_facecolor(self.backgroundGray)
        self.figTop.set_size_inches(100, 100)
        # self.figTop.set_size_inches(15, 4.75)
        self.figTop.subplots_adjust(left=0.1, right=0.99, bottom=0.01, top=0.97, wspace=0, hspace=0)
        self.figTop.set_tight_layout(True)
        self.canvasTopPlot = FigureCanvasTkAgg(self.figTop, master=self.frameTopPlot)
        self.canvasTopPlot.get_tk_widget().pack(side='right', fill='both', expand=True)
        self.canvasTopPlot.draw()

        self.figBot, self.axBot = plt.subplots()
        self.figBot.suptitle("Spectrum")
        self.figBot.set_facecolor(self.backgroundGray)
        self.figBot.set_size_inches(100, 100)
        # self.figBot.set_size_inches(15, 4.75)
        self.figBot.subplots_adjust(left=0.1, right=0.99, bottom=0.01, top=0.97, wspace=0, hspace=0)
        self.figBot.set_tight_layout(True)
        self.canvasBotPlot = FigureCanvasTkAgg(self.figBot, master=self.frameBottomPlot)
        self.canvasBotPlot.get_tk_widget().pack(side='right', fill='both', expand=True)
        self.canvasBotPlot.draw()

        self.updatePlot()
        plt.close()
        plt.close()

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

        self.ApplicationController.performInitialization()

        # run the app
        self.root.update()
        self.root.mainloop()

    def updateStatusMessage(self, message):
        self.statusLabel.configure(text=message)
        self.root.update()

    def setGeneralReadyFlag(self, isReady):
        if isReady:
            self.hardwareStatusLabel.configure(text="READY", text_color="lightgreen")
        else:
            self.hardwareStatusLabel.configure(text="NOT\nREADY", text_color="red")

    def setDAQReadyFlag(self, isReady):
        if isReady:
            self.mfliStatusLabel.configure(text="READY", text_color="lightgreen")
        else:
            self.mfliStatusLabel.configure(text="NOT\nREADY", text_color="red")

    def setDelayLineReadyFlag(self, isReady):
        if isReady:
            self.zaberStatusLabel.configure(text="READY", text_color="lightgreen")
        else:
            self.zaberStatusLabel.configure(text="NOT\nREADY", text_color="red")

    def receiveMeasurementResults(self, interfX, interfY, spectrumX, spectrumY):
        self.currentSpectrumX = spectrumX
        self.currentSpectrumY = spectrumY
        self.currentInterferogramX = interfX
        self.currentInterferogramY = interfY
        self.updatePlot()

    def onCmdRefreshCOMPorts(self):
        ports = serial.tools.list_ports.comports()
        portsList = []
        for port, desc, hwid in sorted(ports):
            portsList.append("{}".format(port))

        if len(portsList) == 0:
            portsList.append("NONE")

        self.zaberPortCombo.configure(values=portsList)
        self.zaberPortCombo.set(portsList[0])

    def onCmdSingleCapture(self):
        self.ApplicationController.performMeasurements(measurementsCount=1,
                                                       samplingFrequency=self.MFLIFreqneuenciesAsStrings.
                                                                                index(self.samplingFreqCombo.get()),
                                                       scanStart=self.configuredStartingPosition,
                                                       scanLength=self.configuredScanLength,
                                                       scanSpeed=self.configuredScanSpeed)
        # self.updateStatusMessage("Single capture in progress...")
        # print(self.MFLIFreqneuenciesAsStrings.index(self.samplingFreqCombo.get()))
        # self.MFLIDrv.configureForMeasurement(self.MFLIFreqneuenciesAsStrings.index(self.samplingFreqCombo.get()), 1000)
        # self.MFLIDrv.measureData()
        #
        # self.currentInterferogramY = self.MFLIDrv.lastInterferogramData
        # self.currentInterferogramX = np.arange(len(self.currentInterferogramY))
        #
        # self.currentSpectrumY = self.MFLIDrv.lastReferenceData
        # self.currentSpectrumX = np.arange(len(self.currentSpectrumY))
        #
        # self.updatePlot()
        # self.updateStatusMessage("Single capture done")

    def onCmdUpdateScanLengthFromSlider(self, other):
        sliderSetting = self.scanLengthSlider.get()
        self.scanLengthBox.delete(0, "end")
        self.scanLengthBox.insert(0, str(int(sliderSetting)))
        self.configuredScanLength = sliderSetting

    def onCmdUpdateScanLengthFromBox(self, other):
        minSetting = 1000
        maxSetting =  (ZaberDriver.DelayLineNominalLength -
                       (ZaberDriver.DelayLineNominalLength - self.configuredStartingPosition))

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
        self.configuredScanLength = newSetting

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
        self.configuredStartingPosition = newSetting

        # make sure scan length settings are valid and slider is configured correctly
        self.scanLengthSlider.configure(to=ZaberDriver.DelayLineNominalLength -
                                           (ZaberDriver.DelayLineNominalLength -
                                           self.configuredStartingPosition))
        self.scanLengthSlider.configure(number_of_steps=(ZaberDriver.DelayLineNominalLength -
                                                    (ZaberDriver.DelayLineNominalLength -
                                                    self.configuredStartingPosition) -
                                                    self.minimalScanLength) / 100)
        # use this command to make sure settings are ok
        self.onCmdUpdateScanLengthFromBox(None)

    def onCmdScanSpeedUpdateFromSlider(self, other):
        self.configuredScanSpeed = self.scanSpeedSlider.get()
        self.scanSpeedValueLabel.configure(text=str(int(self.configuredScanSpeed)))

    def onCmdUnusedButton(self):
        self.ZaberDrv.setPosition(75000)
        self.ZaberDrv.waitUntilIdle()
        self.ZaberDrv.setPosition(10000)
        print("Unused button click")

    def onCmdConnectHardware(self):
        strippedMFLIID = self.mfliIDBox.get("0.0", "end").replace(' ', '').replace('\t', '').replace('\n', '').replace(
            '\r', '')

        strippedZaberPort = self.zaberPortCombo.get().replace(' ', '').replace('\t', '').replace('\n', '').replace(
            '\r', '')

        if self.MFLIDrv.isConnected and self.MFLIDrv.deviceID == strippedMFLIID:
            # the correct MFLI is currently connected and no further action is required
            print("Correct MFLI is already connected")
        else:
            if self.MFLIDrv.tryConnect(strippedMFLIID):
                print("Connection to MFLI successful")
            else:
                print("Connection to MFLI failed")

        if strippedZaberPort != "NONE":
            if self.ZaberDrv.tryConnect(strippedZaberPort):
                print(f"Zaber connected at {strippedZaberPort}")
            else:
                print(f"Zaber failed to connect at {strippedZaberPort}")
        else:
            self.updateStatusMessage("Invalid COM for Zaber")

    def onCmdOpenSpectrumPlot(self):
        plt.figure()
        plt.title("Spectrum")
        plt.plot(self.currentSpectrumX, self.currentSpectrumY)
        plt.ion()
        plt.pause(1.0)
        plt.show()
        plt.pause(1.0)
        plt.ioff()

    def onCmdOpenInterferogramPlot(self):
        plt.figure()
        plt.title("Interferogram")
        plt.plot(self.currentInterferogramX, self.currentInterferogramY)
        plt.ion()
        plt.pause(1.0)
        plt.show()
        plt.pause(1.0)
        plt.ioff()

    # def onCmdConfigureHardware(self):
    #     print("Configure hardware")
    #
    #     # construct the hardware configuration window
    #     newWindow = ctk.CTkToplevel()
    #     newWindow.title("Hardware configuration window")
    #     newWindow.geometry("400x300")
    #     newWindow.attributes("-topmost", True)
    #     newWindow.resizable(False, False)
    #
    #     newWindow.columnconfigure(0, weight=1)
    #     newWindow.columnconfigure(1, weight=2)
    #
    #     newWindow.rowconfigure(0, weight=1, minsize=30)
    #     newWindow.rowconfigure(1, weight=1, minsize=30)
    #     newWindow.rowconfigure(2, weight=4)
    #     newWindow.rowconfigure(3, weight=4)
    #
    #     label1 = ctk.CTkLabel(newWindow, text="MFLI status").grid(row=0, column=0)
    #     labelMFLIStatus = ctk.CTkLabel(newWindow, text="MFLI disconnected", text_color="red").grid(row=0, column=1,
    #                                                                                                sticky="W")
    #     label2 = ctk.CTkLabel(newWindow, text="Zaber status").grid(row=1, column=0)
    #     labelZaberStatus = ctk.CTkLabel(newWindow, text="Zaber disconnected", text_color="red").grid(row=1, column=1,
    #                                                                                                  sticky="W")
    #     buttonMFLI = ctk.CTkButton(master=newWindow,
    #                                        text="Connect MFLI",
    #                                        width=200,
    #                                        height=80,
    #                                        corner_radius=10,
    #                                        command=self.onCmdUnusedButton)
    #     buttonMFLI.grid(row=2, column=0, columnspan=2, sticky="NSEW", padx=5, pady=5)

    def onClosing(self):
        # make sure the application closes properly when the main window is destroyed
        sys.exit()

    # def createPlot(self):
    # fig.subplots_adjust(left=0, right=1, bottom=0, top=1, wspace=0, hspace=0)
    # canvas.get_tk_widget().grid(row=0, column=1, padx=(15, 0), pady=10, sticky="NW")
    # fig.set_size_inches(11, 5.3)
    # fig2.subplots_adjust(left=0, right=1, bottom=0, top=1, wspace=0, hspace=0)
    # canvas.get_tk_widget().grid(row=0, column=1, padx=(15, 0), pady=10, sticky="NW")
    # canvas.grid(row=0, column=1, padx=(10, 5), pady=10, sticky=customtkinter.W)
    # canvas.get_tk_widget().place(relx=0.33, rely=0.025)
    # canvas.get_tk_widget().pack(side="top", fill='both', expand=True)
    # plt.ion()
    # plt.pause(0.1)
    # plt.show()
    # plt.pause(0.1)
    # plt.ioff()
    # canvas.pack(side="top", fill='both', expand=True)

    def updatePlot(self):
        # self.currentInterferogramX = np.arange(0, 100, 1)
        # self.currentInterferogramY = np.random.random(len(self.currentInterferogramX))

        # self.currentSpectrumX = np.arange(0, 100, 1)
        # self.currentSpectrumY = np.random.random(len(self.currentSpectrumX))

        self.loadDataToPlots(self.currentInterferogramX, self.currentInterferogramY,
                             self.currentSpectrumX, self.currentSpectrumY)

    def loadDataToPlots(self, interferogramX, interferogramY, spectrumX, spectrumY):

        self.axBot.clear()
        self.axTop.clear()

        if len(spectrumX) == len(spectrumY) and len(spectrumX) > 0:
            self.axBot.grid(color=self.backgroundGray, linestyle='-', linewidth=1, alpha=0.6)
            self.axBot.plot(spectrumX, spectrumY, color="dodgerblue")
            self.axBot.set_xlim(np.min(spectrumX), np.max(spectrumX))

        if len(interferogramX) == len(interferogramY) and len(interferogramX) > 0:
            self.axTop.grid(color=self.backgroundGray, linestyle='-', linewidth=1, alpha=0.6)
            self.axTop.plot(interferogramX, interferogramY, color="dodgerblue")
            self.axTop.set_xlim(np.min(interferogramX), np.max(interferogramX))

        self.canvasTopPlot.draw()
        self.canvasBotPlot.draw()
        self.root.update()


# run the app
if __name__ == "__main__":
    CTK_Window = FTSApp()
