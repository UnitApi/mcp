# Hardware configuration script for unitmcp on Windows
# Must be run as Administrator

# Stop on any error
$ErrorActionPreference = "Stop"

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

# Function to list available devices
function List-Devices {
    Write-Host "Available video devices:"
    Get-PnpDevice -Class Camera -Status OK | ForEach-Object {
        Write-Host "  $($_.FriendlyName)"
        Write-Host "    Device ID: $($_.InstanceId)"
        Write-Host ""
    }

    Write-Host "Available audio devices:"
    Get-PnpDevice -Class Media -Status OK | Where-Object { $_.Name -match "microphone|audio" } | ForEach-Object {
        Write-Host "  $($_.FriendlyName)"
        Write-Host "    Device ID: $($_.InstanceId)"
        Write-Host ""
    }
}

# Function to configure video device
function Configure-Video {
    param([string]$deviceId)

    Write-Host "Configuring video device: $deviceId"

    # Get device capabilities using DirectShow
    Add-Type -AssemblyName System.Drawing
    $source = New-Object DirectShowLib.FilterGraph
    $deviceFilter = New-Object DirectShowLib.CaptureGraphBuilder2
    
    try {
        $deviceFilter.SetFiltergraph($source)
        $device = [DirectShowLib.DsDevice]::GetDevicesOfCat([DirectShowLib.FilterCategory]::VideoInputDevice) | 
            Where-Object { $_.DevicePath -match $deviceId }

        if ($device) {
            $streamConfig = $device.QueryInterface([DirectShowLib.IAMStreamConfig])
            $caps = $streamConfig.GetStreamCaps()

            Write-Host "Device capabilities:"
            $caps | ForEach-Object {
                Write-Host "  Resolution: $($_.Width)x$($_.Height)"
                Write-Host "  Format: $($_.SubType)"
                Write-Host "  FPS: $($_.MaxFrameRate)"
                Write-Host ""
            }

            # Set default format (1280x720 @ 30fps)
            $defaultCap = $caps | Where-Object { 
                $_.Width -eq 1280 -and 
                $_.Height -eq 720 -and 
                $_.MaxFrameRate -ge 30 
            } | Select-Object -First 1

            if ($defaultCap) {
                $streamConfig.SetFormat($defaultCap)
                Write-Host "Set default format: 1280x720 @ 30fps"
            }
        }
    }
    finally {
        if ($deviceFilter) { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($deviceFilter) }
        if ($source) { [System.Runtime.InteropServices.Marshal]::ReleaseComObject($source) }
    }

    Write-Host "Video device configured"
}

# Function to configure audio device
function Configure-Audio {
    param([string]$deviceId)

    Write-Host "Configuring audio device: $deviceId"

    # Configure audio device using Windows Audio Session API
    Add-Type -AssemblyName System.Windows.Forms

    try {
        # Get audio device
        $device = [NAudio.Wave.WaveIn]::GetCapabilities() | 
            Where-Object { $_.ProductName -match $deviceId }

        if ($device) {
            Write-Host "Device capabilities:"
            Write-Host "  Channels: $($device.Channels)"
            Write-Host "  Supported formats:"
            
            # Test common formats
            $formats = @(
                [NAudio.Wave.WaveFormat]::CreateIeeeFloatWaveFormat(44100, 2),
                [NAudio.Wave.WaveFormat]::CreateIeeeFloatWaveFormat(48000, 2),
                [NAudio.Wave.WaveFormat]::Create(44100, 16, 2),
                [NAudio.Wave.WaveFormat]::Create(48000, 16, 2)
            )

            foreach ($format in $formats) {
                try {
                    $waveIn = New-Object NAudio.Wave.WaveIn
                    $waveIn.DeviceNumber = $device.ProductName
                    $waveIn.WaveFormat = $format
                    Write-Host "    $($format.SampleRate)Hz, $($format.BitsPerSample)bit, $($format.Channels) channels"
                }
                catch {
                    # Format not supported
                }
                finally {
                    if ($waveIn) { $waveIn.Dispose() }
                }
            }

            # Set default format (44.1kHz, 16-bit, stereo)
            Write-Host "Setting default format: 44.1kHz, 16-bit, stereo"
        }
    }
    catch {
        Write-Host "Error configuring audio device: $_"
    }

    Write-Host "Audio device configured"
}

# Function to save device configuration
function Save-Config {
    param(
        [string]$deviceType,
        [string]$deviceName,
        [hashtable]$settings
    )

    # Create config directory if needed
    $configDir = Join-Path $PROJECT_DIR "config\devices"
    if (-not (Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir | Out-Null
    }

    # Save device configuration
    $configFile = Join-Path $configDir "$deviceName.yaml"
    @"
# Device configuration for $deviceName
type: $deviceType
enabled: true
settings:
"@ | Set-Content $configFile

    # Add settings
    foreach ($key in $settings.Keys) {
        "  $key`: $($settings[$key])" | Add-Content $configFile
    }

    Write-Host "Configuration saved to: config\devices\$deviceName.yaml"
}

# Main script
switch ($args[0]) {
    "list" {
        List-Devices
    }
    "video" {
        if (-not $args[1]) {
            Write-Host "Usage: .\configure_hardware.ps1 video DEVICE_ID"
            exit 1
        }
        Configure-Video $args[1]
        Save-Config "USB_CAMERA" "camera1" @{
            "resolution" = "1280x720"
            "framerate" = "30"
            "format" = "MJPEG"
        }
    }
    "audio" {
        if (-not $args[1]) {
            Write-Host "Usage: .\configure_hardware.ps1 audio DEVICE_ID"
            exit 1
        }
        Configure-Audio $args[1]
        Save-Config "USB_MICROPHONE" "mic1" @{
            "sample_rate" = "44100"
            "channels" = "2"
            "format" = "S16_LE"
        }
    }
    "usb-audio" {
        Configure-Audio "USB"
        Save-Config "USB_MICROPHONE" "usbmic" @{
            "sample_rate" = "44100"
            "channels" = "2"
            "format" = "S16_LE"
        }
    }
    default {
        Write-Host "Usage: .\configure_hardware.ps1 COMMAND [ARGS]"
        Write-Host
        Write-Host "Commands:"
        Write-Host "  list                List available devices"
        Write-Host "  video DEVICE_ID     Configure video device"
        Write-Host "  audio DEVICE_ID     Configure audio device"
        Write-Host "  usb-audio           Configure USB audio device"
        exit 1
    }
}

Write-Host "Hardware configuration complete!"
