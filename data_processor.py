import numpy as np
from scipy.signal import find_peaks
from scipy import signal
from scipy.signal import hilbert


def getApodizationWindowsTypesList():
    return [
    "boxcar",
    "hanning",
    "triangular",
    "blackman-harris",
    "gauss",
    "tukey_0.1",
    "tukey_0.2",
    "tukey_0.5",
]

class DataProcessor:

    def __init__(self):
        print("DataProcessor created")

        self.ref_laser_wavelength = 1.547718 #um
        self.K = 8 # zero-padding factor
        self.detector_sensitivity = 7.0E4 # [V/W]

    def analyzeData(self, rawReferenceSignal, rawInterferogram):
        print("Analyzing data")
        detector_sensitivity = 7.0E4 # [V/W]

        ref_volt = rawReferenceSignal - np.mean(rawReferenceSignal)
        meas_volt = rawInterferogram - np.mean(rawInterferogram)

        # normalize reference interferometer signal
        ref_volt = (ref_volt - np.min(ref_volt)) / (np.max(ref_volt) - np.min(ref_volt))

        # find peaks
        ref_pos_peaks, _ = find_peaks(ref_volt, prominence=0.075)
        ref_pos_peaks_neg, _ = find_peaks(-ref_volt, prominence=0.075)

        ref_pos_peaks = np.concatenate((ref_pos_peaks, ref_pos_peaks_neg))
        ref_pos_peaks.sort(kind='mergesort')

        # resample the interferograms
        mirror_travel_distance_total = self.ref_laser_wavelength / 4 * len(ref_pos_peaks)
        print("Total REF mirror travel = ", mirror_travel_distance_total, "\u03BCm")

        # create an array for the new interferogram
        resampled_interferogram = np.zeros(len(meas_volt))

        # this array will hold position of the mirror for each index in um
        resampled_X = np.zeros(len(ref_volt))

        um_per_ref_peak = self.ref_laser_wavelength / 4

        # populate the new x axis with known positions (indices corresponding to ref peaks)
        for i in range(0, len(ref_pos_peaks)):
            resampled_X[ref_pos_peaks[i]] = i * um_per_ref_peak

        new_x = np.linspace(0, len(resampled_X), num=len(resampled_X)).astype(int)
        resampled_X = np.interp(new_x, new_x[resampled_X > 0], resampled_X[resampled_X > 0])

        # create new X axis with evenly spaced x points
        equ_dist_pts_cnt = len(meas_volt)
        equ_pts_spacing = mirror_travel_distance_total / equ_dist_pts_cnt
        equidistant_x_axis = np.zeros(equ_dist_pts_cnt)
        equidistant_y_axis = np.zeros(equ_dist_pts_cnt)

        for i in range(0, len(equidistant_x_axis)):
            equidistant_x_axis[i] = i * equ_pts_spacing

        equidistant_y_axis = np.interp(equidistant_x_axis, resampled_X, meas_volt)
        # zero-padding
        np_pad_zeros = np.zeros(int(((self.K - 1) * len(meas_volt))))
        meas_volt_padded = np.concatenate((equidistant_y_axis, np_pad_zeros))

        # calculate spectrum
        spectrum_x = np.arange(0, len(meas_volt), 1)
        spectrum = np.fft.fft(meas_volt_padded)

        # cut spectrum to match the correct X axis (required due to padding)
        spectrum = spectrum[0:len(spectrum_x) - 1]
        # calculate absolute value from the spectrum
        spectrum_abs = np.abs(spectrum)

        #normalize
        # spectrum_abs = (spectrum_abs-np.min(spectrum_abs))/(np.max(spectrum_abs)-np.min(spectrum_abs))
        spectrum_abs = spectrum_abs / (len(spectrum_abs) / 2)
        # convert Y axis from volts to watts
        spectrum_abs = spectrum_abs / detector_sensitivity
        # conver Y axis from watts to dBm
        spectrum_abs = 10.0 * np.log10(1.0E3 * spectrum_abs)

        # convert k to wavelength in um
        spectrum_x_recalc = np.zeros(len(spectrum_abs))

        for i in range(1, len(spectrum_abs)):
            spectrum_x_recalc[i] = (2 * mirror_travel_distance_total / spectrum_x[i]) * self.K

        #cut the important part
        spectrum_slicing_index_start = 1
        spectrum_slicing_index_stop = len(spectrum_abs) - 2

        spectrum_abs = spectrum_abs[spectrum_slicing_index_start : spectrum_slicing_index_stop]
        spectrum_x_recalc = spectrum_x_recalc[spectrum_slicing_index_start : spectrum_slicing_index_stop]

        output = {"spectrumX": spectrum_x_recalc,
                  "spectrumY": spectrum_abs,
                  "interferogramX": equidistant_x_axis,
                  "interferogramY": equidistant_y_axis}

        return output

    def find_nearest(self, array, value):
        array = np.asarray(array)
        idx = (np.abs(array - value)).argmin()
        return idx

    def analyzeDataHilbertInterpolation(self, rawReferenceSignal, rawInterferogram, apodizationWindowType):
        print("Analyzing data (Hilbert transform-based interpolation algorithm)")

        ref_volt = rawReferenceSignal - np.mean(rawReferenceSignal)
        meas_volt = rawInterferogram - np.mean(rawInterferogram)

        # calculate X axis for the acquired interferogram using the Hiblert transform
        interferogram_X_from_Hilbert = hilbert(ref_volt)
        interferogram_X_from_Hilbert = np.unwrap(np.angle(interferogram_X_from_Hilbert))

        # convert X from instantaneous phase to [um]
        interferogram_X_from_Hilbert = interferogram_X_from_Hilbert / (2 * np.pi) * (self.ref_laser_wavelength / 2)

        # create an array for Y axis of the resampled interferogram signal
        resampled_interferogram_Y = np.zeros(len(meas_volt))
        # create an array for X axis of the resampled interferogram signal, where all X values are evenly spaced
        resampled_interferogram_X = np.linspace(start=np.min(interferogram_X_from_Hilbert),
                                                stop=np.max(interferogram_X_from_Hilbert),
                                                num=len(resampled_interferogram_Y),
                                                endpoint=True)

        # resample Y axis with accordance with the new X axis retrieved with the use of the Hilbert transform
        resampled_interferogram_Y = np.interp(resampled_interferogram_X, interferogram_X_from_Hilbert, meas_volt)

        # copy the interferogram before apodization
        rawInterferogramY = np.copy(resampled_interferogram_Y)

        # apodize the interferogram
        print(f"Applied apodization window: {apodizationWindowType}")
        window = self.createAssymetricApodizationWindow(resampled_interferogram_Y, apodizationWindowType)
        resampled_interferogram_Y = resampled_interferogram_Y * window

        # calculate total distance traveled by the mirror
        mirror_travel_distance_total = np.max(interferogram_X_from_Hilbert)

        # zero-padding
        np_pad_zeros = np.zeros(int(((self.K - 1) * len(resampled_interferogram_Y))))
        meas_volt_padded = np.concatenate((resampled_interferogram_Y, np_pad_zeros))

        # calculate spectrum
        spectrum_x = np.arange(0, len(resampled_interferogram_Y), 1)
        spectrum = np.fft.rfft(meas_volt_padded)

        # cut spectrum to match the correct X axis (required due to padding)
        spectrum = spectrum[0:len(spectrum_x)]
        # calculate absolute value from the spectrum
        spectrum_abs = np.abs(spectrum)

        # normalize
        spectrum_abs = spectrum_abs / (len(spectrum_abs) / 2)
        # convert Y axis from volts to watts
        spectrum_abs = spectrum_abs / self.detector_sensitivity
        # conver Y axis from watts to dBm
        spectrum_abs = 10.0 * np.log10(1.0E3 * spectrum_abs)

        # convert k to wavelength in um
        spectrum_x_recalc = np.zeros(len(spectrum_abs))

        for i in range(1, len(spectrum_abs)):
            spectrum_x_recalc[i] = (2 * mirror_travel_distance_total / spectrum_x[i]) * self.K

        # cut the important part
        spectrum_slicing_index_start = 1
        spectrum_slicing_index_stop = len(spectrum_abs) - 2

        spectrum_abs = spectrum_abs[spectrum_slicing_index_start: spectrum_slicing_index_stop]
        spectrum_x_recalc = spectrum_x_recalc[spectrum_slicing_index_start: spectrum_slicing_index_stop]

        # make a new X axis, common to all spectra and interpolate them on it
        spectrum_config_x_min = 0.1
        spectrum_config_x_max = 300.0
        spectrum_config_pts = int(2E6)
        common_spectrum_X = np.linspace(start=spectrum_config_x_min,
                                        stop=spectrum_config_x_max,
                                        num=spectrum_config_pts,
                                        endpoint=True)

        common_spectrum_X = np.flip(common_spectrum_X)

        start_index = self.find_nearest(spectrum_x_recalc, spectrum_config_x_min)
        stop_index = self.find_nearest(spectrum_x_recalc, spectrum_config_x_max)

        print(f"Start index: {start_index}, Stop index: {stop_index}")
        print(f"X Start: {spectrum_x_recalc[start_index]}, Stop: {spectrum_x_recalc[stop_index]}")
        print(f"Y Start: {spectrum_abs[start_index]}, Stop: {spectrum_abs[stop_index]}")

        axisXCut = spectrum_x_recalc[stop_index:start_index]
        axisYCut = spectrum_abs[stop_index:start_index]

        axisXCut = np.flip(axisXCut)
        axisYCut = np.flip(axisYCut)

        spectrum_abs = np.interp(common_spectrum_X, axisXCut, axisYCut)

        output = {"spectrumX": common_spectrum_X,                   # spectrum X axis
                  "spectrumY": spectrum_abs,                        # spectrum Y axis
                  "interferogramX": resampled_interferogram_X,      # interferogram X axis in um
                  "interferogramY": resampled_interferogram_Y,      # interferogram Y axis (after apodization)
                  "apodizationWindow": window,                      # applied apodization window
                  "rawInterferogramY": rawInterferogramY}           # interferogram Y axis (before apodization)

        return output

    def createAssymetricApodizationWindow(self, interferogram, windowType):

        # find the ZPD index
        zpdIdx = self.find_nearest(interferogram, np.max(interferogram))

        if windowType == "triangular":
            winLeft = signal.windows.triang((zpdIdx + 1) * 2)
            winLeft = winLeft[:int(len(winLeft) / 2)]
            winRight = signal.windows.triang(((len(interferogram) - 1) - zpdIdx) * 2)
            winRight = winRight[int(len(winRight) / 2):]
            window = np.concatenate((winLeft, winRight))

            return window

        elif windowType == "blackman-harris":
            winLeft = signal.windows.blackmanharris((zpdIdx + 1) * 2)
            winLeft = winLeft[:int(len(winLeft) / 2)]
            winRight = signal.windows.blackmanharris(((len(interferogram) - 1) - zpdIdx) * 2)
            winRight = winRight[int(len(winRight) / 2):]
            window = np.concatenate((winLeft, winRight))

            return window

        elif windowType == "gauss":
            winLeft = signal.windows.gaussian((zpdIdx + 1) * 2, std=7)
            winLeft = winLeft[:int(len(winLeft) / 2)]
            winRight = signal.windows.gaussian(((len(interferogram) - 1) - zpdIdx) * 2, std=7)
            winRight = winRight[int(len(winRight) / 2):]
            window = np.concatenate((winLeft, winRight))

            return window

        elif windowType == "hanning":
            winLeft = signal.windows.hann((zpdIdx + 1) * 2)
            winLeft = winLeft[:int(len(winLeft) / 2)]
            winRight = signal.windows.hann(((len(interferogram) - 1) - zpdIdx) * 2)
            winRight = winRight[int(len(winRight) / 2):]
            window = np.concatenate((winLeft, winRight))

            return window

        elif windowType == "boxcar":
            window = signal.windows.boxcar(len(interferogram))

            return window

        elif windowType == "tukey_0.1":
            winLeft = signal.windows.tukey((zpdIdx + 1) * 2, 0.1)
            winLeft = winLeft[:int(len(winLeft) / 2)]
            winRight = signal.windows.tukey(((len(interferogram) - 1) - zpdIdx) * 2, 0.1)
            winRight = winRight[int(len(winRight) / 2):]
            window = np.concatenate((winLeft, winRight))

            return window

        elif windowType == "tukey_0.2":
            winLeft = signal.windows.tukey((zpdIdx + 1) * 2, 0.2)
            winLeft = winLeft[:int(len(winLeft) / 2)]
            winRight = signal.windows.tukey(((len(interferogram) - 1) - zpdIdx) * 2, 0.2)
            winRight = winRight[int(len(winRight) / 2):]
            window = np.concatenate((winLeft, winRight))

            return window

        elif windowType == "tukey_0.5":
            winLeft = signal.windows.tukey((zpdIdx + 1) * 2, 0.5)
            winLeft = winLeft[:int(len(winLeft) / 2)]
            winRight = signal.windows.tukey(((len(interferogram) - 1) - zpdIdx) * 2, 0.5)
            winRight = winRight[int(len(winRight) / 2):]
            window = np.concatenate((winLeft, winRight))

            return window

        # elif type == "nb_weak":
        #     # norton-beer weak
        #     signal.windows.

        #     return interferogram

        else:
            return None