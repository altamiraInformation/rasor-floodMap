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
        self.footPrint = ''
        self.wkt = ''
        self.startTime = ''

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
                    self.startTime = dt.strftime('%d%b%Y')
                    print 'StartTime: '+self.startTime
                if metadataObj.attrib['ID'] == 'measurementFrameSet':
                    self.footPrint=metadataObj[0][0][0][0][0][0].text
                    print 'Footprint: '+self.footPrint
        except Exception, e:  
            # Inform the user in the console
            print 'ERROR: '+str(e)
            return False			
        return True

    def getTime(self):
        return self.startTime

    def getFootprint(self):
        coord=self.footPrint.split(' ')
        first=''
        # xy and replace ','
        for co in coord:            
            c=co.split(',')
            self.wkt=self.wkt+c[1]+' '+c[0]+', ' 
            if first == '':
                first = self.wkt                

        # Add first point (close polygon)
        self.wkt+=first
        return self.wkt[:-2]