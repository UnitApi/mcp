# Zaktualizowany Plan Wdrożenia UnitMCP Runner z Rozszerzonym Wsparciem dla AI

Biorąc pod uwagę aktualne potrzeby rozwoju UnitMCP z większym naciskiem na różne technologie AI, przedstawiam rozszerzony plan implementacji z szerokim wsparciem dla LLM, NLP, ML, TTS i STT.

## Faza 1: Framework Integracji AI (Tydzień 1)

### Etap 1.1: Architektura Modułu AI (Dni 1-2)
- Utworzenie ujednoliconej architektury dla modułów AI w `src/unitmcp/ai/`
- Zaprojektowanie interfejsów dla różnych technologii AI

```bash
mkdir -p src/unitmcp/ai
mkdir -p src/unitmcp/ai/llm
mkdir -p src/unitmcp/ai/nlp
mkdir -p src/unitmcp/ai/speech
mkdir -p src/unitmcp/ai/vision
mkdir -p src/unitmcp/ai/common
```

### Etap 1.2: System Konfiguracji AI (Dni 3-4)
- Utworzenie standardu konfiguracji dla modułów AI w `configs/yaml/ai/`
- Implementacja mechanizmu ładowania konfiguracji AI

```bash
mkdir -p configs/yaml/ai
touch configs/yaml/ai/llm_config.yaml
touch configs/yaml/ai/nlp_config.yaml
touch configs/yaml/ai/speech_config.yaml
touch configs/yaml/ai/vision_config.yaml
```

### Etap 1.3: Integracja Bazowych Interfejsów (Dni 5-7)
- Implementacja bazowych interfejsów dla każdej kategorii AI
- Przygotowanie mechanizmu rozszerzeń dla łatwego dodawania nowych modeli

```python
# src/unitmcp/ai/common/model_interface.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class AIModelInterface(ABC):
    """Base interface for all AI models in UnitMCP."""
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the model with given configuration."""
        pass
    
    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """Process input data and return results."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources used by the model."""
        pass
```

## Faza 2: Implementacja Modułów LLM (Tydzień 2)

### Etap 2.1: Integracja Ollama Framework (Dni 1-2)
- Implementacja pełnego wsparcia dla różnych modeli Ollama
- Wsparcie dla różnych rozmiarów modeli (od lekkich po zaawansowane)

```python
# src/unitmcp/ai/llm/ollama.py
import requests
import logging
from typing import Dict, Any, Optional, List
from unitmcp.ai.common.model_interface import AIModelInterface

class OllamaModel(AIModelInterface):
    """Ollama LLM integration for UnitMCP."""
    
    AVAILABLE_MODELS = [
        "llama3", "llama3:8b", "llama3:70b",
        "mistral", "mistral:7b", "mistral:instruct",
        "phi", "phi:2", "phi:3",
        "tinyllama", "gemma:2b", "gemma:7b"
    ]
    
    def __init__(self):
        self.host = "localhost"
        self.port = 11434
        self.model = "llama3"
        self.initialized = False
        self.logger = logging.getLogger("UnitMCP-Ollama")
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the Ollama model."""
        self.host = config.get("host", self.host)
        self.port = config.get("port", self.port)
        self.model = config.get("model", self.model)
        
        # Check if model is available and pull if not
        # Implementation...
        
        return True
    
    async def process(self, input_text: str) -> str:
        """Process input text and generate a response."""
        # Implementation...
        return "Response text"
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        pass
```

### Etap 2.2: Integracja Claude API (Dni 3-4)
- Rozszerzenie istniejącej integracji Claude o pełne wsparcie API
- Implementacja wsparcia dla różnych wersji Claude (3, 3.5, 3.7, etc.)

```python
# src/unitmcp/ai/llm/claude.py
import requests
import logging
import json
import os
from typing import Dict, Any, Optional, List
from unitmcp.ai.common.model_interface import AIModelInterface

class ClaudeModel(AIModelInterface):
    """Claude API integration for UnitMCP."""
    
    AVAILABLE_MODELS = [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-3.5-sonnet-20240620",
        "claude-3.7-sonnet-20250131"
    ]
    
    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.model = "claude-3-sonnet-20240229"
        self.initialized = False
        self.logger = logging.getLogger("UnitMCP-Claude")
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the Claude model."""
        self.api_key = config.get("api_key", self.api_key)
        self.model = config.get("model", self.model)
        
        if not self.api_key:
            self.logger.error("No API key provided for Claude")
            return False
        
        # Test connection
        # Implementation...
        
        return True
    
    async def process(self, input_text: str) -> str:
        """Process input text and generate a response."""
        # Implementation...
        return "Response text"
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        pass
```

### Etap 2.3: Implementacja Adaptera OpenAI (Dni 5-7)
- Dodanie wsparcia dla modeli OpenAI (GPT-3.5, GPT-4)
- Implementacja kompatybilnej warstwy konwersji formatów zapytań

```python
# src/unitmcp/ai/llm/openai.py
import openai
import logging
import os
from typing import Dict, Any, Optional, List
from unitmcp.ai.common.model_interface import AIModelInterface

class OpenAIModel(AIModelInterface):
    """OpenAI API integration for UnitMCP."""
    
    AVAILABLE_MODELS = [
        "gpt-3.5-turbo",
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4o"
    ]
    
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        self.model = "gpt-3.5-turbo"
        self.initialized = False
        self.logger = logging.getLogger("UnitMCP-OpenAI")
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the OpenAI model."""
        # Implementation...
        return True
    
    async def process(self, input_text: str) -> str:
        """Process input text and generate a response."""
        # Implementation...
        return "Response text"
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        pass
```

## Faza 3: Implementacja Modułów NLP i ML (Tydzień 3)

### Etap 3.1: Integracja z Hugging Face (Dni 1-3)
- Implementacja wsparcia dla biblioteki Transformers
- Integracja z Hugging Face Hub dla łatwego pobierania modeli

