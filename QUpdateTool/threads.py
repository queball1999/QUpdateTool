from PySide6.QtCore import QThread, Signal

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import os
from tqdm import tqdm
import threading


class DownloadThread(QThread):
    update_progress = Signal(dict)
    finished = Signal(str)

    def __init__(self, 
                 api_endpoint: str = "",
                 download_location: str = r"",
                 gui: bool = True,
                 parent=None):
        super(DownloadThread, self).__init__(parent)
        self.api_endpoint = api_endpoint
        self.download_location = download_location
        self.gui = gui
        self.output_file = ""

        DownloadThread.session = requests.Session()
        retry_strategy = Retry(
            total=2,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=2
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        DownloadThread.session.mount("https://", adapter)
        DownloadThread.session.timeout = 2


    def run(self):
        print(f"Downloading from {self.api_endpoint}")
        response = DownloadThread.session.get(self.api_endpoint, stream=True)

        if response.status_code == 200:
            filename = response.headers.get("content-disposition", 0).replace("inline; filename=", "")
            total_size = int(response.headers.get("content-length", 0))
            self.output_file = os.path.join(self.download_location, filename)

            progress_bar = tqdm(total=total_size, unit="MB", unit_scale=True) if not self.gui else None
            progress_dict = {"unit": "MB", "n": 0, "total": total_size}

            with open(self.output_file, "wb") as file:
                bytes_count = 0
                chunk_size = 128
                for chunk in response.iter_content(chunk_size=chunk_size):
                    file.write(chunk)
                    if progress_bar:
                        threading.Thread(target=progress_bar.update, args=(len(chunk),)).start()
                        progress_dict = progress_bar.format_dict
                    else:
                        progress_dict = {"unit": "MB", "n": bytes_count, "total": total_size}
                        bytes_count += chunk_size
                    self.update_progress.emit(progress_dict)
                    #threading.Thread(target=progress_bar.update(len(chunk)))
                    #self.update_progress.emit(progress_bar.format_dict)

            if progress_bar:
                progress_bar.close()

            message = "Downloaded update successfully!"
        else:
            message = f"Error downloading file. Status code: {response.status_code}\n{response.text}" 

        self.finished.emit(message)