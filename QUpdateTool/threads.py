from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QApplication, QLabel, QProgressBar, QVBoxLayout, QWidget
from PySide6.QtGui import QPixmap
from PySide6.QtCore import QTimer, Qt

import requests
import os
from tqdm import tqdm


class DownloadThread(QThread):
    update_progress = Signal(dict)
    finished = Signal(str)

    def __init__(self, 
                 api_endpoint: str = '',
                 filename: str = '',
                 download_location: str = r"",
                 get_latest: bool = True,
                 parent=None):
        super(DownloadThread, self).__init__(parent)
        self.api_endpoint = api_endpoint
        self.filename = filename
        self.download_location = download_location
        self.get_latest = get_latest
        self.output_file = os.path.join(self.download_location, filename)   ## will need to change is get_latest is newer and true


    def run(self):

        if self.get_latest:
            pass
            # get latest url / call
        else:
            pass
            # specific file call

        response = requests.get(self.api_endpoint + self.filename, stream=True)
        print(response.status_code)
        if response.status_code == 200:
            total_size = int(response.headers.get('content-length', 0))

            progress_bar = tqdm(total=total_size, unit='MB', unit_scale=True)

            
            with open(self.output_file, 'wb') as file:
                for chunk in response.iter_content(chunk_size=128):
                    file.write(chunk)
                    progress_bar.update(len(chunk))
                    self.update_progress.emit(progress_bar.format_dict)

            progress_bar.close()
            message = "Downloaded update successfully!"
        else:
            message = f"Error downloading file. Status code: {response.status_code}\n{response.text}" 

        print(message)
        self.finished.emit(message)