```python
# src/unitmcp/ai/nlp/huggingface.py
import torch
from transformers import pipeline, AutoTokenizer, AutoModel
import logging
from typing import Dict, Any, Optional, List
from unitmcp.ai.common.model_interface import AIModelInterface

class HuggingFaceModel(AIModelInterface):
    """Hugging Face models integration for UnitMCP."""
    
    def __init__(self):
        self.model_name = "bert-base-uncased"
        self.task = "text-classification"
        self.device = "cpu"
        self.pipeline = None
        self.initialized = False
        self.logger = logging.getLogger("UnitMCP-HuggingFace")
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the Hugging Face model."""
        self.model_name = config.get("model_name", self.model_name)
        self.task = config.get("task", self.task)
        self.device = config.get("device", self.device)
        
        try:
            self.pipeline = pipeline(self.task, model=self.model_name, device=self.device)
            self.initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize HuggingFace model: {e}")
            return False
    
    async def process(self, input_data: Any) -> Any:
        """Process input data using the Hugging Face pipeline."""
        if not self.initialized:
            raise RuntimeError("Model not initialized")
        
        return self.pipeline(input_data)
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        self.pipeline = None
        torch.cuda.empty_cache()
```

### Etap 3.2: Implementacja Modułów Spacy (Dni 4-5)
- Integracja z biblioteką spaCy dla zaawansowanego NLP
- Obsługa zadań NER, dependency parsing, klasyfikacji, etc.

```python
# src/unitmcp/ai/nlp/spacy_integration.py
import spacy
import logging
from typing import Dict, Any, Optional, List
from unitmcp.ai.common.model_interface import AIModelInterface

class SpacyModel(AIModelInterface):
    """spaCy NLP integration for UnitMCP."""
    
    AVAILABLE_MODELS = [
        "en_core_web_sm",
        "en_core_web_md",
        "en_core_web_lg",
        "pl_core_news_sm",
        "pl_core_news_md",
        "pl_core_news_lg"
    ]
    
    def __init__(self):
        self.model_name = "en_core_web_md"
        self.nlp = None
        self.initialized = False
        self.logger = logging.getLogger("UnitMCP-Spacy")
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the spaCy model."""
        self.model_name = config.get("model_name", self.model_name)
        
        try:
            self.nlp = spacy.load(self.model_name)
            self.initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to load spaCy model: {e}")
            return False
    
    async def process(self, text: str) -> Dict[str, Any]:
        """Process text using the spaCy model."""
        if not self.initialized:
            raise RuntimeError("Model not initialized")
        
        doc = self.nlp(text)
        
        # Extract various NLP features
        result = {
            "entities": [(ent.text, ent.label_) for ent in doc.ents],
            "tokens": [token.text for token in doc],
            "pos_tags": [(token.text, token.pos_) for token in doc],
            "dependencies": [(token.text, token.dep_, token.head.text) for token in doc],
            "noun_chunks": [chunk.text for chunk in doc.noun_chunks]
        }
        
        return result
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        self.nlp = None
```

### Etap 3.3: Implementacja PyTorch i scikit-learn (Dni 6-7)
- Integracja z bibliotekami ML dla zaawansowanych zadań uczenia maszynowego
- Implementacja interfejsów dla modeli PyTorch i scikit-learn

```python
# src/unitmcp/ai/ml/pytorch.py
import torch
import torch.nn as nn
import logging
import os
from typing import Dict, Any, Optional, List
from unitmcp.ai.common.model_interface import AIModelInterface

class PyTorchModel(AIModelInterface):
    """PyTorch model integration for UnitMCP."""
    
    def __init__(self):
        self.model_path = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.initialized = False
        self.logger = logging.getLogger("UnitMCP-PyTorch")
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the PyTorch model."""
        self.model_path = config.get("model_path")
        self.device = config.get("device", self.device)
        
        if not self.model_path or not os.path.exists(self.model_path):
            self.logger.error(f"Model path not found: {self.model_path}")
            return False
        
        try:
            self.model = torch.load(self.model_path, map_location=self.device)
            self.model.eval()
            self.initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to load PyTorch model: {e}")
            return False
    
    async def process(self, input_data: torch.Tensor) -> torch.Tensor:
        """Process input data using the PyTorch model."""
        if not self.initialized:
            raise RuntimeError("Model not initialized")
        
        with torch.no_grad():
            output = self.model(input_data.to(self.device))
        
        return output
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        self.model = None
        torch.cuda.empty_cache()
```

## Faza 4: Implementacja Modułów Speech (TTS i STT) (Tydzień 4)

### Etap 4.1: Integracja z Systemami TTS (Dni 1-2)
- Implementacja wsparcia dla różnych silników TTS (pyttsx3, gTTS, etc.)
- Integracja z zaawansowanymi modelami TTS z Hugging Face

```python
# src/unitmcp/ai/speech/tts.py
import pyttsx3
import torch
from TTS.api import TTS as TTSModel
import logging
import os
from typing import Dict, Any, Optional, List
from unitmcp.ai.common.model_interface import AIModelInterface

class TTSEngine(AIModelInterface):
    """Text-to-Speech integration for UnitMCP."""
    
    ENGINES = ["pyttsx3", "gtts", "coqui", "huggingface"]
    
    def __init__(self):
        self.engine_type = "pyttsx3"
        self.engine = None
        self.voice = None
        self.rate = 150
        self.volume = 1.0
        self.initialized = False
        self.logger = logging.getLogger("UnitMCP-TTS")
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the TTS engine."""
        self.engine_type = config.get("engine", self.engine_type)
        self.voice = config.get("voice")
        self.rate = config.get("rate", self.rate)
        self.volume = config.get("volume", self.volume)
        
        try:
            if self.engine_type == "pyttsx3":
                self.engine = pyttsx3.init()
                if self.voice:
                    self.engine.setProperty('voice', self.voice)
                self.engine.setProperty('rate', self.rate)
                self.engine.setProperty('volume', self.volume)
            elif self.engine_type == "coqui":
                self.engine = TTSModel.create(model_name="tts_models/en/vctk/vits")
            # Implementation for other engine types...
            
            self.initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS engine: {e}")
            return False
    
    async def process(self, text: str, output_file: Optional[str] = None) -> str:
        """Convert text to speech."""
        if not self.initialized:
            raise RuntimeError("TTS engine not initialized")
        
        try:
            if self.engine_type == "pyttsx3":
                if output_file:
                    self.engine.save_to_file(text, output_file)
                    self.engine.runAndWait()
                    return output_file
                else:
                    self.engine.say(text)
                    self.engine.runAndWait()
                    return "Speech played"
            elif self.engine_type == "coqui":
                output_path = output_file or "output.wav"
                self.engine.tts_to_file(text=text, file_path=output_path)
                return output_path
            # Implementation for other engine types...
            
            return "Speech processing completed"
        except Exception as e:
            self.logger.error(f"TTS processing error: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        if self.engine_type == "pyttsx3" and self.engine:
            self.engine.stop()
```

