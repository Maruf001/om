# This file is part of OnDA.
#
# OnDA is free software: you can redistribute it and/or modify it under the terms of
# the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# OnDA is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with OnDA.
# If not, see <http://www.gnu.org/licenses/>.
#
# Copyright 2014-2019 Deutsches Elektronen-Synchrotron DESY,
# a research centre of the Helmholtz Association.
"""
Event structure.

Structure used to store retrieved events.
"""
from __future__ import absolute_import, division, print_function

import sys
import types

from future.utils import iteritems

from onda.utils import exceptions


class DataEvent(object):
    """
    Retrieved event information and data.

    Stores data and information for an event retrieved from a facility. Event handling
    methods, used to open, close and get basic information about the event, are
    defined when an instance of the class is created. Data extraction functions are
    instead injected dynamically, based on users' requests, after the creation of the
    class.
    """

    def __init__(self, event_handling_funcs, data_extraction_funcs):
        """
        Initializes the Event class.

        Args:

            event_handling_funcs (Dict): dictionary containg a set of event handling
                functions for the event.

            data_extraction_funcs (Dict): dictionary containg a set of data extraction
                functions to be run on the event.
        """

        self.open_event = types.MethodType(event_handling_funcs["open_event"], self)
        self.close_event = types.MethodType(event_handling_funcs["close_event"], self)
        self.get_num_frames_in_event = types.MethodType(
            event_handling_funcs["get_num_frames_in_event"], self
        )

        self.data = None
        self.metadata = None
        self.timestamp = None
        self.current_frame = None
        self.framework_info = {}
        self.data_extraction_functions = data_extraction_funcs

    def extract_data(self):
        """
        Extracts data from event.

        Runs the necessary data extraction functions and returns a dictionary where
        the keys are the name of the data extraction functions and the values are
        the results returned by each function.
        """
        data = {}
        # Tries to extract the data by calling the data extraction functions one after
        # the other. Stores the values returned by the functions in the data
        # dictionary, each with a key corresponding to the name of the extraction
        # function.
        try:
            for f_name, func in iteritems(self.data_extraction_functions):
                data[f_name] = func(self)
        # One should never do the following, but it is not possible to anticipate
        # every possible error raised by the facility frameworks.
        except Exception:
            exc_type, exc_value = sys.exc_info()[:2]
            raise exceptions.DataExtractionError(
                "OnDA Warning: Cannot interpret {0} event data due to the following "
                "error: {1}: {2}".format(func.__name__, exc_type.__name__, exc_value)
            )

        return data