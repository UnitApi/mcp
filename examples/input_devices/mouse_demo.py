"""Mouse control examples."""

import asyncio
from unitmcp import MCPHardwareClient


async def mouse_movement():
    """Demonstrate mouse movement."""
    async with MCPHardwareClient() as client:
        print("Moving mouse in 3 seconds...")
        await asyncio.sleep(3)

        # Get current position
        pos = await client.get_mouse_position()
        print(f"Current position: {pos}")

        # Move to specific coordinates
        print("Moving to (500, 300)")
        await client.move_mouse(500, 300)
        await asyncio.sleep(1)

        # Relative movement
        print("Moving 100 pixels right and down")
        await client.move_mouse(100, 100, relative=True)
        await asyncio.sleep(1)

        print("Mouse movement complete")


async def mouse_clicks():
    """Demonstrate different click types."""
    async with MCPHardwareClient() as client:
        print("Click demonstration in 3 seconds...")
        await asyncio.sleep(3)

        # Left click
        print("Left click")
        await client.click("left")
        await asyncio.sleep(1)

        # Right click
        print("Right click")
        await client.right_click()
        await asyncio.sleep(1)

        # Double click
        print("Double click")
        await client.double_click()
        await asyncio.sleep(1)

        print("Click demonstration complete")


async def drag_and_drop():
    """Demonstrate drag and drop."""
    async with MCPHardwareClient() as client:
        print("Drag and drop in 3 seconds...")
        await asyncio.sleep(3)

        # Move to start position
        start_x, start_y = 200, 200
        await client.move_mouse(start_x, start_y)
        await asyncio.sleep(1)

        # Drag to end position
        end_x, end_y = 600, 400
        print(f"Dragging from ({start_x}, {start_y}) to ({end_x}, {end_y})")
        await client.drag_to(end_x, end_y, duration=1.0)

        print("Drag and drop complete")


async def screenshot_demo():
    """Take screenshots."""
    async with MCPHardwareClient() as client:
        print("Taking screenshot in 3 seconds...")
        await asyncio.sleep(3)

        # Full screen screenshot
        result = await client.screenshot()
        print("Full screenshot taken")

        # Region screenshot
        region = (100, 100, 800, 600)  # x, y, width, height
        result = await client.screenshot(region=region)
        print(f"Region screenshot taken: {region}")

        print("Screenshot demo complete")


if __name__ == "__main__":
    print("Mouse Control Demo")
    print("1. Mouse movement")
    print("2. Mouse clicks")
    print("3. Drag and drop")
    print("4. Screenshots")

    choice = input("Select demo (1-4): ")

    if choice == "1":
        asyncio.run(mouse_movement())
    elif choice == "2":
        asyncio.run(mouse_clicks())
    elif choice == "3":
        asyncio.run(drag_and_drop())
    elif choice == "4":
        asyncio.run(screenshot_demo())
    else:
        print("Invalid choice")