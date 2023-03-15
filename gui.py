from PySide6.QtCore import Qt, QLocale, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QPushButton,
    QSizePolicy,
    QPlainTextEdit,
    QSplitter
)

import sys

from GUI.Utils import EmittingStream
from GUI.CustomWidgets import TimeSlider, InputDataWidget, PlotResultsWidget
from GUI.ProjectData import ProjectData
from GUI.CalculationWorker import CalculationWorker

import sys,os

class MainWindow(QMainWindow):
    calculation_requested = Signal(dict)

    def __init__(self):
        super().__init__()

        # Window title
        self.setWindowTitle("ExpressFrac Simulator")

        self.project_data = ProjectData()#мини база данных хранит результаты полученные от solvera

        # Main window layout
        page_layout = QHBoxLayout()
        self._set_input_layout(page_layout)
        self._set_results_layout(page_layout)

        container = QWidget()
        container.setLayout(page_layout)
        self.setCentralWidget(container)

    def _set_input_layout(self, page_layout):
        layout_input = QVBoxLayout()

        # ------------------------------------------------------
        # Input data form widget
        # ------------------------------------------------------
        self.input_data_widget = InputDataWidget()

        # ------------------------------------------------------
        # Update results button
        # ------------------------------------------------------
        self.start_calc_button = QPushButton("Start calculation")
        self.start_calc_button.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        self.start_calc_button.setMinimumWidth(250)

        # Create calculation thread and move worker to the thread
        self.calc_worker = CalculationWorker()
        self.calc_worker_thread = QThread(parent=self)
        self.calc_worker.moveToThread(self.calc_worker_thread)

        # Connect calculation signals to handlers
        self.start_calc_button.clicked.connect(self.calculation_start)
        self.calculation_requested.connect(self.calc_worker.run_simulation)
        self.calc_worker.progress.connect(self.calculation_results_obtained)
        self.calc_worker.completed.connect(self.calculation_completed)

        # ------------------------------------------------------
        # Assemble input layout
        # ------------------------------------------------------
        layout_input.addWidget(self.input_data_widget)
        layout_input.addWidget(self.start_calc_button)
        layout_input.addStretch()

        page_layout.addLayout(layout_input)

    def _set_results_layout(self, page_layout):
        layout_results = QVBoxLayout()

        # ------------------------------------------------------
        # Time slider widget
        # ------------------------------------------------------
        self.time_slider = TimeSlider(-1, -1, time_data=[0])
        self.time_slider.slider.valueChanged.connect(self.update_plot_widget)

        # ------------------------------------------------------
        # Plot results widget
        # ------------------------------------------------------
        self.plot_results_widget = PlotResultsWidget()

        # ------------------------------------------------------
        # Solver log
        # ------------------------------------------------------
        self.solver_log = QPlainTextEdit()
        self.solver_log.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.solver_log.setReadOnly(True)
        self.solver_log.setPlainText("sys.stdout will be printed here during calculation\n\n")

        # ------------------------------------------------------
        # Assemble results layout
        # ------------------------------------------------------
        self.plot_log_splitter = QSplitter(Qt.Vertical)
        self.plot_log_splitter.addWidget(self.plot_results_widget)
        self.plot_log_splitter.addWidget(self.solver_log)
        layout_results.addWidget(self.time_slider)
        layout_results.addWidget(self.plot_log_splitter)

        page_layout.addLayout(layout_results)

    def calculation_start(self):
        sys.stdout.write("Print before sys.stdout redirecting\n")

        # Reset saved results, solver log and plots
        self.project_data.clear_results()
        self.solver_log.clear()
        self.time_slider.reset()

        # Redirect stdout to EmittingStream
        sys.stdout = EmittingStream()
        sys.stdout.stdout_written.connect(self.update_solver_log)

        sys.stdout.write("GUI: start calculation button clicked. Emit \"calculation_requested\" signal")

        # Disable button and change text
        self.start_calc_button.setEnabled(False)
        self.start_calc_button.setText("Calculating...")
        # Start worker thread
        self.calc_worker_thread.start()

        # Generate input JSON data for calculation
        self.project_data.update_input_data(self.input_data_widget)

        # Request simulation running and pass input data
        self.calculation_requested.emit(self.project_data.input_data)

    def calculation_results_obtained(self):
        # Get obtained data from worker
        self.project_data.append_result(self.calc_worker.results)
        t = self.project_data.results_by_time[-1]["summary"]["time"]
        sys.stdout.write("GUI: Results obtained from worker. Time: {t}".format(t=t))

        # Update time slider and update plot
        self.time_slider.appendTime(t)

    def calculation_completed(self):
        sys.stdout.write("GUI: Calculation completed. Final time: {t}".format(t=self.calc_worker.results["summary"]["time"]))

        # Restore sys.stdout
        sys.stdout = sys.__stdout__
        sys.stdout.write("Print fter sys.stdout restoring\n")

        # Stop worker thread
        self.calc_worker_thread.quit()
        self.calc_worker_thread.wait()

        # Enable button and change text
        self.start_calc_button.setEnabled(True)
        self.start_calc_button.setText("Start calculation")

    def update_solver_log(self, text):
        self.solver_log.appendPlainText(text)

    def update_plot_widget(self, time_index):
        if time_index >= 0:
            self.plot_results_widget.plot_results(self.project_data, time_index)
        else:
            self.plot_results_widget.clear_plots()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    app.exec()
