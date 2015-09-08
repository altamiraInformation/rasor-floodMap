from PIL import Image
from PIL.ExifTags import TAGS
import xml.etree.ElementTree as ET

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