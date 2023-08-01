import customtkinter as ctk
from PIL import Image, ImageOps
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sys
from mfli_driver import MFLIDriver
from zaber_driver import ZaberDriver
import time


class FTSApp:

    def __init__(self):
        # constants
        self.backgroundGray = "#242424"

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
        self.root.columnconfigure(0, weight=1, minsize=250)
        self.root.columnconfigure(1, weight=3)

        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self.root.resizable(True, True)
        self.root.state('zoomed')

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

        self.settingsTabs.tab("Hardware").columnconfigure(0, weight=1)
        self.settingsTabs.tab("Hardware").columnconfigure(1, weight=1)

        self.hardwareStatusLabelHeader = ctk.CTkLabel(master=self.settingsTabs.tab("Hardware"),
                                                      text="General\nstatus",
                                                      font=ctk.CTkFont(size=12))
        self.hardwareStatusLabelHeader.grid(row=0, column=0, sticky="E", padx=5, pady=5)

        self.hardwareStatusLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Hardware"),
                                                text="READY",
                                                text_color="lightgreen",
                                                font=ctk.CTkFont(size=14, weight="bold"))
        self.hardwareStatusLabel.grid(row=0, column=1, sticky="W", padx=5, pady=5)

        self.mfliStatusLabelHeader = ctk.CTkLabel(master=self.settingsTabs.tab("Hardware"),
                                                  text="DAQ\nsystem",
                                                  font=ctk.CTkFont(size=12))
        self.mfliStatusLabelHeader.grid(row=1, column=0, sticky="E", padx=5, pady=5)

        self.mfliStatusLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Hardware"),
                                            text="READY",
                                            text_color="lightgreen",
                                            font=ctk.CTkFont(size=14, weight="bold"))
        self.mfliStatusLabel.grid(row=1, column=1, sticky="W", padx=5, pady=5)

        self.zaberStatusLabelHeader = ctk.CTkLabel(master=self.settingsTabs.tab("Hardware"),
                                                   text="Delay\nline",
                                                   font=ctk.CTkFont(size=12))
        self.zaberStatusLabelHeader.grid(row=2, column=0, sticky="E", padx=5, pady=5)

        self.zaberStatusLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Hardware"),
                                             text="READY",
                                             text_color="lightgreen",
                                             font=ctk.CTkFont(size=14, weight="bold"))
        self.zaberStatusLabel.grid(row=2, column=1, sticky="W", padx=5, pady=5)

        self.zaberCOMLabel = ctk.CTkLabel(master=self.settingsTabs.tab("Hardware"),
                                          text="Zaber port",
                                          font=ctk.CTkFont(size=12))
        self.zaberCOMLabel.grid(row=3, column=0, sticky="W", padx=5, pady=5)

        self.zaberPortCombo = ctk.CTkComboBox(master=self.settingsTabs.tab("Hardware"),
                                              values=["COM1", "COM14", "COM6"],
                                              width=140)
        self.zaberPortCombo.grid(row=3, column=1, sticky="E", padx=5, pady=5)

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

        # create plots
        plt.style.use('dark_background')
        self.figTop, self.axTop = plt.subplots()
        self.figTop.suptitle("Interferogram")
        self.figTop.set_facecolor(self.backgroundGray)
        self.figTop.set_size_inches(15, 4.75)
        self.figTop.subplots_adjust(left=0.1, right=0.99, bottom=0.01, top=0.97, wspace=0, hspace=0)
        self.figTop.set_tight_layout(True)
        self.canvasTopPlot = FigureCanvasTkAgg(self.figTop, master=self.frameTopPlot)
        self.canvasTopPlot.get_tk_widget().pack(side='right', fill='both', expand=True)
        self.canvasTopPlot.draw()

        self.figBot, self.axBot = plt.subplots()
        self.figBot.suptitle("Spectrum")
        self.figBot.set_facecolor(self.backgroundGray)
        self.figBot.set_size_inches(15, 4.75)
        self.figBot.subplots_adjust(left=0.1, right=0.99, bottom=0.01, top=0.97, wspace=0, hspace=0)
        self.figBot.set_tight_layout(True)
        self.canvasBotPlot = FigureCanvasTkAgg(self.figBot, master=self.frameBottomPlot)
        self.canvasBotPlot.get_tk_widget().pack(side='right', fill='both', expand=True)
        self.canvasBotPlot.draw()

        self.updatePlot()
        plt.close()
        plt.close()

        # create driver
        self.MFLIDrv = MFLIDriver(self.mfliIDBox.get("0.0", "end"))
        self.ZaberDrv = ZaberDriver()

        # run the app
        self.root.update()
        self.root.mainloop()

    def onCmdSingleCapture(self):
        print("Single capture command")
        self.MFLIDrv.configureForMeasurement()
        self.MFLIDrv.measureData()

        self.currentInterferogramY = self.MFLIDrv.lastInterferogramData
        self.currentInterferogramX = np.arange(len(self.currentInterferogramY))

        self.currentSpectrumY = self.MFLIDrv.lastReferenceData
        self.currentSpectrumX = np.arange(len(self.currentSpectrumY))

        self.updatePlot()

    def onCmdUnusedButton(self):
        print("Unused button click")

    def onCmdConnectHardware(self):
        strippedMFLIID = self.mfliIDBox.get("0.0", "end").replace(' ', '').replace('\t', '').replace('\n', '').replace(
            '\r', '')

        if self.MFLIDrv.isConnected and self.MFLIDrv.deviceID == strippedMFLIID:
            # the correct MFLI is currently connected and no further action is required
            print("Correct MFLI is already connected")
        else:
            if self.MFLIDrv.tryConnect(strippedMFLIID):
                print("Connection to MFLI successful")
            else:
                print("Connection to MFLI failed")

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
