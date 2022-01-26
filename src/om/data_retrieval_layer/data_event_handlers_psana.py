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
Handling of psana-based data events.

This module contains Data Event Handler classes that manipulate events originating from
the psana software framework (used at the LCLS facility).
"""
import sys
from typing import Any, Dict, Generator, List, Union

import numpy

from om.data_retrieval_layer import base as drl_base
from om.data_retrieval_layer import data_sources_psana as ds_psana
from om.utils import exceptions, parameters

try:
    import psana  # type: ignore
except ImportError:
    raise exceptions.OmMissingDependencyError(
        "The following required module cannot be imported: psana"
    )


def _psana_offline_event_generator(
    *, psana_source: Any, node_rank: int, mpi_pool_size: int
) -> Any:
    # Computes how many events the current processing node should process. Splits the
    # events as equally as possible amongst the processing nodes. If the number of
    # events cannot be exactly divided by the number of processing nodes, an additional
    # processing node is assigned the residual events.
    run: Any
    for run in psana_source.runs():
        times: Any = run.times()
        num_events_curr_node: int = int(
            numpy.ceil(len(times) / float(mpi_pool_size - 1))
        )
        events_curr_node: Any = times[
            (node_rank - 1) * num_events_curr_node : node_rank * num_events_curr_node
        ]
        evt: Any
        for evt in events_curr_node:

            yield run.event(evt)


class PsanaDataEventHandler(drl_base.OmDataEventHandler):
    """
    See documentation of the `__init__` function.
    """

    def __init__(
        self,
        *,
        source: str,
        data_sources: Dict[str, drl_base.OmDataSource],
        monitor_parameters: parameters.MonitorParams,
    ) -> None:
        """
        Data Event Handler for psana events.

        This method overrides the corresponding method of the base class: please also
        refer to the documentation of that class for more information.

        This class handles data events retrieved from the psana software framework at
        the LCLS facility.

        * For this Event Handler, a data event corresponds to the content of an
          individual psana event.

        * The source string required by this Data Event Handler is a string of the type
          used by psana to identify specific runs, experiments, or live data streams.

        Arguments:

            source: A string describing the data event source.

            data_sources: A dictionary containing a set of Data Sources.

                * Each dictionary key must define the name of a data source.

                * The corresponding dictionary value must store the instance of the
                  [Data Source class][om.data_retrieval_layer.base.OmDataSource] that
                  describes the source.

            monitor_parameters: An object storing OM's configuration parameters.
        """

        self._source: str = source
        self._monitor_params: parameters.MonitorParams = monitor_parameters
        self._data_sources: Dict[str, drl_base.OmDataSource] = data_sources

    def initialize_event_handling_on_collecting_node(
        self, *, node_rank: int, node_pool_size: int
    ) -> None:
        """
        Initializes psana event handling on the collecting node.

        This method overrides the corresponding method of the base class: please also
        refer to the documentation of that class for more information.

        Psana event sources do not need to be initialized on the collecting node, so
        this function actually does nothing.

        Arguments:

            node_rank: The rank, in the OM pool, of the processing node calling the
                function.

            node_pool_size: The total number of nodes in the OM pool, including all the
                processing nodes and the collecting node.
        """
        pass

    def initialize_event_handling_on_processing_node(
        self, node_rank: int, node_pool_size: int
    ) -> None:
        """
        Initializes psana event handling on the processing nodes.

        This method overrides the corresponding method of the base class: please also
        refer to the documentation of that class for more information.

        Arguments:

            node_rank: The rank, in the OM pool, of the processing node calling the
                function.

            node_pool_size: The total number of nodes in the OM pool, including all the
                processing nodes and the collecting node.
        """
        required_data: List[str] = self._monitor_params.get_parameter(
            group="data_retrieval_layer",
            parameter="required_data",
            parameter_type=list,
            required=True,
        )

        self._required_data_sources = drl_base.filter_data_sources(
            data_sources=self._data_sources,
            required_data=required_data,
        )

        lcls_extra_entry: List[List[str]] = self._monitor_params.get_parameter(
            group="data_retrieval_layer",
            parameter="lcls_extra",
            parameter_type=list,
        )

        if lcls_extra_entry:
            self._lcls_extra: Union[Dict[str, Any], None] = {}

            data_item: List[str]
            for data_item in lcls_extra_entry:
                if not isinstance(data_item, list) or len(data_item) != 3:
                    raise exceptions.OmWrongParameterTypeError(
                        "The 'lcls_extra' entry of the 'data_retrieval_layer' group "
                        "in the configuration file is not formatted correctly."
                    )
                for entry in data_item:
                    if not isinstance(entry, str):
                        raise exceptions.OmWrongParameterTypeError(
                            "The 'lcls_extra' entry of the 'data_retrieval_layer' "
                            "group in the configuration file is not formatted "
                            "correctly."
                        )
                    identifier: str
                    name: str
                    data_type, identifier, name = data_item
                    if data_type == "acqiris_waveform":
                        self._lcls_extra[name] = ds_psana.AcqirisDetector(
                            data_source_name=f"psana-{identifier}",
                            monitor_parameters=self._monitor_params,
                        )
                    elif data_type == "epics_pv":
                        self._lcls_extra[name] = ds_psana.EpicsVariablePsana(
                            data_source_name=f"psana-{identifier}",
                            monitor_parameters=self._monitor_params,
                        )
                    elif data_type == "wave8_total_intensity":
                        self._lcls_extra[name] = ds_psana.Wave8Detector(
                            data_source_name=f"psana-{identifier}",
                            monitor_parameters=self._monitor_params,
                        )
                    else:
                        raise exceptions.OmWrongParameterTypeError(
                            f"The requested '{data_type}' LCLS-specific data type is "
                            "not supported."
                        )
        else:
            self._lcls_extra = None

    def event_generator(
        self,
        *,
        node_rank: int,
        node_pool_size: int,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Retrieves psana events.

        This method overrides the corresponding method of the base class: please also
        refer to the documentation of that class for more information.

        This function retrieves events for processing (each event corresponds to a
        single psana event). When OM retrieves real-time data at the LCLS facility,
        each processing node receives data from a shared memory server operated by the
        facility, running on the same machine as the node. The sever takes care of
        distributing the data events. When instead OM uses the psana framework to read
        offline data, this function tries to distribute the events as evenly as
        possible across all the processing nodes. Each node should ideally process the
        same number of events. Only the last node might process fewer, depending on how
        evenly the total number can be split.

        Arguments:

            node_rank: The rank, in the OM pool, of the processing node calling the
                function.

            node_pool_size: The total number of nodes in the OM pool, including all the
                processing nodes and the collecting node.
        """
        # TODO: Check types of Generator
        # Detects if data is being read from an online or offline source.
        if "shmem" in self._source:
            offline: bool = False
        else:
            offline = True
        if offline and not self._source[-4:] == ":idx":
            self._source += ":idx"

        # If the psana calibration directory is provided in the configuration file, it
        # is added as an option to psana before the DataSource is set.
        psana_calib_dir: str = self._monitor_params.get_parameter(
            group="data_retrieval_layer",
            parameter="psana_calibration_directory",
            parameter_type=str,
        )
        if psana_calib_dir is not None:
            psana.setOption("psana.calib-dir", psana_calib_dir)
        else:
            print("OM Warning: Calibration directory not provided or not found.")

        psana_source = psana.DataSource(self._source)

        self._data_sources["timestamp"].initialize_data_source()
        source_name: str
        for source_name in self._required_data_sources:
            self._data_sources[source_name].initialize_data_source()

        data_event: Dict[str, Any] = {}
        data_event["additional_info"] = {}

        # Initializes the psana event source and starts retrieving events.
        if offline:
            psana_events: Any = _psana_offline_event_generator(
                psana_source=psana_source,
                node_rank=node_rank,
                mpi_pool_size=node_pool_size,
            )
        else:
            psana_events = psana_source.events()

        psana_event: Any
        for psana_event in psana_events:
            data_event["data"] = psana_event

            # Recovers the timestamp from the psana event (as seconds from the Epoch)
            # and stores it in the event dictionary to be retrieved later.
            data_event["additional_info"]["timestamp"] = self._data_sources[
                "timestamp"
            ].get_data(event=data_event)

            yield data_event

    def open_event(self, *, event: Dict[str, Any]) -> None:
        """
        Opens a psana event.

        This method overrides the corresponding method of the base class: please also
        refer to the documentation of that class for more information.

        Psana events do not need to be opened, so this function actually does nothing.

        Arguments:

            event: a dictionary storing the event data.
        """
        pass

    def close_event(self, *, event: Dict[str, Any]) -> None:
        """
        Closes a psana event.

        This method overrides the corresponding method of the base class: please also
        refer to the documentation of that class for more information.

        Psana events do not need to be closed, so this function actually does nothing.

        Arguments:

            event: a dictionary storing the event data.
        """
        pass

    def get_num_frames_in_event(self, *, event: Dict[str, Any]) -> int:
        """
        Gets the number of frames in a psana event.

        This method overrides the corresponding method of the base class: please also
        refer to the documentation of that class for more information.

        Each psana event stores data associated with a single detector frame, so this
        function always returns 1.

        Arguments:

            event: a dictionary storing the event data.

        Returns:

            int: the number of frames in the event.
        """
        return 1

    def extract_data(
        self,
        *,
        event: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Extracts data from a psana data event.

        This method overrides the corresponding method of the base class: please also
        refer to the documentation of that class for more information.

        Arguments:

            event: A dictionary storing the event data.

        Returns:

            A dictionary storing the extracted data.

            * Each dictionary key identifies a Data Source in the event for which data
              has been retrieved.

            * The corresponding dictionary value stores the data extracted from the
              Data Source for the frame being processed.
        """
        data: Dict[str, Any] = {}
        f_name: str
        data["timestamp"] = event["additional_info"]["timestamp"]
        for source_name in self._required_data_sources:
            try:
                data[source_name] = self._data_sources[source_name].get_data(
                    event=event
                )
            # One should never do the following, but it is not possible to anticipate
            # every possible error raised by the facility frameworks.
            except Exception:
                exc_type, exc_value = sys.exc_info()[:2]
                if exc_type is not None:
                    raise exceptions.OmDataExtractionError(
                        f"OM Warning: Cannot interpret {source_name} event data due "
                        f"to the following error: {exc_type.__name__}: {exc_value}"
                    )

        if self._lcls_extra:
            data["lcls_extra"] = {}
            name: str
            for name in self._lcls_extra:
                data["lcls_extra"][name] = self._lcls_extra[name].get_data(event)

        return data
