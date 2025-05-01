# Installation script for Windows systems
# Must be run as Administrator

# Stop on any error
$ErrorActionPreference = "Stop"

Write-Host "Installing unitmcp on Windows"

# Get script directory
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$PROJECT_DIR = Split-Path -Parent $SCRIPT_DIR

# Function to check if running as Administrator
function Test-Administrator {
    $user = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($user)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Check for Administrator privileges
if (-not (Test-Administrator)) {
    Write-Host "Please run this script as Administrator"
    exit 1
}

# Function to check if winget is available
function Test-Winget {
    try {
        winget --version | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Function to check if a program is installed
function Test-ProgramInstalled {
    param([string]$program)
    return (Get-Command $program -ErrorAction SilentlyContinue)
}

# Install winget if not present
if (-not (Test-Winget)) {
    Write-Host "Installing winget..."
    Start-Process "ms-appinstaller:?source=https://aka.ms/getwinget"
    Read-Host "Please install winget from the Microsoft Store, then press Enter to continue"
}

# Install system dependencies
Write-Host "Installing system dependencies..."

# Install Python if not present
if (-not (Test-ProgramInstalled python)) {
    Write-Host "Installing Python..."
    winget install -e --id Python.Python.3.11
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# Install Git if not present
if (-not (Test-ProgramInstalled git)) {
    Write-Host "Installing Git..."
    winget install -e --id Git.Git
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# Install Visual Studio Build Tools
Write-Host "Installing Visual Studio Build Tools..."
winget install -e --id Microsoft.VisualStudio.2022.BuildTools --override "--wait --quiet --add Microsoft.VisualStudio.Component.VC.Tools.x86.x64"

# Install FFmpeg
if (-not (Test-ProgramInstalled ffmpeg)) {
    Write-Host "Installing FFmpeg..."
    winget install -e --id Gyan.FFmpeg
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# Install OpenCV dependencies
Write-Host "Installing OpenCV dependencies..."
pip install opencv-python

# Create virtual environment
Write-Host "Creating Python virtual environment..."
python -m venv "$PROJECT_DIR\.venv"
& "$PROJECT_DIR\.venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..."
python -m pip install --upgrade pip

# Install Python dependencies
Write-Host "Installing Python dependencies..."
pip install -r "$PROJECT_DIR\requirements.txt"

# Install development dependencies if present
if (Test-Path "$PROJECT_DIR\requirements-dev.txt") {
    Write-Host "Installing development dependencies..."
    pip install -r "$PROJECT_DIR\requirements-dev.txt"
}

# Install the package in development mode
Write-Host "Installing unitmcp package..."
pip install -e "$PROJECT_DIR"

# Configure hardware if script exists
if (Test-Path "$SCRIPT_DIR\configure_hardware.ps1") {
    Write-Host "Configuring hardware..."
    & "$SCRIPT_DIR\configure_hardware.ps1" list
}

# Install models if needed
if (Test-Path "$SCRIPT_DIR\install_models.ps1") {
    Write-Host "Installing AI models..."
    & "$SCRIPT_DIR\install_models.ps1"
}

# Setup service if needed
if (Test-Path "$SCRIPT_DIR\setup_service.ps1") {
    Write-Host "Setting up system service..."
    & "$SCRIPT_DIR\setup_service.ps1"
}

# Configure Windows permissions
Write-Host "Configuring Windows permissions..."

# Enable camera access for apps
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\webcam" -Name "Value" -Value "Allow"

# Enable microphone access for apps
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\microphone" -Name "Value" -Value "Allow"

Write-Host "Installation complete!"
Write-Host
Write-Host "To activate the virtual environment, run:"
Write-Host "& '$PROJECT_DIR\.venv\Scripts\Activate.ps1'"
Write-Host
Write-Host "Important Notes:"
Write-Host "1. Make sure to grant camera and microphone permissions in Windows Settings"
Write-Host "2. You may need to restart your terminal for PATH changes to take effect"
Write-Host
Write-Host "To configure specific hardware devices, use:"
Write-Host "& '$SCRIPT_DIR\configure_hardware.ps1' [video|audio|usb-audio] [device]"
