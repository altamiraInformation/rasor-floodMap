from osgeo import ogr

class Shapefile():
    '''Worker in order to run time-consuming tasks of S1-TBX'''
    def __init__(self, shp_path):
		self.shpFile = shp_path

    def getBBOX(self):
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
			# Export geometry to WKT
			#print "minX: %f, minY: %f, maxX: %f, maxY: %f" %(env[0],env[2],env[1],env[3])			
			wkt="POLYGON ((%f %f , %f %f , %f %f , %f %f , %f %f))" %(env[0],env[2], env[0],env[3], env[1],env[3], env[1],env[2], env[0],env[2])	
			return wkt
        except Exception, e:  
			# Inform the user in the console
            print 'ERROR: '+str(e)
            return False			
        return True