# Windows Setup Script for Desktop Automation Bot
# Run with Administrator Privileges

# Require Administrator Rights
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator"))
{
    Write-Warning "Please run this script as an Administrator!"
    pause
    exit
}

# Set Execution Policy to allow script execution
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# Create a log file for tracking installation
$LogFile = "$env:TEMP\desktop_bot_setup.log"
Start-Transcript -Path $LogFile

# Function to check and install Chocolatey package manager
function Install-Chocolatey {
    if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
        Write-Host "Installing Chocolatey package manager..." -ForegroundColor Cyan
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072

        try {
            Invoke-WebRequest https://chocolatey.org/install.ps1 -UseBasicParsing | Invoke-Expression

            # Refresh environment variables
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

            Write-Host "Chocolatey installed successfully!" -ForegroundColor Green
        }
        catch {
            Write-Error "Failed to install Chocolatey. Please install manually."
            exit 1
        }
    }
}

# Function to install Python
function Install-Python {
    Write-Host "Checking Python installation..." -ForegroundColor Cyan

    # Try to get Python version
    $pythonVersion = $null
    try {
        $pythonVersion = (python --version 2>&1)
    }
    catch {}

    # If Python is not installed or version is too low, install it
    if (!$pythonVersion -or !($pythonVersion -match "Python 3\.(8|9|\d{2,})")) {
        Write-Host "Installing Python 3.9..." -ForegroundColor Yellow
        choco install python --version=3.9.7 -y

        # Refresh environment variables
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    }
}

# Function to install Tesseract OCR
function Install-TesseractOCR {
    Write-Host "Installing Tesseract OCR..." -ForegroundColor Cyan
    choco install tesseract -y
}

# Function to install Git
function Install-Git {
    Write-Host "Installing Git..." -ForegroundColor Cyan
    choco install git -y
}

# Function to setup project environment
function Setup-ProjectEnvironment {
    # Project directory
    $ProjectDir = "C:\Projects\desktop-bot"

    # Create project directory
    if (!(Test-Path -Path $ProjectDir)) {
        New-Item -ItemType Directory -Force -Path $ProjectDir
    }

    # Change to project directory
    Set-Location $ProjectDir

    # Clone repository (replace with actual repository URL)
    if (!(Test-Path -Path "$ProjectDir\.git")) {
        Write-Host "Cloning desktop automation bot repository..." -ForegroundColor Cyan
        git clone https://github.com/automatyzer/desktop-bot.git .
    }

    # Create virtual environment
    Write-Host "Creating Python virtual environment..." -ForegroundColor Cyan
    python -m venv venv

    # Activate virtual environment
    .\venv\Scripts\Activate

    # Upgrade pip and setuptools
    python -m pip install --upgrade pip setuptools wheel

    # Install project dependencies
    pip install -r requirements.txt

    # Verify all requirements are installed
    pip install lxml python-dotenv apscheduler schedule requests \
                flask flask-cors flask-limiter gunicorn pytest \
                werkzeug termcolor pyautogui paramiko pytesseract \
                pillow opencv-python

    Write-Host "Project environment setup complete!" -ForegroundColor Green
}

# Main installation process
function Main {
    try {
        # Check and install Chocolatey
        Install-Chocolatey

        # Install core dependencies
        Install-Python
        Install-TesseractOCR
        Install-Git

        # Setup project environment
        Setup-ProjectEnvironment

        Write-Host "Desktop Automation Bot environment setup complete!" -ForegroundColor Green
        Write-Host "Project installed in: C:\Projects\desktop-bot" -ForegroundColor Green
        Write-Host "To activate virtual environment, run: C:\Projects\desktop-bot\venv\Scripts\Activate" -ForegroundColor Green
    }
    catch {
        Write-Error "An error occurred during setup: $_"
    }
    finally {
        Stop-Transcript
    }
}

# Run the main function
Main

# Pause to view results
pause