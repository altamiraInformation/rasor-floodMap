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

#########################################################################################
### Description: Class in order to wrap the Sentinel-1 XML format needed for the 4 steps.
#########################################################################################

class StepOne:
    """
    Step One of the processing Chain (Calibration + Subset + Co-Registration using SNAP)
    """

    def __init__(self, xml_step1a_file, xml_step1b_file, image_reference_path, image_flood_path, subset1, subset2, output_path, date_reference, date_flood):
        self.xml_step1a_file = xml_step1a_file
        self.xml_step1b_file = xml_step1b_file
        self.image_reference_path = image_reference_path
        self.image_flood_path = image_flood_path
        self.output_path = output_path
        self.subset1 = subset1
        self.subset2= subset2
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
                parameter.text = self.subset1
                print "#### Subset Reference changed"
            elif node.attrib.get('id') == 'Subset-Flood':
                parameter = node.find("parameters/geoRegion")
                parameter.text = self.subset1
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
                parameter.text = self.subset2
                print "#### Subset Reference changed"
            elif node.attrib.get('id') == 'Subset-Flood':
                parameter = node.find("parameters/geoRegion")
                parameter.text = self.subset2
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
    Step Two of the processing Chain (RGB Composition using SNAP)
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
    Step Three of the processing Chain (Mean filtering using OTB)
    """

    def __init__(self, xml_step3_file, image_rgb_file, output_path, radius=5, range=15):
        self.xml_step3_file = xml_step3_file
        self.image_rgb_file = image_rgb_file
        self.output_path = output_path
        self.radius = radius
        self.range = range

    def write_xml(self):
        print "## Step 3: Create xml for Mean filtering"
        print "#### Using " + self.xml_step3_file

        tree = ET.parse(self.xml_step3_file)
        root = tree.getroot()

        for parameter in root.findall('application/parameter'):
            if parameter.find('key').text == 'in':
                value = parameter.find("value")
                value.text = self.image_rgb_file
                print "#### RGB Image from Step 2: " + value.text
            elif parameter.find('key').text == 'fout':
                value = parameter.find("value")
                value.text = self.output_path + '/RGB-Mean.tif'
                print "#### Mean filter image: " + value.text
            elif parameter.find('key').text == 'foutpos':
                value = parameter.find("value")
                value.text = self.output_path + '/RGB-Mean_spatial.tif'
                print "#### Output RGB mean spatial image path: " + value.text
            elif parameter.find('key').text == 'spatialr':
                value = parameter.find("value")
                value.text = str(self.radius)
                print "#### Mean filter with radius: " + str(self.radius)

        tree.write(self.output_path + '/Step3.xml')


class StepFour:
    """
    Step Four of the processing Chain (Classification using OTB)
    """

    def __init__(self, xml_step4_file, image_mean_file, output_path, num_classes=3):
        self.xml_step4_file = xml_step4_file
        self.image_mean_file = image_mean_file
        self.output_path = output_path
        self.num_classes = num_classes

    def write_xml(self):
        print "## Step 4: Create xml for Classification"
        print "#### Using " + self.xml_step4_file

        tree = ET.parse(self.xml_step4_file)
        root = tree.getroot()

        for parameter in root.findall('application/parameter'):
            if parameter.find('key').text == 'in':
                value = parameter.find("value")
                value.text = self.image_mean_file
                print "#### RGB-Mean Image from Step 3: " + value.text
            elif parameter.find('key').text == 'out':
                value = parameter.find("value")
                value.text = self.output_path + '/RGB-Mean-Kmeans.tif'
                print "#### Mean filter image: " + value.text
            elif parameter.find('key').text == 'nc':
                value = parameter.find("value")
                value.text = str(self.num_classes)
                print "#### Num classes Kmeans: " + str(self.num_classes)

        tree.write(self.output_path + '/Step4.xml')
