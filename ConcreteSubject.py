import time
from typing import List

from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import threading
import numpy as np
from scipy import signal
import AbstractSubject
from pyOpenBCI import OpenBCICyton
import sys

from Observer import Observer

sys.path.append('C:/Users/oren_/AppData/Local/Programs/Python/Python310/Lib/site-packages')


SCALE_FACTOR = (4500000) / 24 / (2 ** 23 - 1)  # From the pyOpenBCI repo
colors = 'rgbycmwr'

# Set up GUI Layout
app = QtGui.QApplication([])
win = pg.GraphicsWindow(title='Python OpenBCI GUI')
ts_plots = [win.addPlot(row=i, col=0, colspan=2, title='Channel %d' % i, labels={'left': 'uV'}) for i in
            range(1, 9)]
fft_plot = win.addPlot(row=1, col=2, rowspan=4, title='FFT Plot', labels={'left': 'uV', 'bottom': 'Hz'})
fft_plot.setLimits(xMin=1, xMax=125, yMin=0, yMax=1e7)
waves_plot = win.addPlot(row=5, col=2, rowspan=4, title='EEG Bands',
                         labels={'left': 'uV', 'bottom': 'EEG Band'})
waves_plot.setLimits(xMin=0.5, xMax=5.5, yMin=0)
waves_xax = waves_plot.getAxis('bottom')
waves_xax.setTicks([list(zip(range(6), ('', 'Delta', 'Theta', 'Alpha', 'Beta', 'Gama')))])
data = [[0, 0, 0, 0, 0, 0, 0, 0]]

"""
The Subject owns some important state and notifies observers when the state
changes.
"""


class ConcreteSubject(AbstractSubject):
    _state = 0

    """
    For the sake of simplicity, the Subject's state, essential to all
    subscribers, is stored in this variable.
    """

    _observers: List[Observer] = []
    """
    List of subscribers. In real life, the list of subscribers can be stored
    more comprehensively (categorized by event type, etc.).
    """

    def attach(self, observer: Observer) -> None:
        print("Subject: Attached an observer.")
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)

    """
    The subscription management methods.
    """

    def notify(self) -> None:
        """
        Trigger an update in each subscriber.
        """

        print("Subject: Notifying observers...")
        for observer in self._observers:
            observer.update(self)

    def print_raw(sample):
        print(sample.channels_data)

    # Define OpenBCI callback function
    def save_data(sample):
        global data
        data.append([i * SCALE_FACTOR for i in sample.channels_data])

    # Define function to update the graphs
    def updater(self):
        global data, plots, colors
        t_data = np.array(data[-1250:]).T  # transpose data
        fs = 250  # Hz

        # Notch Filter
        def notch_filter(val, data, fs=250):
            notch_freq_Hz = np.array([float(val)])
            for freq_Hz in np.nditer(notch_freq_Hz):
                bp_stop_Hz = freq_Hz + 3.0 * np.array([-1, 1])
                b, a = signal.butter(3, bp_stop_Hz / (fs / 2.0), 'bandstop')
                fin = data = signal.lfilter(b, a, data)
            return fin

        # Bandpass filter
        def bandpass(start, stop, data, fs=250):
            bp_Hz = np.array([start, stop])
            b, a = signal.butter(5, bp_Hz / (fs / 2.0), btype='bandpass')
            return signal.lfilter(b, a, data, axis=0)

        # Applying the filters
        nf_data = [[], [], [], [], [], [], [], []]
        bp_nf_data = [[], [], [], [], [], [], [], []]

        for i in range(8):
            nf_data[i] = notch_filter(60, t_data[i])
            bp_nf_data[i] = bandpass(15, 80, nf_data[i])

        # Plot a time series of the raw data
        for j in range(8):
            ts_plots[j].clear()
            ts_plots[j].plot(pen=colors[j]).setData(t_data[j])

        # Get an FFT of the data and plot it
        sp = [[], [], [], [], [], [], [], []]
        freq = [[], [], [], [], [], [], [], []]

        fft_plot.clear()
        for k in range(8):
            sp[k] = np.absolute(np.fft.fft(bp_nf_data[k]))
            freq[k] = np.fft.fftfreq(bp_nf_data[k].shape[-1], 1.0 / fs)
            fft_plot.plot(pen=colors[k]).setData(freq[k], sp[k])

        # Define EEG bands
        eeg_bands = {'Delta': (1, 4),
                     'Theta': (4, 8),
                     'Alpha': (8, 12),
                     'Beta': (12, 30),
                     'Gamma': (30, 45)}

        # Take the mean of the fft amplitude for each EEG band (Only consider first channel)
        eeg_band_fft = dict()
        sp_bands = np.absolute(np.fft.fft(t_data[1]))
        freq_bands = np.fft.fftfreq(t_data[1].shape[-1], 1.0 / fs)

        for band in eeg_bands:
            freq_ix = np.where((freq_bands >= eeg_bands[band][0]) &
                               (freq_bands <= eeg_bands[band][1]))[0]
            eeg_band_fft[band] = np.mean(sp_bands[freq_ix])

        sleep_status = (eeg_band_fft['Delta']+eeg_band_fft['Theta'])/sum(eeg_band_fft.values())
        threshold_before_sleep = 0.5
        if sleep_status >= threshold_before_sleep:
            self.notify()
            time.sleep(70)

        # Plot EEG Bands
        bg1 = pg.BarGraphItem(x=[1, 2, 3, 4, 5], height=[eeg_band_fft[band] for band in eeg_bands], width=0.6,
                              brush='r')
        waves_plot.clear()
        waves_plot.addItem(bg1)

    # Define thread function
    def start_board(self):
        board = OpenBCICyton(port='COM3')
        board.start_stream(self.save_data)
        board.disconnect()

    def some_business_logic(self) -> None:
        """
        Usually, the subscription logic is only a fraction of what a Subject can
        really do. Subjects commonly hold some important business logic, that
        triggers a notification method whenever something important is about to
        happen (or after it).
        """

        print("\nSubject starting GUI logic")
        x = threading.Thread(target=self.start_board)
        x.daemon = True
        x.start()
        timer = QtCore.QTimer()
        timer.timeout.connect(self.updater)
        timer.start(0)

        QtGui.QApplication.instance().exec_()
