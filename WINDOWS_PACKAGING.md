# Creating a Windows Executable for SnapAI

This guide explains how to package SnapAI into a single `.exe` file for easy distribution on Windows.

## Prerequisites

1.  **Windows Environment**: You must run these steps on a Windows machine.
2.  **Python Installed**: Ensure Python 3.8+ is installed and added to your PATH.
3.  **Visual C++ Redistributable**: Usually installed on most Windows systems.

## Step-by-Step Instructions

### 1. Set up the Environment
Open a terminal (PowerShell or CMD) in the `SnapAI` directory and run:

```powershell
./setup_venv.bat
.venv\Scripts\activate
```

### 2. Install PyInstaller
PyInstaller is the tool used to bundle the Python application:

```powershell
pip install pyinstaller
```

### 3. Build the Executable
Run PyInstaller using the provided `.spec` file. This file contains all the necessary configurations (assets, hidden imports, etc.):

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --clean snapai.spec
```

### 4. Locate your Application
Once the build process completes:
-   The final `.exe` will be located in the **`dist/`** folder.
-   The name of the file will be **`SnapAI.exe`**.

## How it Works
The bundled executable includes:
-   The Python interpreter.
-   All required libraries (PyQt5, Flask, etc.).
-   Web assets (templates/static).
-   The SnapAI logic.

When you run `SnapAI.exe`, it will automatically spawn the internal server and client components just like `python main.py` does in development.

## Troubleshooting
-   **Missing Modules**: If the app fails to start, check the `hiddenimports` list in `snapai.spec`.
-   **Antivirus**: Some antivirus software may flag PyInstaller-generated executables as false positives. You may need to whitelist the application.
