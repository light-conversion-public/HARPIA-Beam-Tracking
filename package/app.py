#!/usr/bin/env python
# -*- coding: utf-8 -*-
#==========================================================================
# Harpia REST API Interface example
#--------------------------------------------------------------------------
# Copyright (c) 2021 Light Conversion, UAB
# All rights reserved.
# www.lightcon.com
#==========================================================================
     
import lclauncher

import os
import sys    
import time
import numpy as np
import lightcon.style

# lightcon.style.apply_style()

sys.path.append(os.path.dirname(os.path.realpath(sys.argv[0])))
os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

# if connections to devices are used, they are initiated here:
connections = lclauncher.establish_connections()

# initialize and connect to HARPIA
harpia = connections.get_connection('harpia')

# initialize and connect to CameraApp
camera = connections.get_connection('camera')

# check if connection successful
if not harpia:
    sys.exit("Could not connect to Harpia")

# check if connection successful
if not camera:
    sys.exit("Could not connect to CameraApp")

import matplotlib
matplotlib.use('Qt5Agg')

from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot, QObject, QThread, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(dict)

    def run(self):
        self.is_running = True
        camera.enable_beam_profiler()
        camera.set_beam_profiler_mode('ISO')
        

        while self.is_running:
            time.sleep(0.2)
            beam_parameters = camera.get_beam_parameters()

            self.progress.emit({'position': harpia._get('DelayLine/ActualDistance'), 'beam_parameters' : beam_parameters})
        self.finished.emit()
        
    def stop(self):
        self.is_running = False
        
class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax1 = fig.add_subplot(111)
        self.ax2 = self.ax1.twinx()
        super(MplCanvas, self).__init__(fig)
        
class MainWindow(QMainWindow):
    sc = None
    beam_log = []
    
    def __init__(self, title):
        super().__init__()
        self.title = title
        self.left = 100
        self.top = 100
        self.width = 900
        self.height = 900
        self.initUI()
        
            
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        
        self.start_button = QPushButton('START', self)
        self.start_button.setToolTip('Start measuring')
        self.start_button.clicked.connect(self.start_button_on_click)

        self.stop_button = QPushButton('STOP', self)
        self.stop_button.setToolTip('Stop measuring')
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_button_on_click)

        self.clear_button = QPushButton('CLEAR', self)
        self.clear_button.clicked.connect(self.clear_button_on_click)
                
        self.sc = [MplCanvas(self, width=5, height=3, dpi=100), MplCanvas(self, width=5, height=3, dpi=100)]

        outerLayout = QVBoxLayout()
        topLayout = QHBoxLayout()            
        bottomLayout = QVBoxLayout()

        topLayout.addWidget(self.start_button, 1)
        topLayout.addWidget(self.stop_button, 1)
        topLayout.addWidget(self.clear_button, 1)

        bottomLayout.addWidget(self.sc[0])        
        bottomLayout.addWidget(self.sc[1])        
        
        outerLayout.addLayout(topLayout)
        outerLayout.addLayout(bottomLayout)
        
        widget = QWidget()
        widget.setLayout(outerLayout)

        self.setCentralWidget(widget)  
        self.show()
        
    def runLongTask(self):        
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.progress.connect(self.addToPlots)
        self.thread.start()
        # Final resets       
        # self.thread.finished.connect(self.addToPlots)

    def stopLongTask(self):
        self.worker.stop()

    def addToPlots(self, info):
        if (len(self.beam_log) > 0):
            if info['position'] == self.beam_log[-1]['position']:
                self.beam_log[-1] = info
            else:
                self.beam_log = self.beam_log + [info]
        else:
            self.beam_log = self.beam_log + [info]

        imin = np.argmin([item['position'] for item in self.beam_log])
        imax = np.argmax([item['position'] for item in self.beam_log])

        if (imin < imax):
            if (imax != len(self.beam_log) - 1):
                self.beam_log = self.beam_log[imax:]
        else:
            if (imin != len(self.beam_log) - 1):
                self.beam_log = self.beam_log[imin:]
        
        # self.beam_log = self.beam_log[-100:]

        for sc in self.sc:
            sc.ax1.cla()
            sc.ax2.cla()
            sc.ax1.set_xlabel('Delay line position, mm')

        x = [item['position'] for item in self.beam_log]
        fx = [x[0],x[-1]]
        y = [[item['beam_parameters']['MeanX'] for item in self.beam_log], [item['beam_parameters']['MeanY'] for item in self.beam_log]]
        f = [np.poly1d(np.polyfit(x,y[0],1))(fx), np.poly1d(np.polyfit(x,y[1],1))(fx) ]
        lns = []

        lns = lns + self.sc[0].ax1.plot(x, y[0], '.-', color='C0', label = '$\\Delta X$ {:.0f} um'.format((np.max(y[0]) - np.min(y[0]))*1.0e3))
        lns = lns + self.sc[0].ax2.plot(x, y[1], '.-',color='C1', label = '$\\Delta Y$ {:.0f} um'.format((np.max(y[1]) - np.min(y[1]))*1.0e3))    
        self.sc[0].ax1.plot(fx, f[0], '--', color='C0')
        self.sc[0].ax2.plot(fx, f[1], '--',color='C1')  
        self.sc[0].ax1.set_ylabel('X beam position, mm')
        self.sc[0].ax2.set_ylabel('Y beam position, mm')
        
        self.sc[0].ax1.legend(lns, [l.get_label() for l in lns])

        y = [[item['beam_parameters']['SigmaPrimary'] for item in self.beam_log], [item['beam_parameters']['SigmaSecondary'] for item in self.beam_log]]
        f = [np.poly1d(np.polyfit(x,y[0],1))(fx), np.poly1d(np.polyfit(x,y[1],1))(fx) ]

        self.sc[1].ax1.plot(x, y[0], '.-', color='C0')
        self.sc[1].ax2.plot(x, y[1], '.-',color='C1')
        self.sc[1].ax1.plot(fx, f[0], '--', color='C0')
        self.sc[1].ax2.plot(fx, f[1], '--',color='C1')  
        self.sc[1].ax1.set_ylabel('X beam sigma P, mm')
        self.sc[1].ax2.set_ylabel('Y beam sigma S, mm')

        for sc in self.sc:
            sc.draw_idle()
        
    @pyqtSlot()
    def start_button_on_click(self):
        # camera.enable_beam_profiler()
        self.runLongTask()
        self.stop_button.setEnabled(True)
        self.start_button.setEnabled(False)
        
    @pyqtSlot()
    def stop_button_on_click(self):
        # camera.enable_beam_profiler()
        self.stopLongTask()
        self.stop_button.setEnabled(False)
        self.start_button.setEnabled(True)


    @pyqtSlot()
    def clear_button_on_click(self):
        # camera.enable_beam_profiler()
        self.beam_log = []

app = QApplication([])
w = MainWindow('HARPIA beam tracking')
app.exec_()
