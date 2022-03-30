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
OM's GUI for Crystallography.

This module contains a graphical interface that displays reduced and aggregated data in
serial crystallography experiments.
"""
import signal
import sys
import time
from typing import Any, Dict, List, Tuple, Union

import click
import numpy
from numpy.typing import NDArray
from scipy import constants  # type: ignore

from om.graphical_interfaces import base as graph_interfaces_base
from om.utils import exceptions

try:
    from PyQt5 import QtCore, QtGui, QtWidgets
except ImportError:
    raise exceptions.OmMissingDependencyError(
        "The following required module cannot be imported: PyQt5"
    )

try:
    import pyqtgraph  # type: ignore
except ImportError:
    raise exceptions.OmMissingDependencyError(
        "The following required module cannot be imported: pyqtgraph"
    )


class SpiGui(graph_interfaces_base.OmGui):
    """
    See documentation of the `__init__` function.
    """

    def __init__(self, *, url: str) -> None:
        """
        OM graphical user interface for crystallography.

        This class implements a graphical user interface for serial crystallography
        experiments. The GUI receives reduced and aggregated data from an OnDA Monitor,
        but only when it is tagged with the `view:omdata` label. The data
        must contain information about the position of detected Bragg peaks, together
        with information about the current hit rate. The GUI will then display a plot
        showing the evolution of the hit rate over time, plus a virtual powder pattern
        generated using the positions of the detected Bragg peaks on the detector .

        Arguments:

            url: The URL at which the GUI will connect and listen for data. This must
                be a string in the format used by the ZeroMQ protocol.
        """
        super(SpiGui, self).__init__(
            url=url,
            tag="omdata",
        )

        self._received_data: Dict[str, Any] = {}

        pyqtgraph.setConfigOption("background", 0.2)

        self._hit_rate_plot_widget: Any = pyqtgraph.PlotWidget()
        self._hit_rate_plot_widget.setTitle("Hit Rate vs. Events")
        self._hit_rate_plot_widget.setLabel(axis="bottom", text="Events")
        self._hit_rate_plot_widget.setLabel(axis="left", text="Hit Rate")
        self._hit_rate_plot_widget.showGrid(x=True, y=True)
        self._hit_rate_plot_widget.setYRange(0, 100.0)
        self._hit_rate_plot: Any = self._hit_rate_plot_widget.plot(
            tuple(range(-5000, 0)), [0.0] * 5000
        )
        self._hit_rate_plot_dark: Any = None

        vertical_layout: Any = QtWidgets.QVBoxLayout()
        vertical_layout.addWidget(self._hit_rate_plot_widget)
        self._central_widget: Any = QtWidgets.QWidget()
        self._central_widget.setLayout(vertical_layout)
        self.setCentralWidget(self._central_widget)
        self.show()

    def update_gui(self) -> None:
        """
        Updates the elements of the Crystallography GUI.

        This method overrides the corresponding method of the base class: please also
        refer to the documentation of that class for more information.

        This method, which is executed at regular intervals, calls the internal
        functions that update the hit rate history plot and the virtual powder pattern.
        """

        if self._received_data:
            # Resets the 'received_data' attribute to None. One can then check if
            # data has been received simply by checking wether the attribute is not
            # None.
            local_data = self._received_data
            self._received_data = {}
        else:
            # If no data has been received, returns without drawing anything.
            return

        QtWidgets.QApplication.processEvents()

        self._hit_rate_plot.setData(
            tuple(range(-5000, 0)), local_data["hit_rate_history"]
        )

        QtWidgets.QApplication.processEvents()

        # Computes the estimated age of the received data and prints it into the status
        # bar (a GUI is supposed to be a Qt MainWindow widget, so it is supposed to
        # have a status bar).
        timenow: float = time.time()
        estimated_delay: float = round(timenow - local_data["timestamp"], 6)
        self.statusBar().showMessage(f"Estimated delay: {estimated_delay}")


@click.command()
@click.argument("url", type=str, required=False)
def main(*, url: str) -> None:
    """
    OM Graphical User Interface for Crystallography. This program must connect to a
    running OnDA Monitor for Crystallography. If the monitor broadcasts the necessary
    information, this GUI will display the evolution of the hit rate over time, plus a
    real-time virtual powder pattern created using the positions, on the detector, of
    the detected Bragg peaks

    The GUI connects to and OnDA Monitor running at the IP address (or hostname)
    specified by the URL string. This is a string in the format used by the ZeroMQ
    protocol. The URL string is optional. If not provided, it defaults to
    "tcp://127.0.0.1:12321": the GUI will connect, using the tcp protocol, to a monitor
    running on the local machine at port 12321.
    """
    # This function is turned into a script by the Click library. The docstring
    # above becomes the help string for the script.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    if url is None:
        url = "tcp://127.0.0.1:12321"
    app: Any = QtWidgets.QApplication(sys.argv)
    _ = SpiGui(url=url)
    sys.exit(app.exec_())