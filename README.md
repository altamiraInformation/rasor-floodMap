#### Synopsis:

Plugin developed for the FP7 RASOR Project (http://www.rasor-project.eu/)

#### Pre-requisites:

+ Windows 7 or higher (64-bit version)
+ ESA SNAP version 2.0.2 / Sentinel-1 Toolbox (http://step.esa.int/main/download/previous-versions/)
+ CNES Orfeo Toolbox OTB - MINGW package 5.2.0 (https://www.orfeo-toolbox.org/packages/OTB-5.2.1-win64.zip)
+ QGIS 2.6 or higher (http://www.qgis.org/es/site/)

#### Important information:

In order to work with big flooded areas memory tunning for SNAP must be set. 

To do so, please edit (C:\Program Files\snap\bin\gpt.vmoptions) by **adding the following line at the end of the file**:

-Xmx4096m

#### Main capabilites:

The RASOR flood map plugin is a QGIS (Quantum GIS) open-source plugin capable of extracting a flood map from a couple of Sentinel-1 Ground Range Detected (GRD) images with change detection techniques. The plugin uses other open-source software components such as SNAP and Orfeo Toolbox in order to make the analysis.
