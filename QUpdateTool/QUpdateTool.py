import sys
import os
import signal
import platform
import argparse
import configparser
import subprocess
import psutil
import threading

from PySide6.QtWidgets import QApplication

from gui import UpdaterWindow
from threads import DownloadThread

__location__ = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))


class QUpdateTool():
    def __init__(self):
        QUpdateTool.app = QApplication(sys.argv)
        QUpdateTool.clipboard = QUpdateTool.app.clipboard()
        self.programName = "QUpdateTool"
        self.window = None
        QUpdateTool.qsoftware_logo = os.path.join(__location__, "QSoftware.png")

        self.main()


    def main(self):
        try:
            self.show_image()
            debug = "001"
            args, remaining_argv = self.parse_arguments()
            debug = "002"
            if all([value is None for value in vars(args).values()]):
                debug = "003"
                self.no_args = True
                self.show_intro()
                sys.exit()
            else:
                self.check_args(args)
                debug = "004"
                self.set_default_args(args)
                debug = "005"
                config = self.load_config(args.config)
                debug = "006"
                self.merged_args = self.merge_config_and_args(config, args)
                debug = "007"
                threading.Thread(target=self.check_running_process())
                debug = "008"
                if not self.merged_args.noGUI:
                    debug = "009"
                    self.window = UpdaterWindow(main=QUpdateTool,
                                                software_name=self.merged_args.software_to_update,
                                                current_version=self.merged_args.current_version,
                                                download_location=self.merged_args.temp_download_directory,
                                                api_endpoint=self.merged_args.download_url)
                    debug = "010"
                    self.window.closeEvent.connect(self.handle_download_finish)
                    debug = "011"

                else:
                    debug = "012"
                    self.download_update()
                    debug = "013"

        except Exception as e:
            print(f"An error occurred (main) {debug}: {str(e)}")


    def show_image(self):
        intro_image = f"""
           ____  _    _           _       _    _______          _ 
          / __ \\| |  | |         | |     | |  |__   __|        | |
         | |  | | |  | |_ __   __| | __ _| |_ ___| | ___   ___ | |
         | |  | | |  | | "_ \\ / _` |/ _` | __/ _ \\ |/ _ \\ / _ \\| |
         | |__| | |__| | |_) | (_| | (_| | ||  __/ | (_) | (_) | |
          \\___\\_\\\\____/| .__/ \\__,_|\\__,_|\\__\\___|_|\\___/ \\___/|_|
                       | |                                        
                       |_|                                        
        """
        print(intro_image)


    def show_intro(self):
        intro_text = """
        Welcome to QUpdateTool - A simple software update tool.
        Written by: Que

        Run with the following flags:

          --config-file          Path to the config file. If no path is provided, the program will search for the config 
                                 file in the root directory of the running program. The config file will be loaded as
                                 arguments, but any additional flags will overwrite the config file items. 

          (**) If the --config-file flag is NOT passed, these are required for the program to run

          --software-to-update              Name of the software to update

          --calling-pid                     PID of the program calling the updater

          --current-version                 Version number of the current program

          --noGUI                           Disable GUI (True/False). If not passed this will default FALSE.
          
          --download_url  (**)              Download URL

          --temp_download_directory (**)    Temporary download directory.

          --run_installer_as_admin          Run installer as admin (True/False). If not passed this will default TRUE.

          --run_after_download              Run after download (True/False). If not passed this will default TRUE.

          --installer_flags_msi             Installer flags for MSI Installers. If not passed this will default NONE.

        Example:
            Running Python:
                python QUpdateTool.py --software_to_update MyApp --calling_pid 12345 --current_version 1.0 --noGUI=True
            Running EXE:
                QUpdateTool.exe --software_to_update MyApp --calling_pid 12345 --current_version 1.0
        """
        print(intro_text)


    def load_config(self, config_file):
        try:
            config = configparser.ConfigParser()
            if config_file and os.path.isfile(config_file):
                config.read(config_file)
            elif "update.ini" in os.listdir(__location__):
                config.read(os.path.join(__location__, "update.ini"))
            return config
        except FileNotFoundError:
            print(f"Config file not found: {config_file}")
        except PermissionError:
            print(f"Permission error: Unable to access the update file directory - {config_file}")
        except argparse.ArgumentError as e:
            print(f"Config error: {str(e)}")
        except Exception as e:
            print(f"An unexpected error occurred while loading config: {str(e)}")


    def parse_arguments(self):
        try:
            parser = argparse.ArgumentParser(description="Updater tool for MyApp")
            parser.add_argument("--software-to-update", type=str, help="Name of the software to update")
            parser.add_argument("--calling-pid", type=int, help="PID of the program calling the updater")
            parser.add_argument("--current-version", type=str, help="Version number of the current program")
            parser.add_argument("--noGUI", help="Disable GUI")
            parser.add_argument("--config", type=str, help="Path to the config file")
            parser.add_argument("--download_url", type=str, help="Download URL")
            parser.add_argument("--temp_download_directory", type=str, help="Temporary download directory")
            parser.add_argument("--run_installer_as_admin", action=argparse.BooleanOptionalAction, help="Run installer as admin (True/False)")
            parser.add_argument("--run_after_download", action=argparse.BooleanOptionalAction, help="Run after download (True/False)")
            parser.add_argument("--installer_flags_msi", type=str, help="Installer flags for MSI")

            return parser.parse_known_args()

        except argparse.ArgumentError as e:
            print(f"Argument error: {str(e)}")
            sys.exit(1)
            

    def check_args(self, args):
        ## Required args are download_url and temp_download_directory
        if not isinstance(args.config, str):
            ## look for config file and set if needed.
            if not isinstance(args.download_url, str):
                print('You must pass a URL for the download!')
                sys.exit(1)
            if not isinstance(args.temp_download_directory, str):
                print('You must pass a temp directory for the download!')
                sys.exit(1)

    def set_default_args(self, args):
        args.noGUI = False if args.noGUI == None else args.noGUI
        args.run_installer_as_admin = True if args.run_installer_as_admin == None else args.run_installer_as_admin
        args.run_after_download = True if args.run_after_download == None else args.run_after_download


    def merge_config_and_args(self, config, args):
        config_args = dict(config.items("Updater")) if "Updater" in config.sections() else {}
        for key, value in vars(args).items():
            if value is not None:
                config_args[key] = value

        return argparse.Namespace(**config_args)


    def check_running_process(self):
        running_process = {}
        print(f"Check for running PID {self.merged_args.calling_pid}...")
        for process in psutil.process_iter(["pid", "name", "status"]):
            if (process.info["pid"] == self.merged_args.calling_pid or 
                process.info["name"].lower().replace(".exe", "") == self.merged_args.software_to_update.lower()):
                running_process = process.info

        if running_process:
            pid = running_process["pid"]
            try:
                os.kill(pid, signal.SIGTERM)
            except:
                print("Ran into issue closing PID {pid}. Please re-run update.")
                sys.exit(0)


    def download_update(self):
        print("Updating via CLI...")
        self.download_thread = DownloadThread(api_endpoint=self.merged_args.download_url,
                                              download_location=self.merged_args.temp_download_directory,
                                              gui=False)


        self.download_thread.start()
        self.download_thread.wait()
        self.handle_download_finish(self.download_thread.download_location, self.download_thread.output_file)


    def handle_download_finish(self, download_location, filename):
        if self.window:
            self.window.close()

        print("Downloaded update successfully!")
        if download_location and filename:
            update_script_path = os.path.join(download_location, filename) 
        else:
            print("Ran into issue running downloaded update.")
            sys.exit(0)

        if self.merged_args.run_after_download:
            try:
                subprocess.Popen([update_script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                #subprocess.run(update_script_path, check=True, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                sys.exit(0)
            except subprocess.CalledProcessError as e:
                print(f"An error occurred while running the installer: {str(e)}")
                sys.exit(1)
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
            print("Could not open file manager. Unsupported operating system.")


if __name__ == "__main__":
    try:
        updater = QUpdateTool()
        sys.exit(QUpdateTool.app.exec())

    except Exception as e:
        print(f"An error occurred (__name__): {str(e)}")
