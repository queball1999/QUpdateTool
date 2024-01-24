import sys
import os
import signal
import platform
import argparse
import configparser
import subprocess
import time
from tqdm import tqdm

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

from gui import UpdaterWindow
from threads import DownloadThread

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))

class QUpdateTool():
    def __init__(self):
        QUpdateTool.app = QApplication(sys.argv)
        QUpdateTool.clipboard = QUpdateTool.app.clipboard()
        self.programName = 'QUpdateTool'
        self.window = None
        QUpdateTool.qsoftware_logo = os.path.join(__location__, 'QSoftware.png')
        self.main()


    def main(self):
        self.show_intro()

        args, remaining_argv = self.parse_arguments()
        config = self.load_config(args.config_file)
        print(args, config)
        self.merged_args = self.merge_config_and_args(config, args)

        print(self.merged_args)

        if not self.merged_args.noGUI:
            self.window = UpdaterWindow(main=QUpdateTool,
                                        software_name=self.merged_args.software_to_update,
                                        current_version=self.merged_args.current_version,
                                        filename=self.merged_args.file_to_download,
                                        download_location=self.merged_args.temp_download_directory,
                                        api_endpoint=self.merged_args.download_url)
            self.window.closeEvent.connect(self.handle_download_finish)

        else:
            self.download_update()



    def show_intro(self):
        intro_image = """
           ____  _    _           _       _    _______          _ 
          / __ \| |  | |         | |     | |  |__   __|        | |
         | |  | | |  | |_ __   __| | __ _| |_ ___| | ___   ___ | |
         | |  | | |  | | '_ \ / _` |/ _` | __/ _ \ |/ _ \ / _ \| |
         | |__| | |__| | |_) | (_| | (_| | ||  __/ | (_) | (_) | |
          \___\_\\____/| .__/ \__,_|\__,_|\__\___|_|\___/ \___/|_|
                       | |                                        
                       |_|                                        
        """

        intro_text = """
        Welcome to QUpdateTool - A simple software update tool.
        Written by: Que

        Run with the following flags:
          --get_latest           Given a software-to-update string, get_latest=True will download the latest version.
                                 If you want to download an older version, run without this flag.
          --software-to-update   Name of the software to update
          --calling-pid          PID of the program calling the updater
          --current-version      Version number of the current program
          --noGUI                Disable GUI
          --config-file          Path to the config file
          --download_url         Download URL
          --file_to_download     File to download from URL
          --temp_download_directory   Temporary download directory
          --run_installer_as_admin    Run installer as admin (True/False)
          --run_after_download   Run after download (True/False)
          --installer_flags_msi  Installer flags for MSI

        Example:
            Running Python:
                python QUpdateTool.py --software_to_update MyApp --calling_pid 12345 --current_version 1.0 --GUI=True
            Running EXE:
                QUpdateTool.exe --software_to_update MyApp --calling_pid 12345 --current_version 1.0 --GUI=True
        """
        print(intro_image)
        print(intro_text)


    def load_config(self, config_file):
        config = configparser.ConfigParser()
        if config_file and os.path.isfile(config_file):
            config.read(config_file)
        elif 'update.ini' in os.listdir(__location__):
            config.read(os.path.join(__location__, 'update.ini'))
        return config


    def parse_arguments(self):
        parser = argparse.ArgumentParser(description="Updater tool for MyApp")
        parser.add_argument("--get_latest", type=str, help="Given a softare-to-update string, get_latest=True will download the latest version. If you want to download an older version, run without this flag.")
        parser.add_argument("--software-to-update", type=str, help="Name of the software to update")
        parser.add_argument("--calling-pid", type=int, help="PID of the program calling the updater")
        parser.add_argument("--current-version", type=str, help="Version number of the current program")
        parser.add_argument("--noGUI", default=False, help="Disable GUI")
        parser.add_argument("--config-file", type=str, help="Path to the config file")
        parser.add_argument('--download_url', type=str, help="Download URL")
        parser.add_argument('--file_to_download', type=str, help="File to download from URL")
        parser.add_argument('--temp_download_directory', type=str, help="Temporary download directory")
        parser.add_argument('--run_installer_as_admin', action=argparse.BooleanOptionalAction, default=True, help="Run installer as admin (True/False)")
        parser.add_argument('--run_after_download', action=argparse.BooleanOptionalAction, default=True, help="Run after download (True/False)")
        parser.add_argument('--installer_flags_msi', type=str, default=None, help="Installer flags for MSI")

        return parser.parse_known_args()



    def merge_config_and_args(self, config, args):
        config_args = dict(config.items('Updater')) if 'Updater' in config.sections() else {}
    
        for key, value in vars(args).items():
            if value is not None:
                config_args[key] = value
    
        return argparse.Namespace(**config_args)


    def download_update(self):

        self.download_thread = DownloadThread(api_endpoint=self.merged_args.download_url,
                                              filename=self.merged_args.file_to_download,
                                              download_location=self.merged_args.temp_download_directory)


        self.download_thread.start()
        self.download_thread.wait()
        self.handle_download_finish(self.download_thread.download_location, self.download_thread.filename)


    def handle_download_finish(self, download_location, filename):
        if self.merged_args.calling_pid:
            print('CALLING FROM ANOTHER APPLICATION!!!!')
            os.kill(self.merged_args.calling_pid, signal.SIGTERM)

        self.window.close()
        update_script_path = os.path.join(download_location, filename)
        if self.merged_args.run_after_download:
            subprocess.run(update_script_path, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        else:
            self.open_file_manager(download_location)


    def open_file_manager(self, directory_path):
        system = platform.system().lower()
        if system == "windows":
            subprocess.run(["explorer", directory_path])
        elif system == "linux":
            subprocess.run(["xdg-open", directory_path])
        elif system == "darwin":
            subprocess.run(["open", directory_path])
        else:
            print("Unsupported operating system")


if __name__ == "__main__":
    updater = QUpdateTool()
    sys.exit(QUpdateTool.app.exec())
