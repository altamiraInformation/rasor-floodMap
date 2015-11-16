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

import xml.etree.ElementTree as ET
from datetime import datetime, date, time

class Manifest():
    '''Worker in order to run time-consuming tasks of S1-TBX'''
    def __init__(self, manifest_path):
		self.manifest_path = manifest_path

    def parseXML(self):
        try:
        	startTime = ""
        	# Read file and replace ':'
        	with open (self.manifest_path, "r") as myfile:
        	    data=myfile.read().replace(':', '')
        	
        	# Read XML from string
        	root = ET.fromstring(data)
        	metadata = root.find('metadataSection')

        	# Parse XML
        	for metadataObj in metadata.findall('metadataObject'):
        		if metadataObj.attrib['ID'] == 'acquisitionPeriod':
        			parts=metadataObj[0][0][0][0].text.split('T')
        			dt = datetime.strptime(parts[0], "%Y-%m-%d")
        			startTime = dt.strftime('%d%b%Y')    

        	return startTime
        except Exception, e:  
        	# Inform the user in the console
        	print 'ERROR: '+str(e)
        	return None			
        return True
