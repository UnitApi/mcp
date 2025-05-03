#!/usr/bin/env python3
"""
UnitMCP AI Demo

This example demonstrates how to use the UnitMCP AI infrastructure,
including LLM, TTS, STT, NLP, and vision capabilities.
"""

import asyncio
import logging
import os
import sys
import tempfile
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.unitmcp.utils.env_loader import EnvLoader
from src.unitmcp.ai import (
    # LLM models
    ollama,
    
    # Speech models
    TTSModel, PyTTSX3Config, PyTTSX3Model,
    STTModel, WhisperConfig, WhisperModel,
    
    # NLP models
    SpacyConfig, SpacyNLPModel,
    
    # Vision models
    ImageProcessingModel, ImageProcessingConfig,
    YOLOConfig, YOLOModel,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def demo_llm():
    """Demonstrate LLM capabilities."""
    logger.info("Demonstrating LLM capabilities...")
    
    # Initialize the Ollama model
    ollama_config = ollama.OllamaConfig(
        model="llama2",
        host="localhost",
        port=11434,
    )
    llm = ollama.OllamaModel("demo-llm", ollama_config)
    
    # Initialize the model
    initialized = await llm.initialize()
    if not initialized:
        logger.error("Failed to initialize Ollama model")
        return
    
    # Generate text
    prompt = "Explain how robots can use AI to interact with the world in 3 sentences."
    response = await llm.generate(prompt)
    
    logger.info(f"Prompt: {prompt}")
    logger.info(f"Response: {response}")
    
    # Clean up
    await llm.cleanup()


async def demo_tts():
    """Demonstrate TTS capabilities."""
    logger.info("Demonstrating TTS capabilities...")
    
    # Initialize the PyTTSX3 model
    tts_config = PyTTSX3Config(
        rate=150,
        volume=1.0,
    )
    tts = PyTTSX3Model("demo-tts", tts_config)
    
    # Initialize the model
    initialized = await tts.initialize()
    if not initialized:
        logger.error("Failed to initialize PyTTSX3 model")
        return
    
    # Convert text to speech
    text = "Hello, I am UnitMCP, your robotic assistant."
    audio_data = await tts.text_to_speech(text)
    
    # Save the audio to a file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        temp_path = temp_file.name
        temp_file.write(audio_data)
    
    logger.info(f"Text: {text}")
    logger.info(f"Audio saved to: {temp_path}")
    
    # Clean up
    await tts.cleanup()


async def demo_stt():
    """Demonstrate STT capabilities."""
    logger.info("Demonstrating STT capabilities...")
    
    # Check if we have an audio file to transcribe
    audio_file = Path(__file__).parent / "sample_audio.wav"
    if not audio_file.exists():
        logger.warning(f"Sample audio file not found: {audio_file}")
        logger.info("Skipping STT demo")
        return
    
    # Initialize the Whisper model
    stt_config = WhisperConfig(
        model_size="base",
        language="en",
    )
    stt = WhisperModel("demo-stt", stt_config)
    
    # Initialize the model
    initialized = await stt.initialize()
    if not initialized:
        logger.error("Failed to initialize Whisper model")
        return
    
    # Read the audio file
    with open(audio_file, "rb") as f:
        audio_data = f.read()
    
    # Convert speech to text
    text = await stt.speech_to_text(audio_data)
    
    logger.info(f"Audio file: {audio_file}")
    logger.info(f"Transcription: {text}")
    
    # Clean up
    await stt.cleanup()


async def demo_nlp():
    """Demonstrate NLP capabilities."""
    logger.info("Demonstrating NLP capabilities...")
    
    # Initialize the spaCy model
    nlp_config = SpacyConfig(
        model_name="en_core_web_sm",
    )
    nlp = SpacyNLPModel("demo-nlp", nlp_config)
    
    # Initialize the model
    initialized = await nlp.initialize()
    if not initialized:
        logger.error("Failed to initialize spaCy model")
        return
    
    # Process text
    text = "Apple is looking at buying U.K. startup for $1 billion. The robot picked up the red ball."
    result = await nlp.process(text)
    
    logger.info(f"Text: {text}")
    logger.info(f"Entities: {result['entities']}")
    logger.info(f"Sentences: {result['sentences']}")
    
    # Extract entities
    entities = await nlp.extract_entities(text)
    logger.info(f"Extracted entities: {entities}")
    
    # Clean up
    await nlp.cleanup()


async def demo_vision():
    """Demonstrate vision capabilities."""
    logger.info("Demonstrating vision capabilities...")
    
    # Check if we have an image file to process
    image_file = Path(__file__).parent / "sample_image.jpg"
    if not image_file.exists():
        logger.warning(f"Sample image file not found: {image_file}")
        logger.info("Skipping vision demo")
        return
    
    # Initialize the image processing model
    vision_config = ImageProcessingConfig(
        resize=(640, 480),
        normalize=True,
    )
    vision = ImageProcessingModel("demo-vision", vision_config)
    
    # Initialize the model
    initialized = await vision.initialize()
    if not initialized:
        logger.error("Failed to initialize image processing model")
        return
    
    # Read the image file
    with open(image_file, "rb") as f:
        image_data = f.read()
    
    # Process the image
    processed_data = await vision.process_image(image_data, grayscale=True)
    
    # Save the processed image
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
        temp_path = temp_file.name
        temp_file.write(processed_data)
    
    logger.info(f"Original image: {image_file}")
    logger.info(f"Processed image saved to: {temp_path}")
    
    # Extract features
    features = await vision.extract_features(image_data)
    logger.info(f"Image dimensions: {features['dimensions']}")
    
    # Clean up
    await vision.cleanup()


async def demo_object_detection():
    """Demonstrate object detection capabilities."""
    logger.info("Demonstrating object detection capabilities...")
    
    # Check if we have an image file to process
    image_file = Path(__file__).parent / "sample_image.jpg"
    if not image_file.exists():
        logger.warning(f"Sample image file not found: {image_file}")
        logger.info("Skipping object detection demo")
        return
    
    # Initialize the YOLO model
    yolo_config = YOLOConfig(
        model_version="yolov8n",
        confidence_threshold=0.5,
    )
    yolo = YOLOModel("demo-yolo", yolo_config)
    
    # Initialize the model
    initialized = await yolo.initialize()
    if not initialized:
        logger.error("Failed to initialize YOLO model")
        return
    
    # Read the image file
    with open(image_file, "rb") as f:
        image_data = f.read()
    
    # Detect objects
    detections = await yolo.detect_objects(image_data)
    
    logger.info(f"Image: {image_file}")
    logger.info(f"Detected {len(detections)} objects:")
    for i, detection in enumerate(detections):
        logger.info(f"  {i+1}. {detection['class']['name']} "
                   f"(confidence: {detection['confidence']:.2f})")
    
    # Clean up
    await yolo.cleanup()


async def main():
    """Run the AI demo."""
    # Load environment variables
    env_loader = EnvLoader()
    env_loader.load_env()
    
    # Run the demos
    try:
        await demo_llm()
        print("\n" + "-" * 50 + "\n")
        
        await demo_tts()
        print("\n" + "-" * 50 + "\n")
        
        await demo_stt()
        print("\n" + "-" * 50 + "\n")
        
        await demo_nlp()
        print("\n" + "-" * 50 + "\n")
        
        await demo_vision()
        print("\n" + "-" * 50 + "\n")
        
        await demo_object_detection()
    except Exception as e:
        logger.exception(f"Error in AI demo: {e}")


if __name__ == "__main__":
    asyncio.run(main())
