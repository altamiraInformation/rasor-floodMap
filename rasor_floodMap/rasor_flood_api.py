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

from qgis.gui import QgsMessageBar
from qgis.core import *
from PyQt4 import QtCore, QtGui

from osgeo import gdal
import os, subprocess, traceback, tempfile, contextlib, time, signal, ctypes, array

# Local imports
from rasor_gtiff_api import GeoTiff
from rasor_poly_api import Shapefile

class StepWorker(QtCore.QObject):
    '''Worker in order to run time-consuming tasks of S1-TBX'''
    def __init__(self, tbx, subcmd, tbx_dir, xmlFileB, xmlFileA, outdir):
		QtCore.QObject.__init__(self)
		self.tbx_dir = tbx_dir
		self.type = tbx
		self.xmlFileB = xmlFileB
		self.xmlFileA = xmlFileA
		self.killed = False
		self.pro = None
		self.ret = True
		self.subcmd = subcmd
		self.outdir = outdir
	
	# Build CMD - Step 1,2
    def build_cmd(self, xmlFile):
		if self.type == 's1tbx':	return self.build_cmd_s1tbx(xmlFile)
		else:						return self.build_cmd_otbx_s3(xmlFile)

	# Build S1-CMD - Step 1,2
    def build_cmd_s1tbx(self, xmlFile):
		args = [
				self.tbx_dir.replace(r'\\', r'\\\\')+"\\gpt.exe",
				xmlFile		
		]
		return args

	# Build OTB-CMD - Step 3
    def build_cmd_otbx_s3(self, xmlFile):
		args = [
				self.tbx_dir.replace(r'\\', r'\\\\')+"\\otbApplicationLauncherCommandLine.exe",
				self.subcmd,
				"-inxml",
				xmlFile		
		]
		return args

	# Execute
    def execute(self, args, mod_env, tmpdir, info):
		## Show user start info
		self.infoSIGNAL.emit(info)
		## Execute command
		print args
		pro = subprocess.Popen(args,								 
							 bufsize=0,
							 universal_newlines=True,
							 env=mod_env,
							 cwd=tmpdir,
							 stdin=subprocess.PIPE,
							 stdout=subprocess.PIPE,
							 stderr=subprocess.STDOUT)
		self.pro = pro
		
		## Standard S1TBX Output Loop	
		if self.type == 's1tbx':
			line = ""
			#last_per = 0
			while pro.poll() is None:
				char = pro.stdout.read(1) 
				line=line+char
				# Communicate with GUI
				self.infoSIGNAL.emit(info+'<br>'+line)	
				time.sleep(0.1)
		## Standard OTBX Output Loop	
		else:
			line = ""
			while pro.poll() is None:
				line = pro.stdout.readline()
				# Percent
				per=self.get_percent(line)
				if per:	self.progressSIGNAL.emit(per)
				# Info
				self.infoSIGNAL.emit(info+'<br>'+line)
    
    # Get percent
    def get_percent(self, msg):		
		return None

	# Run S1-CMD
    def run(self):
        try:
			# Work in a tempdir
			tmpdir=tempfile.gettempdir()
			os.chdir(tmpdir)
						
			# Environement variable neeeded for S1-toolbox (clean environement)
			mod_env=os.environ.copy()
			
			if self.type == 's1tbx':	
				mod_env["S1TBX_HOME"] = "\"" + self.tbx_dir.replace(r'\\', r'\\\\') + "\""
			else:		
				lib_dir=os.path.abspath(os.path.join(self.tbx_dir, os.pardir))+"\\lib\\otb\\applications"				
				mod_env["ITK_AUTOLOAD_PATH"] = lib_dir.replace(r'\\', r'\\\\')
				print "\"" + lib_dir.replace(r'\\', r'\\\\') + "\""

			# Build commands (1 or 2 xml files)
			args=self.build_cmd(self.xmlFileB)
			self.execute(args, mod_env, tmpdir, 'Executing '+self.type+' ... ')	

			if self.xmlFileA: 
				args2=self.build_cmd(self.xmlFileA)
				self.execute(args2, mod_env, tmpdir, 'Subsetting + Orthorectification ... ')

			if self.subcmd == 'KMeansClassification':
				geo = GeoTiff(self.outdir+'/RGB-Mean-Kmeans.tif') 
				geo.polygonize(self.outdir+'/RGB-Class.shp')
				shp=Shapefile(self.outdir+'/RGB-Class.shp')

        except Exception, e:  
			# Inform the user in the console
            print 'ERROR: '+str(e)
            # forward the exception upstream
            self.errorSIGNAL.emit(e, traceback.format_exc())
            self.ret = False
		
		# Finished
        self.finishSIGNAL.emit(self.ret)
		
	# Slot definition (Abort)
    def killSLOT(self):
		self.killed = True
		self.pro.kill()
		self.ret = False

	# Signals definition
    finishSIGNAL = QtCore.pyqtSignal(object)
    errorSIGNAL = QtCore.pyqtSignal(Exception, basestring)
    progressSIGNAL = QtCore.pyqtSignal(float)	
    infoSIGNAL = QtCore.pyqtSignal(basestring)