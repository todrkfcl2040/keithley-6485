from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QListWidget, QFileDialog, QLineEdit, QLabel
from PyQt5.QtCore import QTimer
import sys
import csv
import pyvisa
import time
rm = pyvisa.ResourceManager()
try:
    inst = rm.open_resource('GPIB0::14::INSTR')  # Replace 22 with actual GPIB address of 6485
    demo_mode = False
except Exception:
    inst = None
    demo_mode = True

import matplotlib.pyplot as plt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Keithley 2110 측정 프로그램")
        self.setGeometry(100, 100, 1000, 600)

        self.mode_list = QListWidget()
        self.mode_list.addItems([
            "CAP (Capacitance)", "RES (Resistance)", "IND (Inductance)",
            "COND (Conductance)", "VOLT (Voltage)", "CURR (Current)"
        ])
        self.mode_list.currentTextChanged.connect(self.change_mode)

        self.rate_label = QLabel("Sampling Rate (ms):")
        self.rate_input = QLineEdit("500")

        self.start_button = QPushButton("Start")
        self.pause_button = QPushButton("Pause")
        self.stop_button = QPushButton("Stop")
        self.save_button = QPushButton("Save CSV")
        self.reset_button = QPushButton("Reset")

        self.start_button.clicked.connect(self.start_measurement)
        self.pause_button.clicked.connect(self.pause_measurement)
        self.stop_button.clicked.connect(self.stop_measurement)
        self.save_button.clicked.connect(self.save_data)
        self.reset_button.clicked.connect(self.reset_data)

        left_layout = QVBoxLayout()
        left_layout.addWidget(self.mode_list)
        left_layout.addWidget(self.rate_label)
        left_layout.addWidget(self.rate_input)
        left_layout.addWidget(self.start_button)
        left_layout.addWidget(self.pause_button)
        left_layout.addWidget(self.stop_button)
        left_layout.addWidget(self.save_button)
        left_layout.addWidget(self.reset_button)

        self.canvas = plt.figure(figsize=(5, 4)).add_subplot(111)
        self.figure = self.canvas.figure
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
        self.plot_widget = FigureCanvasQTAgg(self.figure)

        main_layout = QHBoxLayout()
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        main_layout.addWidget(left_widget)
        main_layout.addWidget(self.plot_widget, stretch=1)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.paused = False
        self.times = []
        self.values = []
        self.start_time = None
        self.current_mode = "CAP"

        if demo_mode:
            print("Demo mode activated. No instrument connected.")
        else:
            inst.write("*RST")
            inst.write("SYST:ZCH OFF")  # Disable zero check
            inst.write("SYST:ZCOR OFF") # Disable zero correct
            inst.write("RANG:AUTO ON")  # Auto range on
            inst.write("TRIG:COUNT 1")  # One reading per trigger
            # Move these from update_plot to here
            inst.write("NPLC 0.01")         # Fastest sampling
            inst.write("AZER OFF")          # Autozero off
            inst.write("AVER:STAT OFF")     # Averaging off
            inst.write("FORM:ELEM READ")    # Read only value

    def change_mode(self, mode_text):
        mode_code = mode_text.split()[0]
        self.current_mode = mode_code
        if not demo_mode:
            inst.write(f"CONF:{mode_code}")
            if mode_code == "CAP":
                inst.write("CAP:RANG:AUTO ON")
            elif mode_code == "RES":
                inst.write("RES:RANG:AUTO ON")
            elif mode_code == "IND":
                inst.write("IND:RANG:AUTO ON")
            elif mode_code == "COND":
                inst.write("COND:RANG:AUTO ON")
            elif mode_code == "VOLT":
                inst.write("VOLT:RANG:AUTO ON")
            elif mode_code == "CURR":
                inst.write("CURR:RANG:AUTO ON")

    def start_measurement(self):
        try:
            interval = int(self.rate_input.text())
            if interval <= 0:
                raise ValueError
        except ValueError:
            print("Invalid sampling rate.")
            return
        interval = max(interval, 1)  # allow very fast sampling (1 ms minimum)
        self.timer.setInterval(interval)
        self.rate_input.setEnabled(False)

        self.start_time = time.time()
        self.times.clear()
        self.values.clear()
        if not demo_mode:
            inst.write(f"CONF:{self.current_mode}")  # Set return format
        self.timer.start(interval)

    def pause_measurement(self):
        self.paused = not self.paused

    def stop_measurement(self):
        self.timer.stop()
        self.rate_input.setEnabled(True)

    def update_plot(self):
        ylabels = {
            "CAP": "Capacitance (F)", "RES": "Resistance (Ω)", "IND": "Inductance (H)",
            "COND": "Conductance (S)", "VOLT": "Voltage (V)", "CURR": "Current (A)"
        }
        if self.paused:
            return
        if demo_mode:
            elapsed = time.time() - self.start_time
            import math
            value = math.sin(elapsed)
            self.times.append(elapsed)
            self.values.append(value)
            self.canvas.clear()
            self.canvas.plot(self.times, self.values, marker='o')
            ylabel = ylabels.get(self.current_mode, self.current_mode)
            self.canvas.set_title(f"{ylabel} vs Time")
            self.canvas.set_xlabel("Time (s)")
            self.canvas.set_ylabel(ylabel)
            self.canvas.grid(True)
            self.plot_widget.draw()
            return
        elapsed = time.time() - self.start_time
        try:
            value = float(inst.query("READ?").strip().split(',')[0])
            self.times.append(elapsed)
            self.values.append(value)
            self.canvas.clear()
            self.canvas.plot(self.times, self.values, marker='o')
            ylabel = ylabels.get(self.current_mode, self.current_mode)
            self.canvas.set_title(f"{ylabel} vs Time")
            self.canvas.set_xlabel("Time (s)")
            self.canvas.set_ylabel(ylabel)
            self.canvas.grid(True)
            self.plot_widget.draw()
        except Exception as e:
            print("Error:", e)

    def save_data(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if path:
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Time", self.current_mode])
                for t, v in zip(self.times, self.values):
                    writer.writerow([t, v])

    def reset_data(self):
        ylabels = {
            "CAP": "Capacitance (F)", "RES": "Resistance (Ω)", "IND": "Inductance (H)",
            "COND": "Conductance (S)", "VOLT": "Voltage (V)", "CURR": "Current (A)"
        }
        self.times.clear()
        self.values.clear()
        self.canvas.clear()
        self.canvas.set_title(f"Real-Time {self.current_mode} Measurement")
        self.canvas.set_xlabel("Time (s)")
        self.canvas.set_ylabel(ylabels.get(self.current_mode, self.current_mode))
        self.canvas.grid(True)
        self.plot_widget.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())