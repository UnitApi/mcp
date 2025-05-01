# Desktop Automation Bot - linux environment Setup Scripts

## Overview

These scripts automate the setup of the desktop automation bot environment on different Linux distributions.

## Prerequisites

- A Linux system (Ubuntu or Fedora)
- `sudo` access
- Internet connection

## Supported Distributions

- Ubuntu 20.04 and newer
- Fedora 33 and newer

## Usage

### Ubuntu

```bash
# Download the script
wget https://raw.githubusercontent.com/automatyzer/desktop-bot/main/ubuntu_setup.sh

# Make executable
chmod +x ubuntu_setup.sh

# Run with sudo
sudo bash ubuntu_setup.sh
```

### Fedora

```bash
# Download the script
wget https://raw.githubusercontent.com/automatyzer/desktop-bot/main/fedora_setup.sh

# Make executable
chmod +x fedora_setup.sh

# Run with sudo
sudo bash fedora_setup.sh
```

## What the Scripts Do

1. Update system packages
2. Install system dependencies
3. Install Python and virtual environment
4. Clone the desktop automation bot repository
5. Setup Python virtual environment
6. Install Python dependencies
7. Configure system for GUI automation

## Post-Installation

After running the script:
- The project is installed in `/opt/desktop-bot`
- A virtual environment is created
- Activate the environment with: 
  ```bash
  source /opt/desktop-bot/venv/bin/activate
  ```

## Troubleshooting

- Ensure you have `sudo` access
- Check internet connection
- Verify Python 3.8+ is installed
- If any dependency fails, you may need to install it manually

## Security Notes

- Review the script before running
- Only download from trusted sources
- The script requires root access, so use caution

## Customization

Modify the scripts to:
- Change installation directory
- Add/remove specific dependencies
- Adjust Python version

## Contributing

- Report issues on the GitHub repository
- Submit pull requests with improvements

## License

# Windows 


# Desktop Automation Bot - Windows Setup Guide

## Prerequisites

- Windows 10 or Windows 11
- Administrator access
- Internet connection

## Installation Methods

### Method 1: PowerShell Script (Recommended)

1. **Download the Script**
   - Right-click on [windows_setup.ps1 link]
   - Select "Save link as..."
   - Save to a known location (e.g., Downloads folder)

2. **Run PowerShell as Administrator**
   - Press `Win + X`
   - Select "Windows PowerShell (Admin)"

3. **Execute Setup Script**
   ```powershell
   # Navigate to script location
   cd C:\Users\automatyzer\Downloads

   # Allow script execution
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

   # Run the script
   .\windows_setup.ps1
   ```

### Method 2: Manual Installation

#### Install Dependencies Manually

1. **Install Chocolatey Package Manager**
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force
   [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
   iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
   ```

2. **Install Core Dependencies**
   ```powershell
   # Install Python
   choco install python --version=3.9.7 -y

   # Install Tesseract OCR
   choco install tesseract -y

   # Install Git
   choco install git -y
   ```

3. **Create Project Environment**
   ```powershell
   # Create project directory
   mkdir C:\Projects\desktop-bot
   cd C:\Projects\desktop-bot

   # Clone repository
   git clone https://github.com/automatyzer/desktop-bot.git .

   # Create virtual environment
   python -m venv venv
   .\venv\Scripts\Activate

   # Install dependencies
   pip install -r requirements.txt
   ```

## Post-Installation

### Activate Virtual Environment
```powershell
# Navigate to project directory
cd C:\Projects\desktop-bot

# Activate virtual environment
.\venv\Scripts\Activate
```

### Run the Application
```powershell
# With virtual environment activated
python app.py
```

## Troubleshooting

### Common Issues

1. **Script Execution Policy**
   - Ensure you run PowerShell as Administrator
   - Use `Set-ExecutionPolicy RemoteSigned`

2. **Python Not Recognized**
   - Restart PowerShell after installation
   - Verify Python installation: `python --version`

3. **Dependency Installation Fails**
   - Check internet connection
   - Ensure you have the latest pip: `python -m pip install --upgrade pip`

## System Requirements

- Minimum Python Version: 3.8
- Recommended: Python 3.9+
- At least 2 GB RAM
- 500 MB free disk space

## Security Notes

- Only download scripts from trusted sources
- Review script contents before execution
- Use a dedicated project user if possible

## Customization

- Modify `windows_setup.ps1` to:
  - Change Python version
  - Adjust installation paths
  - Add/remove specific dependencies

## Contributing

- Report issues on GitHub
- Submit pull requests with improvements

## License

## Support

- Check project documentation
- Open GitHub issues for specific problems