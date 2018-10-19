__author__ = 'volkerhilsenstein'

#############################################
# Volker.Hilsenstein@embl.de
# (c) July 2015
#############################################

from colorbox import ColorBox
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from QxtSpanSlider import QxtSpanSlider
import numpy as np


class ABPanel(QGroupBox):
    """
    Antibody GUI Panel
    This GUI panel contains a color select box, an intensity slider and a z ragne slider.
    If the Panel is initialized with DAPIPanel=True and a list of antibodies in ablist there
    will also be a set of radio buttons to select the appropriate antibody from which the DAPI
    channel image was taken
    """
    changed  =  pyqtSignal()
    def __init__(self,ab="ABname", min_initial=0, max_initial=255, zmin=0, zmax=4, color_initial=(0,255,0), visible=False, parent=None, DAPIPanel=False, ablist=None, laserpower=None):
        super(ABPanel, self).__init__(parent)
        # TODO: should pass in the settings rather than creating them here. This seems a bad design.
        self.isDAPIPanel= DAPIPanel
        self.ablist = ablist
        self.ab = ab

        # Fill Settings dictionary
        self.ABsettings = {}
        self.ABsettings["Antibody"]=self.ab
        self.ABsettings["intensity_range"]=(min_initial,max_initial)
        self.ABsettings["zrange"]=(zmin,zmax)
        self.ABsettings["rgb"]=color_initial
        self.ABsettings["visible"]=visible
        self.ABsettings["selected_DAPI_channel"]=None

        if laserpower is not None:
            if DAPIPanel:
                lp= "      laser:  {:3.1f}".format(laserpower[0])
            else:
                lp = "     laser: {:3.1f}".format(laserpower[1])
        else:
            lp = ""

        self.setTitle(self.ab+lp)

        self.abpanellayout = QGridLayout()
        # channel visibility checkbox
        self.abEnabledCB = QCheckBox("visible")
        self.abEnabledCB.setObjectName(self.ab+"_cb")
        #self.abEnabledCB.stateChanged.connect(self.updateSettings)
        # color select box
        self.colorBox = ColorBox()
        self.colorBox.setObjectName(self.ab+"colorbox")
        #self.colorBox.colorchanged.connect(self.updateSettings)
        # pixel intensity range slider
        self.spansliderInt = QxtSpanSlider()
        self.spansliderInt.setObjectName(self.ab+"spansliderInt")
        self.labelMaxInt = QLabel(str(max_initial))
        self.spansliderInt.setRange(0,255)
        self.spansliderInt.setSpan(0,255)
        #self.spansliderInt.spanChanged.connect(self.updateSettings)
        # Z stack slider
        self.spansliderZ = QxtSpanSlider()
        self.spansliderZ.setObjectName(self.ab+"spansliderZ")
        self.labelMaxZ = QLabel()   # TODO: initiliaze properly
        self.spansliderZ.setRange(zmin,zmax)
        self.spansliderZ.setSpan(zmin,zmax)
        #self.spansliderZ.spanChanged.connect(self.updateSettings)

        self.abpanellayout.addWidget(self.abEnabledCB, 0, 0)
        self.abpanellayout.addWidget(QLabel("Color:"), 0, 1)
        self.abpanellayout.addWidget(self.colorBox, 0, 2)
        self.minIntensityLabel = QLabel()
        self.abpanellayout.addWidget(self.minIntensityLabel, 3, 0)
        self.abpanellayout.addWidget(self.spansliderInt, 3, 1, 1, 1)
        self.abpanellayout.addWidget(self.labelMaxInt, 3, 2)
        self.minZLabel = QLabel()
        if zmax > zmin:
            self.abpanellayout.addWidget(self.minZLabel, 4, 0)
            self.abpanellayout.addWidget(self.spansliderZ, 4, 1, 1, 1)
            self.abpanellayout.addWidget(self.labelMaxZ, 4, 2)


        self.radiobuttons = []
        if DAPIPanel:
            assert ablist is not None
            for i,antibody in enumerate(ablist):
                radiobutton = QRadioButton(antibody)
                radiobutton.setObjectName(antibody+"_rb")
                self.radiobuttons.append(radiobutton)
                if i==0: # select DAPI of first channel during initialization
                    self.ABsettings["selected_DAPI_channel"]=antibody
                    radiobutton.setChecked(True)
                self.abpanellayout.addWidget(radiobutton)

        self.connect_all_widgets()
        self.updateLabels()
        self.setLayout(self.abpanellayout)

    def setZrange(self, zrange):
        self.spansliderZ.setLowerValue(int(zrange[0]))
        self.spansliderZ.setUpperValue(int(zrange[1]))

    def getZrange(self):
        return (self.spansliderZ.lowerValue,self.spansliderZ.upperValue)

    def connect_all_widgets(self):
        self.abEnabledCB.stateChanged.connect(self.updateSettings)
        self.colorBox.colorchanged.connect(self.updateSettings)
        self.spansliderInt.spanChanged.connect(self.updateSettings)
        self.spansliderZ.spanChanged.connect(self.updateSettings)
        for button in self.radiobuttons:
            button.clicked.connect(self.updateSettings)

    def disconnect_all_widgets(self):
        self.abEnabledCB.stateChanged.disconnect()
        self.colorBox.colorchanged.disconnect()
        self.spansliderInt.spanChanged.disconnect()
        self.spansliderZ.spanChanged.disconnect()
        for button in self.radiobuttons:
            button.clicked.disconnect()


    def settingstowidgets(self):
        """
        Updates the widgets so they reflect the current settings
        """

        # disconnect before updating, otherwise
        # the current GUI settings will be reinstated
        # after the first GUI element is updated
        self.disconnect_all_widgets()

        self.spansliderInt.setLowerValue(int(self.ABsettings["intensity_range"][0]))
        self.spansliderInt.setUpperValue(int(self.ABsettings["intensity_range"][1]))
        print "vis setting ",self.ABsettings["visible"]
        if self.ABsettings["visible"]:
            print "setting ",self.objectName(), " to visible"
            self.abEnabledCB.setChecked(True)
        else:
            print "setting ",self.objectName(), " to invisible"
            self.abEnabledCB.setChecked(False)
        self.spansliderZ.setLowerValue(int(self.ABsettings["zrange"][0]))
        self.spansliderZ.setUpperValue(int(self.ABsettings["zrange"][1]))
        #self.ABsettings["Antibody"]=self.ab
        self.colorBox.setRGB(self.ABsettings["rgb"])
        if self.isDAPIPanel:
            for rb in self.radiobuttons:
                print "radio button ", str(rb.objectName())
                if str(rb.objectName()).split("_")[0]==self.ABsettings["selected_DAPI_channel"]:
                    rb.setChecked(True)
                    print "is checked"

        # reconnect everything
        self.connect_all_widgets()
        self.updateSettings()

    def widgetstosettings(self):
        """
        Updates the settings dictionary so they reflect the current settings
        """
        print "in widgets to settings"
        self.ABsettings["intensity_range"]=(self.spansliderInt.lowerValue,self.spansliderInt.upperValue)
        self.ABsettings["rgb"]=self.colorBox.getRGB
        self.ABsettings["visible"]=self.abEnabledCB.isChecked()
        self.ABsettings["zrange"]=(self.spansliderZ.lowerValue,self.spansliderZ.upperValue)
        self.ABsettings["Antibody"]=self.ab
        for button in self.radiobuttons:
            if button.isChecked():
                self.ABsettings["selected_DAPI_channel"]=str(button.objectName())[:-3]
                print "Dapi channel setting is ", self.ABsettings["selected_DAPI_channel"]


    def updateLabels(self):
        """
        Updates the text labels that display the slider values
        """
        # Intensity range
        self.minIntensityLabel.setText("Intensity: "+str(self.ABsettings["intensity_range"][0]).rjust(3))
        self.labelMaxInt.setText(str(self.ABsettings["intensity_range"][1]).ljust(3))
        # Z range
        self.minZLabel.setText("Z range: "+str(self.ABsettings["zrange"][0]+1).rjust(2))
        self.labelMaxZ.setText(str(self.ABsettings["zrange"][1]+1).ljust(2))


    def updateSettings(self):
        #print "updateSettings"
        #sender = self.sender()
        self.widgetstosettings()
        self.updateLabels()
        self.changed.emit()

    def getABdisplaySettings(self):
        return self.ABsettings

    def setABdisplaySettings(self, new_settings):
        print "in ", self.objectName()
        for key in new_settings.keys():
            self.ABsettings[key] = new_settings[key]
            print "setting ", key , "changed to ", self.ABsettings[key]
        #
        # self.ABsettings = new_settings
        self.settingstowidgets()
        self.updateLabels()
        self.updateSettings()