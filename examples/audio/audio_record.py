"""Audio recording and playback examples."""

import asyncio
from unitmcp import MCPHardwareClient


async def record_audio():
    """Record audio for 5 seconds."""
    async with MCPHardwareClient() as client:
        print("Recording audio for 5 seconds...")

        # Start recording
        await client.send_request("audio.startRecording", {})

        # Wait for recording duration
        await asyncio.sleep(5)

        # Stop recording and get audio data
        result = await client.send_request("audio.stopRecording", {})

        print("Recording complete")
        print(f"Duration: {result.get('duration', 0):.2f} seconds")

        return result.get("audio_data")


async def play_audio(audio_data):
    """Play recorded audio."""
    async with MCPHardwareClient() as client:
        print("Playing audio...")

        await client.send_request("audio.playAudio", {
            "audio_data": audio_data
        })

        print("Playback complete")


async def volume_control():
    """Demonstrate volume control."""
    async with MCPHardwareClient() as client:
        # Get current volume
        result = await client.send_request("audio.getVolume", {})
        current_volume = result.get("volume", 0)
        print(f"Current volume: {current_volume}%")

        # Set volume to 50%
        print("Setting volume to 50%")
        await client.send_request("audio.setVolume", {"volume": 50})

        # Play test sound
        await client.send_request("audio.textToSpeech", {
            "text": "Testing volume at 50 percent"
        })

        await asyncio.sleep(2)

        # Restore original volume
        print(f"Restoring volume to {current_volume}%")
        await client.send_request("audio.setVolume", {"volume": current_volume})


async def text_to_speech():
    """Convert text to speech."""
    async with MCPHardwareClient() as client:
        messages = [
            "Hello, this is a text to speech demo.",
            "The MCP Hardware library can convert text to speech.",
            "Thank you for using our system."
        ]

        for message in messages:
            print(f"Speaking: {message}")
            await client.send_request("audio.textToSpeech", {
                "text": message,
                "rate": 150
            })
            await asyncio.sleep(1)


if __name__ == "__main__":
    print("Audio Demo")
    print("1. Record and play audio")
    print("2. Volume control")
    print("3. Text to speech")

    choice = input("Select demo (1-3): ")

    if choice == "1":
        audio_data = asyncio.run(record_audio())
        if audio_data:
            play = input("Play recording? (y/n): ")
            if play.lower() == 'y':
                asyncio.run(play_audio(audio_data))
    elif choice == "2":
        asyncio.run(volume_control())
    elif choice == "3":
        asyncio.run(text_to_speech())
    else:
        print("Invalid choice")