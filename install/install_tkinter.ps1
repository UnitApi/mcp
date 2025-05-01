# PowerShell script to install tkinter for Windows

Write-Host "Checking Python installation..." -ForegroundColor Cyan

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python not found. Please install Python from python.org" -ForegroundColor Red
    Write-Host "Make sure to check the 'tcl/tk and IDLE' option during installation." -ForegroundColor Yellow
    exit 1
}

# Check if tkinter is available
Write-Host "Checking tkinter installation..." -ForegroundColor Cyan
$tkinterCheck = python -c "try: import tkinter; print('Tkinter is installed'); except ImportError: print('Tkinter is NOT installed')"

if ($tkinterCheck -eq "Tkinter is installed") {
    Write-Host "Tkinter is already installed." -ForegroundColor Green
} else {
    Write-Host "Tkinter is not installed." -ForegroundColor Yellow
    Write-Host "On Windows, tkinter should be included with Python." -ForegroundColor Yellow
    Write-Host "Please reinstall Python from python.org and make sure to check the 'tcl/tk and IDLE' option during installation." -ForegroundColor Yellow
}

# Install other dependencies
Write-Host "`nInstalling Python dependencies..." -ForegroundColor Cyan
python -m pip install -r requirements.txt

Write-Host "`nInstallation complete!" -ForegroundColor Green
Write-Host "If you encounter any issues with tkinter, please refer to the documentation." -ForegroundColor Cyan
