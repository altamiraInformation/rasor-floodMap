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

class StepWorker(QtCore.QObject):
    '''Worker in order to run time-consuming tasks of S1-TBX'''
    def __init__(self, s1dir, xmlFileB, xmlFileA):
		QtCore.QObject.__init__(self)
		self.s1dir = s1dir
		self.xmlFileB = xmlFileB
		self.xmlFileA = xmlFileA
		self.killed = False
		self.pro = None
		self.ret = True
	
	# Build S1-CMD
    def build_cmd_old_s1tbx(self, xmlFile):
		args = [
				self.s1dir.replace(r'\\', r'\\\\')+"\\jre\\bin\\java.exe",
				"-Xms512M",
				"-Xmx2048M",
				"-Xverify:none",
				"-XX:+AggressiveOpts",
				"-XX:+UseFastAccessorMethods",
				"-XX:+UseParallelGC",
				"-XX:+UseNUMA",
				"-XX:+UseLoopPredicate",
				"-Dceres.context=s1tbx",
				"-Ds1tbx.mainClass=org.esa.beam.framework.gpf.main.GPT",
				"-Ds1tbx.home="+self.s1dir.replace(r'\\', r'\\\\'),
				"-Ds1tbx.debug=false",
				"-Ds1tbx.consoleLog=false",
				"-Ds1tbx.logLevel=WARNING",
				"-Dncsa.hdf.hdflib.HDFLibrary.hdflib="+self.s1dir.replace(r'\\', r'\\\\')+"\\jhdf.dll",
				"-Dncsa.hdf.hdf5lib.H5.hdf5lib="+self.s1dir.replace(r'\\', r'\\\\')+"\\jhdf5.dll",
				"-jar",
				self.s1dir.replace(r'\\', r'\\\\')+"\\bin\\snap-launcher.jar",
				xmlFile		
		]
		return args
	
	# Build S1-CMD
    def build_cmd(self, xmlFile):
		args = [
				self.s1dir.replace(r'\\', r'\\\\')+"\\gpt.exe",
				xmlFile		
		]
		return args

	# Execute
    def execute(self, args, mod_env, tmpdir, info):
		## Show user start info
		self.infoSIGNAL.emit(info)
		## Execute command
		pro = subprocess.Popen(args,								 
							 bufsize=0,
							 universal_newlines=True,
							 env=mod_env,
							 cwd=tmpdir,
							 stdin=subprocess.PIPE,
							 stdout=subprocess.PIPE,
							 stderr=subprocess.STDOUT)
		self.pro = pro
		## Standard Output Loop	
		line = ""
		#last_per = 0
		while pro.poll() is None:
			char = pro.stdout.read(1) 
			line=line+char
			#per=self.get_percent(line)
			#if per < last_per: line = line+'<br>'
			#last_per=per
			# Communicate with GUI
			self.infoSIGNAL.emit(info+'<br>'+line)			
			#if per:	self.progressSIGNAL.emit(per)			
			time.sleep(0.15)
		print line

	# Run S1-CMD
    def run(self):
        try:
			# Work in a tempdir
			tmpdir=tempfile.gettempdir()
			os.chdir(tmpdir)
						
			# Environement variable neeeded for S1-toolbox (clean environement)
			mod_env=os.environ.copy()
			mod_env["S1TBX_HOME"] = "\"" + self.s1dir.replace(r'\\', r'\\\\') + "\""

			# Build commands (1 or 2 xml files)
			args=self.build_cmd(self.xmlFileB)
			self.execute(args, mod_env, tmpdir, 'Working ... ')	
			#self.progressSIGNAL.emit(0)
			if self.xmlFileA: 
				args2=self.build_cmd(self.xmlFileA)
				self.execute(args2, mod_env, tmpdir, 'Working on the second image ... ')

        except Exception, e:  
			# Inform the user in the console
            print 'ERROR: '+str(e)
            # forward the exception upstream
            self.errorSIGNAL.emit(e, traceback.format_exc())
            self.ret = False
		
		# Finished
        self.finishSIGNAL.emit(self.ret)

	# Lousy progress definition
    def get_percent(self, msg):
		per=["10%","20%","30%","40%","50%","60%","70%","80%","90%","100%"]
		tot=array.array('i',(0 for i in range(0,10)))	
		i=0
		while i < 10:
			tot[i]=msg.count(per[i])
			i=i+1
		# magic
		return (sum(tot)*10)%100
		
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