### Etap 4.2: Integracja z Systemami STT (Dni 3-4)
- Implementacja wsparcia dla różnych silników STT (speech_recognition, Whisper, etc.)
- Integracja z zaawansowanymi modelami STT

```python
# src/unitmcp/ai/speech/stt.py
import speech_recognition as sr
import torch
from transformers import pipeline
import logging
import os
from typing import Dict, Any, Optional, List
from unitmcp.ai.common.model_interface import AIModelInterface

class STTEngine(AIModelInterface):
    """Speech-to-Text integration for UnitMCP."""
    
    ENGINES = ["google", "wit", "sphinx", "whisper", "huggingface"]
    
    def __init__(self):
        self.engine_type = "google"
        self.api_key = None
        self.model = None
        self.recognizer = None
        self.language = "en-US"
        self.initialized = False
        self.logger = logging.getLogger("UnitMCP-STT")
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the STT engine."""
        self.engine_type = config.get("engine", self.engine_type)
        self.api_key = config.get("api_key")
        self.language = config.get("language", self.language)
        
        try:
            self.recognizer = sr.Recognizer()
            
            if self.engine_type == "whisper":
                self.model = pipeline("automatic-speech-recognition", model="openai/whisper-base")
            # Implementation for other engine types...
            
            self.initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize STT engine: {e}")
            return False
    
    async def process(self, audio_file: str) -> str:
        """Convert speech to text."""
        if not self.initialized:
            raise RuntimeError("STT engine not initialized")
        
        try:
            with sr.AudioFile(audio_file) as source:
                audio_data = self.recognizer.record(source)
                
                if self.engine_type == "google":
                    return self.recognizer.recognize_google(audio_data, language=self.language, key=self.api_key)
                elif self.engine_type == "sphinx":
                    return self.recognizer.recognize_sphinx(audio_data, language=self.language)
                elif self.engine_type == "whisper":
                    result = self.model(audio_file)
                    return result["text"]
                # Implementation for other engine types...
                
            return "Speech recognition failed"
        except Exception as e:
            self.logger.error(f"STT processing error: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        self.model = None
        torch.cuda.empty_cache()
```

### Etap 4.3: Integracja z Zaawansowanymi Funkcjami Audio (Dni 5-7)
- Implementacja funkcji rozpoznawania emocji w głosie
- Wsparcie dla detekcji i identyfikacji mówcy
- Rozpoznawanie dźwięków otoczenia

```python
# src/unitmcp/ai/speech/audio_analysis.py
import librosa
import numpy as np
import torch
from transformers import pipeline
import logging
from typing import Dict, Any, Optional, List
from unitmcp.ai.common.model_interface import AIModelInterface

class AudioAnalysisEngine(AIModelInterface):
    """Audio analysis integration for UnitMCP."""
    
    ANALYSIS_TYPES = ["emotion", "speaker_id", "environment", "music"]
    
    def __init__(self):
        self.analysis_type = "emotion"
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.initialized = False
        self.logger = logging.getLogger("UnitMCP-AudioAnalysis")
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the audio analysis engine."""
        self.analysis_type = config.get("analysis_type", self.analysis_type)
        self.device = config.get("device", self.device)
        
        try:
            if self.analysis_type == "emotion":
                self.model = pipeline("audio-classification", model="ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition")
            elif self.analysis_type == "speaker_id":
                # Implementation for speaker identification...
                pass
            # Implementation for other analysis types...
            
            self.initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize audio analysis engine: {e}")
            return False
    
    async def process(self, audio_file: str) -> Dict[str, Any]:
        """Analyze audio file."""
        if not self.initialized:
            raise RuntimeError("Audio analysis engine not initialized")
        
        try:
            if self.analysis_type == "emotion":
                result = self.model(audio_file)
                return {
                    "emotion": result[0]["label"],
                    "confidence": result[0]["score"],
                    "all_emotions": result
                }
            # Implementation for other analysis types...
            
            return {"error": "Unsupported analysis type"}
        except Exception as e:
            self.logger.error(f"Audio analysis error: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        self.model = None
        torch.cuda.empty_cache()
```

## Faza 5: Implementacja Modułów Vision (Tydzień 5)

### Etap 5.1: Integracja z Bibliotekami Computer Vision (Dni 1-3)
- Implementacja wsparcia dla OpenCV, pillow, etc.
- Implementacja podstawowych funkcji przetwarzania obrazu

