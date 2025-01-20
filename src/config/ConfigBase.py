import os

import yaml


class Config:
    def __init__(self):
        self.cached = 0
        # Update the file path if necessary
        self.file = os.path.join(os.path.dirname(__file__), 'config.yaml')
        self.config = {}

    def getConfig(self):
        # Check the modification time of the file
        stamp = os.stat(self.file).st_mtime

        # Load the config file if it has been modified since last load
        if stamp != self.cached:
            self.cached = stamp

            try:
                # Using a context manager to open the file
                with open(self.file, 'r') as f:
                    self.config = yaml.safe_load(f)  # Load the YAML configuration
            except FileNotFoundError:
                print(f"Configuration file '{self.file}' not found.")
                self.config = {}  # Or handle it as needed
            except yaml.YAMLError as exc:
                print(f"Error parsing YAML file: {exc}")
                self.config = {}  # Or handle it as needed

        return self.config