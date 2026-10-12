# SPDX-License-Identifier: GPL-2.0-or-later
"""Responsive engine downloads using the same installer as Processing."""

from __future__ import annotations

from qgis.core import (
    QgsApplication,
    QgsProcessingAlgRunnerTask,
    QgsProcessingContext,
    QgsProcessingFeedback,
)
from qgis.PyQt.QtCore import QCoreApplication, Qt, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

_CONTEXT = "GeoCompEngineInstall"


def _tr(text: str) -> str:
    return QCoreApplication.translate(_CONTEXT, text)


class InstallFeedback(QgsProcessingFeedback):
    """Worker updates arrive at widgets through queued Qt signals."""

    status_changed = pyqtSignal(str)
    busy_changed = pyqtSignal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.error = ""
        self.warnings: list[str] = []

    def setProgressText(self, text: str) -> None:
        super().setProgressText(text)
        self.status_changed.emit(text)

    def setBusy(self, busy: bool) -> None:
        self.busy_changed.emit(busy)

    def reportError(self, error: str, fatalError: bool = False) -> None:  # noqa: N803 -- QGIS interface
        self.error = error
        super().reportError(error, fatalError)

    def pushWarning(self, warning: str) -> None:
        self.warnings.append(warning)
        super().pushWarning(warning)


class EngineInstallDialog(QDialog):
    """Download, verify, install and check an engine without blocking the UI."""

    installation_changed = pyqtSignal()

    def __init__(self, engine: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.engine = engine
        self._task = None
        self._context = None
        self._feedback = None
        name = "DynAdjust" if engine == "dynadjust" else "RTKLIB"
        self.setWindowTitle(_tr("Download %1").replace("%1", name))
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setMinimumWidth(480)
        layout = QVBoxLayout(self)
        description = QLabel(
            _tr("Downloads the verified release into your QGIS profile, checks its checksum, "
                "installs it and checks that it runs."), self,
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        self._licence = QCheckBox(
            _tr("I understand that DynAdjust is a separate program under its own licence"), self,
        )
        if engine == "dynadjust":
            description.setText(description.text() + " " + _tr(
                "DynAdjust is by Geoscience Australia, under the Apache-2.0 licence."
            ))
            layout.addWidget(self._licence)
        else:
            self._licence.hide()
            description.setText(description.text() + " " + _tr(
                "RTKLIB is under the BSD-2-Clause licence. This downloads a prebuilt "
                "executable for your operating system; no compiler is required."
            ))
        self.status = QLabel(_tr("Ready to download."), self)
        self.status.setObjectName("geocompInstallStatus")
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.status)
        self.progress = QProgressBar(self)
        self.progress.setObjectName("geocompInstallProgress")
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        buttons = QHBoxLayout()
        self.download = QPushButton(_tr("Download"), self)
        self.download.setObjectName("geocompStartDownload")
        self.download.setEnabled(engine != "dynadjust")
        self._licence.toggled.connect(self.download.setEnabled)
        self.download.clicked.connect(self.start)
        self.cancel = QPushButton(_tr("Close"), self)
        self.cancel.clicked.connect(self.reject)
        buttons.addWidget(self.download)
        buttons.addWidget(self.cancel)
        layout.addLayout(buttons)

    @property
    def busy(self) -> bool:
        return self._task is not None

    def start(self) -> None:
        if self.busy or (self.engine == "dynadjust" and not self._licence.isChecked()):
            return
        algorithm = QgsApplication.processingRegistry().algorithmById("geocomp:project_install_engine")
        if algorithm is None:
            self.status.setText(_tr("The engine installer is unavailable. Enable the GeoComp provider."))
            return
        self.download.setEnabled(False)
        self._licence.setEnabled(False)
        self.cancel.setText(_tr("Cancel"))
        self.progress.setRange(0, 0)
        self.status.setText(_tr("Preparing the download…"))
        # Context and feedback must stay alive until the task has finished.
        self._context = QgsProcessingContext()
        self._feedback = InstallFeedback()
        self._feedback.status_changed.connect(self.status.setText)
        self._feedback.busy_changed.connect(self._set_busy_progress)
        self._feedback.progressChanged.connect(self._set_progress)
        parameters = {"ENGINE": 0 if self.engine == "dynadjust" else 1,
                      "ACKNOWLEDGE_LICENCE": self._licence.isChecked()}
        self._task = QgsProcessingAlgRunnerTask(algorithm, parameters, self._context, self._feedback)
        self._task.executed.connect(self._finished)
        QgsApplication.taskManager().addTask(self._task)

    def _set_busy_progress(self, busy: bool) -> None:
        self.progress.setRange(0, 0 if busy else 100)

    def _set_progress(self, value: float) -> None:
        self.progress.setValue(round(value))

    def _finished(self, successful: bool, results: dict) -> None:
        cancelled = self._feedback.isCanceled()
        self._task = None
        self.progress.setRange(0, 100)
        self.cancel.setText(_tr("Close"))
        self.cancel.setEnabled(True)
        self._licence.setEnabled(True)
        if cancelled:
            self.status.setText(_tr("Download cancelled."))
        elif successful:
            self.progress.setValue(100)
            self.status.setText(
                _tr("Installed version %1 in %2. The program runs successfully.")
                .replace("%1", str(results["OUTPUT_VERSION"]))
                .replace("%2", str(results["OUTPUT_DIRECTORY"]))
            )
            if self._feedback.warnings:
                self.status.setText(self.status.text() + "\n" + "\n".join(self._feedback.warnings))
        else:
            self.status.setText(self._feedback.error or _tr("Installation failed. See the GeoComp log."))
        self.download.setEnabled(not successful or cancelled)
        self.installation_changed.emit()

    def reject(self) -> None:
        if self.busy:
            self._feedback.cancel()
            self._task.cancel()
            self.cancel.setEnabled(False)
            self.status.setText(_tr("Cancelling; waiting for the background work to stop…"))
        else:
            super().reject()

    def closeEvent(self, event) -> None:
        if self.busy:
            self.reject()
            event.ignore()
        else:
            super().closeEvent(event)
