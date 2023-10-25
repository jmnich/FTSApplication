import os
import time

import customtkinter as ctk
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sys
from tkinter import messagebox

class AdjustmentTool:

    def __init__(self, root, zaberController):

        self.zaberDriver = zaberController

        # build GUI
        ctk.set_appearance_mode("dark")
        self.adjustmenRoot = ctk.CTkToplevel()
        self.adjustmenRoot.geometry("300x550")
        self.adjustmenRoot.minsize(width=300, height=550)
        self.adjustmenRoot.title("Adjustment tool")
        self.adjustmenRoot.iconbitmap(default='icon.ico')
        self.adjustmenRoot.resizable(True, True)

        self.backgroundGray = "#242424"


        self.adjustmenRoot.columnconfigure(0, weight=1)
        self.adjustmenRoot.columnconfigure(1, weight=1)

        # self.adjustmenRoot.rowconfigure(0, weight=1)
        # self.adjustmenRoot.rowconfigure(1, weight=1)
        # self.adjustmenRoot.rowconfigure(2, weight=1)
        # self.adjustmenRoot.rowconfigure(3, weight=1)
        # self.adjustmenRoot.rowconfigure(4, weight=1)

        # Center point controls
        # =================================================================================
        self.centerPointLabel = ctk.CTkLabel(master=self.adjustmenRoot,
                                                    text="Center point",
                                                    font=ctk.CTkFont(size=12))
        self.centerPointLabel.grid(row=0, column=0, sticky="SE", padx=5, pady=(30, 15))

        self.centerPointBox = ctk.CTkEntry(master=self.adjustmenRoot,
                                        width=80, height=30)
        self.centerPointBox.insert(0, f"{self.zaberDriver.DelayLineNominalLength / 2.0}")
        self.centerPointBox.grid(row=0, column=1, sticky="SW", padx=5, pady=(30, 15))
        # self.yMaxBox.bind("<FocusOut>", self.onCmdUpdatePlotRanges)
        # self.yMaxBox.bind("<Return>", self.onCmdUpdatePlotRanges)

        self.centerPointUpBtn = ctk.CTkButton(master=self.adjustmenRoot,
                                            text="\u2191 \u2191 \u2191 \u2191 \u2191",
                                            width=80,
                                            height=40,
                                            corner_radius=10,
                                            command=None)
        self.centerPointUpBtn.grid(row=1, column=0, sticky="NE", padx=5, pady=5)

        self.centerPointDownBtn = ctk.CTkButton(master=self.adjustmenRoot,
                                            text="\u2193 \u2193 \u2193 \u2193 \u2193",
                                            width=80,
                                            height=40,
                                            corner_radius=10,
                                            command=None)
        self.centerPointDownBtn.grid(row=1, column=1, sticky="NW", padx=5, pady=5)

        # Amplitude controls
        # =================================================================================
        self.amplitudeLabel = ctk.CTkLabel(master=self.adjustmenRoot,
                                                    text="Amplitude",
                                                    font=ctk.CTkFont(size=12))
        self.amplitudeLabel.grid(row=2, column=0, sticky="SE", padx=5, pady=(50,15))

        self.amplitudeBox = ctk.CTkEntry(master=self.adjustmenRoot,
                                        width=80, height=30)
        self.amplitudeBox.insert(0, f"{5000}")
        self.amplitudeBox.grid(row=2, column=1, sticky="SW", padx=5, pady=(50,15))
        # self.yMaxBox.bind("<FocusOut>", self.onCmdUpdatePlotRanges)
        # self.yMaxBox.bind("<Return>", self.onCmdUpdatePlotRanges)

        self.amplitudeUpBtn = ctk.CTkButton(master=self.adjustmenRoot,
                                            text="\u2191 \u2191 \u2191 \u2191 \u2191",
                                            width=80,
                                            height=40,
                                            corner_radius=10,
                                            command=None)
        self.amplitudeUpBtn.grid(row=3, column=0, sticky="NE", padx=5, pady=5)

        self.amplitudeDownBtn = ctk.CTkButton(master=self.adjustmenRoot,
                                            text="\u2193 \u2193 \u2193 \u2193 \u2193",
                                            width=80,
                                            height=40,
                                            corner_radius=10,
                                            command=None)
        self.amplitudeDownBtn.grid(row=3, column=1, sticky="NW", padx=5, pady=5)

        # Time period controls
        # =================================================================================
        self.timePeriodLabel = ctk.CTkLabel(master=self.adjustmenRoot,
                                                    text="Time period",
                                                    font=ctk.CTkFont(size=12))
        self.timePeriodLabel.grid(row=4, column=0, sticky="SE", padx=5, pady=(50,15))

        self.timePeriodBox = ctk.CTkEntry(master=self.adjustmenRoot,
                                        width=80, height=30)
        self.timePeriodBox.insert(0, f"{2000}")
        self.timePeriodBox.grid(row=4, column=1, sticky="SW", padx=5, pady=(50,15))
        # self.yMaxBox.bind("<FocusOut>", self.onCmdUpdatePlotRanges)
        # self.yMaxBox.bind("<Return>", self.onCmdUpdatePlotRanges)

        self.timePeriodUpBtn = ctk.CTkButton(master=self.adjustmenRoot,
                                            text="\u2191 \u2191 \u2191 \u2191 \u2191",
                                            width=80,
                                            height=40,
                                            corner_radius=10,
                                            command=None)
        self.timePeriodUpBtn.grid(row=5, column=0, sticky="NE", padx=5, pady=5)

        self.timePeriodDownBtn = ctk.CTkButton(master=self.adjustmenRoot,
                                            text="\u2193 \u2193 \u2193 \u2193 \u2193",
                                            width=80,
                                            height=40,
                                            corner_radius=10,
                                            command=None)
        self.timePeriodDownBtn.grid(row=5, column=1, sticky="NW", padx=5, pady=5)

        # Buttons
        # =================================================================================
        self.stopButton = ctk.CTkButton(master=self.adjustmenRoot,
                                            text="STOP",
                                            width=100,
                                            height=80,
                                            corner_radius=10,
                                            fg_color="darkred",
                                            command=None)
        self.stopButton.grid(row=6, column=0, sticky="E", padx=5, pady=(30, 15))

        self.executeButton = ctk.CTkButton(master=self.adjustmenRoot,
                                        text="Execute",
                                        width=100,
                                        height=80,
                                        corner_radius=10,
                                        fg_color="darkgreen",
                                        command=None)
        self.executeButton.grid(row=6, column=1, sticky="W", padx=5, pady=(30, 15))



        self.adjustmenRoot.attributes('-topmost', 1)
        self.adjustmenRoot.grab_set()

        self.adjustmenRoot.update()


    def executeScan(self, startPosition, amplitude, timePeriod):
        self.zaberDriver.waitUntilIdle()
        self.zaberDriver.setPosition(startPosition)
        self.zaberDriver.waitUntilIdle()
        self.zaberDriver.sineMove(amplitude, timePeriod)

    def stopScan(self):
        self.zaberDriver.stop()
