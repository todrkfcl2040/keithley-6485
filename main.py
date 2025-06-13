from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QListWidget, QFileDialog, QLineEdit, QLabel
from PyQt5.QtCore import QTimer
import sys
import csv
import pyvisa
import time
rm = pyvisa.ResourceManager()
try:
    inst = rm.open_resource('USB0::0x05E6::0x2110::8014482::INSTR')
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
        self.mode_list.addItems(["CAP (Capacitance)", "RES (Resistance)", "IND (Inductance)", "COND (Conductance)"])
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
            inst.write("CONF:CAP")
            inst.write("CAP:RES 0.00001")
            inst.write("CAP:RANG:AUTO ON")

    def change_mode(self, mode_text):
        mode_code = mode_text.split()[0]
        self.current_mode = mode_code
        if not demo_mode:
            inst.write(f"CONF:{mode_code}")
            if mode_code == "CAP":
                inst.write("CAP:RANG:AUTO ON")

    def start_measurement(self):
        try:
            interval = int(self.rate_input.text())
            if interval <= 0:
                raise ValueError
        except ValueError:
            print("Invalid sampling rate.")
            return
        self.timer.setInterval(interval)
        self.rate_input.setEnabled(False)

        self.start_time = time.time()
        self.times.clear()
        self.values.clear()
        if not demo_mode:
            inst.write(f"CONF:{self.current_mode}")
        self.timer.start(interval)

    def pause_measurement(self):
        self.paused = not self.paused

    def stop_measurement(self):
        self.timer.stop()
        self.rate_input.setEnabled(True)

    def update_plot(self):
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
            self.canvas.set_title(f"Real-Time {self.current_mode} Measurement")
            self.canvas.set_xlabel("Time (s)")
            self.canvas.set_ylabel(f"{self.current_mode}")
            self.canvas.grid(True)
            self.plot_widget.draw()
            return
        elapsed = time.time() - self.start_time
        try:
            value = float(inst.query("READ?").strip())
            self.times.append(elapsed)
            self.values.append(value)
            self.canvas.clear()
            self.canvas.plot(self.times, self.values, marker='o')
            self.canvas.set_title(f"Real-Time {self.current_mode} Measurement")
            self.canvas.set_xlabel("Time (s)")
            self.canvas.set_ylabel(f"{self.current_mode}")
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
        self.times.clear()
        self.values.clear()
        self.canvas.clear()
        self.canvas.set_title(f"Real-Time {self.current_mode} Measurement")
        self.canvas.set_xlabel("Time (s)")
        self.canvas.set_ylabel(f"{self.current_mode}")
        self.canvas.grid(True)
        self.plot_widget.draw()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())