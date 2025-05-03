# Music Player Guide: Using the Orchestrator Shell

This guide explains how to play music on a Raspberry Pi speaker using the UnitMCP orchestrator shell with a configuration file.

## Overview

The `music_player.py` example allows you to play music files on a Raspberry Pi using a YAML configuration file to specify the playlist and settings. The orchestrator shell makes it easy to transfer your configuration and music files from your PC to the Raspberry Pi and run the player remotely.

## Prerequisites

1. A Raspberry Pi with UnitMCP installed
2. Audio output device (headphones, speakers) connected to the Raspberry Pi
3. Music files (MP3, WAV, OGG, or FLAC format)
4. UnitMCP orchestrator shell running on your PC

## Step 1: Prepare Your Configuration File

The configuration file (`music_config.yaml`) specifies your playlist and audio settings:

```yaml
# Music Player Configuration
music_dir: "./music"
output_device: "headphones"  # Use "headphones" for 3.5mm jack on Raspberry Pi
volume: 0.8                  # Volume level (0.0 to 1.0)
shuffle: true                # Shuffle playlist
repeat: false                # Repeat playlist when finished

# Playlist (relative to music_dir or absolute paths)
playlist:
  - "beethoven_fur_elise.mp3"
  - "mozart_eine_kleine_nachtmusik.mp3"
  - "bach_air_on_g_string.mp3"
  - "vivaldi_four_seasons_spring.mp3"
  - "tchaikovsky_nutcracker_dance.mp3"

# Remote execution settings
remote:
  host: "192.168.188.154"    # Raspberry Pi IP address
  port: 9515                 # Port for MCP connection
  ssh_username: "pi"         # SSH username for Raspberry Pi
  ssh_password: "raspberry"  # SSH password
```

You can customize this file to include your own music files and settings.

## Step 2: Start the Orchestrator Shell

Open a terminal and start the UnitMCP orchestrator shell:

```bash
cd /path/to/UnitApi/mcp
python -m unitmcp.orchestrator.shell
```

You should see the orchestrator shell prompt:

```
╔═════════════════════════════════════════════╗
║  UnitMCP Orchestrator                       ║
║  Type 'help' for commands | 'exit' to quit  ║
╚═════════════════════════════════════════════╝

mcp>
```

## Step 3: Connect to Your Raspberry Pi

Connect to your Raspberry Pi using the `connect` command:

```
mcp> connect 192.168.188.154 9515
```

Replace the IP address with your Raspberry Pi's IP address. If successful, you'll see:

```
Connecting to 192.168.188.154:9515...
Connected successfully!
mcp (192.168.188.154:9515)>
```

## Step 4: Transfer Configuration and Music Files

You can transfer your configuration file and music files to the Raspberry Pi using the orchestrator's file transfer capabilities:

```
mcp (192.168.188.154:9515)> upload examples/audio/config/music_config.yaml /home/pi/music_config.yaml
mcp (192.168.188.154:9515)> upload examples/audio/music/ /home/pi/music/
```

## Step 5: Run the Music Player on the Raspberry Pi

Now you can run the music player on the Raspberry Pi using the configuration file:

```
mcp (192.168.188.154:9515)> run audio --example=music_player --config=/home/pi/music_config.yaml --output=headphones --simulation=false
```

## Using the Orchestrator Shell Commands

Here are some useful commands for working with the music player:

### Running with Different Options

```
# Run with default settings
mcp> run audio --example=music_player

# Run with specific configuration file
mcp> run audio --example=music_player --config=examples/audio/config/music_config.yaml

# Run on Raspberry Pi with specific output device
mcp> run audio --example=music_player --host=192.168.188.154 --ssh-username=pi --ssh-password=raspberry --config=/home/pi/music_config.yaml --output=headphones --simulation=false

# Run with shuffle enabled
mcp> run audio --example=music_player --shuffle=true

# Run with repeat enabled
mcp> run audio --example=music_player --repeat=true
```

### Checking Status and Stopping Playback

```
# Check status of running player
mcp> status

# Stop playback
mcp> stop
```

## Creating a Custom Configuration

You can create a custom configuration file with your own playlist:

1. Create a new YAML file (e.g., `my_playlist.yaml`)
2. Add your music directory, output device, and playlist
3. Transfer it to the Raspberry Pi
4. Run the music player with your custom configuration

Example custom configuration:

```yaml
music_dir: "/home/pi/my_music"
output_device: "speakers"
volume: 0.6
shuffle: true
repeat: true
playlist:
  - "song1.mp3"
  - "song2.mp3"
  - "song3.mp3"
```

## Troubleshooting

### No Sound Output

1. Check if your audio device is properly connected
2. Use `--list-devices` to see available audio devices:
   ```
   mcp> run audio --example=music_player --list-devices=true
   ```
3. Make sure the correct output device is specified in your configuration
4. Check the volume level in your configuration

### File Not Found Errors

1. Make sure your music files exist in the specified directory
2. Check if the paths in your playlist are correct (relative to `music_dir` or absolute)
3. Verify that the music files have been properly transferred to the Raspberry Pi

### Connection Issues

1. Verify that your Raspberry Pi is powered on and connected to the network
2. Check if the IP address in your configuration is correct
3. Make sure the UnitMCP service is running on the Raspberry Pi
4. Try restarting the orchestrator shell and reconnecting

## Advanced Usage

### Creating Playlists for Different Genres

You can create multiple configuration files for different genres or moods:

```
/configs/
  classical.yaml
  jazz.yaml
  rock.yaml
  relaxing.yaml
```

### Scheduling Playback

You can schedule music playback using cron jobs on the Raspberry Pi:

```bash
# Play classical music at 8:00 AM
0 8 * * * python /path/to/music_player.py --config=/home/pi/configs/classical.yaml

# Play relaxing music at 10:00 PM
0 22 * * * python /path/to/music_player.py --config=/home/pi/configs/relaxing.yaml
```

### Integration with Home Automation

You can integrate the music player with home automation systems by:

1. Creating a simple REST API endpoint that triggers the music player
2. Using MQTT to send commands to the Raspberry Pi
3. Setting up voice control with a service like Google Assistant or Alexa
