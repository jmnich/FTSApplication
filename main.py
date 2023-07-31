import customtkinter as ctk
from PIL import Image, ImageOps
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class FTSApp:

    def __init__(self):
        # constants
        self.backgroundGray = "#242424"

        # construct GUI
        ctk.set_appearance_mode("dark")
        self.root = ctk.CTk()
        self.root.geometry("1200x800")
        self.root.minsize(800, 800)
        self.root.title("FTS App")
        self.root.iconbitmap(default='icon.ico')
        # self.root.attributes('-fullscreen',True)
        self.root.columnconfigure(0, weight=1, minsize=200)
        self.root.columnconfigure(1, weight=3)

        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        self.root.resizable(True, True)
        self.root.state('zoomed')

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
        self.buttonSingle = ctk.CTkButton(master=self.root,
                                    text="Single capture",
                                    width=120,
                                    height=80,
                                    command=self.onCmdSingleCapture)
        self.buttonSingle.grid(row=0, column=0, sticky="NW", padx=15, pady=15)

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

        # run the app
        self.root.update()
        self.root.mainloop()

    def onCmdSingleCapture(self):
        print("Single capture command")
        self.updatePlot()

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
        x = np.arange(0, 100, 1)
        y = np.random.random(len(x))

        x2 = np.arange(0, 100, 1)
        y2 = np.random.random(len(x2))

        self.loadDataToPlots(x, y, x2, y2)

    def loadDataToPlots(self, interferogramX, interferogramY, spectrumX, spectrumY):
        self.axBot.clear()
        self.axBot.plot(spectrumX, spectrumY, color="white")

        self.axTop.clear()
        self.axTop.plot(interferogramX, interferogramY, color="white")
        self.canvasTopPlot.draw()
        self.canvasBotPlot.draw()
        self.root.update()


# run the app
if __name__ == "__main__":
    CTK_Window = FTSApp()