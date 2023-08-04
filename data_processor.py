import numpy as np
from scipy.signal import find_peaks
from scipy import signal

class DataProcessor:

    def __init__(self):
        print("DataProcessor created")

        self.ref_laser_wavelength = 1.547718 #um
        self.K = 8 # zero-padding factor

    def analyzeData(self, rawReferenceSignal, rawInterferogram):
        print("Analyzing data")

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
        spectrum = np.fft.rfft(meas_volt_padded)

        # cut spectrum to match the correct X axis (required due to padding)
        spectrum = spectrum[0:len(spectrum_x) - 1]
        # calculate absolute value from the spectrum
        spectrum_abs = np.abs(spectrum)

        #normalize
        spectrum_abs = (spectrum_abs-np.min(spectrum_abs))/(np.max(spectrum_abs)-np.min(spectrum_abs))

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
