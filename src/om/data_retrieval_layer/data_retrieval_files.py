# This file is part of OM.
#
# OM is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# OM is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with OM.
# If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2020 -2021 SLAC National Accelerator Laboratory
#
# Based on OnDA - Copyright 2014-2019 Deutsches Elektronen-Synchrotron DESY,
# a research centre of the Helmholtz Association.
"""
Retrieval of data from files.

This module contains Data Retrieval classes that deal with files.
"""
from typing import Dict

from om.data_retrieval_layer import base as drl_base
from om.data_retrieval_layer import data_event_handlers_files as deh_files
from om.data_retrieval_layer import data_sources_files as ds_files
from om.data_retrieval_layer import data_sources_generic as ds_generic
from om.utils import parameters


class PilatusFilesDataRetrieval(drl_base.OmDataRetrieval):
    """
    See documentation of the `__init__` function.
    """

    def __init__(self, *, monitor_parameters: parameters.MonitorParams, source: str):
        """
        Data Retrieval for Pilatus single-frame CBF files.

        This method overrides the corresponding method of the base class: please also
        refer to the documentation of that class for more information.

        This class implements OM's Data Retrieval Layer for a set of single-frame files
        written by a Pilatus detector in CBF format.

        * This class considers an individual data event as corresponding to the content
          of a single Pilatus CBF file.

        * The full path to the CBF file is used as event identifier.

        * Since Pilatus files do not contain any timestamp information, the
          modification time of a file is taken as a first approximation of the
          timestamp of the data it contains.

        * Since Pilatus files do not contain any detector distance or beam energy
          information, their values are retrieved from OM's configuration parameters
          (specifically, the `fallback_detector_distance_in_mm` and
          `fallback_beam_energy_in_eV` entries in the `data_retrieval_layer`
          parameter group).

        * The source string required by this Data Retrieval class is the path to a file
          containing a list of CBF files to process, one per line, with their absolute
          or relative path.

        Arguments:

            monitor_parameters: An object storing OM's configuration parameters.

            source: A string describing the data event source.
        """
        data_sources: Dict[str, drl_base.OmDataSource] = {
            "timestamp": ds_files.TimestampFromFileModificationTime(
                data_source_name="timestamp", monitor_parameters=monitor_parameters
            ),
            "event_id": ds_files.EventIdFromFilePath(
                data_source_name="eventid", monitor_parameters=monitor_parameters
            ),
            "frame_id": ds_generic.FrameIdZero(
                data_source_name="frameid", monitor_parameters=monitor_parameters
            ),
            "detector_data": ds_files.PilatusSingleFrameFiles(
                data_source_name="detector", monitor_parameters=monitor_parameters
            ),
            "beam_energy": ds_generic.FloatEntryFromConfiguration(
                data_source_name="fallback_beam_energy_in_eV",
                monitor_parameters=monitor_parameters,
            ),
            "detector_distance": ds_generic.FloatEntryFromConfiguration(
                data_source_name="fallback_detector_distance_in_mm",
                monitor_parameters=monitor_parameters,
            ),
        }

        self._data_event_handler: drl_base.OmDataEventHandler = (
            deh_files.PilatusFilesEventHandler(
                source=source,
                monitor_parameters=monitor_parameters,
                data_sources=data_sources,
            )
        )

    def get_data_event_handler(self) -> drl_base.OmDataEventHandler:
        """
        Retrieves the Data Event Handler used by the class.

        This method overrides the corresponding method of the base class: please also
        refer to the documentation of that class for more information.

        Returns:

            The Data Event Handler used by the Data Retrieval class.
        """
        return self._data_event_handler


