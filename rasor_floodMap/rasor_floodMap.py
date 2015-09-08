"""
/***************************************************************************
 A QGIS plugin in order to generate Rasor compliant flood maps from Sentinel-1 Images
 For the RASOR FP7 Project (http://www.rasor-project.eu/)
                             -------------------
        begin                : 2015-08-09
        copyright            : (C) 2015 by Altamira-Information.com
        email                : joan.sala@altamira-information.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

# PyQT4 imports
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtCore, QtGui

# QGIS imports
from qgis.core import *
import qgis.utils
from qgis.gui import QgsMessageBar

# Custom imports RASOR
from rasor_flood_api import StepWorker
from rasor_step_api import StepOne
from rasor_step_api import StepTwo
from rasor_step_api import StepThree
from rasor_poly_api import Shapefile
from rasor_gtiff_api import GeoTiff

# Initialize Qt resources from file resources.py
import resources_rc

# Import the code for the dialog
from rasor_floodMap_dialog import rasorDialog

# Imports (packages)
import os.path, json, tempfile, subprocess, threading, locale
from os.path import expanduser

# Global variables
user=""
pwd=""

class rasor:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """

	# Set locale to english (dates)
	QLocale.setDefault(QLocale(QLocale.English, QLocale.UnitedStates))

        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        self.template_dir = os.path.dirname(__file__)+'/templates'
		
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir,'i18n','rasor_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = rasorDialog()
		
        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Rasor Sentinel-1 Flood Mapping')

	# TODO: We are going to let the user set this up in a future iteration
	self.toolbar = self.iface.addToolBar(u'rasorFloodMap')
	self.toolbar.setObjectName(u'rasorFloodMap')
	self.dlg.tabSteps.currentChanged.connect(self.tabChanged)
	self.tabChanged()
	
	# Connect signals/slots
	self.dlg.connect(self.dlg.pushButtRUN, SIGNAL("clicked()"), self.buttRUNCLICK)
	self.dlg.editS1Path.setReadOnly(1)
	self.dlg.connect(self.dlg.buttS1Path, SIGNAL("clicked()"), self.buttS1PathCLICK)
	self.dlg.editOutPath.clear()
	self.dlg.editOutPath.setReadOnly(1)
	self.dlg.connect(self.dlg.buttOutPath, SIGNAL("clicked()"), self.buttOutPathCLICK)	
	self.dlg.editBefore1.clear()
	self.dlg.editBefore1.setReadOnly(1)
	self.dlg.connect(self.dlg.buttBefore1, SIGNAL("clicked()"), self.buttBeforeCLICK1)
	self.dlg.editAfter1.clear()
	self.dlg.editAfter1.setReadOnly(1)
	self.dlg.connect(self.dlg.buttAfter1, SIGNAL("clicked()"), self.buttAfterCLICK1)	
	self.dlg.editBefore2.clear()
	self.dlg.editBefore2.setReadOnly(1)
	self.dlg.connect(self.dlg.buttBefore2, SIGNAL("clicked()"), self.buttBeforeCLICK2)
	self.dlg.editAfter2.clear()
	self.dlg.editAfter2.setReadOnly(1)
	self.dlg.connect(self.dlg.buttAfter2, SIGNAL("clicked()"), self.buttAfterCLICK2)	
	self.dlg.editRGB3.clear()
	self.dlg.editRGB3.setReadOnly(1)
	self.dlg.connect(self.dlg.buttRGB3, SIGNAL("clicked()"), self.buttRGB3CLICK)
	
	self.dlg.editAOI.clear()
	self.dlg.editAOI.setReadOnly(1)
	self.dlg.connect(self.dlg.buttAOI, SIGNAL("clicked()"), self.buttAfterAOI)
	self.dlg.connect(self.dlg.pushButtLOAD1, SIGNAL("clicked()"), self.loadStep1QGIS)
	self.dlg.connect(self.dlg.pushButtLOAD2, SIGNAL("clicked()"), self.loadStep2QGIS)
	self.dlg.connect(self.dlg.pushButtLOAD3, SIGNAL("clicked()"), self.loadStep3QGIS)
	
	# TEST
	self.dlg.editS1Path.setText('C:\Program Files\S1TBX')
	self.dlg.editOutPath.setText('C:\Users\joan.ALTAMIRA-INFORM\Desktop\TEST-S1-PLUGIN')
	self.dlg.editAfter1.setText('C:\Users\joan.ALTAMIRA-INFORM\Desktop\S1A_IW_GRDH_1SDV_20141104T172239_20141104T172304_003135_0039A3_7838.SAFE\manifest.safe')
	self.dlg.editBefore1.setText('C:\Users\joan.ALTAMIRA-INFORM\Desktop\S1A_IW_GRDH_1SDV_20141116T172239_20141116T172304_003310_003D5C_CA09.SAFE\manifest.safe')
	self.dlg.editAOI.setText('C:\Users\joan.ALTAMIRA-INFORM\Desktop\TEST-S1-PLUGIN\PO_river_AREA_SMALL.shp')
	
	# CLICKED functions
    def buttS1PathCLICK(self):
	    dir = self.tr(QFileDialog.getExistingDirectory(self.dlg, "Select S1-TBX Directory", self.getWDIR()))
	    self.dlg.editS1Path.setText(dir)	    
    def buttOutPathCLICK(self):
	    dir = self.tr(QFileDialog.getExistingDirectory(self.dlg, "Select OUTPUT Directory", self.getWDIR()))
	    self.dlg.editOutPath.setText(dir)	    
    def buttBeforeCLICK1(self):
	    file = self.tr(QFileDialog.getOpenFileName(self.dlg, "Select S1 image manifest file", self.getWDIR(), "S1 manifest files (manifest.safe)"))
	    self.dlg.editBefore1.setText(file)
    def buttAfterCLICK1(self):
	    file = self.tr(QFileDialog.getOpenFileName(self.dlg, "Select S1 image manifest file", self.getWDIR(), "S1 manifest files (manifest.safe)"))
	    self.dlg.editAfter1.setText(file)	    
    def buttBeforeCLICK2(self):
	    file = self.tr(QFileDialog.getOpenFileName(self.dlg, "Select S1 prepared TIF", self.getWDIR(), "S1 prepared tif (*.tif)"))
	    self.dlg.editBefore2.setText(file)
	    tiffReader=GeoTiff(file)
	    self.dlg.lineEditBefore.setText(tiffReader.getDATE())
    def buttAfterCLICK2(self):
	    file = self.tr(QFileDialog.getOpenFileName(self.dlg, "Select S1 prepared TIF", self.getWDIR(), "S1 prepared tif (*.tif)"))
	    self.dlg.editAfter2.setText(file)
	    tiffReader=GeoTiff(file)
	    self.dlg.lineEditAfter.setText(tiffReader.getDATE())
    def buttRGB3CLICK(self):
	    file = self.tr(QFileDialog.getOpenFileName(self.dlg, "Select RGB tiff from step 2", self.getWDIR(), "S2 prepared tif (*.tif)"))
	    self.dlg.editRGB3.setText(file)		
    def buttAfterAOI(self):
	    shp_file = self.tr(QFileDialog.getOpenFileName(self.dlg, "Select Area of Interest SHP", self.getWDIR(), "ESRI Shapefile (*.shp)"))
	    self.dlg.editAOI.setText(shp_file)
    def loadStep1QGIS(self):
		file1=self.get_out_path()+"\\after.tif"
		file2=self.get_out_path()+"\\before.tif"
		self.load_raster_QGIS(file1)
		self.load_raster_QGIS(file2)
    def loadStep2QGIS(self):
		file1=self.get_out_path()+"\\RGB.tif"
		self.load_raster_QGIS(file1)
    def loadStep3QGIS(self):
		file1=self.get_out_path()+"\\RGB_Segmentation.tif"
		self.load_raster_QGIS(file1)

	# Read raster and load it to QGIS
    def load_raster_QGIS(self, fileName):
		if os.path.exists(fileName):
			fileInfo = QFileInfo(fileName)
			baseName = fileInfo.baseName()
			rlayer = QgsRasterLayer(fileName, baseName)			
			if not rlayer.isValid():
				print "Unable to load raster layer: "+fileName
			else:
				if rlayer.bandCount() == 1:
					# Black transparent
					myPixel = QgsRasterTransparency.TransparentSingleValuePixel()
					myPixel.pixelValue = 0
					myPixel.percentTransparent = 100
					myTransparencyList = []
					myTransparencyList.append(myPixel)
					rlayer.renderer().rasterTransparency().setTransparentSingleValuePixelList(myTransparencyList)
					QgsMapLayerRegistry.instance().addMapLayer(rlayer)
				else:
					# RGB black transparent
					myPixel = QgsRasterTransparency.TransparentThreeValuePixel()
					myPixel.red = 0
					myPixel.green = 0
					myPixel.blue = 0
					myPixel.percentTransparent = 100
					myTransparencyList = []
					myTransparencyList.append(myPixel)
					rlayer.renderer().rasterTransparency().setTransparentThreeValuePixelList(myTransparencyList)
					QgsMapLayerRegistry.instance().addMapLayer(rlayer)
		else:
			self.show_error('The file '+fileName+' does not exist. Please check your working directory.')
	
	# Run function
    def buttRUNCLICK(self):
	    index=self.dlg.tabSteps.currentIndex()
	    self.dlg.textBrowser.clear()
	    if index == 1:
			print 'Running Step 1: Calibration -> Orthorectification -> Speckle filtering'
			self.run_step_1()
	    if index == 2:
			print 'Running Step 2: RGB composition -> Change detection'
			self.run_step_2()
	    if index == 3:
			print 'Running Step 3: Segmentation'
			self.run_step_3()
	    if index == 4:
			print 'Running Step 4: Classification'	
			self.run_step_4()

	# Get working directory
    def getWDIR(self):
		wdir = self.dlg.editOutPath.text()
		if not wdir:
			wdir = expanduser("~")
		return wdir

	# Called on tab changed event
    def tabChanged(self):
	    index=self.dlg.tabSteps.currentIndex()
	    self.dlg.textBrowser.clear()
	    if index == 0:
			self.dlg.textBrowser.setText("<b><font color=\"green\">CONFIG:</font></b><br/><br/><b><font color=\"blue\">EXE_DIR:</font></b> Sentinel-1 Toolbox (S1TBX) executables directory (usually C:\Program Files\S1TBX).<br/><b><font color=\"blue\">WORKSPACE:</font></b> Output directory where files will be stored.<br/><b><font color=\"blue\">AOI (Area of Interest):</font></b> One shapefile with an area of interest (polygon)")		
	    if index == 1:
			self.dlg.textBrowser.setText("<b><font color=\"green\">INPUT:</font></b><br/>two manifest files from Sentinel-1 Images, one before the flood event and one after. One shapefile with an area of interest (polygon)<br/><br/><b><font color=\"green\">OUTPUT:</font></b><br/>The two images calibrated, orthorectified and subsetted by the polygon bounding box in GeoTIFF format.")
	    if index == 2:
			self.dlg.textBrowser.setText("<b><font color=\"green\">INPUT:</font></b><br/>two Geotiff images alredy processed in the previous step with their associated dates of acquisition.<br/><br/><b><font color=\"green\">OUTPUT:</font></b><br/>RGB composition ready for change detection.")
	    if index == 3:
			self.dlg.textBrowser.setText("<b><font color=\"green\">INPUT:</font></b><br/>one RGB Geotiff image with the change detection information from the previous step <br/><br/><b><font color=\"green\">OUTPUT:</font></b><br/> one RGB Geotiff with the segmentation output")
	    if index == 4:
			self.dlg.textBrowser.setText("<b><font color=\"green\">INPUT:</font></b><br/> ... <br/><br/><b><font color=\"green\">OUTPUT:</font></b><br/> ... ")

    # Called on error
    def show_error(self, errmsg):
		self.dlg.textBrowser.setText("<b><font color=\"red\">ERROR:</font></b><br/>"+errmsg)	

	# Called on batch task start
    def start_task(self):
		# Start progress bar
		self.dlg.progressGUI.setValue(0)
		self.dlg.progressGUI.setTextVisible(True)

	# Called on batch task end
    def end_task(self):
		# Stop progress bar
		self.dlg.progressGUI.setValue(0)
		self.dlg.progressGUI.setTextVisible(False)
		# Clear text
		self.tabChanged()

	# Run S1-TBX on a separate thread
    def startWorker(self, dir, xmlStepB, xmlStepA):
		# create a new worker instance
		self.start_task()
		workerGUI = StepWorker(dir, xmlStepB, xmlStepA)

		# configure the QgsMessageBar
		messageBar = self.iface.messageBar().createMessage('Executing Sentinel-1 Toolbox ...', )
		cancelButton = QtGui.QPushButton()
		cancelButton.setText('Cancel')
		cancelButton.clicked.connect(workerGUI.killSLOT)
		self.dlg.pushButtSTOP.clicked.connect(workerGUI.killSLOT)
		messageBar.layout().addWidget(cancelButton)
		self.iface.messageBar().pushWidget(messageBar, self.iface.messageBar().INFO)
		self.messageBar = messageBar

		# Start the worker in a new thread
		threadGUI = QThread(self.dlg)
		workerGUI.moveToThread(threadGUI)
		workerGUI.finishSIGNAL.connect(self.workerFinishedSLOT)
		workerGUI.errorSIGNAL.connect(self.workerErrorSLOT)
		workerGUI.infoSIGNAL.connect(self.workerInfoSLOT)
		workerGUI.progressSIGNAL.connect(self.dlg.progressGUI.setValue)

		# Launch
		threadGUI.started.connect(workerGUI.run)
		threadGUI.start()
		self.threadGUI = threadGUI
		self.workerGUI = workerGUI

	# SLOT: Task finished
    def workerFinishedSLOT(self, ret):
		print 'FINISHED:' + str(ret)
		# remove widget from message bar
		self.iface.messageBar().clearWidgets()
		if ret is True:
			# notify the user that finished OK
			self.iface.messageBar().pushMessage('FloodMap Plugin finished [OK]', level=QgsMessageBar.INFO, duration=3)		
			# Clean up the worker and thread
			self.workerGUI.deleteLater()
			self.threadGUI.quit()
			self.threadGUI.wait()
			self.threadGUI.deleteLater()
		else:
			# notify the user that finished ERROR
			self.iface.messageBar().pushMessage('FloodMap Plugin finished [ERROR]', level=QgsMessageBar.CRITICAL, duration=3)			
		# Reset GUI
		self.end_task()

	# SLOT: Task Error
    def workerErrorSLOT(self, e, exception_string):
		print 'ERROR: ' + exception_string
		self.dlg.textBrowser.setText("<b><font color=\"red\">ERROR:</font></b><br/>"+exception_string)
		#QgsMessageLog.logMessage('Worker thread raised an exception:\n'.format(exception_string), level=QgsMessageLog.CRITICAL)
	
	# SLOT: Task info
    def workerInfoSLOT(self, info_string):
		self.dlg.textBrowser.clear()
		self.dlg.textBrowser.append(self.tr("<b><font color=\"blue\">PROCESSING:</font></b><br/>"+info_string))
		# Scroll to the end
		sb = self.dlg.textBrowser.verticalScrollBar()
		sb.setValue(sb.maximum())

	# Geters for steps
    def get_s1_path(self):
		# Get S1TBX exe dir
		s1dir = self.dlg.editS1Path.text()
		if os.path.exists(s1dir):
			return os.path.normpath(s1dir)
		else:
			self.show_error('Please provide a valid Sentinel-1 image after the flood (CONFIG tab)')
			return None
    def get_out_path(self):
		# Get S1TBX exe dir
		outdir = self.dlg.editOutPath.text()
		if os.path.exists(outdir):
			return os.path.normpath(outdir)
		else:
			self.show_error('Please provide a valid output directory for the flood results (CONFIG tab)')
			return None			
    def get_polygon_s1(self):
		# Get Polygon BBOX
		shp_file = self.dlg.editAOI.text()
		if os.path.exists(shp_file):
			shp = Shapefile(shp_file)
			return shp.getBBOX()
		else:
			self.show_error('Please provide a valid Polygon Shapefile')	
			return None
    def get_image_before_s1(self):
		# Get Image Before
		image_before1 = self.dlg.editBefore1.text()
		if os.path.exists(image_before1):
			return os.path.normpath(image_before1)
		else:
			self.show_error('Please provide a valid Sentinel-1 image before the flood')	
			return None
    def get_image_after_s1(self):
		# Get Image After
		image_after1 = self.dlg.editAfter1.text()
		if os.path.exists(image_after1):
			return os.path.normpath(image_after1)
		else:
			self.show_error('Please provide a valid Sentinel-1 image after the flood')
			return None
    def get_image_before_s2(self):
		# Get Image Before
		image_before2 = self.dlg.editBefore2.text()
		if os.path.exists(image_before2):
			return os.path.normpath(image_before2)
		else:
			self.show_error('Please provide a valid TIFF image output from STEP-1 before the flood')	
			return None
    def get_image_after_s2(self):
		# Get Image After
		image_after2 = self.dlg.editAfter2.text()
		if os.path.exists(image_after2):
			return os.path.normpath(image_after2)
		else:
			self.show_error('Please provide a valid TIFF image output from STEP-1 after the flood')
			return None				
    def get_date_before_s2(self):
		return self.dlg.lineEditBefore.text()
    def get_date_after_s2(self):
		return self.dlg.lineEditAfter.text()
    def get_image_rgb_cd(self):
		return self.dlg.editRGB3.text()
		
	# Run STEP-1
    def run_step_1(self):	
		# Gather info for step1
		s1tbx_path=self.get_s1_path()
		output_path=self.get_out_path()
		image_after=self.get_image_after_s1()
		image_before=self.get_image_before_s1()
		bbox=self.get_polygon_s1()
		if (s1tbx_path is None) or (output_path is None) or (image_after is None) or (image_before is None) or (bbox is None):	return #Params check
		
		# Write xml for the step
		xml_step1= self.template_dir+'\Step1.xml'
		step_one = StepOne(xml_step1, image_before, image_after, bbox, output_path)
		step_one.write_xml()
		xmlStepB=output_path.replace('\\', '\\\\')+'\\\\Step1-before.xml'
		xmlStepA=output_path.replace('\\', '\\\\')+'\\\\Step1-after.xml'
	
		# Start worker on a new thread
		self.startWorker(str(s1tbx_path), str(xmlStepB), str(xmlStepA))
	
	# Run STEP-2
    def run_step_2(self):
		# Gather info for step1
		s1tbx_path=self.get_s1_path()
		output_path=self.get_out_path()
		image_after=self.get_image_after_s2()
		image_before=self.get_image_before_s2()
		date_before=self.get_date_before_s2()
		date_after=self.get_date_after_s2()
		if (s1tbx_path is None) or (output_path is None) or (image_after is None) or (image_before is None) or (date_after is None) or (date_before is None):	return #Params check
		
		# Write xml for the step
		xml_step2= self.template_dir+'\Step2.xml'
		step_two = StepTwo(xml_step2, image_before, date_before, image_after, date_after, output_path)
		step_two.write_xml()
		xmlStep=output_path.replace('\\', '\\\\')+'\\\\Step2-RGB.xml'
	
		# Start worker on a new thread (one cmd)
		self.startWorker(str(s1tbx_path), str(xmlStep), str(""))
	
	# Run STEP-3
    def run_step_3(self):
		# Gather info for step1
		s1tbx_path=self.get_s1_path()
		output_path=self.get_out_path()
		image_rgb_cd=self.get_image_rgb_cd()
		if (s1tbx_path is None) or (output_path is None) or (image_rgb_cd is None):	return #Params check
		
		# Write xml for the step
		xml_step3= self.template_dir+'\Step3.xml'
		step_three = StepThree(xml_step3, image_rgb_cd, output_path)
		step_three.write_xml()
		xmlStep=output_path.replace('\\', '\\\\')+'\\\\Step3-Segmentation.xml'
	
		# Start worker on a new thread (one cmd)
		self.startWorker(str(s1tbx_path), str(xmlStep), str(""))

	# noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.
 
        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('rasorFloodMap', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)
        return action

    def initGui(self):
		icon_flood_path = ':/plugins/rasor/rasor_icon_flood.png'	
			
		"""Create new exposure layer"""        	
		self.add_action(
			icon_flood_path,
			text=self.tr(u'Rasor Flood Mapping Plugin'),
			callback=self.run,
			parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Rasor Flood Mapping Plugin'),
                action)
            self.iface.removeToolBarIcon(action)

    def run(self):	
	# show the dialog
	self.dlg.show()

	# Run the dialog event loop
	result = self.dlg.exec_()		