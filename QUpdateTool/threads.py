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
                 parent=None):
        super(DownloadThread, self).__init__(parent)
        self.api_endpoint = api_endpoint
        self.download_location = download_location
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
        """
        DownloadThread.headers = {"Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.main.api_token}"
            }
        """


    def run(self):
        print(f"Downloading from {self.api_endpoint}")
        response = DownloadThread.session.get(self.api_endpoint, stream=True)

        if response.status_code == 200:
            filename = response.headers.get("content-disposition", 0).replace("inline; filename=", "")
            total_size = int(response.headers.get("content-length", 0))
            self.output_file = os.path.join(self.download_location, filename)
            progress_bar = tqdm(total=total_size, unit="MB", unit_scale=True)
            
            with open(self.output_file, "wb") as file:
                for chunk in response.iter_content(chunk_size=128):
                    file.write(chunk)
                    threading.Thread(target=progress_bar.update(len(chunk)))
                    self.update_progress.emit(progress_bar.format_dict)

            progress_bar.close()
            message = "Downloaded update successfully!"
        else:
            message = f"Error downloading file. Status code: {response.status_code}\n{response.text}" 

        self.finished.emit(message)