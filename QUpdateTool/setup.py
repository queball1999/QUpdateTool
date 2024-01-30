import sys
from cx_Freeze import setup, Executable

# Create an executable from your .pyc file
executables = [Executable(script="QUpdateTool.py")]

setup(
    name="QUpdateTool",
    version="1.0",
    description="A simple CLI/GUI update tool",
    executables=executables,
)