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
OM's Processing Layer.

This package contains OM's Processing Layer. This is where the pipeline of scientific
data analysis for all kind of monitors is defined. Each module in this package contains
the implementation of a different type of OnDA Monitor.
"""
from om.processing_layer.crystallography import CrystallographyProcessing
from om.processing_layer.xes import XESProcessing
from om.processing_layer.cheetah import CheetahProcessing

CrystallographyMonitor = CrystallographyProcessing
XESMonitor = XESProcessing
Cheetah = CheetahProcessing
