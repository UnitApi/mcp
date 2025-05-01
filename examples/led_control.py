"""Simple LED control example."""

import asyncio
from unitmcp import MCPHardwareClient


async def blink_led():
    """Blink an LED 5 times."""
    async with MCPHardwareClient() as client:
        # Setup LED on GPIO pin 17
        await client.setup_led("led1", pin=17)
        print("LED setup complete")

        # Blink LED 5 times
        for i in range(5):
            print(f"Blink {i+1}")
            await client.control_led("led1", "on")
            await asyncio.sleep(0.5)
            await client.control_led("led1", "off")
            await asyncio.sleep(0.5)

        print("LED blinking complete")


async def led_patterns():
    """Demonstrate different LED patterns."""
    async with MCPHardwareClient() as client:
        # Setup LED
        await client.setup_led("led1", pin=17)

        # Pattern 1: Fast blink
        print("Fast blink pattern")
        await client.control_led("led1", "blink", on_time=0.1, off_time=0.1)
        await asyncio.sleep(3)

        # Pattern 2: Slow blink
        print("Slow blink pattern")
        await client.control_led("led1", "blink", on_time=0.5, off_time=0.5)
        await asyncio.sleep(3)

        # Turn off
        await client.control_led("led1", "off")
        print("LED patterns complete")


if __name__ == "__main__":
    print("LED Control Demo")
    print("1. Simple blink")
    print("2. LED patterns")

    choice = input("Select demo (1-2): ")

    if choice == "1":
        asyncio.run(blink_led())
    elif choice == "2":
        asyncio.run(led_patterns())
    else:
        print("Invalid choice")