```python
# src/unitmcp/ai/vision/image_processing.py
import cv2
import numpy as np
from PIL import Image
import logging
from typing import Dict, Any, Optional, List, Tuple
from unitmcp.ai.common.model_interface import AIModelInterface

class ImageProcessor(AIModelInterface):
    """Image processing integration for UnitMCP."""
    
    PROCESSING_TYPES = ["resize", "filter", "crop", "enhance", "transform"]
    
    def __init__(self):
        self.processing_type = "resize"
        self.initialized = False
        self.logger = logging.getLogger("UnitMCP-ImageProcessor")
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the image processor."""
        self.processing_type = config.get("processing_type", self.processing_type)
        self.initialized = True
        return True
    
    async def process(self, input_data: Dict[str, Any]) -> Any:
        """Process image according to specified type."""
        if not self.initialized:
            raise RuntimeError("Image processor not initialized")
        
        image_path = input_data.get("image_path")
        if not image_path:
            raise ValueError("No image path provided")
        
        try:
            if self.processing_type == "resize":
                width = input_data.get("width", 800)
                height = input_data.get("height", 600)
                return self._resize_image(image_path, width, height)
            elif self.processing_type == "filter":
                filter_type = input_data.get("filter", "blur")
                return self._apply_filter(image_path, filter_type)
            # Implementation for other processing types...
            
            return {"error": "Unsupported processing type"}
        except Exception as e:
            self.logger.error(f"Image processing error: {e}")
            raise
    
    def _resize_image(self, image_path: str, width: int, height: int) -> Dict[str, Any]:
        """Resize an image to given dimensions."""
        img = cv2.imread(image_path)
        resized = cv2.resize(img, (width, height))
        output_path = image_path.replace(".jpg", "_resized.jpg")
        cv2.imwrite(output_path, resized)
        return {"output_path": output_path, "width": width, "height": height}
    
    def _apply_filter(self, image_path: str, filter_type: str) -> Dict[str, Any]:
        """Apply a filter to an image."""
        img = cv2.imread(image_path)
        
        if filter_type == "blur":
            filtered = cv2.GaussianBlur(img, (15, 15), 0)
        elif filter_type == "sharpen":
            kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            filtered = cv2.filter2D(img, -1, kernel)
        # Implementation for other filters...
        
        output_path = image_path.replace(".jpg", f"_{filter_type}.jpg")
        cv2.imwrite(output_path, filtered)
        return {"output_path": output_path, "filter": filter_type}
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        pass
```

### Etap 5.2: Integracja z Modelami Object Detection (Dni 4-5)
- Implementacja wsparcia dla modeli detekcji obiektów (YOLO, Faster R-CNN, etc.)
- Integracja z modelami z Hugging Face

```python
# src/unitmcp/ai/vision/object_detection.py
import cv2
import torch
import numpy as np
from PIL import Image
from transformers import DetrImageProcessor, DetrForObjectDetection
import logging
from typing import Dict, Any, Optional, List
from unitmcp.ai.common.model_interface import AIModelInterface

class ObjectDetector(AIModelInterface):
    """Object detection integration for UnitMCP."""
    
    DETECTOR_TYPES = ["yolo", "faster_rcnn", "detr", "ssd"]
    
    def __init__(self):
        self.detector_type = "detr"
        self.model = None
        self.processor = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.threshold = 0.5
        self.initialized = False
        self.logger = logging.getLogger("UnitMCP-ObjectDetector")
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the object detector."""
        self.detector_type = config.get("detector_type", self.detector_type)
        self.threshold = config.get("threshold", self.threshold)
        self.device = config.get("device", self.device)
        
        try:
            if self.detector_type == "detr":
                self.processor = DetrImageProcessor.from_pretrained("facebook/detr-resnet-50")
                self.model = DetrForObjectDetection.from_pretrained("facebook/detr-resnet-50").to(self.device)
            elif self.detector_type == "yolo":
                # Implementation for YOLO...
                pass
            # Implementation for other detector types...
            
            self.initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize object detector: {e}")
            return False
    
    async def process(self, image_path: str) -> Dict[str, Any]:
        """Detect objects in an image."""
        if not self.initialized:
            raise RuntimeError("Object detector not initialized")
        
        try:
            image = Image.open(image_path)
            
            if self.detector_type == "detr":
                inputs = self.processor(images=image, return_tensors="pt").to(self.device)
                outputs = self.model(**inputs)
                
                # Convert outputs to results
                target_sizes = torch.tensor([image.size[::-1]]).to(self.device)
                results = self.processor.post_process_object_detection(outputs, target_sizes=target_sizes, threshold=self.threshold)[0]
                
                detections = []
                for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
                    box = [round(i, 2) for i in box.tolist()]
                    detections.append({
                        "label": self.model.config.id2label[label.item()],
                        "score": round(score.item(), 3),
                        "box": box
                    })
                
                return {"detections": detections}
            # Implementation for other detector types...
            
            return {"error": "Unsupported detector type"}
        except Exception as e:
            self.logger.error(f"Object detection error: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        self.model = None
        torch.cuda.empty_cache()
```

### Etap 5.3: Integracja z Zaawansowanymi Funkcjami Vision (Dni 6-7)
- Implementacja rozpoznawania twarzy i emocji
- Wsparcie dla śledzenia ruchu
- Implementacja segmentacji obrazu

```python
# src/unitmcp/ai/vision/face_analysis.py
import cv2
import numpy as np
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from deepface import DeepFace
import logging
from typing import Dict, Any, Optional, List
from unitmcp.ai.common.model_interface import AI Kontynuując implementację modułu Face Analysis:

```python
# src/unitmcp/ai/vision/face_analysis.py
import cv2
import numpy as np
import torch
from facenet_pytorch import MTCNN, InceptionResnetV1
from deepface import DeepFace
import logging
from typing import Dict, Any, Optional, List
from unitmcp.ai.common.model_interface import AIModelInterface

