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
    Step One of the processing Chain (Calibration + Subset + Co-Registration)
    """

    def __init__(self, xml_step1a_file, xml_step1b_file, image_reference_path, image_flood_path, subset, output_path, date_reference, date_flood):
        self.xml_step1a_file = xml_step1a_file
        self.xml_step1b_file = xml_step1b_file
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
                parameter = node.find("parameters/file")
                parameter.text = self.image_reference_path
                print "#### Reference image path " + parameter.text
            elif node.attrib.get('id') == 'Read-Flood':
                parameter = node.find("parameters/file")
                parameter.text = self.image_flood_path
                print "#### Flood image path " + parameter.text
            elif node.attrib.get('id') == 'Calibration-Reference':
                print "#### Calibration-Reference does not require parameters"
            elif node.attrib.get('id') == 'Calibration-Flood':
                print "#### Calibration-Flood does not require parameters"
            elif node.attrib.get('id') == 'Subset-Reference':
                parameter = node.find("parameters/geoRegion")
                parameter.text = self.subset
                print "#### Subset Reference changed"
            elif node.attrib.get('id') == 'Subset-Flood':
                parameter = node.find("parameters/geoRegion")
                parameter.text = self.subset
                print "#### Subset Flood changed"
            elif node.attrib.get('id') == 'CreateStack':
                print "#### CreateStack does not require parameters"
            elif node.attrib.get('id') == 'GCP-Selection':
                print "#### GCP-Selection does not require parameters"
            elif node.attrib.get('id') == 'Warp':
                print "#### Warp do not require parameters"
            elif node.attrib.get('id') == 'BandSelect-Reference':
                parameter = node.find("parameters/sourceBands")
                parameter.text = "Sigma0_VV_slv1_" + self.date_reference
                print "#### Reference image band name: " + parameter.text
            elif node.attrib.get('id') == 'BandSelect-Flood':
                parameter = node.find("parameters/sourceBands")
                parameter.text = "Sigma0_VV_mst_" + self.date_flood
                print "#### Flood image band name: " + parameter.text
            elif node.attrib.get('id') == 'Write-Reference':
                parameter = node.find("parameters/file")
                parameter.text = self.output_path + "\\Reference.tif"
                print "#### Reference Image output file " + parameter.text
            elif node.attrib.get('id') == 'Write-Flood':
                parameter = node.find("parameters/file")
                parameter.text = self.output_path + "\\Flood.tif"
                print "#### Flood Image output file" + parameter.text

        tree.write(self.output_path+'/Step1a.xml')

        print "## Step 1b: Create xml for Subset and Orthorectification (quicklook)"
        print "#### Using " + self.xml_step1b_file
        tree = ET.parse(self.xml_step1b_file)
        root = tree.getroot()

        # For each node set the parameters based on the python plugin input
        for node in root.findall('node'):
            if node.attrib.get('id') == 'Read-Reference':
                parameter = node.find("parameters/file")
                parameter.text = self.output_path + "\\Reference.tif"
                print "#### Co-registered Reference image path " + parameter.text
            elif node.attrib.get('id') == 'Read-Flood':
                parameter = node.find("parameters/file")
                parameter.text = self.output_path + "\\Flood.tif"
                print "#### Co-registered Flood image path " + parameter.text
            elif node.attrib.get('id') == 'Subset-Reference':
                parameter = node.find("parameters/geoRegion")
                parameter.text = self.subset
                print "#### Subset Reference changed"
            elif node.attrib.get('id') == 'Subset-Flood':
                parameter = node.find("parameters/geoRegion")
                parameter.text = self.subset
                print "#### Subset Flood changed"
            elif node.attrib.get('id') == 'Write-Reference':
                parameter = node.find("parameters/file")
                parameter.text = self.output_path + "\\Reference-Subset.tif"
                print "#### Reference Image output file " + parameter.text
            elif node.attrib.get('id') == 'Write-Flood':
                parameter = node.find("parameters/file")
                parameter.text = self.output_path + "\\Flood-Subset.tif"
                print "#### Flood Image output file" + parameter.text
            elif node.attrib.get('id') == 'Terrain-Correction-Reference':
                print "#### Terrain-Correction-Reference does not require parameters"
            elif node.attrib.get('id') == 'Terrain-Correction-Flood':
                print "#### Terrain-Correction-Flood does not require parameters"
            elif node.attrib.get('id') == 'Write-Reference-TC':
                parameter = node.find("parameters/file")
                parameter.text = self.output_path + "\\Reference-Subset-TC.tif"
                print "#### Reference Image TC output file " + parameter.text
            elif node.attrib.get('id') == 'Write-Flood-TC':
                parameter = node.find("parameters/file")
                parameter.text = self.output_path + "\\Flood-Subset-TC.tif"
                print "#### Flood Image TC output file" + parameter.text

        tree.write(self.output_path+'/Step1b.xml')


class StepTwo:
    """
    Step Two of the processing Chain (RGB Composition)
    """

    def __init__(self, xml_step2_file, image_reference_path, date_reference, image_flood_path, date_flood,  output_path):
        self.xml_step2_file = xml_step2_file
        self.image_reference_path = image_reference_path
        self.date_reference = date_reference
        self.image_flood_path = image_flood_path
        self.date_flood = date_flood
        self.output_path = output_path

    def write_xml(self):
        print "## Step 2: Create xml for RGB Composition"
        print "#### Using " + self.xml_step2_file

        tree = ET.parse(self.xml_step2_file)
        root = tree.getroot()

        for node in root.findall('node'):
            # For each node set the parameters based on the python plugin input
            if node.attrib.get('id') == 'Read-Flood':
                parameter = node.find("parameters/file")
                parameter.text = self.image_flood_path
                print "#### Image flood path " + parameter.text
            elif node.attrib.get('id') == 'Read-Reference':
                parameter = node.find("parameters/file")
                parameter.text = self.image_reference_path
                print "#### Image reference path " + parameter.text
            elif node.attrib.get('id') == 'CreateStack':
                print "#### CreateStack does not require parameters"
            elif node.attrib.get('id') == 'BandMaths-Difference':
                parameter = node.find("parameters/targetBands/targetBand/expression")
                parameter.text = "log(abs(Sigma0_VV_mst_" + self.date_flood + " - Sigma0_VV_slv1_" + self.date_reference + '_slv1_' + self.date_flood + '))'
                print "#### Expression for Difference operation: " + parameter.text
            elif node.attrib.get('id') == 'BandMaths-Ratio':
                parameter = node.find("parameters/targetBands/targetBand/expression")
                parameter.text = 'log(abs(Sigma0_VV_mst_' + self.date_flood + " / Sigma0_VV_slv1_" + self.date_reference + '_slv1_' + self.date_flood + '))'
                print "#### Expression for Ratio operation: " + parameter.text
            elif node.attrib.get('id') == 'BandMaths-Flood':
                parameter = node.find("parameters/targetBands/targetBand/expression")
                parameter.text = "Sigma0_VV_mst_" + self.date_flood
                print "#### Expression for Flood operation: " + parameter.text
            elif node.attrib.get('id') == 'Write-RGB':
                parameter = node.find("parameters/file")
                parameter.text = self.output_path + "\\RGB.tif"
                print "#### Output image path " + parameter.text
        tree.write(self.output_path + '/Step2.xml')


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


# python main.py /path/to/image/before /path/to/image/after region geoRegion
if __name__ == '__main__':
    print "# Generating xml for Vietnam Zone 1"

    xml_step1a_file = 'C:/Users/alex.ALTAMIRA-INFORM/Projects/08.RASOR/01.Sofware/github/rasor-floodMap/rasor_floodMap/templates/Step1a.xml'
    xml_step1b_file = 'C:/Users/alex.ALTAMIRA-INFORM/Projects/08.RASOR/01.Sofware/github/rasor-floodMap/rasor_floodMap/templates/Step1b.xml'
    image_reference_path = 'C:\\Users\\alex.ALTAMIRA-INFORM\\Projects\\08.RASOR\\01.Sofware\\Flood Mapping tool\\Input\\Zone 1\S1A_IW_GRDH_1SDV_20150724T105730_20150724T105759_006952_00969F_AFC6.SAFE\\manifest.safe'
    image_flood_path = 'C:\\Users\\alex.ALTAMIRA-INFORM\\Projects\\08.RASOR\\01.Sofware\\Flood Mapping tool\\Input\\Zone 1\\S1A_IW_GRDH_1SDV_20150817T105732_20150817T105756_007302_00A042_05C4.SAFE\\manifest.safe'
    subset = "POLYGON ((106.49468118665962 20.531887746800493, 106.34572730547497 21.258832517147873, 107.14589170596244 21.40277153419721, 107.29092536531218 20.676267553038453, 106.49468118665962 20.531887746800493))"
    output_path = "C:\\Users\\alex.ALTAMIRA-INFORM\\Projects\\08.RASOR\\01.Sofware\\Flood Mapping tool\\Output\\Zone 1 New"
    date_reference = "24Jul2015"
    date_flood = "17Aug2015"

    step_one = StepOne(xml_step1a_file, xml_step1b_file, image_reference_path, image_flood_path, subset, output_path, date_reference, date_flood)
    step_one.write_xml()

    xml_step2_file = 'C:/Users/alex.ALTAMIRA-INFORM/Projects/08.RASOR/01.Sofware/github/rasor-floodMap/rasor_floodMap/templates/Step2.xml'
    image_reference_path = output_path + '/Reference-Subset.tif'
    image_flood_path = output_path + '/Flood-Subset.tif'
    date_reference = "24Jul2015"
    date_flood = "17Aug2015"

    step_two = StepTwo(xml_step2_file, image_reference_path, date_reference, image_flood_path, date_flood,  output_path)
    step_two.write_xml()