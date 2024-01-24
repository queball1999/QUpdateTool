import sys
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

from threads import DownloadThread

class UpdaterWindow(QWidget):
    closeEvent = Signal(str, str)
    def __init__(self,
                 main=None,
                 software_name='MyApp',
                 current_version='1.0',
                 filename="",
                 download_location=r"",
                 api_endpoint='',
                 parent=None):
        super(UpdaterWindow, self).__init__(parent)
        self.setWindowTitle("QUpdateTool")
        self.main = main
        self.software_name = software_name
        self.current_version = current_version
        self.filename = filename
        self.download_location = download_location
        self.api_endpoint = api_endpoint
        self.download_progress_data = {}

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_progress_bar)
        self.update_timer.setInterval(20)

        layout = QGridLayout()
        
        self.icon = QLabel()
        self.icon.setPixmap(QPixmap(self.main.qsoftware_logo).scaled(50, 50))
        
        self.label = QLabel(f"Updating {self.software_name} (v{self.current_version})...")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_update)

        layout.addWidget(self.icon, 0, 0, 1, 3)
        layout.addWidget(self.label, 1, 0, 1, 3)
        layout.addWidget(self.progress_bar, 2, 0, 1, 3)
        layout.addWidget(self.cancel_button, 3, 2, 1, 1)
        self.setLayout(layout)

        self.initUI()


    def download_update(self):
        self.download_thread = DownloadThread(api_endpoint=self.api_endpoint,
                                              filename=self.filename,
                                              download_location=self.download_location)

        self.download_thread.update_progress.connect(self.update_download_progress)
        self.download_thread.finished.connect(self.handle_download_finish)
        self.download_thread.start()


    def update_download_progress(self, data):
        self.download_progress_data = data
        self.update_timer.start()


    def handle_download_finish(self, message):
        self.progress_bar.setValue(100)
        self.label.setText(message)
        self.main.app.processEvents()
        QTimer.singleShot(20, lambda: self.close_window())


    def update_progress_bar(self):
        unit = self.download_progress_data['unit']
        n = self.format_size(self.download_progress_data['n'], unit)
        total_size = self.format_size(self.download_progress_data['total'], unit)
        percentage = (n / total_size) * 100
        self.progress_bar.setValue(percentage)
        self.progress_bar.setFormat(f"{percentage:.2f}% | {n:.2f}{unit}/{total_size:.0f}{unit}")
        self.main.app.processEvents()


    def format_size(self, bytes, unit):
        if unit.lower() == 'gb':
            return bytes / (1024 * 1024 * 1024)
        elif unit.lower() == 'mb':
            return bytes / (1024 * 1024)
        elif unit.lower() == 'kb':
            return bytes / 1024
        else:
            return bytes
        

    def cancel_update(self):
        self.download_thread.terminate()  # Terminate the download thread
        self.handle_download_finish("Update cancelled by user")


    def close_window(self):
        self.closeEvent.emit(self.download_location, self.filename)
        self.close()


    def set_window_size(self):
        window_width = 400
        window_height = 150
        screen = QApplication.primaryScreen()
        screen_size = screen.geometry()
        center_point = screen.geometry().center()

        horz_scaling_factor = screen.geometry().width() / screen_size.width()
        vert_scaling_factor = screen.geometry().height() / screen_size.height()
        scaling_factor = min(horz_scaling_factor, vert_scaling_factor)
        window_width = int(window_width * scaling_factor)
        window_height = int(window_height * scaling_factor)
        left = int(center_point.x() - window_width / 2)
        top = int(center_point.y() - window_height / 2)

        self.setGeometry(left, top, window_width, window_height)
        self.setFixedSize(window_width, window_height)


    def initUI(self):
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.set_window_size()
        self.show()
        self.download_update()