class FaceAnalyzer(AIModelInterface):
    """Face detection and analysis integration for UnitMCP."""
    
    ANALYSIS_TYPES = ["detection", "recognition", "emotion", "age", "gender", "tracking"]
    
    def __init__(self):
        self.analysis_type = "detection"
        self.face_detector = None
        self.face_recognizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.initialized = False
        self.logger = logging.getLogger("UnitMCP-FaceAnalyzer")
        self.known_faces = {}
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the face analyzer."""
        self.analysis_type = config.get("analysis_type", self.analysis_type)
        self.device = config.get("device", self.device)
        
        try:
            # Initialize face detector
            self.face_detector = MTCNN(keep_all=True, device=self.device)
            
            # Initialize face recognizer if needed
            if self.analysis_type in ["recognition"]:
                self.face_recognizer = InceptionResnetV1(pretrained='vggface2').eval().to(self.device)
                
                # Load known faces if provided
                known_faces_path = config.get("known_faces_path")
                if known_faces_path and os.path.exists(known_faces_path):
                    self.known_faces = torch.load(known_faces_path)
            
            self.initialized = True
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize face analyzer: {e}")
            return False
    
    async def process(self, image_path: str) -> Dict[str, Any]:
        """Analyze faces in an image."""
        if not self.initialized:
            raise RuntimeError("Face analyzer not initialized")
        
        try:
            image = cv2.imread(image_path)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            if self.analysis_type == "detection":
                # Detect faces
                boxes, probs = self.face_detector.detect(image_rgb)
                
                if boxes is None:
                    return {"faces": []}
                
                faces = []
                for box, prob in zip(boxes, probs):
                    if prob > 0.9:  # Confidence threshold
                        box = [int(b) for b in box]
                        faces.append({
                            "box": box,
                            "confidence": float(prob)
                        })
                
                return {"faces": faces}
                
            elif self.analysis_type == "emotion":
                # Analyze emotions in faces
                results = DeepFace.analyze(image_rgb, actions=['emotion'], enforce_detection=False)
                
                if isinstance(results, list):
                    emotions = [r['emotion'] for r in results]
                else:
                    emotions = [results['emotion']]
                
                return {"emotions": emotions}
                
            elif self.analysis_type == "recognition":
                # Detect faces first
                boxes, probs = self.face_detector.detect(image_rgb)
                
                if boxes is None:
                    return {"recognitions": []}
                
                recognitions = []
                for box, prob in zip(boxes, probs):
                    if prob > 0.9:  # Confidence threshold
                        box = [int(b) for b in box]
                        
                        # Crop face
                        x1, y1, x2, y2 = box
                        face_img = image_rgb[y1:y2, x1:x2]
                        face_tensor = self.face_detector.extract(face_img, None, save_path=None)
                        
                        # Get embedding
                        with torch.no_grad():
                            embedding = self.face_recognizer(face_tensor.unsqueeze(0).to(self.device))
                        
                        # Compare with known faces
                        recognition = {"box": box, "confidence": float(prob), "identity": "unknown"}
                        
                        if self.known_faces:
                            best_match = None
                            best_distance = float('inf')
                            
                            for identity, known_embedding in self.known_faces.items():
                                distance = torch.nn.functional.pairwise_distance(embedding, known_embedding)
                                distance = distance.item()
                                
                                if distance < best_distance and distance < 0.6:  # Threshold
                                    best_distance = distance
                                    best_match = identity
                            
                            if best_match:
                                recognition["identity"] = best_match
                                recognition["distance"] = best_distance
                        
                        recognitions.append(recognition)
                
                return {"recognitions": recognitions}
            
            # Implementation for other analysis types...
            
            return {"error": "Unsupported analysis type"}
        except Exception as e:
            self.logger.error(f"Face analysis error: {e}")
            raise
    
    async def cleanup(self) -> None:
        """Clean up resources."""
        self.face_detector = None
        self.face_recognizer = None
        torch.cuda.empty_cache()
```

## Faza 6: Integracja z UnitMCP Runner (Tydzień 6)

### Etap 6.1: Tworzenie API Fasady AI dla Runnera (Dni 1-3)
- Implementacja jednolitego interfejsu dla wszystkich modułów AI
- Stworzenie fabryki modeli AI w zależności od konfiguracji

```python
# src/unitmcp/runner/ai_factory.py
import logging
import asyncio
from typing import Dict, Any, Optional, List, Type
from unitmcp.ai.common.model_interface import AIModelInterface
from unitmcp.ai.llm.ollama import OllamaModel
from unitmcp.ai.llm.claude import ClaudeModel
from unitmcp.ai.llm.openai import OpenAIModel
from unitmcp.ai.nlp.huggingface import HuggingFaceModel
from unitmcp.ai.nlp.spacy_integration import SpacyModel
from unitmcp.ai.speech.tts import TTSEngine
from unitmcp.ai.speech.stt import STTEngine
from unitmcp.ai.vision.object_detection import ObjectDetector
from unitmcp.ai.vision.face_analysis import FaceAnalyzer

class AIModelFactory:
    """Factory for creating AI models in UnitMCP Runner."""
    
    MODEL_TYPES = {
        # LLM models
        "ollama": OllamaModel,
        "claude": ClaudeModel,
        "openai": OpenAIModel,
        
        # NLP models
        "huggingface": HuggingFaceModel,
        "spacy": SpacyModel,
        
        # Speech models
        "tts": TTSEngine,
        "stt": STTEngine,
        
        # Vision models
        "object_detection": ObjectDetector,
        "face_analysis": FaceAnalyzer
    }
    
    @classmethod
    async def create_model(cls, model_type: str, config: Dict[str, Any]) -> AIModelInterface:
        """
        Create and initialize an AI model.
        
        Args:
            model_type: Type of model to create
            config: Configuration for the model
            
        Returns:
            Initialized AI model
            
        Raises:
            ValueError: If model type is not supported
        """
        if model_type not in cls.MODEL_TYPES:
            raise ValueError(f"Unsupported model type: {model_type}")
        
        model_class = cls.MODEL_TYPES[model_type]
        model = model_class()
        
        success = await model.initialize(config)
        if not success:
            raise RuntimeError(f"Failed to initialize {model_type} model")
        
        return model
```

### Etap 6.2: Integracja AI z Runnerem (Dni 4-5)
- Implementacja menedżera modeli AI w runnerze
- Wsparcie dla dynamicznego ładowania i zwalniania modeli

```python
# src/unitmcp/runner/ai_manager.py
import logging
import asyncio
from typing import Dict, Any, Optional, List
from unitmcp.runner.ai_factory import AIModelFactory
from unitmcp.ai.common.model_interface import AIModelInterface

class AIManager:
    """Manager for AI models in UnitMCP Runner."""
    
    def __init__(self):
        self.models = {}
        self.logger = logging.getLogger("UnitMCP-AIManager")
    
    async def load_model(self, model_id: str, model_type: str, config: Dict[str, Any]) -> bool:
        """
        Load and initialize an AI model.
        
        Args:
            model_id: Identifier for the model
            model_type: Type of model to load
            config: Configuration for the model
            
        Returns:
            True if model was loaded successfully, False otherwise
        """
        try:
            # Unload existing model with the same ID if it exists
            if model_id in self.models:
                await self.unload_model(model_id)
            
            # Create and initialize the model
            model = await AIModelFactory.create_model(model_type, config)
            self.models[model_id] = model
            
            self.logger.info(f"Model loaded: {model_id} ({model_type})")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load model {model_id}: {e}")
            return False
    
    async def process(self, model_id: str, input_data: Any) -> Any:
        """
        Process data using an AI model.
        
        Args:
            model_id: Identifier for the model
            input_data: Input data for processing
            
        Returns:
            Processing result
            
        Raises:
            ValueError: If model is not loaded
        """
        if model_id not in self.models:
            raise ValueError(f"Model not loaded: {model_id}")
        
        model = self.models[model_id]
        return await model.process(input_data)
    
    async def unload_model(self, model_id: str) -> bool:
        """
        Unload an AI model.
        
        Args:
            model_id: Identifier for the model
            
        Returns:
            True if model was unloaded successfully, False otherwise
        """
        if model_id not in self.models:
            return False
        
        try:
            model = self.models[model_id]
            await model.cleanup()
            del self.models[model_id]
            
            self.logger.info(f"Model unloaded: {model_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to unload model {model_id}: {e}")
            return False
    
    async def unload_all(self) -> None:
        """Unload all AI models."""
        model_ids = list(self.models.keys())
        for model_id in model_ids:
            await self.unload_model(model_id)
```

### Etap 6.3: Implementacja Interfejsu Konwersacyjnego (Dni 6-7)
- Integracja wszystkich modułów AI w interfejsie konwersacyjnym
- Wsparcie dla złożonych scenariuszy wykorzystujących wiele modeli AI

```python
# src/unitmcp/runner/conversation_manager.py
import logging
import asyncio
import json
from typing import Dict, Any, Optional, List
from unitmcp.runner.ai_manager import AIManager

class ConversationManager:
    """Manager for conversational interactions in UnitMCP Runner."""
    
    def __init__(self, ai_manager: AIManager):
        self.ai_manager = ai_manager
        self.conversations = {}
        self.logger = logging.getLogger("UnitMCP-ConversationManager")
    
    async def process_message(self, conversation_id: str, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a message in a conversation.
        
        Args:
            conversation_id: Identifier for the conversation
            message: Message text
            context: Additional context for processing
            
        Returns:
            Processing result
        """
        # Create conversation if it doesn't exist
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = {
                "history": [],
                "context": context or {}
            }
        
        conversation = self.conversations[conversation_id]
        
        # Add message to history
        conversation["history"].append({
            "role": "user",
            "content": message
        })
        
        # Update context
        if context:
            conversation["context"].update(context)
        
        # Process the message using the LLM
        llm_result = await self._process_with_llm(conversation_id, message)
        
        # Check for hardware commands or other AI tasks
        tasks = self._extract_tasks(llm_result)
        
        # Execute tasks if present
        task_results = {}
        if tasks:
            task_results = await self._execute_tasks(tasks, conversation["context"])
        
        # Generate final response
        response = await self._generate_response(conversation_id, llm_result, task_results)
        
        # Add response to history
        conversation["history"].append({
            "role": "assistant",
            "content": response
        })
        
        return {
            "response": response,
            "task_results": task_results
        }
    
    async def _process_with_llm(self, conversation_id: str, message: str) -> str:
        """Process a message using the LLM."""
        try:
            conversation = self.conversations[conversation_id]
            
            # Prepare input for LLM
            input_data = {
                "message": message,
                "history": conversation["history"],
                "context": conversation["context"]
            }
            
            # Process using the LLM
            return await self.ai_manager.process("llm", input_data)
        except Exception as e:
            self.logger.error(f"Error processing message with LLM: {e}")
            return f"Error processing message: {str(e)}"
    
    def _extract_tasks(self, llm_result: str) -> List[Dict[str, Any]]:
        """Extract AI and hardware tasks from LLM result."""
        tasks = []
        
        try:
            # Look for task markers in the result
            if "[[TASK:" in llm_result and "]]" in llm_result:
                task_markers = llm_result.split("[[TASK:")
                for marker in task_markers[1:]:
                    task_json = marker.split("]]")[0]
                    task = json.loads(task_json)
                    tasks.append(task)
        except Exception as e:
            self.logger.error(f"Error extracting tasks: {e}")
        
        return tasks
    
    async def _execute_tasks(self, tasks: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AI and hardware tasks."""
        results = {}
        
        for task in tasks:
            try:
                task_type = task.get("type")
                task_id = task.get("id")
                input_data = task.get("input")
                
                if not task_type or not task_id:
                    continue
                
                # Add context to input data
                if isinstance(input_data, dict):
                    input_data["context"] = context
                
                # Execute the task
                if task_type == "ai":
                    model_id = task.get("model_id")
                    if model_id:
                        result = await self.ai_manager.process(model_id, input_data)
                        results[task_id] = result
                elif task_type == "hardware":
                    # TODO: Implement hardware task execution
                    pass
            except Exception as e:
                self.logger.error(f"Error executing task {task.get('id')}: {e}")
                results[task.get("id")] = {"error": str(e)}
        
        return results
    
    async def _generate_response(self, conversation_id: str, llm_result: str, task_results: Dict[str, Any]) -> str:
        """Generate the final response."""
        try:
            # Remove task markers from the result
            response = llm_result
            if "[[TASK:" in response and "]]" in response:
                task_markers = response.split("[[TASK:")
                response = task_markers[0]
                for marker in task_markers[1:]:
                    if "]]" in marker:
                        response += marker.split("]]", 1)[1]
            
            # Replace task result placeholders
            if "[[RESULT:" in response and "]]" in response:
                for task_id, result in task_results.items():
                    placeholder = f"[[RESULT:{task_id}]]"
                    if placeholder in response:
                        result_str = str(result)
                        response = response.replace(placeholder, result_str)
            
            return response
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return "I encountered an error while processing your request. Please try again."
```

## Faza 7: Przykłady i Scenariusze Użycia (Tydzień 7-8)

### Etap 7.1: Implementacja Przykładów Podstawowych (Dni 1-3)
- Przygotowanie przykładów dla podstawowych modułów AI
- Implementacja prostych scenariuszy użycia

```python
# examples/ai/llm_examples.py
import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from unitmcp.ai.llm.ollama import OllamaModel
from unitmcp.ai.llm.claude import ClaudeModel

async def run_ollama_example():
    """Example of using Ollama LLM model."""
    print("Running Ollama LLM example...")
    
    # Initialize the model
    ollama = OllamaModel()
    config = {
        "host": "localhost",
        "port": 11434,
        "model": "llama3"
    }
    
    success = await ollama.initialize(config)
    if not success:
        print("Failed to initialize Ollama model")
        return
    
    try:
        # Process some queries
        queries = [
            "Explain how a Raspberry Pi GPIO works",
            "What are the key components of an LED circuit?",
            "Give me a simple Python example to control an LED"
        ]
        
        for query in queries:
            print(f"\nQuery: {query}")
            response = await ollama.process(query)
            print(f"Response: {response}")
    
    finally:
        # Clean up
        await ollama.cleanup()

async def run_claude_example():
    """Example of using Claude LLM model."""
    print("Running Claude LLM example...")
    
    # Check if API key is available
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Claude API key not found. Please set ANTHROPIC_API_KEY environment variable.")
        return
    
    # Initialize the model
    claude = ClaudeModel()
    config = {
        "api_key": api_key,
        "model": "claude-3-sonnet-20240229"
    }
    
    success = await claude.initialize(config)
    if not success:
        print("Failed to initialize Claude model")
        return
    
    try:
        # Process some queries
        queries = [
            "How can I set up a simple home automation system with Raspberry Pi?",
            "What sensors would be best for a weather monitoring station?",
            "Write a short Python script to read temperature from a DHT22 sensor"
        ]
        
        for query in queries:
            print(f"\nQuery: {query}")
            response = await claude.process(query)
            print(f"Response: {response}")
    
    finally:
        # Clean up
        await claude.cleanup()

async def main():
    """Run the LLM examples."""
    await run_ollama_example()
    print("\n" + "="*50 + "\n")
    await run_claude_example()

if __name__ == "__main__":
    asyncio.run(main())
```

### Etap 7.2: Implementacja Przykładów Multimodalnych (Dni 4-6)
- Przygotowanie przykładów łączących różne moduły AI
- Implementacja złożonych scenariuszy użycia

```python
# examples/ai/multimodal_example.py
import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from unitmcp.runner.ai_manager import AIManager
from unitmcp.runner.conversation_manager import ConversationManager

async def run_multimodal_example():
    """Example of using multiple AI models together."""
    print("Running multimodal AI example...")
    
    # Initialize AI manager
    ai_manager = AIManager()
    
    # Initialize conversation manager
    conversation_manager = ConversationManager(ai_manager)
    
    try:
        # Load LLM model
        llm_config = {
            "host": "localhost",
            "port": 11434,
            "model": "llama3"
        }
        await ai_manager.load_model("llm", "ollama", llm_config)
        
        # Load TTS model
        tts_config = {
            "engine": "pyttsx3",
            "rate": 150,
            "volume": 1.0
        }
        await ai_manager.load_model("tts", "tts", tts_config)
        
        # Load STT model
        stt_config = {
            "engine": "google",
            "language": "en-US"
        }
        await ai_manager.load_model("stt", "stt", stt_config)
        
        # Load object detection model
        object_config = {
            "detector_type": "detr",
            "threshold": 0.5
        }
        await ai_manager.load_model("object_detector", "object_detection", object_config)
        
        # Create a new conversation
        conversation_id = "multimodal_example"
        
        # Scenario 1: Text to speech
        print("\nScenario 1: Text to speech")
        message = "Convert this text to speech: 'Hello, I am UnitMCP, your hardware assistant.'"
        result = await conversation_manager.process_message(conversation_id, message)
        print(f"Response: {result['response']}")
        
        # Scenario 2: Object detection
        print("\nScenario 2: Object detection")
        message = "Detect objects in the image 'examples/ai/data/test_image.jpg'"
        result = await conversation_manager.process_message(conversation_id, message)
        print(f"Response: {result['response']}")
        
        # Scenario 3: Combined voice and vision
        print("\nScenario 3: Combined voice and vision")
        message = "Analyze the image 'examples/ai/data/room.jpg' and describe what you see using speech output"
        result = await conversation_manager.process_message(conversation_id, message)
        print(f"Response: {result['response']}")
        
        # Scenario 4: Hardware control
        print("\nScenario 4: Hardware control")
        message = "Turn on the LED on pin 17 and blink it 3 times"
        result = await conversation_manager.process_message(conversation_id, message)
        print(f"Response: {result['response']}")
    
    finally:
        # Clean up
        await ai_manager.unload_all()

async def main():
    """Run the multimodal example."""
    await run_multimodal_example()

if __name__ == "__main__":
    asyncio.run(main())
```

### Etap 7.3: Dokumentacja i Instrukcje Użycia (Dni 7-8)
- Przygotowanie szczegółowej dokumentacji modułów AI
- Implementacja przewodników i tutoriali

```markdown
# UnitMCP AI Modules Guide

This guide explains how to use the AI modules in UnitMCP for various tasks.

## Overview

UnitMCP includes several AI modules for different purposes:

- **LLM (Large Language Models)**: For natural language processing and generation
- **NLP (Natural Language Processing)**: For text analysis and understanding
- **Speech**: For text-to-speech (TTS) and speech-to-text (STT)
- **Vision**: For image processing and computer vision
- **ML (Machine Learning)**: For various machine learning tasks

## Getting Started

### Basic Usage

Here's a simple example of using an LLM model:

```python
from unitmcp.ai.llm.ollama import OllamaModel

async def main():
    # Initialize the model
    ollama = OllamaModel()
    await ollama.initialize({"model": "llama3"})
    
    # Process a query
    response = await ollama.process("How can I control an LED with Raspberry Pi?")
    print(response)
    
    # Clean up
    await ollama.cleanup()
```

### Using the AI Manager

For more complex scenarios, use the AI Manager:

```python
from unitmcp.runner.ai_manager import AIManager

async def main():
    # Initialize AI manager
    ai_manager = AIManager()
    
    # Load models
    await ai_manager.load_model("llm", "ollama", {"model": "llama3"})
    await ai_manager.load_model("tts", "tts", {"engine": "pyttsx3"})
    
    # Process with LLM
    llm_result = await ai_manager.process("llm", "Generate a greeting")
    
    # Convert to speech
    await ai_manager.process("tts", llm_result)
    
    # Clean up
    await ai_manager.unload_all()
```

## Available Models

### LLM Models

- **Ollama**: Local LLM models like Llama, Mistral, etc.
- **Claude**: Anthropic's Claude models (requires API key)
- **OpenAI**: OpenAI's GPT models (requires API key)

### NLP Models

- **HuggingFace**: Various NLP models from Hugging Face
- **spaCy**: For efficient NLP tasks like NER, POS tagging, etc.

### Speech Models

- **TTS Engines**: pyttsx3, gTTS, Coqui, etc.
- **STT Engines**: Google, Whisper, Sphinx, etc.

### Vision Models

- **Object Detection**: DETR, YOLO, etc.
- **Face Analysis**: Face detection, recognition, emotion analysis, etc.
- **Image Processing**: Basic image processing functions

## Configuration

Each model has its own configuration options. Here are some examples:

### Ollama Configuration

```python
config = {
    "host": "localhost",
    "port": 11434,
    "model": "llama3",
    "temperature": 0.7,
    "max_tokens": 1000
}
```

### Claude Configuration

```python
config = {
    "api_key": "your-api-key",
    "model": "claude-3-sonnet-20240229",
    "temperature": 0.7,
    "max_tokens": 1000
}
```

### TTS Configuration

```python
config = {
    "engine": "pyttsx3",
    "voice": None,  # Use default voice
    "rate": 150,
    "volume": 1.0
}
```

## Advanced Usage

### Combining Models in a Pipeline

You can combine multiple AI models in a pipeline:

```python
async def ai_pipeline(image_path, audio_output_path):
    # Initialize AI manager
    ai_manager = AIManager()
    
    # Load models
    await ai_manager.load_model("object_detector", "object_detection", {"detector_type": "detr"})
    await ai_manager.load_model("llm", "ollama", {"model": "llama3"})
    await ai_manager.load_model("tts", "tts", {"engine": "pyttsx3"})
    
    try:
        # Detect objects in image
        detection_result = await ai_manager.process("object_detector", image_path)
        
        # Generate description using LLM
        prompt = f"Describe this scene with these objects: {detection_result['detections']}"
        description = await ai_manager.process("llm", prompt)
        
        # Convert description to speech
        await ai_manager.process("tts", {"text": description, "output_file": audio_output_path})
        
        return {
            "detections": detection_result,
            "description": description,
            "audio_path": audio_output_path
        }
    
    finally:
        # Clean up
        await ai_manager.unload_all()
```

### Using the Conversation Manager

For interactive applications, use the Conversation Manager:

```python
from unitmcp.runner.ai_manager import AIManager
from unitmcp.runner.conversation_manager import ConversationManager

async def interactive_session():
    # Initialize managers
    ai_manager = AIManager()
    conversation_manager = ConversationManager(ai_manager)
    
    # Load LLM model
    await ai_manager.load_model("llm", "ollama", {"model": "llama3"})
    
    # Create conversation
    conversation_id = "interactive_session"
    
    try:
        while True:
            # Get user input
            user_input = input("> ")
            if user_input.lower() in ["exit", "quit", "q"]:
                break
            
            # Process message
            result = await conversation_manager.process_message(conversation_id, user_input)
            
            # Print response
            print(result["response"])
    
    finally:
        # Clean up
        await ai_manager.unload_all()
```

## Troubleshooting

### Common Issues

- **Model Initialization Failures**: Check configuration, API keys, and network connectivity
- **GPU Memory Issues**: Try reducing model size or switching to CPU
- **Performance Issues**: Consider optimizing configurations or using lighter models

### Getting Help

For more help, refer to the documentation or open an issue on the UnitMCP GitHub repository.
```

## Podsumowanie Rozszerzonego Planu

Ten rozszerzony plan wdrożenia UnitMCP Runner z zaawansowanym wsparciem dla AI oferuje:

1. **Jednolity Interfejs AI**: Umożliwiający łatwą integrację różnych technologii AI
2. **Wsparcie dla Wielu Modeli**: Od prostych lokalnych modeli po zaawansowane API
3. **Multimodalne Zdolności**: Integracja tekstu, mowy, obrazu i kontroli sprzętu
4. **Skalowalność**: Od prostych zapytań po złożone scenariusze łączące wiele technologii
5. **Łatwość Rozbudowy**: Modułowa architektura umożliwiająca dodawanie nowych modeli i funkcji

Plan ten znacznie rozszerza możliwości UnitMCP, przekształcając go z prostego systemu sterowania sprzętem w zaawansowaną platformę do tworzenia inteligentnych, multimodalnych aplikacji IoT.