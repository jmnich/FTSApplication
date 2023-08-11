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

        # create button frames
        

        # create plots
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