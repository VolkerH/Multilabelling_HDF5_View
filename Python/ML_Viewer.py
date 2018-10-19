#!/usr/bin/env python

# TODO: keeping settings in dictionaries is probably not the best idea - find something better
# TODO: implement synchronize Z-sliders
# TODO: implement save settings
# TODO: fallback to simple mixer without image registration if no displacement information is found in HDF5 file

import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from imageviewerwidget import ImageViewer
from antibodypanel import ABPanel
from dropzone import DropZone
import h5py
import numpy as np
import qimage2ndarray
#import jsonpickle
import pickle

import time
# debugging stuff
import pdb
from PyQt4.QtCore import pyqtRemoveInputHook, pyqtRestoreInputHook


class ABViewerWidget(QSplitter):
    """
        The ABviewer widget consists of a horizontal QSplitter dividing two parts
        On the left side of the splitter is the panel of antibodies contained in
         a scroll area.
         On the right side there is a Widget with a vertical layout containing an
          ImageViewer on top and additional control widgets below.
    """
    def __init__(self, hdf5file, parent=None):
        super(ABViewerWidget, self).__init__(parent)
        self.hdf5file = hdf5file

        # open hdf5 file
        try:
            self.f = h5py.File(self.hdf5file,"r")
        except Exception:
            print "Error opening file"
            import traceback
            print traceback.format_exc()
            return

        # get image dimensions
        self.imshape = self.f["AB_"+self.f['ordering'][0]]['imaging']['data']['stack'][:,:,0,:].shape
        print "imshape ", self.imshape
        print self.imshape[2]-1
        self.imageviewer = ImageViewer()

        # Create a container widget and layout that will hold the panels for all antibodies
        self.panels = QWidget()
        self.panellayout = QVBoxLayout(self)
        self.abpaneldict = {}

        if "AB_" + self.f['ordering'][0] + "/imaging/laserpower" in self.f:
            self.dp = ABPanel("DAPI",DAPIPanel=True,ablist=self.f["ordering"],zmax=self.imshape[2]-1, laserpower=self.f["AB_"+self.f['ordering'][0]]['imaging/laserpower'])
        else:
            self.dp = ABPanel("DAPI", DAPIPanel=True, ablist=self.f["ordering"], zmax=self.imshape[2] - 1)

        self.dp.setObjectName("DAPI_widget")
        self.abpaneldict["DAPI"] = self.dp

        self.dp.changed.connect(self.updateUi)
        self.panellayout.addWidget(self.dp)
        for a in self.f["ordering"]:
            if "AB_"+a+"/imaging/laserpower" in self.f:
                abpanelwidget = ABPanel(a, zmax=self.imshape[2]-1, laserpower=self.f["AB_"+a+'/imaging/laserpower'])
            else:
                abpanelwidget = ABPanel(a, zmax=self.imshape[2] - 1)
            abpanelwidget.setObjectName(a+"_widget")
            abpanelwidget.changed.connect(self.updateUi)
            self.panellayout.addWidget(abpanelwidget)
            self.abpaneldict[a]=abpanelwidget

        self.panellayout.addStretch() # TODO: do I need this ????
        self.panels.setLayout(self.panellayout)

        #Scroll Area Properties
        self.scroll = QScrollArea()
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.panels)
        #self.scroll.setFixedWidth(600)

        self.setOrientation(Qt.Horizontal)
        #self.splitter() = QSplitter(Qt.Horizontal)
        w = self.width()
        self.setSizes ([400, max(400,w-400)])

        self.leftHalf = QWidget()
        self.leftHalfLayout = QVBoxLayout()
        self.leftHalfLayout.addWidget(self.scroll)


        # synchronize Z-sliders
        self.synchronizeZCB =  QCheckBox("Synchronize Z sliders")
        self.synchronizeZCB.setObjectName("synchronize_Z_cb")
        self.synchronizeZCB.stateChanged.connect(self.updateUi)
        self.leftHalfLayout.addWidget(self.synchronizeZCB)
        self.leftHalf.setLayout(self.leftHalfLayout)

        self.addWidget(self.leftHalf)
        # Right half of the splitter
        # contains image viewer on top
        # then additional controls for Z
        self.rightHalf = QWidget()
        self.rightHalfLayout = QVBoxLayout()
        self.rightHalfLayout.addWidget(self.imageviewer)

        # button area for save/load buttons and z-synch checkbox
        self.buttonarea = QWidget()
        self.buttonlayout = QHBoxLayout()

        #self.buttonlayout.addWidget(self.synchronizeZCB)

        # Save button
        self.savebutton = QPushButton("Save View")
        self.savebutton.clicked.connect(self.saveImageAs)
        self.buttonlayout.addWidget(self.savebutton)


        # Save/Load settings buttons
        self.savesettingsbutton = QPushButton("Save Settings")
        self.savesettingsbutton.clicked.connect(self.saveSettings)
        self.buttonlayout.addWidget(self.savesettingsbutton)
        self.loadsettingsbutton = QPushButton("Load Settings")
        self.loadsettingsbutton.clicked.connect(self.loadSettings)
        self.buttonlayout.addWidget(self.loadsettingsbutton)

        self.buttonarea.setLayout(self.buttonlayout)
        self.rightHalfLayout.addWidget(self.buttonarea)

        self.rightHalf.setLayout(self.rightHalfLayout)
        self.addWidget((self.rightHalf))
        #self.addWidget(QLabel("space reserved for viewer widget"))

        # run channelmixer once # TODO: is this necessary ?
        self.channelmixer()

    def loadSettings(self):
        """
        Reads and applies viewer settings from a pickle file saved with saveSettings
        :return:
        """
        filename = QFileDialog.getOpenFileName()
        print "Opening settings pickle file: ", str(filename)
        f = open(filename,"rb")
        absettingsdict = pickle.load(f)
        print absettingsdict
        current_antibodies = self.abpaneldict.keys()
        for ab in absettingsdict.keys():
            if ab in current_antibodies:
                self.abpaneldict[ab].setABdisplaySettings(absettingsdict[ab])

    def saveSettings(self):
        """
        Saves the current viewer settings, i.e. visibility, intensity, z range and color
        for each antibody.
        This is achieved by pickling the settings dictionary and saving the pickle object to a file
        :return:
        """
        filename = QFileDialog.getSaveFileName()
        print "Saving settings as pickle file: ", str(filename)
        absettingsdict = {}
        for k in self.abpaneldict.keys():
            panel=self.abpaneldict[k]
            absettingsdict[k]=panel.getABdisplaySettings()
        f = open(filename, 'wb')
        pickle.dump(absettingsdict,f)

    def saveImageAs(self):
        filename = QFileDialog.getSaveFileName()
        print "Saving current view as file: ", str(filename)
        image = qimage2ndarray.array2qimage(self.mixedimage)
        image.save(filename,quality=100)

    def channelmixer(self):
        """
        creates a blended RGB array based on selected colormaps and visibility checkboxes
        for each antibody.
        :return:
        """
        # get image shape from data of first antibody
        # note that we drop the first dimension (channel) as we
        # make the hard-coded assumption that every stack has two channels,
        # namely channel 0 for DAPI and channel 1 for the antibody stain
        # TODO: need to make sure we have four dimensions (channel, z, y, x)


        print("in channelmixer")
        imshape = self.f["AB_"+self.f['ordering'][0]]['imaging']['data']['stack'][:,:,0,:].shape
        nx, ny, nz = imshape

        # get all displacements from hdf5 file
        # and calculate padding in x,y required to create target image canvas
        displacements = np.zeros((len(self.f['ordering']),2),dtype=np.int16)
        for i, ab in enumerate(self.f['ordering']):
            displacements[i,0]=self.f['AB_'+ab]['imaging']['registration']['displacement'][0]
            displacements[i,1]=self.f['AB_'+ab]['imaging']['registration']['displacement'][1]
        max_disp = np.amax(displacements, axis=0)
        min_disp = np.amin(displacements, axis=0)
        min_disp[0]= min(0,min_disp[0])
        min_disp[1]= min(0,min_disp[1])
        padding = max_disp - min_disp

        # Calculate shape of final padded RGB image
        targetshape = [nx+padding[0], ny+padding[1], 3]

        # create float image of same shape. We will do the mixing in float
        # to avoid rounding errors
        self.mixedimage = np.zeros(targetshape,float)
        tmpimage = np.zeros(imshape,np.float)

        for ab in self.abpaneldict.keys():
            absetting = self.abpaneldict[ab].getABdisplaySettings()
            if absetting['visible']:
                if ab is not "DAPI":
                    hdf5index="AB_"+ab
                    channel = 1
                else:
                    hdf5index="AB_"+absetting['selected_DAPI_channel']
                    channel = 0
                # scale, apply color and add to mixedimage
                tmpimage[:,:,:] = self.f[hdf5index]['imaging']['data']['stack'][:,:,channel,:]
                zrange = absetting['zrange']
                # project
                if zrange[1]>zrange[0]:
                    #print "projecting slice  ", zrange[0], "-", zrange[1]
                    image2d = np.max(tmpimage[:,:,zrange[0]:zrange[1]],axis=2)
                elif zrange[1]==zrange[0]:
                    image2d = tmpimage[:,:,zrange[1]]
                else:
                    print "zrange limits inverted. this should never happen"
                range = np.array(absetting['intensity_range'],np.float)
                image2d = 255.0/(range[1]-range[0])*(image2d-range[0])
                outerp =  np.outer(image2d, np.array(absetting['rgb']))
                outerp /= 255.0

                x = self.f[hdf5index]['imaging']['registration']['displacement'][0]-min_disp[0]
                y = self.f[hdf5index]['imaging']['registration']['displacement'][1]-min_disp[1]
                self.mixedimage[x:x+nx, y:y+ny, :] += outerp.reshape(list(imshape[:-1])+[3])

        self.mixedimage = self.mixedimage.clip(0.0, 255.0)
        self.imageviewer.setimage_ndarray(self.mixedimage[:,:,:])

    def updateUi(self):
        print 'upadateUI for file ', self.hdf5file
        sender = self.sender()
            #pdb.set_trace()
        if sender is not None:
            if  isinstance(sender, ABPanel):
                sendername = sender.objectName()
                print "received message from", sendername
                #print sender.getABdisplaySettings()
                print "================================"
        # print "=== Begin Settings Summary"
        # for k in self.abpaneldict.keys():
        #     panel=self.abpaneldict[k]
        #     print panel.getABdisplaySettings()
        # print "=== End Settings Summary"
        if self.synchronizeZCB.isChecked():
             print "Z slider synchronization active"
             try:
                 zrange=sender.getZrange()
                 for key in self.abpaneldict.keys():
                     self.abpaneldict[key].disconnect_all_widgets()
                 for key in self.abpaneldict.keys():
                     self.abpaneldict[key].setZrange(zrange)
                 for key in self.abpaneldict.keys():
                     self.abpaneldict[key].connect_all_widgets()
             except Exception:
                 print "Error synchronizing"
        else:
             print "Z slider synchronization off"
        self.channelmixer()

