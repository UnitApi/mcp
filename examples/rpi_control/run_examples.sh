#!/bin/bash
# Script to run all UnitMCP example files

# Set terminal colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== UnitMCP Examples Runner ===${NC}"
echo -e "${YELLOW}This script will run all the example files in sequence.${NC}"
echo -e "${YELLOW}Press Ctrl+C at any time to stop the current example and move to the next.${NC}"
echo ""

# Function to run an example with a timeout
run_example() {
    local example=$1
    local description=$2
    local duration=${3:-30}
    local args=${4:-""}
    
    echo -e "${GREEN}Running: ${example}${NC}"
    echo -e "${YELLOW}${description}${NC}"
    echo -e "${YELLOW}Duration: ${duration} seconds${NC}"
    echo -e "${YELLOW}Press Ctrl+C to skip to the next example${NC}"
    echo ""
    
    # Run the example with a timeout
    timeout ${duration}s python ${example} ${args} || true
    
    echo ""
    echo -e "${GREEN}Example completed or skipped.${NC}"
    echo "---------------------------------------------"
    echo ""
    # Small pause between examples
    sleep 2
}

# Configuration Automation Example
run_example "config_automation_example.py" "Configuration-based automation using YAML files" 30 "--config my_custom_config.yaml"

# Hardware Client Example
run_example "hardware_client.py" "Hardware client for controlling GPIO devices" 30 "--demo all"

# GPIO Example
run_example "gpio_example.py" "Direct GPIO control example" 20

# Audio Example
run_example "audio_example.py" "Audio playback and recording example" 20

# LCD Example (if available)
if [ -f "lcd_example.py" ]; then
    run_example "lcd_example.py" "LCD display control example" 20
fi

# Hardware Discovery Example
run_example "hardware_discovery_example.py" "Hardware discovery and enumeration" 10

echo -e "${BLUE}=== All examples completed ===${NC}"
echo -e "${YELLOW}Thank you for exploring UnitMCP examples!${NC}"
