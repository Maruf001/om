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
OM's Radial Profile Viewer.


"""
import collections
import copy
import signal
import sys
import time
from typing import Any, Deque, Dict, Union

import click
import numpy  # type: ignore
from om.graphical_interfaces import base as graph_interfaces_base
from om.utils import exceptions

try:
    from PyQt5 import QtCore, QtGui, QtWidgets  # type: ignore
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


class CrystallographyRAViewer(graph_interfaces_base.OmGui):
    """
    See documentation of the `__init__` function.

    Base class: [`OmGui`][om.graphical_interfaces.base.OmGui]
    """

    def __init__(self, url: str):
        """
        OM frame viewer for crystallography.

        This class implements a radial average viewer for crystallography experiments.
        It is a subclass of the [OmGui][om.graphical_interfaces.base.OmGui] base class.

        Arguments:

            url (str): the URL at which the GUI will connect and listen for data. This
                must be a string in the format used by the ZeroMQ Protocol.
        """
        super(CrystallographyRAViewer, self).__init__(
            url=url,
            tag=u"view:omradialaverage",
        )

        self._frame_list: Deque[Dict[str, Any]] = collections.deque(maxlen=20)
        self._current_frame_index: int = -1

        self._received_data: Dict[str, Any] = {}

        pyqtgraph.setConfigOption("background", 0.2)

        self._plot_widget: Any = pyqtgraph.GraphicsLayoutWidget()
        self._plot = self._plot_widget.addPlot(title="Radial average")
        self._plot_line: Any = self._plot.plot()

        self._back_button: Any = QtWidgets.QPushButton(text="Back")
        self._back_button.clicked.connect(self._back_button_clicked)

        self._forward_button: Any = QtWidgets.QPushButton(text="Forward")
        self._forward_button.clicked.connect(self._forward_button_clicked)

        self._play_pause_button: Any = QtWidgets.QPushButton(text="Pause")
        self._play_pause_button.clicked.connect(self._play_pause_button_clicked)

        self._horizontal_layout: Any = QtWidgets.QHBoxLayout()
        self._horizontal_layout.addWidget(self._back_button)
        self._horizontal_layout.addWidget(self._forward_button)
        self._horizontal_layout.addWidget(self._play_pause_button)
        self._vertical_layout: Any = QtWidgets.QVBoxLayout()
        self._vertical_layout.addWidget(self._plot_widget)
        self._vertical_layout.addLayout(self._horizontal_layout)
        self._central_widget: Any = QtWidgets.QWidget()
        self._central_widget.setLayout(self._vertical_layout)
        self.setCentralWidget(self._central_widget)

        self.show()

    def _update_plot(self) -> None:
        # Updates the image and Bragg peaks shown by the viewer.

        try:
            current_data: numpy.ndarray = self._frame_list[self._current_frame_index]
        except IndexError:
            # If the framebuffer is empty, returns without drawing anything.
            return

        QtWidgets.QApplication.processEvents()

        self._plot_line.setData(
            numpy.arange(len(current_data["radial_average"])),
            current_data["radial_average"],
        )

        QtWidgets.QApplication.processEvents()

        # Computes the estimated age of the received data and prints it into the status
        # bar (a GUI is supposed to be a Qt MainWindow widget, so it is supposed to
        # have a status bar).
        timenow: float = time.time()
        self.statusBar().showMessage(
            "Estimated delay: {0} seconds".format(
                round(timenow - current_data["timestamp"], 6)
            )
        )

    def update_gui(self) -> None:
        """
        Updates the elements of the Crystallography Frame Viewer.

        This method overrides the corresponding method of the base class: please also
        refer to the documentation of that class for more information.

        This function stores the data received from OM, and calls the internal
        functions that update the displayed detector frame and the detected peaks.
        """
        # Makes sure that the data shown by the viewer is updated if data is
        # received.

        if self._received_data:
            # Resets the 'received_data' attribute to None. One can then check if
            # data has been received simply by checking wether the attribute is not
            # False.
            local_data = self._received_data
            self._received_data = {}
        else:
            # If no data has been received, returns without drawing anything.
            return

        self._frame_list.append(copy.deepcopy(local_data))
        self._current_frame_index = len(self._frame_list) - 1

        self._update_plot()

    def _back_button_clicked(self) -> None:
        # Manages clicks on the 'back' button.
        self._stop_stream()
        if self._current_frame_index > 0:
            self._current_frame_index -= 1
        print("Showing frame {0} in the buffer".format(self._current_frame_index))
        self._update_plot()

    def _forward_button_clicked(self) -> None:
        # Manages clicks on the 'forward' button.
        self._stop_stream()
        if (self._current_frame_index + 1) < len(self._frame_list):
            self._current_frame_index += 1
        print("Showing frame {0} in the buffer".format(self._current_frame_index))
        self._update_plot()

    def _stop_stream(self) -> None:
        # Disconnects from the OM monitor and stops receiving data.
        if self.listening:
            self._play_pause_button.setText("Play")
            self.stop_listening()

    def _start_stream(self) -> None:
        # Connects to the the OM monitor and starts receiving data.
        if not self.listening:
            self._play_pause_button.setText("Pause")
            self.start_listening()

    def _play_pause_button_clicked(self) -> None:
        # Manages clicks on the 'play/pause' button.
        if self.listening:
            self._stop_stream()
        else:
            self._start_stream()


@click.command()
@click.argument("url", type=str, required=False)
def main(url: str) -> None:
    """
    OM Frame Viewer for Crystallography. This program must connect to a running OnDA
    Monitor for Crystallography. If the monitor broadcasts detector frame data, this
    viewer will display it. The viewer will also show, overlayed on the frame data,
    any detected Bragg peak. The data stream from the monitor can also be temporarily
    paused, and any of 10 most recently displayed detector frames can be recalled for
    inspection.

    The viewer connects to and OnDA Monitor running at the IP address (or hostname)
    specified by the URL string. This is a string in the format used by the ZeroMQ
    Protocol. The URL string is optional. If not provided, it defaults to
    "tcp://127.0.0.1:12321" and the viewer connects, using the tcp protocol, to a
    monitor running on the local machine at port 12321.
    """
    # This function is turned into a script by the Click library. The docstring
    # above becomes the help string for the script.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    if url is None:
        url = "tcp://127.0.0.1:12321"
    app: Any = QtWidgets.QApplication(sys.argv)
    _ = CrystallographyRAViewer(url)
    sys.exit(app.exec_())
