# -*- coding: utf-8 -*-
"""
/***************************************************************************
 rasor
                                 A QGIS plugin
 Plugin in order to generate Rasor compliant data and upload it to the platform
                             -------------------
        begin                : 2015-03-11
        copyright            : (C) 2015 by Joan Sala
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
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load rasor class from file rasor.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .rasor_floodMap import rasor
    return rasor(iface)
