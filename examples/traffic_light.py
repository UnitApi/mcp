"""Traffic light system example."""

import asyncio
from unitmcp import MCPHardwareClient


async def traffic_light_system():
    """Simulate a traffic light system with LEDs."""
    async with MCPHardwareClient() as client:
        # Setup LEDs for traffic light
        print("Setting up traffic light system...")
        await client.setup_led("red", pin=17)
        await client.setup_led("yellow", pin=27)
        await client.setup_led("green", pin=22)

        print("Traffic light running (Ctrl+C to stop)")

        try:
            while True:
                # Red light (5 seconds)
                print("RED")
                await client.control_led("red", "on")
                await client.control_led("yellow", "off")
                await client.control_led("green", "off")
                await asyncio.sleep(5)

                # Red + Yellow (prepare to go - 2 seconds)
                print("RED + YELLOW")
                await client.control_led("yellow", "on")
                await asyncio.sleep(2)

                # Green light (5 seconds)
                print("GREEN")
                await client.control_led("red", "off")
                await client.control_led("yellow", "off")
                await client.control_led("green", "on")
                await asyncio.sleep(5)

                # Yellow light (2 seconds)
                print("YELLOW")
                await client.control_led("green", "off")
                await client.control_led("yellow", "on")
                await asyncio.sleep(2)

        except KeyboardInterrupt:
            print("\nStopping traffic light...")
            # Turn off all LEDs
            await client.control_led("red", "off")
            await client.control_led("yellow", "off")
            await client.control_led("green", "off")
            print("Traffic light stopped")


async def pedestrian_crossing():
    """Traffic light with pedestrian crossing button."""
    async with MCPHardwareClient() as client:
        # Setup traffic lights
        await client.setup_led("car_red", pin=17)
        await client.setup_led("car_green", pin=22)
        await client.setup_led("ped_red", pin=23)
        await client.setup_led("ped_green", pin=24)

        # Setup button for pedestrian crossing
        await client.send_request("gpio.setupButton", {
            "device_id": "ped_button",
            "pin": 25
        })

        print("Pedestrian crossing system running...")

        # Start with cars green, pedestrians red
        await client.control_led("car_green", "on")
        await client.control_led("car_red", "off")
        await client.control_led("ped_red", "on")
        await client.control_led("ped_green", "off")

        try:
            while True:
                # Check for button press
                result = await client.send_request("gpio.readButton", {
                    "device_id": "ped_button"
                })

                if result.get("is_pressed"):
                    print("Pedestrian crossing requested")

                    # Change to yellow for cars
                    await client.control_led("car_green", "off")
                    await client.control_led("car_red", "on")
                    await asyncio.sleep(3)

                    # Allow pedestrians to cross
                    await client.control_led("ped_red", "off")
                    await client.control_led("ped_green", "on")
                    await asyncio.sleep(10)

                    # Flash pedestrian green
                    for _ in range(3):
                        await client.control_led("ped_green", "off")
                        await asyncio.sleep(0.5)
                        await client.control_led("ped_green", "on")
                        await asyncio.sleep(0.5)

                    # Back to normal
                    await client.control_led("ped_green", "off")
                    await client.control_led("ped_red", "on")
                    await asyncio.sleep(2)
                    await client.control_led("car_red", "off")
                    await client.control_led("car_green", "on")

                await asyncio.sleep(0.1)

        except KeyboardInterrupt:
            print("\nStopping pedestrian crossing...")
            # Turn off all LEDs
            for led in ["car_red", "car_green", "ped_red", "ped_green"]:
                await client.control_led(led, "off")


if __name__ == "__main__":
    print("Traffic Light Examples")
    print("1. Basic traffic light")
    print("2. Pedestrian crossing")

    choice = input("Select demo (1-2): ")

    if choice == "1":
        asyncio.run(traffic_light_system())
    elif choice == "2":
        asyncio.run(pedestrian_crossing())
    else:
        print("Invalid choice")