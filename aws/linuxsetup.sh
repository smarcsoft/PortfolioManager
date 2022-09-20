#!/bin/bash
echo "Creating python virtual environment..."
python3.10 -m venv smarcsoft
source smarcsoft/bin/activate
echo "Make 3.10 the default python"
ln -fs /usr/local/bin/python3.10 smarcsoft/bin/python3
echo "Upgrading pip..."
python -m pip install --upgrade pip
echo "Installing EOD..."
python -m pip install eod
echo "Installing pyodbc..."
python -m pip install pyodbc
echo "Creating log directory..."
mkdir -p ../backend/log
