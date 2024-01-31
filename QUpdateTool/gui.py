import sys
import os
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QProgressBar, QPushButton, QGridLayout, QMessageBox
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, QTimer, Signal

from threads import DownloadThread

class UpdaterWindow(QWidget):
    closeEvent = Signal(str, str)
    def __init__(self,
                 main=None,
                 software_name="software using QUpdateTool",
                 current_version="{unknown}",
                 download_location=r"",
                 api_endpoint="",
                 parent=None):
        super(UpdaterWindow, self).__init__(parent)
        self.setWindowTitle("QUpdateTool")
        self.main = main
        self.software_name = software_name
        self.current_version = current_version
        self.download_location = download_location
        self.api_endpoint = api_endpoint
        self.download_progress_data = {}

        self.close_timer = QTimer()
        self.close_timer.timeout.connect(self.close_window)
        self.close_timer.setInterval(20)

        self.widgets()


    def widgets(self):
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
        print("Update via GUI...")
        try:
            self.download_thread = DownloadThread(api_endpoint=self.api_endpoint,
                                                  download_location=self.download_location,
                                                  gui=True)

            self.download_thread.update_progress.connect(self.update_download_progress, Qt.DirectConnection)
            self.download_thread.finished.connect(self.handle_download_finish, Qt.DirectConnection)
            self.download_thread.start()

        except Exception as e:
            response = self.main.show_message_box(icon=QMessageBox.Critical, 
                                      text="Issue loading thread to download update. Please try again\t\nIf the issue persists, contact administrator at admin@quynnbell.com.\t\n\n", 
                                      title="Download Thread Error", 
                                      buttons=QMessageBox.Retry | QMessageBox.Close,
                                      default_button=QMessageBox.Retry)

            if response == QMessageBox.Retry:
                self.download_update()


    def update_download_progress(self, data):
        self.download_progress_data = data
        self.update_progress_bar()


    def handle_download_finish(self, message):
        self.progress_bar.setValue(100)
        self.label.setText(message)
        self.main.app.processEvents()
        self.closeEvent.emit(self.download_location, self.download_thread.output_file)


    def update_progress_bar(self):
        unit = self.download_progress_data["unit"]
        n, total_size = map(lambda key: self.format_size(self.download_progress_data[key], unit), ["n", "total"])
        percentage = (n / total_size) * 100
        self.progress_bar.setValue(percentage)
        self.progress_bar.setFormat(f"{percentage:.1f}% | {n:.2f}{unit}/{total_size:.0f}{unit}")


    def format_size(self, bytes, unit):
        if unit.lower() == "gb":
            return bytes / (1024 * 1024 * 1024)
        elif unit.lower() == "mb":
            return bytes / (1024 * 1024)
        elif unit.lower() == "kb":
            return bytes / 1024
        else:
            return bytes
        

    def cancel_update(self):
        self.download_thread.terminate()
        self.download_thread.wait()

        self.filepath = os.path.join(self.download_location, "update.exe")
        if os.path.exists(self.filepath):
            os.remove(self.filepath)

        self.handle_download_finish("Update cancelled by user")
        self.close_window()


    def close_window(self):
        self.closeEvent.emit(self.download_location, "update.exe")
        self.close()


    def show_message_box(self,
                         icon: QMessageBox.Icon = QMessageBox.Information,
                         text: str = "",
                         title: str = "Error",
                         buttons: QMessageBox.button =  QMessageBox.Ok, 
                         default_button: QMessageBox.button =  QMessageBox.Ok):

        msg_box = QMessageBox()
        msg_box.setIcon(icon)
        msg_box.setText(text)
        msg_box.setWindowTitle(title)
        msg_box.setStandardButtons(buttons)
        msg_box.setDefaultButton(default_button)
        msg_box.setWindowIcon(QIcon(self.main.program_icon))
        response = msg_box.exec()

        if response == QMessageBox.Close:
            sys.exit()
            
        return response


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
        try:
            self.setWindowModality(Qt.ApplicationModal)
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
            self.set_window_size()
            self.show()
            self.download_update()

        except Exception as e:
            response = self.main.show_message_box(icon=QMessageBox.Critical, 
                                      text="Issue loading GUI window. Please try again or try running with --noGUI=True flag.\t\nIf the issue persists, contact administrator at admin@quynnbell.com.\t\n\n", 
                                      title="Window Error", 
                                      buttons=QMessageBox.Retry | QMessageBox.Close,
                                      default_button=QMessageBox.Retry)

            if response == QMessageBox.Retry:
                self.initUI()   




