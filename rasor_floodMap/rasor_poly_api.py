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

from osgeo import ogr
import numpy as np
import osr

class Shapefile():
    '''Polygon utilites'''
    def __init__(self, shp_path):
		self.shpFile = shp_path

    def getAreaBBOX(self, env, barda):
		## BBox
		minX = float(env[0])-barda
		minY = float(env[2])-barda
		maxX = float(env[1])+barda
		maxY = float(env[3])+barda
		print "minX: %f, minY: %f, maxX: %f, maxY: %f" %(minX,minY,maxX,maxY)
		
		## To UTM
		inEPSG = 4326 ## Latlong
		outEPSG = 3857 ## Web mercator
		inSpatialRef = osr.SpatialReference()
		inSpatialRef.ImportFromEPSG(inEPSG)
		outSpatialRef = osr.SpatialReference()
		outSpatialRef.ImportFromEPSG(outEPSG)		
		coordTransform = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)
		
		# transform point
		pointMax = ogr.Geometry(ogr.wkbPoint)
		pointMin = ogr.Geometry(ogr.wkbPoint)
		pointMax.AddPoint(maxX,maxY)
		pointMin.AddPoint(minX,minY)
		pointMax.Transform(coordTransform)
		pointMin.Transform(coordTransform)
		area_m2 = ((pointMax.GetX()-pointMin.GetX())*(pointMax.GetY()-pointMin.GetY()))/(1000.0*1000.0)
		print "TOTAL_AREA (m2): %f" % area_m2
		
		return area_m2

    def getBBOX(self, big):
        try:
			# Read SHP Features
			driver = ogr.GetDriverByName('ESRI Shapefile')
			dataSource = driver.Open(self.shpFile, 0)
			inLayer = dataSource.GetLayer()
			
			# Collect all Geometry
			geomcol = ogr.Geometry(ogr.wkbGeometryCollection)
			for feature in inLayer:
				geomcol.AddGeometry(feature.GetGeometryRef())
			
			# Calculate convex hull and BBOX
			convexhull = geomcol.ConvexHull()
			env = convexhull.GetEnvelope()
			if big: 	barda = 0.2  # 22Km margin aprox
			else:		barda = 0.02 # 2.2Km margin aprox
			area = self.getAreaBBOX(env, barda)
			if (area > 10000): 
				print "AREA is too big, try entering another polygon"
				return -1
			# Export geometry to WKT			
			wkt="POLYGON ((%f %f , %f %f , %f %f , %f %f , %f %f))" %(float(env[0])-barda, float(env[2])-barda, float(env[0])-barda, float(env[3])+barda, float(env[1])+barda, float(env[3])+barda, float(env[1])+barda, float(env[2])-barda, float(env[0])-barda, float(env[2])-barda)							
			print wkt
			return wkt
        except Exception, e:  
			# Inform the user in the console
            print 'ERROR: '+str(e)
            return False			
        return True