"""Keyboard automation examples."""

import asyncio
from unitmcp import MCPHardwareClient


async def type_text_demo():
    """Simple text typing demonstration."""
    async with MCPHardwareClient() as client:
        print("Typing text in 3 seconds...")
        await asyncio.sleep(3)

        # Type a simple message
        await client.type_text("Hello, World!")
        print("Text typed")

        # Press Enter
        await client.press_key("enter")
        print("Enter pressed")


async def keyboard_shortcuts():
    """Demonstrate keyboard shortcuts."""
    async with MCPHardwareClient() as client:
        print("Demonstrating keyboard shortcuts...")

        # Type some text
        await client.type_text("This is a test message")
        await asyncio.sleep(1)

        # Select all (Ctrl+A)
        print("Selecting all text")
        await client.hotkey("ctrl", "a")
        await asyncio.sleep(1)

        # Copy (Ctrl+C)
        print("Copying text")
        await client.hotkey("ctrl", "c")
        await asyncio.sleep(1)

        # Move to end and paste
        await client.press_key("end")
        await client.press_key("enter")

        # Paste (Ctrl+V)
        print("Pasting text")
        await client.hotkey("ctrl", "v")

        print("Keyboard shortcuts complete")


async def form_filling_demo():
    """Simulate form filling."""
    async with MCPHardwareClient() as client:
        print("Form filling demo (make sure a form is open)")
        await asyncio.sleep(3)

        # Fill first field
        await client.type_text("John Doe")
        await client.press_key("tab")

        # Fill email
        await client.type_text("john.doe@example.com")
        await client.press_key("tab")

        # Fill password
        await client.type_text("SecurePass123!")
        await client.press_key("tab")

        print("Form filling complete")


if __name__ == "__main__":
    print("Keyboard Automation Demo")
    print("1. Type text")
    print("2. Keyboard shortcuts")
    print("3. Form filling")

    choice = input("Select demo (1-3): ")

    if choice == "1":
        asyncio.run(type_text_demo())
    elif choice == "2":
        asyncio.run(keyboard_shortcuts())
    elif choice == "3":
        asyncio.run(form_filling_demo())
    else:
        print("Invalid choice")