class AntibodySelectionDlg(QDialog):
    def __init__(self, url, parent=None):
        super(AntibodySelectionDlg, self).__init__(parent)
        self.setWindowTitle(url)
        self.setMinimumWidth(900)
        self.setMinimumHeight(768)
        self.abviewer = ABViewerWidget(url)
        # Layout
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.abviewer)
        self.setLayout(self.layout)

    def updateUi(self):
        print 'upadateUI'
        sender = self.sender()
        if sender is not None:
            if isinstance(sender, ABPanel):
               sendername = sender.objectName()
               print sender.getABdisplaySettings()

class DropZoneDlg(QDialog):
    def __init__(self, irgendwas = "nichts", parent=None):
        super(DropZoneDlg, self).__init__(parent)
        print "initializing drop zone dialog ", irgendwas
        self.forms =[]
        self.setWindowTitle("Drop HDF Files below")
        # Filedrop Widget
        self.filedrop = DropZone()
        self.filedrop.newFilesSignal.connect(self.opennewviewer)
        # Layout
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.filedrop)
        self.setLayout(self.layout)

    def opennewviewer(self, urls):
        for url in urls:
            print "received ", url
            form = AntibodySelectionDlg(str(url.toLocalFile()))
            form.show()
            self.forms.append(form)
        return self.forms

app = QApplication(sys.argv)
form = DropZoneDlg()
form.show()
app.exec_()
