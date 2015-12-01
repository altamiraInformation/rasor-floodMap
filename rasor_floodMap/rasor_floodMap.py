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
from rasor_step_api import StepFour
from rasor_poly_api import Shapefile
from rasor_gtiff_api import GeoTiff
from rasor_manifest_api import Manifest

# Initialize Qt resources from file resources.py
import resources_rc

# Import the code for the dialog
from rasor_floodMap_dialog import rasorDialog

# Imports (packages)
import os, json, tempfile, subprocess, threading, locale
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
	self.dlg.editS1Path.clear()
	self.dlg.editS1Path.setReadOnly(1)
	self.dlg.connect(self.dlg.buttS1Path, SIGNAL("clicked()"), self.buttS1PathCLICK)
	self.dlg.editOrfeoPath.clear()
	self.dlg.editOrfeoPath.setReadOnly(1)
	self.dlg.connect(self.dlg.buttOrfeoPath, SIGNAL("clicked()"), self.buttOrfeoPathCLICK)	
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
	self.dlg.editAfter2.clear()
	self.dlg.editAfter2.setReadOnly(1)	
	self.dlg.editRGB3.clear()
	self.dlg.editRGB3.setReadOnly(1)
	self.dlg.editRGB4.clear()
	self.dlg.editRGB4.setReadOnly(1)	
	self.dlg.editAOI.clear()
	self.dlg.editAOI.setReadOnly(1)
	self.dlg.connect(self.dlg.buttAOI, SIGNAL("clicked()"), self.buttAfterAOI)
	self.dlg.connect(self.dlg.pushButtLOAD1, SIGNAL("clicked()"), self.loadStep1QGIS)
	self.dlg.connect(self.dlg.pushButtLOAD2, SIGNAL("clicked()"), self.loadStep2QGIS)
	self.dlg.connect(self.dlg.pushButtLOAD3, SIGNAL("clicked()"), self.loadStep3QGIS)
	self.dlg.connect(self.dlg.pushButtLOAD4, SIGNAL("clicked()"), self.loadStep4QGIS)
	# Tab3 logic
	self.dlg.checkBoxS3.stateChanged.connect(self.advEnableS3)
	self.dlg.sliderMeanFiltRadius.valueChanged.connect(self.dlg.lcdNumberRadius.display)
	self.dlg.sliderMeanFiltRange.valueChanged.connect(self.dlg.lcdNumberRange.display)
	# Tab4 logic
	self.dlg.checkBoxS4.stateChanged.connect(self.advEnableS4)
	self.dlg.sliderKMeans.valueChanged.connect(self.dlg.lcdNumberKMeans.display)

	# Load settings
	s = QSettings()
	s1tbx_path = s.value("rasor_floodMap/s1tbx_path")
	work_path = s.value("rasor_floodMap/work_path")
	shp_path = s.value("rasor_floodMap/shp_path")
	orfeo_path = s.value("rasor_floodMap/orfeo_path")
	if shp_path: self.dlg.editAOI.setText(shp_path)
	if work_path: self.dlg.editOutPath.setText(work_path)
	if s1tbx_path: self.dlg.editS1Path.setText(s1tbx_path)
	if orfeo_path: self.dlg.editOrfeoPath.setText(orfeo_path)

	# ADVANCED functions
    def advEnableS3(self, state=QtCore.Qt.Checked):
		self.dlg.sliderMeanFiltRange.setEnabled(state)	
		self.dlg.sliderMeanFiltRadius.setEnabled(state)
    def advEnableS4(self, state=QtCore.Qt.Checked):
		self.dlg.sliderKMeans.setEnabled(state)
	# CLICKED functions
    def buttS1PathCLICK(self):
	    dire = self.tr(QFileDialog.getExistingDirectory(self.dlg, "Select S1-TBX bin Directory", self.getRootDIR()))
	    if dire:
			file_path = dire + "\\gpt.exe"
			if os.path.exists(file_path):
				self.dlg.editS1Path.setText(dire)
				s = QSettings()
				s.setValue("rasor_floodMap/s1tbx_path", dire)
			else:
				error_message = QtGui.QErrorMessage(self.dlg)
				error_message.setWindowTitle("Wrong directory")
				error_message.showMessage("Impossible to find the gpt.exe executable in this directory. Please provide another one")
    def buttOrfeoPathCLICK(self):
	    dire = self.tr(QFileDialog.getExistingDirectory(self.dlg, "Select Orfeo Toolbox bin Directory", self.getRootDIR()))
	    if dire:
			file_path = dire + "\\otbApplicationLauncherCommandLine.exe"
			if os.path.exists(file_path):
				self.dlg.editOrfeoPath.setText(dire)
				s = QSettings()
				s.setValue("rasor_floodMap/orfeo_path", dire)
			else:
				error_message = QtGui.QErrorMessage(self.dlg)
				error_message.setWindowTitle("Wrong directory")
				error_message.showMessage("Impossible to find the otbApplicationLauncherCommandLine.exe executable in this directory. Please provide another one")
    def buttOutPathCLICK(self):
	    dire = self.tr(QFileDialog.getExistingDirectory(self.dlg, "Select OUTPUT Directory", self.getWDIR()))	    
	    if dire:
			self.dlg.editOutPath.setText(dire)
			s = QSettings()
			s.setValue("rasor_floodMap/work_path", dire)	
    def buttBeforeCLICK1(self):
	    file_path = self.tr(QFileDialog.getOpenFileName(self.dlg, "Select S1 image manifest file_path", self.getWDIR(), "S1 manifest files (manifest.safe)"))
	    if file_path:
			self.dlg.editBefore1.setText(file_path)
			maniReader=Manifest(file_path)
			dateBefore=maniReader.parseXML()			
			self.dlg.lineEditBefore.setText(dateBefore)	
			self.dlg.lineEditBefore2.setText(dateBefore)	
    def buttAfterCLICK1(self):
	    file_path = self.tr(QFileDialog.getOpenFileName(self.dlg, "Select S1 image manifest file_path", self.getWDIR(), "S1 manifest files (manifest.safe)"))
	    if file_path:
			self.dlg.editAfter1.setText(file_path)
			maniReader=Manifest(file_path)
			dateAfter=maniReader.parseXML()
			self.dlg.lineEditAfter.setText(dateAfter)
			self.dlg.lineEditAfter2.setText(dateAfter)    
    def buttAfterAOI(self):
	    shp_file = self.tr(QFileDialog.getOpenFileName(self.dlg, "Select Area of Interest SHP", self.getWDIR(), "ESRI Shapefile (*.shp)"))	    
	    if shp_file: 
			self.dlg.editAOI.setText(shp_file)
			s = QSettings()
			s.setValue("rasor_floodMap/shp_path", shp_file)
    def loadStep1QGIS(self):
		file1=self.get_out_path()+"/STEP1/Reference-Subset-TC.tif"
		file2=self.get_out_path()+"/STEP1/Flood-Subset-TC.tif"
		self.unload_layer("Reference-Subset-TC")
		self.load_raster_QGIS(file1)
		self.unload_layer("Flood-Subset-TC")
		self.load_raster_QGIS(file2)
    def loadStep2QGIS(self):
		file1=self.get_out_path()+"/STEP2/RGB.tif"
		self.unload_layer("RGB")
		self.load_raster_QGIS(file1)
    def loadStep3QGIS(self):
		file1=self.get_out_path()+"/STEP3/RGB-Mean.tif"
		self.unload_layer("RGB-Mean")
		self.load_raster_QGIS(file1)
    def loadStep4QGIS(self):
		self.unload_layer("RGB-Class")
		file1=self.get_out_path()+"/STEP4/RGB-Class.shp"
		self.load_shp_QGIS(file1)

	# Unload layer from QGIS
    def unload_layer(self, layerName):
		for layer in QgsMapLayerRegistry.instance().mapLayers().values():
			if layer.name() == layerName: 
				print "Unloading: " + layer.name()
				QgsMapLayerRegistry.instance().removeMapLayer(layer.id()) # just in case

	# Read raster and load it to QGIS
    def load_raster_QGIS(self, fileName):
		if os.path.exists(fileName):
			fileInfo = QFileInfo(fileName)
			baseName = fileInfo.baseName()			
			rlayer = QgsRasterLayer(fileName, baseName)			
			if not rlayer.isValid():
				print "Unable to load raster layer: "+fileName
			else:
				# Grayscale SIGMA
				if rlayer.bandCount() == 1:					
					fcn = QgsColorRampShader()
					fcn.setColorRampType(QgsColorRampShader.INTERPOLATED)
					lst = [QgsColorRampShader.ColorRampItem(0.0, QColor(0,0,0)), QgsColorRampShader.ColorRampItem(1.0, QColor(255,255,255))]
					fcn.setColorRampItemList(lst)
					shader = QgsRasterShader()
					shader.setRasterShaderFunction(fcn)
					renderer = QgsSingleBandPseudoColorRenderer(rlayer.dataProvider(), 1, shader)
					rlayer.setRenderer(renderer)
				# Add layer				
				QgsMapLayerRegistry.instance().addMapLayer(rlayer)
				qgis.utils.iface.zoomToActiveLayer()				
		else:
			self.show_error('The file_path '+fileName+' does not exist. Please check your working directory.')

	# Read Shapefile and load it to QGIS
    def load_shp_QGIS(self, fileName):
		if os.path.exists(fileName):
			fileInfo = QFileInfo(fileName)
			baseName = fileInfo.baseName()
			slayer = QgsVectorLayer(fileName, baseName, "ogr")	
			if not slayer.isValid():
				print "Unable to load shp layer: "+fileName
			else:
				# Get distinct attributes
				attlist=slayer.uniqueValues(0)
				Natt=len(attlist)
				minat=float(min(attlist))
				maxat=float(max(attlist))
				thr=(minat+maxat)/2
				categories = []
				fixed=20
				alpha=170
				for att in attlist:					
					# Color decision										
					if   att == maxat:		color=QColor(fixed   , fixed,    fixed, alpha) # = -> dark contour probably
					elif att == minat:		color=QColor(fixed*2 , fixed*2,  fixed, alpha) # = -> light contour probably
					else:
						variable=int((float(abs(att+1))/Natt)*255)
						color=QColor(0, variable, 255, alpha) # < -> Blue scale

					# Symbol
					symbol = QgsSymbolV2.defaultSymbol(slayer.geometryType())
					symbol.setColor(color)
					category = QgsRendererCategoryV2(att, symbol, str(att))
					categories.append(category)

				# Render to QGIS
				myRenderer = QgsCategorizedSymbolRendererV2('CLASS', categories)
				slayer.setRendererV2(myRenderer)
				QgsMapLayerRegistry.instance().addMapLayer(slayer)
		else:
			self.show_error('The file_path '+fileName+' does not exist. Please check your working directory.')

	# Run function
    def buttRUNCLICK(self):
	    index=self.dlg.tabSteps.currentIndex()
	    self.dlg.textBrowser.clear()
	    if index == 1:
			print 'Running Step 1: Calibration -> Orthorectification -> Speckle filtering'
			self.unload_layer("Reference-Subset-TC")
			self.unload_layer("Flood-Subset-TC")
			self.run_step_1()
	    if index == 2:
			print 'Running Step 2: RGB composition -> Change detection'
			self.unload_layer("RGB")
			self.run_step_2()
	    if index == 3:
			print 'Running Step 3: Segmentation'
			self.unload_layer("RGB-Mean")
			self.run_step_3()
	    if index == 4:
			print 'Running Step 4: Classification'	
			self.unload_layer("RGB-Class")
			self.run_step_4()

	# Get working directory
    def getWDIR(self):
		wdir = self.dlg.editOutPath.text()
		if not wdir:
			wdir = expanduser("~")
		return wdir	
    def getRootDIR(self):
		return os.path.abspath(os.sep)
		
	# Called on tab changed event
    def tabChanged(self):
		# Check if config is filled
		output_path=self.get_out_path()
		index=self.dlg.tabSteps.currentIndex()
		if index and not output_path:
			self.dlg.tabSteps.setCurrentIndex(0)
			return
		# Show info	
		self.dlg.textBrowser.clear()
		self.dlg.pushButtRUN.setText("RUN\nSTEP")
		self.dlg.pushButtRUN.setVisible(True)
		if index == 0:
			self.dlg.pushButtRUN.setVisible(False)
			self.dlg.textBrowser.setText("<b><font color=\"green\">CONFIG:</font></b><br/><br/><b><font color=\"blue\">S1TBX_DIR:</font></b> Sentinel-1 Toolbox (S1TBX) executables <b>bin</b> directory. (http://step.esa.int/main/toolboxes/snap/)<br/><b><font color=\"blue\">ORFEO_DIR:</font></b> Orfeo Toolbox (OTB) executables <b>bin</b> directory. (https://www.orfeo-toolbox.org/download/)<br/><b><font color=\"blue\">WORKSPACE:</font></b> Output directory where files will be stored.<br/><b><font color=\"blue\">AOI (Area of Interest):</font></b> One shapefile with an area of interest (polygon) that will be used to make a subset the results.")		
		if index == 1:
			self.dlg.textBrowser.setText("<b><font color=\"green\">INPUT:</font></b><br/>Two <b>manifest</b> files from Sentinel-1 Images, one before the flood event (Reference) and one after (Flood).<br/><br/><b><font color=\"green\">OUTPUT:</font></b><br/>The two images calibrated, orthorectified and subsetted by the polygon bounding box specified in the CONFIG tab in GeoTIFF format.")
		if index == 2:
			self.dlg.editBefore2.setText(output_path+'/STEP1/Reference-Subset.tif')
			self.dlg.editAfter2.setText(output_path+'/STEP1/Flood-Subset.tif')
			self.dlg.textBrowser.setText("<b><font color=\"green\">INPUT:</font></b><br/>Two <b>Geotiff</b> images alredy processed in the previous step with their associated dates of acquisition.<br/><br/><b><font color=\"green\">OUTPUT:</font></b><br/>One <b>GeoTiff</b> RGB composition ready for change detection.")
		if index == 3:
			self.dlg.editRGB3.setText(output_path+'/STEP2/RGB.tif')
			self.dlg.textBrowser.setText("<b><font color=\"green\">INPUT:</font></b><br/>One RGB <b>Geotiff</b> image with the change detection information from the previous step <br/><br/><b><font color=\"green\">OUTPUT:</font></b><br/>One RGB <b>Geotiff</b> with the segmentation output")
		if index == 4:
			self.dlg.editRGB4.setText(output_path+'/STEP3/RGB-Mean.tif')
			self.dlg.textBrowser.setText("<b><font color=\"green\">INPUT:</font></b><br/>One RGB <b>Geotiff</b> image for the classification<br/><br/><b><font color=\"green\">OUTPUT:</font></b><br/>One <b>Shapefile</b> with the classes")

    # Called on error
    def show_error(self, errmsg):
		self.dlg.textBrowser.setText("<b><font color=\"red\">ERROR:</font></b><br/>"+errmsg)	

	# Called on batch task start
    def start_task(self):
		# Start progress bar
		self.dlg.progressGUI.setMinimum(0)
		self.dlg.progressGUI.setMaximum(0)
		self.dlg.progressGUI.setValue(0)
		self.dlg.progressGUI.setTextVisible(True)

	# Called on batch task end
    def end_task(self):
		# Stop progress bar
		self.dlg.progressGUI.setMinimum(0)
		self.dlg.progressGUI.setMaximum(100)
		self.dlg.progressGUI.setValue(0)
		self.dlg.progressGUI.setTextVisible(False)
		# Clear text
		self.tabChanged()

	# Run S1-TBX on a separate thread
    def startWorker(self, tbx, subcmd, dire, xmlStepB, xmlStepA, outdir):
		# create a new worker instance
		self.start_task()
		workerGUI = StepWorker(tbx, subcmd, dire, xmlStepB, xmlStepA, outdir)

		# configure the QgsMessageBar
		messageBar = self.iface.messageBar().createMessage('Working ...', )
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
		#workerGUI.progressSIGNAL.connect(self.dlg.progressGUI.setValue)

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
			return None
    def get_orfeo_path(self):
		# Get S1TBX exe dir
		otbdir = self.dlg.editOrfeoPath.text()
		if os.path.exists(otbdir):
			return os.path.normpath(otbdir)
		else:
			return None			
    def get_out_path(self):
		# Get S1TBX exe dir
		outdir = self.dlg.editOutPath.text()
		if os.path.exists(outdir):
			return os.path.normpath(outdir)
		else:
			return None			
    def get_polygon_bbox(self):
		# Get Polygon BBOX
		shp_file = self.dlg.editAOI.text()
		if os.path.exists(shp_file):
			shp = Shapefile(shp_file)
			return shp.getBBOX(False)
		else:
			return None
    def get_polygon_bbox_big(self):
		# Get Polygon BBOX
		shp_file = self.dlg.editAOI.text()
		if os.path.exists(shp_file):
			shp = Shapefile(shp_file)
			return shp.getBBOX(True)
		else:
			return None			
    def get_image_before_s1(self):
		# Get Image Before
		image_before1 = self.dlg.editBefore1.text()
		if os.path.exists(image_before1):
			return os.path.normpath(image_before1)
		else:
			return None
    def get_image_after_s1(self):
		# Get Image After
		image_after1 = self.dlg.editAfter1.text()
		if os.path.exists(image_after1):
			return os.path.normpath(image_after1)
		else:
			return None
    def get_image_before_s2(self):
		# Get Image Before
		image_before2 = self.dlg.editBefore2.text()
		if os.path.exists(image_before2):
			return os.path.normpath(image_before2)
		else:
			return None
    def get_image_after_s2(self):
		# Get Image After
		image_after2 = self.dlg.editAfter2.text()
		if os.path.exists(image_after2):
			return os.path.normpath(image_after2)
		else:
			return None				
    def get_date_before_s1(self):
		return self.dlg.lineEditBefore.text()
    def get_date_after_s1(self):
		return self.dlg.lineEditAfter.text()
    def get_image_rgb3(self):
		return self.dlg.editRGB3.text()
    def get_image_rgb4(self):
		return self.dlg.editRGB4.text()
    def get_nclass(self):
		return self.dlg.sliderKMeans.value()
    def get_filtradius(self):
		return self.dlg.sliderMeanFiltRadius.value()
    def get_filtrange(self):
		return self.dlg.sliderMeanFiltRange.value()
				
	# Run STEP-1
    def run_step_1(self):	
		# Gather info for step1
		s1tbx_path=self.get_s1_path()
		output_path=self.get_out_path()
		image_after=self.get_image_after_s1()
		image_before=self.get_image_before_s1()
		bbox=self.get_polygon_bbox()
		bbox_big=self.get_polygon_bbox_big()
		date_before=self.get_date_before_s1()
		date_after=self.get_date_after_s1()

		# Parameters check
		if (s1tbx_path is None) or (output_path is None) or (bbox is None) or (bbox_big is None):
			self.show_error('Please fill in the parameters in the CONFIG tab')
			return #Params fail

		if (date_after is None) or (date_before is None) or (image_after is None) or (image_before is None):
			self.show_error('Please select two valid Sentinel-1 manifest files')
			return # Dates fail

		if (bbox == -1):
			self.show_error('Please provide a smaller polygon (shapefile in the CONF tab)')
			return # Area fail
		
		# Create folder
		outdir=output_path.replace('\\', '\\\\')+"/STEP1"
		if not os.path.exists(outdir):
			os.makedirs(outdir)

		# Write xml for the step
		xml_step1a_file = self.template_dir+'/Step1a.xml'
		xml_step1b_file = self.template_dir+'/Step1b.xml'
		step_one = StepOne(xml_step1a_file, xml_step1b_file, image_before, image_after, bbox_big, bbox, outdir, date_before, date_after)
		step_one.write_xml()
		xmlStepA=outdir+'/Step1a.xml'
		xmlStepB=outdir+'/Step1b.xml'
		
		# Start worker on a new thread
		self.startWorker('s1tbx', '', str(s1tbx_path), str(xmlStepA), str(xmlStepB), outdir)
	
	# Run STEP-2
    def run_step_2(self):
		# Gather info for step2
		s1tbx_path=self.get_s1_path()
		output_path=self.get_out_path()
		image_after=self.get_image_after_s2()
		image_before=self.get_image_before_s2()
		date_before=self.get_date_before_s1()
		date_after=self.get_date_after_s1()

		# Parameters check
		if (s1tbx_path is None) or (output_path is None) or (s1tbx_path == "") or (output_path == ""):
			self.show_error('Please fill in the parameters in the CONFIG tab')
			return #Params fail

		if (date_after is None) or (date_before is None) or (date_after == "") or (date_before == ""):
			self.show_error('Please select two valid Sentinel-1 manifest files in the Step 1 tab')
			return # Dates fail			

		if (image_after is None) or (image_before is None) or (image_after == "") or (image_before == ""):
			self.show_error('Please select two valid geotiff files (Reference-Subset.tif/Flood-Subset.tif)')
			return # Images fail	
		
		# Create folder
		outdir=output_path.replace('\\', '\\\\')+"/STEP2"
		if not os.path.exists(outdir):
			os.makedirs(outdir)

		# Write xml for the step
		xml_step2= self.template_dir+'\Step2.xml'
		step_two = StepTwo(xml_step2, image_before, date_before, image_after, date_after, outdir)
		step_two.write_xml()
		xmlStep=outdir+'/Step2.xml'
	
		# Start worker on a new thread (one cmd)
		self.startWorker('s1tbx', '', str(s1tbx_path), str(xmlStep), str(""), outdir)
	
	# Run STEP-3
    def run_step_3(self):
		# Gather info for step3
		orfeo_path=self.get_orfeo_path()
		output_path=self.get_out_path()
		image_rgb_cd=self.get_image_rgb3()
		fradius=self.get_filtradius()
		frange=self.get_filtrange()
		if (orfeo_path is None) or (output_path is None) or (image_rgb_cd is None):	return #Params check
		
		# Create folder
		outdir=output_path.replace('\\', '\\\\')+"/STEP3"
		if not os.path.exists(outdir):
			os.makedirs(outdir)

		# Write xml for the step
		xml_step3= self.template_dir+'\Step3.xml'
		step_three = StepThree(xml_step3, image_rgb_cd, outdir, fradius, frange)
		step_three.write_xml()
		xmlStep=outdir+'/Step3.xml'
	
		# Start worker on a new thread (one cmd)
		self.startWorker('otbx', 'MeanShiftSmoothing', str(orfeo_path), str(xmlStep), str(""), outdir)

	# Run STEP-4
    def run_step_4(self):
		# Gather info for step3
		orfeo_path=self.get_orfeo_path()
		output_path=self.get_out_path()
		image_rgb_class=self.get_image_rgb4()
		classes=self.get_nclass()
		if (orfeo_path is None) or (output_path is None) or (image_rgb_class is None):	return #Params check
		
		# Create folder
		outdir=output_path.replace('\\', '\\\\')+"/STEP4"
		if not os.path.exists(outdir):
			os.makedirs(outdir)

		# Write xml for the step
		xml_step4= self.template_dir+'\Step4.xml'
		step_four = StepFour(xml_step4, image_rgb_class, outdir, classes)
		step_four.write_xml()
		xmlStep=outdir+'/Step4.xml'
	
		# Start worker on a new thread (one cmd)
		self.startWorker('otbx', 'KMeansClassification', str(orfeo_path), str(xmlStep), str(""), outdir)
	
	# noinspection PyMethodMayBeStatic
    def tr(self, message):
        """
        Get the translation for a string using Qt translation API.
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