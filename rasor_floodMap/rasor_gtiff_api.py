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

from PIL import Image
from PIL.ExifTags import TAGS
from osgeo import gdal
from osgeo import ogr
import xml.etree.ElementTree as ET
import os, osr

class GeoTiff():
	'''Worker in order to run time-consuming tasks of S1-TBX'''
	def __init__(self, gtiff_path):
		self.gtiff_path = gtiff_path
		self.PRIVATE_BEAM_TIFF_TAG_NUMBER = 65000
		
	def getDATE(self):
		try:
			# Get geotiff S1TBX private header tag
			img = Image.open(self.gtiff_path)
			xml = img.tag.get(self.PRIVATE_BEAM_TIFF_TAG_NUMBER)
			# Parse XML string
			tree = ET.fromstring(xml)
			elem=tree.find("./Production/PRODUCT_SCENE_RASTER_START_TIME")
			# Convert date
			timestamp=elem.text
			(date,hour) = timestamp.split(' ')
			(D,month,Y) = date.split('-')			
			M=month.title()
			return D+M+Y
		except Exception, e:  
			# Inform the user in the console
			print 'ERROR: '+str(e)
			return None
		return True

	def polygonize(self, out_shp):
		# Input GTiff
		src_ds = gdal.Open(self.gtiff_path)
		band = src_ds.GetRasterBand(1)
		bandArray = band.ReadAsArray()
		# Output SHP file
		drv = ogr.GetDriverByName("ESRI Shapefile")
		if os.path.exists(out_shp):
			drv.DeleteDataSource(out_shp)
		# Projection
		dst_ds = drv.CreateDataSource(out_shp)
		srs_in = osr.SpatialReference()
		srs_in.ImportFromWkt(src_ds.GetProjectionRef())
		# Output Layer
		outDatasource = drv.CreateDataSource(out_shp)
		outLayer = outDatasource.CreateLayer("class_polygons", srs=srs_in)
		newField = ogr.FieldDefn('CLASS', ogr.OFTInteger)
		outLayer.CreateField(newField)
		gdal.Polygonize(band, None, outLayer, 0, [], callback=None)		