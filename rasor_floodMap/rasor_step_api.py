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
import os


class StepOne:
    """
    Step One of the processing Chain (Calibration + Subset + Despeckle)
    """

    def __init__(self, xml_step1a_file, xml_step1b_file, image_reference_path, image_flood_path, subset, output_path, date_reference, date_flood):
        self.xml_step1a_file = xml_step1a_file
        self.xml_step1a_path = os.path.dirname(xml_step1a_file)
        self.xml_step1b_file = xml_step1b_file
        self.xml_step1b_path = os.path.dirname(xml_step1b_file)
        self.image_reference_path = image_reference_path
        self.image_flood_path = image_flood_path
        self.output_path = output_path
        self.subset = subset
        self.date_flood = date_flood
        self.date_reference = date_reference

    def write_xml(self):
        print "## Step 1a: Create xml Calibration and Co-registration"
        print "#### Using " + self.xml_step1a_file
        tree = ET.parse(self.xml_step1a_file)
        root = tree.getroot()

        # For each node set the parameters based on the python plugin input
        for node in root.findall('node'):
            if node.attrib.get('id') == 'Read-Reference':
                parameters = node.find("parameters")
                filename = parameters.find("file")
                filename.text = self.image_reference_path
                print "#### Reference image path " + filename.text
            elif node.attrib.get('id') == 'Read-Flood':
                parameters = node.find("parameters")
                filename = parameters.find("file")
                filename.text = self.image_flood_path
                print "#### Flood image path " + filename.text
            elif node.attrib.get('id') == 'Calibration-Reference':
                print "#### Calibration-Reference does not require parameters"
            elif node.attrib.get('id') == 'Calibration-Flood':
                print "#### Calibration-Flood does not require parameters"
            elif node.attrib.get('id') == 'Subset-Reference':
                parameters = node.find("parameters")
                geo_region = parameters.find("geoRegion")
                geo_region.text = self.subset
                print "#### Subset Reference changed"
            elif node.attrib.get('id') == 'Subset-Flood':
                parameters = node.find("parameters")
                geo_region = parameters.find("geoRegion")
                geo_region.text = self.subset
                print "#### Subset Flood changed"
            elif node.attrib.get('id') == 'CreateStack':
                print "#### CreateStack does not require parameters"
            elif node.attrib.get('id') == 'GCP-Selection':
                print "#### GCP-Selection does not require parameters"
            elif node.attrib.get('id') == 'Warp':
                print "#### Warp do not require parameters"
            elif node.attrib.get('id') == 'BandSelect-Reference':
                parameters = node.find("parameters")
                source_bands = parameters.find("sourceBands")
                source_bands.text = "Sigma0_VV_slv1_" + self.date_reference
                print "#### Reference image band name: " + source_bands.text
            elif node.attrib.get('id') == 'BandSelect-Flood':
                parameters = node.find("parameters")
                source_bands = parameters.find("sourceBands")
                source_bands.text = "Sigma0_VV_mst_" + self.date_flood
                print "#### Flood image band name: " + source_bands.text
            elif node.attrib.get('id') == 'Write-Reference':
                parameters = node.find("parameters")
                filename = parameters.find("file")
                filename.text = self.output_path + "\\Reference.tif"
                print "#### Reference Image output file " + filename.text
            elif node.attrib.get('id') == 'Write-Flood':
                parameters = node.find("parameters")
                filename = parameters.find("file")
                filename.text = self.output_path + "\\Flood.tif"
                print "#### Flood Image output file" + filename.text

        tree.write(self.output_path+'/Step1a.xml')

        print "## Step 1b: Create xml for Subset and Orthorectification (quicklook)"
        print "#### Using " + self.xml_step1b_file
        tree = ET.parse(self.xml_step1b_file)
        root = tree.getroot()

        # For each node set the parameters based on the python plugin input
        for node in root.findall('node'):
            if node.attrib.get('id') == 'Read-Reference':
                parameters = node.find("parameters")
                filename = parameters.find("file")
                filename.text = self.output_path + "\\Reference.tif"
                print "#### Co-registered Reference image path " + filename.text
            elif node.attrib.get('id') == 'Read-Flood':
                parameters = node.find("parameters")
                filename = parameters.find("file")
                filename.text = self.output_path + "\\Flood.tif"
                print "#### Co-registered Flood image path " + filename.text
            elif node.attrib.get('id') == 'Subset-Reference':
                parameters = node.find("parameters")
                geo_region = parameters.find("geoRegion")
                geo_region.text = self.subset
                print "#### Subset Reference changed"
            elif node.attrib.get('id') == 'Subset-Flood':
                parameters = node.find("parameters")
                geo_region = parameters.find("geoRegion")
                geo_region.text = self.subset
                print "#### Subset Flood changed"
            elif node.attrib.get('id') == 'Write-Reference':
                parameters = node.find("parameters")
                filename = parameters.find("file")
                filename.text = self.output_path + "\\Reference-Subset.tif"
                print "#### Reference Image output file " + filename.text
            elif node.attrib.get('id') == 'Write-Flood':
                parameters = node.find("parameters")
                filename = parameters.find("file")
                filename.text = self.output_path + "\\Flood-Subset.tif"
                print "#### Flood Image output file" + filename.text
            elif node.attrib.get('id') == 'Terrain-Correction-Reference':
                print "#### CreateStack does not require parameters"
            elif node.attrib.get('id') == 'Terrain-Correction-Flood':
                print "#### CreateStack does not require parameters"
            elif node.attrib.get('id') == 'Write-Reference-TC':
                parameters = node.find("parameters")
                filename = parameters.find("file")
                filename.text = self.output_path + "\\Reference-Subset-TC.tif"
                print "#### Reference Image output file " + filename.text
            elif node.attrib.get('id') == 'Write-Flood-TC':
                parameters = node.find("parameters")
                filename = parameters.find("file")
                filename.text = self.output_path + "\\Flood-Subset-TC.tif"
                print "#### Flood Image output file" + filename.text

        tree.write(self.output_path+'/Step1b.xml')

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