class Jungfrau1MFilesDataRetrieval(drl_base.OmDataRetrieval):
    """
    See documentation of the `__init__` function.
    """

    def __init__(self, *, monitor_parameters: parameters.MonitorParams, source: str):
        """
        Data Retrieval for Jungfrau 1M HDF5 files.

        This method overrides the corresponding method of the base class: please also
        refer to the documentation of that class for more information.

        This class implements OM's Data Retrieval Layer for a set of files written by
        a Jungfrau 1M detector in HDF5 format.

        * This class considers an individual data event as equivalent to an single
          detector frame stored in an HDF5 file.

        * The full path to the file containing the frame, together with the index of
          the frame in the file, is used as event identifier.

        * Jungfrau 1M files do not contain any absolute timestamp information, but they
          store the readout of the internal detector clock for every frame. As a first
          approximation, the modification time of a file is taken as the timestamp of
          the first frame it contains, and the timestamp of all other frames is
          computed according to the internal clock difference.

        * Since Jungfrau 1M files do not contain any detector distance or beam energy
          information, their values are retrieved from OM's configuration parameters
          (specifically, the `fallback_detector_distance_in_mm` and
          `fallback_beam_energy_in_eV` entries in the `data_retrieval_layer`
          parameter group).

        * The source string required by this Data Retrieval class is the path to a file
          containing a list of HDF5 files to process, one per line, with their absolute
          or relative path.

        Arguments:

            monitor_parameters: An object storing OM's configuration parameters.

            source: A string describing the data event source.
        """

        data_sources: Dict[str, drl_base.OmDataSource] = {
            "timestamp": ds_files.TimestampJungfrau1MFiles(
                data_source_name="timestamp", monitor_parameters=monitor_parameters
            ),
            "event_id": ds_files.EventIdJungfrau1MFiles(
                data_source_name="eventid", monitor_parameters=monitor_parameters
            ),
            "frame_id": ds_generic.FrameIdZero(
                data_source_name="frameid", monitor_parameters=monitor_parameters
            ),
            "detector_data": ds_files.Jungfrau1MFiles(
                data_source_name="detector", monitor_parameters=monitor_parameters
            ),
            "beam_energy": ds_generic.FloatEntryFromConfiguration(
                data_source_name="fallback_beam_energy",
                monitor_parameters=monitor_parameters,
            ),
            "detector_distance": ds_generic.FloatEntryFromConfiguration(
                data_source_name="fallback_detector_distance",
                monitor_parameters=monitor_parameters,
            ),
        }

        self._data_event_handler: drl_base.OmDataEventHandler = (
            deh_files.Jungfrau1MFilesDataEventHandler(
                source=source,
                monitor_parameters=monitor_parameters,
                data_sources=data_sources,
            )
        )

    def get_data_event_handler(self) -> drl_base.OmDataEventHandler:
        """
        Retrieves the Data Event Handler used by the class.

        This method overrides the corresponding method of the base class: please also
        refer to the documentation of that class for more information.

        Returns:

            The Data Event Handler used by the Data Retrieval class.
        """
        return self._data_event_handler


class Eiger16MFilesDataRetrieval(drl_base.OmDataRetrieval):
    """
    See documentation of the `__init__` function.
    """

    def __init__(self, *, monitor_parameters: parameters.MonitorParams, source: str):
        """
        Data Retrieval for Eiger 16M HDF5 files.

        This method overrides the corresponding method of the base class: please also
        refer to the documentation of that class for more information.

        This class implements OM's Data Retrieval Layer for a set of files written by
        a Eiger 16M detector in HDF5 format.

        * This class considers an individual data event as corresponding to a single
          detector frame stored in an HDF5 file.

        * The full path to the file containing the frame, together with the index of
          the frame in the file, is used as event identifier.

        * Since Eiger 16M files do not contain any absolute timestamp information, the
          modification time of a file is taken as a first approximation of the
          timestamp of the data it contains.

        * Since Eiger 16M files do not contain any detector distance or beam energy
          information, their values are retrieved from OM's configuration parameters
          (specifically, the `fallback_detector_distance_in_mm` and
          `fallback_beam_energy_in_eV` entries in the `data_retrieval_layer`
          parameter group).

        * The source string required by this Data Retrieval class is the path to a file
          containing a list of HDF5 files to process, one per line, with their absolute
          or relative path.

        Arguments:

            monitor_parameters: An object storing OM's configuration parameters.

            source: A string describing the data event source.
        """
        data_sources: Dict[str, drl_base.OmDataSource] = {
            "timestamp": ds_files.TimestampFromFileModificationTime(
                data_source_name="timestamp", monitor_parameters=monitor_parameters
            ),
            "event_id": ds_files.EventIdEiger16MFiles(
                data_source_name="eventid", monitor_parameters=monitor_parameters
            ),
            "frame_id": ds_generic.FrameIdZero(
                data_source_name="frameid", monitor_parameters=monitor_parameters
            ),
            "detector_data": ds_files.Eiger16MFiles(
                data_source_name="detector", monitor_parameters=monitor_parameters
            ),
            "beam_energy": ds_generic.FloatEntryFromConfiguration(
                data_source_name="fallback_beam_energy",
                monitor_parameters=monitor_parameters,
            ),
            "detector_distance": ds_generic.FloatEntryFromConfiguration(
                data_source_name="fallback_detector_distance",
                monitor_parameters=monitor_parameters,
            ),
        }

        self._data_event_handler: drl_base.OmDataEventHandler = (
            deh_files.Eiger16MFilesDataEventHandler(
                source=source,
                monitor_parameters=monitor_parameters,
                data_sources=data_sources,
            )
        )

    def get_data_event_handler(self) -> drl_base.OmDataEventHandler:
        """
         Retrieves the Data Event Handler used by the class.

         This method overrides the corresponding method of the base class: please also
         refer to the documentation of that class for more information.

        Returns:

             The Data Event Handler used by the Data Retrieval class.
        """
        return self._data_event_handler