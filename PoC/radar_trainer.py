"""sudo apt-get install libxcb-xinerama0"""


import numpy as np
import pyqtgraph as pg
import sys
import serial
import time

from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from time import sleep
from os import system

import serial.tools.list_ports


ports = serial.tools.list_ports.comports()
for port, desc, hwid in sorted(ports):
    portc = port
    print("{}\n".format(portc))
    print("{}\n".format(desc))
    print("{}\n".format(hwid))
    #
    # raw = serial.Serial(port=portc, baudrate=20000000, timeout=1)

raw = serial.Serial(port="/dev/ttyACM0", baudrate=20000000, timeout=1)
# raw = serial.Serial(port="COM5", baudrate=20000000, timeout=1)
# raw = serial.Serial(port="/dev/ttyS0", baudrate=9600, timeout=1)


# data
nSample = 1024
nAscan = 250
nBinMax = nSample / 2


class Plot2D:
    def __init__(self):
        # self.app = QtGui.QApplication([])
        self.app = QtWidgets.QApplication([])
        self.win = pg.GraphicsLayoutWidget()
        self.raw_data = self.win.addPlot(row=0, col=0, title="Raw Data Plot")
        # self.raw_data.setRange(yRange=[-20,20], xRange=[0,nSample])
        self.raw_data.setRange(xRange=[0, nSample])
        self.raw_data.showGrid(y=True)
        self.raw_data_plot = self.raw_data.plot(pen="y")
        self.raw_data_spectrum = self.win.addPlot(
            row=0, col=1, title="Raw Data Spectrum Plot"
        )
        self.raw_data_spectrum.setRange(xRange=[1, 100])
        self.raw_data_spectrum.showGrid(y=True)

        self.raw_data_spectrum_plot = self.raw_data_spectrum.plot(pen="y")
        self.Bscan_plot = self.win.addViewBox(row=1, col=0, colspan=3)

        # self.Bscan_array = np.zeros([nAscan, nBinMax / 2])
        self.Bscan_array = np.zeros([nAscan, int(nBinMax / 2)])

        self.Bscan_img = pg.ImageItem(self.Bscan_array)

        self.histogram = pg.HistogramLUTItem()
        self.histogram.gradient.loadPreset("bipolar")
        self.histogram.setImageItem(self.Bscan_img)

        self.Bscan_img.setLevels([0, 70])
        self.Bscan_plot.addItem(self.Bscan_img)

        self.raw_data.setMouseEnabled(x=False, y=False)  # Disable panning
        # self.raw_data.setAspectLocked(lock=True)  # Fix aspect ratio
        self.raw_data_spectrum.setMouseEnabled(x=False, y=False)  # Disable panning
        # self.raw_data_spectrum.setAspectLocked(lock=True)  # Fix aspect ratio
        self.Bscan_plot.setMouseEnabled(x=False, y=False)  # Disable panning
        # self.Bscan_plot.setAspectLocked(lock=True)  # Fix aspect ratio

        self.winhamm = np.hamming(nSample)
        self.win.showFullScreen()

    def setup_Ascan(self, N):
        self.raw_data.setRange(xRange=[N * 0.05, N * 0.95])
        self.raw_data.showGrid(y=True)

    def trace_raw_data(self, dataset_y):
        self.raw_data_plot.setData(dataset_y)

    def trace_raw_data_spectrum(self, dataset_y):
        self.raw_data_spectrum_plot.setData(dataset_y)

    def Ascan2Bscan(self, aScan_data):
        self.Bscan_array = np.roll(self.Bscan_array, -1, 0)
        self.Bscan_array[-1:] = aScan_data

    def trace_BscanDariAdraw(self):
        self.Bscan_img.setImage(self.Bscan_array, autoLevels=False)

    def start(self):
        # QtGui.QApplication.instance().exec_()
        QtWidgets.QApplication.instance().exec_()

    def onKey(self, e):
        print("SSSS")
        if e.key() == 71:  # "q" quit
            sys.exit()


if __name__ == "__main__":
    i = 0
    i_er = 0
    p = Plot2D()
    nShift = 0
    nSampleT = 5

    def update():
        global p, i, i_er, nShift, nSampleT, count

        dat1 = raw.read(nSample * 2)
        # print(dat1)

        dat2 = np.frombuffer(dat1, dtype="int16", offset=0)
        # print(dat2)

        if len(dat2) == nSample:
            # print("%d  %d" % (i,len(dat2)))
            s = np.array(dat2[0:nSample])
            cekF0F = s[nSample - 1]
            nSampleX = s[nSample - 2]
            sr = s[nSample - 3]
            prf = s[nSample - 4]
            cekIns = s[nSample - 5]
        else:
            cekF0F = 0

        if cekF0F == 3855:
            if nSampleX != nSampleT:
                p.setup_Ascan(nSampleX)
                nSampleT = nSampleX
            s[nSampleX:nSample] = 0
            s = s - (np.sum(s)) / nSampleX
            s[nSampleX:nSample] = 0
            ss = s
            s = s * p.winhamm
            # S = 20*np.log10(abs(np.fft.rfft(s))/np.sqrt(nSampleX)+.001)
            S = 20 * np.log10(abs(np.fft.rfft(s)) / (nSampleX) + 0.001)
            S = S * S / 15
            # S = 2*(S-30)

            p.trace_raw_data(ss)
            p.Ascan2Bscan(S[nShift : int(nShift + nBinMax / 2)])
            p.trace_BscanDariAdraw()
            # p.trace_raw_data_spectrum(S[nShift : int(nShift + nBinMax * 2)])
            p.trace_raw_data_spectrum(S[50 : int(nShift + nBinMax * 2)])
            s[nSample - 4 : nSample - 1] = 10
        else:
            i_er += 1
            raw.flushInput()
            raw.flushOutput()
            raw.close()
            raw.open()
        i += 1
        if i >= 100:
            print(
                "%d/%d  prf`=%d  sr=%dk  M=%d  %d"
                % (i, i_er, prf, sr, nSampleX, cekIns)
            )
            i = 0
            i_er = 0

    try:
        raw.open()
    except:
        pass

    if raw.isOpen():
        time.sleep(0.2)
        try:
            dat1 = raw.read(nSample * 2)
            raw.flushInput()
            raw.flushOutput()
            timer = QtCore.QTimer()
            timer.timeout.connect(update)
            timer.start(5)
            p.start()
        except None:
            pass
