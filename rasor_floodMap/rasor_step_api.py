import xml.etree.ElementTree as ET
import os

class StepOne:
    """
    Step One of the processing Chain (Calibration + Subset + Despeckle)
    """

    def __init__(self, xml_file_path, image_before_path, image_after_path, subset, output_path):
        self.xml_file_path = xml_file_path
        self.xml_path = os.path.dirname(xml_file_path)
        self.image_before_path = image_before_path
        self.image_after_path = image_after_path
        self.output_path = output_path
        self.subset = subset

    def write_xml(self):
        print "## Step 1: Create xml for before and after flooding images processing"
        print "#### Using " + self.xml_file_path
        tree = ET.parse(self.xml_file_path)
        root = tree.getroot()

        for node in root.findall('node'):
            # For each node set the parameters based on the python plugin input
            if node.attrib.get('id') == 'Read':
                parameters = node.find("parameters")
                # set input file name
                filename = parameters.find("file")
                filename.text = self.image_before_path
                print "#### Image before  flood event path " + filename.text
            elif node.attrib.get('id') == 'Calibration':
                parameters = node.find("parameters")
                print "#### Calibration do not require parameters"
            elif node.attrib.get('id') == 'Subset':
                parameters = node.find("parameters")
                # region = parameters.find("region")
                geo_region = parameters.find("geoRegion")
                # region.text =
                geo_region.text = self.subset
                print "#### Subset changed"
            elif node.attrib.get('id') == 'SAR-Simulation':
                parameters = node.find("parameters")
                print "#### SAR-Simulation do not require parameters"
            elif node.attrib.get('id') == 'GCP-Selection':
                parameters = node.find("parameters")
                print "#### GCP-Selection do not require parameters"
            elif node.attrib.get('id') == 'SARSim-Terrain-Correction':
                parameters = node.find("parameters")
                print "SARSim-Terrain-Correction do not require parameters"
            elif node.attrib.get('id') == 'SARSim-Terrain-Correction':
                parameters = node.find("parameters")
                print "#### SARSim-Terrain-Correction do not require parameters"
            elif node.attrib.get('id') == 'Speckle-Filter':
                parameters = node.find("parameters")
                print "#### Speckle-Filter do not require parameters"
            elif node.attrib.get('id') == 'Write':
                parameters = node.find("parameters")
                # set input file name
                filename = parameters.find("file")
                filename.text = self.output_path + "\\before.tif"
                print "#### Image output before flood event path " + filename.text

        tree.write(self.output_path+'/Step1-before.xml')

        # write the xml for the after flooding image
        tree = ET.parse(self.output_path+'/Step1-before.xml')
        root = tree.getroot()
        for node in root.findall('node'):
            # For each node set the parameters based on the python plugin input
            if node.attrib.get('id') == 'Read':
                parameters = node.find("parameters")
                # set input file name
                filename = parameters.find("file")
                filename.text = self.image_after_path
                print "Image after flood event path " + filename.text
            elif node.attrib.get('id') == 'Write':
                parameters = node.find("parameters")
                # set input file name
                filename = parameters.find("file")
                filename.text = self.output_path + "\\after.tif"
                print "Image output after flood event  path " + filename.text

        tree.write(self.output_path + '/Step1-after.xml')

class StepTwo:
    """
    Step Two of the processing Chain (RGB Composition)
    """

    def __init__(self, xml_file_path, image_before_path, date_before, image_after_path, date_after,  output_path):
        self.xml_file_path = xml_file_path
        self.xml_path = os.path.dirname(xml_file_path)
        self.image_before_path = image_before_path
        self.date_before = date_before
        self.image_after_path = image_after_path
        self.date_after = date_after
        self.output_path = output_path

    def write_xml(self):
        print "## Step 2: Create xml for RGB Composition"
        print "#### Using " + self.xml_file_path

        tree = ET.parse(self.xml_file_path)
        root = tree.getroot()

        for node in root.findall('node'):
            # For each node set the parameters based on the python plugin input
            if node.attrib.get('id') == 'After':
                parameters = node.find("parameters")
                # set input file name
                filename = parameters.find("file")
                filename.text = self.image_after_path
                print "#### Image after flood event path " + filename.text
            elif node.attrib.get('id') == 'Before':
                parameters = node.find("parameters")
                # set input file name
                filename = parameters.find("file")
                filename.text = self.image_before_path
                print "#### Image before flood event path " + filename.text
            elif node.attrib.get('id') == 'Difference':
                parameters = node.find("parameters")
                # set input file name
                expression = parameters.find("bandExpression")
                expression.text = "Sigma0_VV_mst_" + self.date_after + " - Sigma0_VV_slv1_" + self.date_before
                print "#### Expression for Difference operation: " + expression.text
            elif node.attrib.get('id') == 'Ratio':
                parameters = node.find("parameters")
                # set input file name
                expression = parameters.find("bandExpression")
                expression.text = "Sigma0_VV_mst_" + self.date_after + " / Sigma0_VV_slv1_" + self.date_before
                print "#### Expression for Ratio operation: " + expression.text
            elif node.attrib.get('id') == 'Write':
                parameters = node.find("parameters")
                # set input file name
                filename = parameters.find("file")
                filename.text = self.output_path + "\\RGB.tif"
                print "#### Output image path " + filename.text
        tree.write(self.output_path + '/Step2-RGB.xml')

class StepThree:
    """
    Step Three of the processing Chain (RGB Segmentation)
    """

    def __init__(self, xml_file_path, image_rgb_path, output_path, cluster_count=14, iteration_count=30):
        self.xml_file_path = xml_file_path
        self.image_rgb_path = image_rgb_path
        self.output_path = output_path
        self.cluster_count = cluster_count
        self.iteration_count = iteration_count

    def write_xml(self):
        print "## Step 3: Create xml for Segmentation"
        print "#### Using " + self.xml_file_path

        tree = ET.parse(self.xml_file_path)
        root = tree.getroot()

        for node in root.findall('node'):
            # For each node set the parameters based on the python plugin input
            if node.attrib.get('id') == 'Read':
                parameters = node.find("parameters")
                # set input file name
                filename = parameters.find("file")
                filename.text = self.image_rgb_path
                print "#### RGB Image from Step 2" + filename.text
            elif node.attrib.get('id') == 'Write':
                parameters = node.find("parameters")
                # set input file name
                filename = parameters.find("file")
                filename.text = self.output_path + "\\RGB_Segmentation.tif"
                print "#### Output RGB Segmtantion image path " + filename.text
            elif node.attrib.get('id') == 'Segmentation':
                parameters = node.find("parameters")
                cluster_count = parameters.find("clusterCount")
                cluster_count.text = str(self.cluster_count)
                iteration_count = parameters.find("iterationCount")
                iteration_count.text = str(self.iteration_count)
                print "#### KMeans Cluster Analysis with default parameters"

        tree.write(self.output_path + '/Step3-Segmentation.xml')