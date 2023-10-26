import os
import time

from threading import *

import customtkinter as ctk
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sys
from tkinter import messagebox

class AdjustmentTool:

    def __init__(self, root, zaberController, mfliController):

        self.zaberDriver = zaberController
        self.MFLIDriver = mfliController

        self.scanStopFlag = False

        self.plotNamePrimary = "Primary"
        self.plotNameReference = "Reference"
        self.currentlySelectedPlot = self.plotNamePrimary

        # config
        self.centerPointIncrement = 250.0
        self.amplitudeIncrement = 250.0
        self.timePeriodIncrement = 250.0

        self.centerPointCurrent = 75000.0
        self.amplitudeCurrent = 5000.0
        self.timePeriodCurrent = 2000.0

        self.limitTPMin = 500.0
        self.limitTPMax = 60000.0
        self.limitAmpMin = 250.0
        self.limitAmpMax = 75000.0
        self.limitCPMin = 1.0
        self.limitCPMax = 149999
        # build GUI
        ctk.set_appearance_mode("dark")
        self.adjustmenRoot = ctk.CTkToplevel()
        self.adjustmenRoot.protocol("WM_DELETE_WINDOW", self.onClosing)
        self.adjustmenRoot.geometry("900x615")
        self.adjustmenRoot.minsize(width=900, height=615)
        self.adjustmenRoot.title("Adjustment tool")
        self.adjustmenRoot.iconbitmap(default='icon.ico')
        self.adjustmenRoot.resizable(True, True)

        self.backgroundGray = "#242424"


        self.adjustmenRoot.columnconfigure(0, weight=1, minsize=120)
        self.adjustmenRoot.columnconfigure(1, weight=1, minsize=120)
        self.adjustmenRoot.columnconfigure(2, weight=5)

        self.adjustmenRoot.rowconfigure(0, weight=1)
        self.adjustmenRoot.rowconfigure(1, weight=1)
        self.adjustmenRoot.rowconfigure(2, weight=1)
        self.adjustmenRoot.rowconfigure(3, weight=1)
        self.adjustmenRoot.rowconfigure(4, weight=1)
        self.adjustmenRoot.rowconfigure(5, weight=1)
        self.adjustmenRoot.rowconfigure(6, weight=1)

        # Center point controls
        # =================================================================================
        self.centerPointLabel = ctk.CTkLabel(master=self.adjustmenRoot,
                                                    text="Center point [\u03BCm]",
                                                    font=ctk.CTkFont(size=12))
        self.centerPointLabel.grid(row=0, column=0, sticky="SE", padx=5, pady=(30, 15))

        self.centerPointBox = ctk.CTkEntry(master=self.adjustmenRoot,
                                        width=80, height=30)
        self.centerPointBox.insert(0, f"{self.centerPointCurrent}")
        self.centerPointBox.grid(row=0, column=1, sticky="SW", padx=5, pady=(30, 15))
        self.centerPointBox.bind("<FocusOut>", self.onUpdateDataFromBoxes)
        self.centerPointBox.bind("<Return>", self.onUpdateDataFromBoxes)

        self.centerPointUpBtn = ctk.CTkButton(master=self.adjustmenRoot,
                                            text="\u2191 \u2191 \u2191 \u2191 \u2191",
                                            width=80,
                                            height=40,
                                            corner_radius=10,
                                            command=self.onCenterPointIncrement)
        self.centerPointUpBtn.grid(row=1, column=0, sticky="NE", padx=5, pady=5)

        self.centerPointDownBtn = ctk.CTkButton(master=self.adjustmenRoot,
                                            text="\u2193 \u2193 \u2193 \u2193 \u2193",
                                            width=80,
                                            height=40,
                                            corner_radius=10,
                                            command=self.onCenterPointDecrement)
        self.centerPointDownBtn.grid(row=1, column=1, sticky="NW", padx=5, pady=5)

        # Amplitude controls
        # =================================================================================
        self.amplitudeLabel = ctk.CTkLabel(master=self.adjustmenRoot,
                                                    text="Amplitude [\u03BCm]",
                                                    font=ctk.CTkFont(size=12))
        self.amplitudeLabel.grid(row=2, column=0, sticky="SE", padx=5, pady=(50,15))

        self.amplitudeBox = ctk.CTkEntry(master=self.adjustmenRoot,
                                        width=80, height=30)
        self.amplitudeBox.insert(0, f"{self.amplitudeCurrent}")
        self.amplitudeBox.grid(row=2, column=1, sticky="SW", padx=5, pady=(50,15))
        self.amplitudeBox.bind("<FocusOut>", self.onUpdateDataFromBoxes)
        self.amplitudeBox.bind("<Return>", self.onUpdateDataFromBoxes)

        self.amplitudeUpBtn = ctk.CTkButton(master=self.adjustmenRoot,
                                            text="\u2191 \u2191 \u2191 \u2191 \u2191",
                                            width=80,
                                            height=40,
                                            corner_radius=10,
                                            command=self.onAmplitudeIncrement)
        self.amplitudeUpBtn.grid(row=3, column=0, sticky="NE", padx=5, pady=5)

        self.amplitudeDownBtn = ctk.CTkButton(master=self.adjustmenRoot,
                                            text="\u2193 \u2193 \u2193 \u2193 \u2193",
                                            width=80,
                                            height=40,
                                            corner_radius=10,
                                            command=self.onAmplitudeDecrement)
        self.amplitudeDownBtn.grid(row=3, column=1, sticky="NW", padx=5, pady=5)

        # Time period controls
        # =================================================================================
        self.timePeriodLabel = ctk.CTkLabel(master=self.adjustmenRoot,
                                                    text="Time period [ms]",
                                                    font=ctk.CTkFont(size=12))
        self.timePeriodLabel.grid(row=4, column=0, sticky="SE", padx=5, pady=(50,15))

        self.timePeriodBox = ctk.CTkEntry(master=self.adjustmenRoot,
                                        width=80, height=30)
        self.timePeriodBox.insert(0, f"{self.timePeriodCurrent}")
        self.timePeriodBox.grid(row=4, column=1, sticky="SW", padx=5, pady=(50,15))
        self.timePeriodBox.bind("<FocusOut>", self.onUpdateDataFromBoxes)
        self.timePeriodBox.bind("<Return>", self.onUpdateDataFromBoxes)

        self.timePeriodUpBtn = ctk.CTkButton(master=self.adjustmenRoot,
                                            text="\u2191 \u2191 \u2191 \u2191 \u2191",
                                            width=80,
                                            height=40,
                                            corner_radius=10,
                                            command=self.onTimePeriodIncrement)
        self.timePeriodUpBtn.grid(row=5, column=0, sticky="NE", padx=5, pady=5)

        self.timePeriodDownBtn = ctk.CTkButton(master=self.adjustmenRoot,
                                            text="\u2193 \u2193 \u2193 \u2193 \u2193",
                                            width=80,
                                            height=40,
                                            corner_radius=10,
                                            command=self.onTimePeriodDecrement)
        self.timePeriodDownBtn.grid(row=5, column=1, sticky="NW", padx=5, pady=5)

        # Radio buttons
        # =================================================================================
        self.selectPrimaryPlotVar = ctk.IntVar(value=0)
        self.selectPrimaryPlotRadioButton = ctk.CTkRadioButton(master=self.adjustmenRoot,
                                                text="Primary",
                                                command=self.onRadioBtnSelPrimary,
                                                value=1,
                                                variable=self.selectPrimaryPlotVar)
        self.selectPrimaryPlotRadioButton.grid(row=6, column=0, sticky="E", padx=5, pady=(30,5))

        self.selectReferencePlotVar = ctk.IntVar(value=0)
        self.selectReferencePlotRadioButton = ctk.CTkRadioButton(master=self.adjustmenRoot,
                                                text="Reference",
                                                command=self.onRadioBtnSelReference,
                                                value=1,
                                                variable=self.selectReferencePlotVar)
        self.selectReferencePlotRadioButton.grid(row=6, column=1, sticky="W", padx=5, pady=(30,5))

        # Buttons
        # =================================================================================
        self.stopButton = ctk.CTkButton(master=self.adjustmenRoot,
                                            text="STOP",
                                            width=100,
                                            height=80,
                                            corner_radius=10,
                                            fg_color="darkred",
                                            command=self.stopScan)
        self.stopButton.grid(row=7, column=0, sticky="E", padx=5, pady=(30, 15))

        self.executeButton = ctk.CTkButton(master=self.adjustmenRoot,
                                        text="Execute",
                                        width=100,
                                        height=80,
                                        corner_radius=10,
                                        fg_color="darkgreen",
                                        command=self.onExecute)
        self.executeButton.grid(row=7, column=1, sticky="W", padx=5, pady=(30, 15))

        # Plot
        # =================================================================================
        self.previewPlotFrame = ctk.CTkFrame(master=self.adjustmenRoot,
                                            fg_color="darkblue")
        # self.frame.place(relx=0.33, rely=0.025)
        self.previewPlotFrame.grid(row=0, column=2, padx=(5, 5), pady=0, rowspan=8)

        plt.style.use('dark_background')
        self.figPreview, self.axPreview = plt.subplots()
        self.figPreview.suptitle("- - - No Data - - - ")
        self.axPreview.set_xlabel('Sample num.')
        self.axPreview.set_ylabel('Voltage [V]')
        self.figPreview.set_facecolor(self.backgroundGray)
        self.figPreview.set_size_inches(100, 100)
        self.figPreview.subplots_adjust(left=0.1, right=0.99, bottom=0.1, top=0.97, wspace=0, hspace=0)
        self.figPreview.set_tight_layout(True)
        # self.axRef.set_yscale("slog")
        self.canvasPreviewPlot = FigureCanvasTkAgg(self.figPreview, master=self.previewPlotFrame)
        self.canvasPreviewPlot.get_tk_widget().pack(side='right', fill='both', expand=True)
        self.canvasPreviewPlot.draw()
        plt.close()

        self.adjustmenRoot.attributes('-topmost', 1)
        self.adjustmenRoot.grab_set()

        self.selectPrimaryPlotRadioButton.select()

        self.adjustmenRoot.update()


    def onExecute(self):
        # start the scanning thread
        t = Thread(target=self.scanningThread, daemon=True)
        t.start()

        # startPos = self.centerPointCurrent - self.amplitudeCurrent
        # self.executeScan(startPos, self.amplitudeCurrent, self.timePeriodCurrent)

    def executeScan(self, startPosition, amplitude, timePeriod):
        self.zaberDriver.stop()
        self.zaberDriver.waitUntilIdle()
        self.zaberDriver.setPosition(startPosition)
        self.zaberDriver.waitUntilIdle()
        self.zaberDriver.sineMove(amplitude, timePeriod)

    def stopScan(self):
        self.scanStopFlag = True
        # self.zaberDriver.stop()

    def refreshValues(self):

        # apply limits
        if self.timePeriodCurrent < self.limitTPMin:
            self.timePeriodCurrent = self.limitTPMin

        if self.timePeriodCurrent > self.limitTPMax:
            self.timePeriodCurrent = self.limitTPMax

        if self.amplitudeCurrent < self.limitAmpMin:
            self.amplitudeCurrent = self.limitAmpMin

        if self.amplitudeCurrent > self.limitAmpMax:
            self.amplitudeCurrent = self.limitAmpMax

        if self.centerPointCurrent < self.limitCPMin:
            self.centerPointCurrent = self.limitCPMin

        if self.centerPointCurrent > self.limitCPMax:
            self.centerPointCurrent = self.limitCPMax

        # refresh values in boxes
        self.timePeriodBox.delete(0, "end")
        self.timePeriodBox.insert(0, f"{self.timePeriodCurrent}")

        self.centerPointBox.delete(0, "end")
        self.centerPointBox.insert(0, f"{self.centerPointCurrent}")

        self.amplitudeBox.delete(0, "end")
        self.amplitudeBox.insert(0, f"{self.amplitudeCurrent}")

        self.adjustmenRoot.update()

    def onAmplitudeIncrement(self):
        self.amplitudeCurrent = self.amplitudeCurrent + self.amplitudeIncrement
        self.refreshValues()

    def onAmplitudeDecrement(self):
        self.amplitudeCurrent = self.amplitudeCurrent - self.amplitudeIncrement
        self.refreshValues()

    def onCenterPointIncrement(self):
        self.centerPointCurrent = self.centerPointCurrent + self.centerPointIncrement
        self.refreshValues()

    def onCenterPointDecrement(self):
        self.centerPointCurrent = self.centerPointCurrent - self.centerPointIncrement
        self.refreshValues()

    def onTimePeriodIncrement(self):
        self.timePeriodCurrent = self.timePeriodCurrent + self.timePeriodIncrement
        self.refreshValues()

    def onTimePeriodDecrement(self):
        self.timePeriodCurrent = self.timePeriodCurrent - self.timePeriodIncrement
        self.refreshValues()


    def onRadioBtnSelReference(self):
        if self.selectReferencePlotVar.get() != 0:
            self.currentlySelectedPlot = self.plotNameReference

        self.selectPrimaryPlotRadioButton.deselect()

    def onRadioBtnSelPrimary(self):
        if self.selectPrimaryPlotVar.get() != 0:
            self.currentlySelectedPlot = self.plotNamePrimary

        self.selectReferencePlotRadioButton.deselect()

    def onUpdateDataFromBoxes(self, other):

        try:
            self.timePeriodCurrent = float(self.timePeriodBox.get())
        except:
            pass

        try:
            self.amplitudeCurrent = float(self.amplitudeBox.get())
        except:
            pass

        try:
            self.centerPointCurrent = float(self.centerPointBox.get())
        except:
            pass

        self.refreshValues()

    def onClosing(self):

        try:
            self.zaberDriver.stop()
        except:
            pass
        finally:
            self.adjustmenRoot.destroy()

    def updatePlotData(self, dataY, title):
        plt.style.use('dark_background')
        self.figPreview.suptitle(title)
        self.axPreview.clear()
        self.axPreview.grid(color="dimgrey", linestyle='-', linewidth=1, alpha=0.6)
        self.axPreview.plot(dataY, color='y')
        self.axPreview.set_xlim(0, len(dataY))

        self.canvasPreviewPlot.draw()
        self.adjustmenRoot.update()

    def scanningThread(self):
        print("Scanning thread started")
        freqIndex = 11

        mfliSamplingFrequency = self.MFLIDriver.MFLISamplingRates[freqIndex]

        startPos = self.centerPointCurrent - self.amplitudeCurrent

        self.zaberDriver.stop()
        self.zaberDriver.waitUntilIdle()
        self.zaberDriver.setPosition(startPos, speed=self.zaberDriver.MaxSpeed)
        self.zaberDriver.waitUntilIdle()

        time.sleep(0.1)

        samplingTime = self.timePeriodCurrent
        sampleCount = samplingTime / 1000.0 * mfliSamplingFrequency

        previous_samplingTime = samplingTime
        previous_sampleCount = sampleCount
        previous_startPos = startPos

        self.MFLIDriver.configureForMeasurement(samplingFreqIndex=freqIndex,
                                                sampleLength=sampleCount,
                                                triggerEnabled=False,
                                                triggerLevel=0,
                                                triggerReference=0,
                                                triggerHysteresis=0)

        while True:

            if self.scanStopFlag:
                self.scanStopFlag = False
                break

            # configure MFLI
            samplingTime = self.timePeriodCurrent
            sampleCount = samplingTime / 1000.0 * mfliSamplingFrequency
            startPos = self.centerPointCurrent - self.amplitudeCurrent

            # if configuration was changed, reinitialize MFLI
            if (samplingTime != previous_samplingTime or
                    sampleCount != previous_sampleCount or
                    startPos != previous_startPos):

                self.MFLIDriver.configureForMeasurement(samplingFreqIndex=freqIndex,
                                                        sampleLength=sampleCount,
                                                        triggerEnabled=False,
                                                        triggerLevel=0,
                                                        triggerReference=0,
                                                        triggerHysteresis=0)

            previous_samplingTime = samplingTime
            previous_sampleCount = sampleCount
            previous_startPos = startPos

            self.zaberDriver.stop()
            self.zaberDriver.waitUntilIdle()
            self.zaberDriver.setPosition(startPos, speed=self.zaberDriver.MaxSpeed)
            self.zaberDriver.waitUntilIdle()

            # self.zaberDriver.sineMoveNTimes(self.amplitudeCurrent, self.timePeriodCurrent, 1)
            # calculate the speed required to complete the movement in the specified time
            requiredMovementSpeed = (self.amplitudeCurrent * 2.0) / (self.timePeriodCurrent / 1000.0) # [um/s]
            self.zaberDriver.setPosition(startPos + (self.amplitudeCurrent * 2.0), speed=requiredMovementSpeed)

            measStatus = self.MFLIDriver.measureDataStandaloneMethod()

            time.sleep((samplingTime/1000) + 0.05)

            self.zaberDriver.waitUntilIdle()
            self.zaberDriver.setPosition(startPos, speed=self.zaberDriver.MaxSpeed) # send the carriage back

            if measStatus != "ok":
                print(f"Preview measurement failed due to: {measStatus}")

            if self.currentlySelectedPlot == self.plotNamePrimary:
                self.updatePlotData(self.MFLIDriver.lastInterferogramData, "Primary detector preview")
            else:
                self.updatePlotData(self.MFLIDriver.lastReferenceData, "Reference detector preview")

