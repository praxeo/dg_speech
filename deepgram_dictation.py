"""
Deepgram Medical Dictation Tool
Push-to-talk medical transcription with clipboard integration
"""

import asyncio
import json
import os
import sys
import threading
import time
import wave
import io
from datetime import datetime
from getpass import getpass
from typing import Optional, List
import queue

# Audio and system libraries
import pyaudio
import pyperclip
from pynput import keyboard
import websocket
import ssl

# Custom modules
from config_manager import ConfigManager
from logger import DictationLogger


class AudioRecorder:
    """Handles audio recording from microphone"""
    
    def __init__(self, logger: DictationLogger):
        self.logger = logger
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_size = 1024
        self.format = pyaudio.paInt16
        
        # Find default microphone
        self.device_index = self._find_default_mic()
        
    def _find_default_mic(self):
        """Find the default microphone device"""
        try:
            info = self.audio.get_host_api_info_by_index(0)
            num_devices = info.get('deviceCount')
            
            for i in range(num_devices):
                device_info = self.audio.get_device_info_by_host_api_device_index(0, i)
                if device_info.get('maxInputChannels') > 0:
                    device_name = device_info.get('name', 'Unknown')
                    self.logger.log_audio_info(device_name, self.sample_rate, self.channels)
                    return i
            
            return None
        except Exception as e:
            self.logger.error(f"Error finding microphone: {e}")
            return None
    
    def start_recording(self):
        """Start recording audio"""
        if self.is_recording:
            return
        
        try:
            self.frames = []
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            self.is_recording = True
            self.stream.start_stream()
            self.logger.info("Recording started")
        except Exception as e:
            self.logger.error(f"Error starting recording: {e}")
            raise
    
    def stop_recording(self):
        """Stop recording and return audio data"""
        if not self.is_recording:
            return None
        
        try:
            self.is_recording = False
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            
            # Convert frames to WAV format
            audio_data = b''.join(self.frames)
            duration = len(audio_data) / (self.sample_rate * 2)  # 2 bytes per sample
            
            self.logger.info(f"Recording stopped ({duration:.1f} seconds)")
            
            # Create WAV file in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(self.audio.get_sample_size(self.format))
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data)
            
            wav_buffer.seek(0)
            return wav_buffer.getvalue(), duration
            
        except Exception as e:
            self.logger.error(f"Error stopping recording: {e}")
            return None, 0
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream"""
        if self.is_recording:
            self.frames.append(in_data)
        return (in_data, pyaudio.paContinue)
    
    def cleanup(self):
        """Clean up audio resources"""
        if self.stream:
            self.stream.close()
        self.audio.terminate()


class DeepgramTranscriber:
    """Handles connection to Deepgram API and transcription"""
    
    def __init__(self, api_key: str, config: ConfigManager, logger: DictationLogger):
        self.api_key = api_key
        self.config = config
        self.logger = logger
        self.ws = None
        self.transcription_result = None
        self.connection_event = threading.Event()
        
    def transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """Transcribe audio using Deepgram API
        
        Args:
            audio_data: WAV audio data
            
        Returns:
            Transcribed text or None if failed
        """
        try:
            # Build WebSocket URL with parameters
            model = self.config.get('model', 'nova-2-medical')
            language = self.config.get('language', 'en-US')
            punctuate = str(self.config.get('auto_punctuation', True)).lower()
            
            url = f"wss://api.deepgram.com/v1/listen"
            url += f"?model={model}"
            url += f"&language={language}"
            url += f"&punctuate={punctuate}"
            url += "&encoding=linear16"
            url += "&sample_rate=16000"
            url += "&channels=1"
            
            self.logger.info(f"Connecting to Deepgram API (Model: {model})")
            
            # Reset result
            self.transcription_result = None
            self.connection_event.clear()
            
            # Create WebSocket connection
            self.ws = websocket.WebSocketApp(
                url,
                header={"Authorization": f"Token {self.api_key}"},
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            
            # Start WebSocket in separate thread
            ws_thread = threading.Thread(
                target=lambda: self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
            )
            ws_thread.daemon = True
            ws_thread.start()
            
            # Wait for connection
            if not self.connection_event.wait(timeout=5):
                self.logger.error("Timeout connecting to Deepgram API")
                return None
            
            # Send audio data
            self.ws.send(audio_data, opcode=websocket.ABNF.OPCODE_BINARY)
            
            # Send close message to indicate end of audio
            self.ws.send(json.dumps({"type": "CloseStream"}))
            
            # Wait for transcription result
            start_time = time.time()
            while self.transcription_result is None and (time.time() - start_time) < 10:
                time.sleep(0.1)
            
            # Close WebSocket
            if self.ws:
                self.ws.close()
            
            return self.transcription_result
            
        except Exception as e:
            self.logger.error(f"Error during transcription: {e}")
            return None
    
    def _on_open(self, ws):
        """WebSocket opened callback"""
        self.logger.debug("WebSocket connection opened")
        self.connection_event.set()
    
    def _on_message(self, ws, message):
        """WebSocket message received callback"""
        try:
            response = json.loads(message)
            
            if response.get('type') == 'Results':
                alternatives = response.get('channel', {}).get('alternatives', [])
                if alternatives and alternatives[0].get('transcript'):
                    transcript = alternatives[0]['transcript']
                    confidence = alternatives[0].get('confidence', 0)
                    
                    # Count words
                    word_count = len(transcript.split()) if transcript else 0
                    
                    self.logger.log_transcription(
                        duration=0,  # Will be updated by caller
                        confidence=confidence,
                        word_count=word_count
                    )
                    
                    self.transcription_result = transcript
                    
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing response: {e}")
    
    def _on_error(self, ws, error):
        """WebSocket error callback"""
        self.logger.error(f"WebSocket error: {error}")
        self.connection_event.set()  # Unblock waiting thread
    
    def _on_close(self, ws, close_status_code, close_msg):
        """WebSocket closed callback"""
        self.logger.debug("WebSocket connection closed")


class DictationApp:
    """Main application class"""
    
    def __init__(self):
        # Initialize configuration
        self.config = ConfigManager()
        
        # Initialize logger
        self.logger = DictationLogger(self.config)
        
        # Initialize components
        self.recorder = AudioRecorder(self.logger)
        self.transcriber = None
        self.api_key = None
        
        # State variables
        self.is_recording = False
        self.preview_mode = self.config.get('preview_mode', True)
        self.running = True
        self.ctrl_pressed = False
        
        # UI state
        self.status = "Ready"
        self.last_transcription = ""
        
    def get_api_key(self):
        """Get API key from config or user input"""
        # Try to get from config
        stored_key = self.config.get('api_key', '')
        if stored_key:
            # Try to decrypt
            decrypted = self.config.decrypt_api_key(stored_key)
            if decrypted:
                self.logger.info("Using stored API key")
                return decrypted
        
        # Get from user
        print("\n" + "=" * 50)
        print("   Deepgram Medical Dictation Tool")
        print("=" * 50)
        print("\nEnter your Deepgram API key:")
        api_key = getpass("API Key: ")
        
        # Ask if user wants to save it
        save = input("\nSave API key for future use? (y/n): ").lower() == 'y'
        if save:
            encrypted = self.config.encrypt_api_key(api_key)
            self.config.set('api_key', encrypted)
            self.config.save_config()
            print("API key saved (encrypted)")
        
        return api_key
    
    def display_ui(self):
        """Display the console UI"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("=" * 50)
        print("   Deepgram Medical Dictation Tool")
        print("=" * 50)
        print()
        print(f"[Status: {self.status}]")
        print(f"Display Mode: Preview {'ON' if self.preview_mode else 'OFF'}")
        print()
        print("Instructions:")
        print("- Hold CTRL to record (left or right)")
        print("- Release to transcribe")
        if self.preview_mode:
            print("- Preview mode: Review before copying")
        else:
            print("- Auto mode: Direct to clipboard")
        print("- Press 'P' to toggle preview mode")
        print("- Press 'L' to toggle logging")
        print("- Press ESC to exit")
        print()
        
        if self.last_transcription:
            preview = self.last_transcription[:50]
            if len(self.last_transcription) > 50:
                preview += "..."
            print(f"Last transcription: {preview}")
    
    def show_preview(self, text: str) -> bool:
        """Show preview and get user decision
        
        Args:
            text: Text to preview
            
        Returns:
            True to copy to clipboard, False to discard
        """
        print("\n" + "-" * 40)
        print("Transcribed Text:")
        print(text)
        print("-" * 40)
        print("[ENTER] Copy to clipboard  [ESC] Discard")
        
        # Wait for user input
        with keyboard.Events() as events:
            for event in events:
                if isinstance(event, keyboard.Events.Press):
                    if event.key == keyboard.Key.enter:
                        return True
                    elif event.key == keyboard.Key.esc:
                        return False
    
    def on_press(self, key):
        """Handle key press events"""
        try:
            # Check for CTRL key
            if key in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
                if not self.ctrl_pressed and not self.is_recording:
                    self.ctrl_pressed = True
                    self.start_recording()
            
            # Check for other keys
            elif hasattr(key, 'char'):
                if key.char and key.char.lower() == 'p':
                    self.preview_mode = not self.preview_mode
                    self.config.set('preview_mode', self.preview_mode)
                    self.display_ui()
                elif key.char and key.char.lower() == 'l':
                    self.logger.toggle_logging()
                    
        except AttributeError:
            pass
    
    def on_release(self, key):
        """Handle key release events"""
        # Check for CTRL release
        if key in [keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
            if self.ctrl_pressed and self.is_recording:
                self.ctrl_pressed = False
                self.stop_recording()
        
        # Check for ESC
        elif key == keyboard.Key.esc:
            self.running = False
            return False  # Stop listener
    
    def start_recording(self):
        """Start recording audio"""
        if self.is_recording:
            return
        
        self.is_recording = True
        self.status = "Recording..."
        self.display_ui()
        
        # Play sound feedback if enabled
        if self.config.get('sound_feedback', True):
            self.play_beep(frequency=1000, duration=100)
        
        # Start recording
        self.recorder.start_recording()
    
    def stop_recording(self):
        """Stop recording and process transcription"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        self.status = "Transcribing..."
        self.display_ui()
        
        # Play sound feedback if enabled
        if self.config.get('sound_feedback', True):
            self.play_beep(frequency=800, duration=100)
        
        # Stop recording and get audio
        audio_data, duration = self.recorder.stop_recording()
        
        if audio_data and duration >= self.config.get('min_recording_duration', 0.5):
            # Transcribe audio
            text = self.transcriber.transcribe_audio(audio_data)
            
            if text:
                self.last_transcription = text
                
                # Handle preview mode
                if self.preview_mode:
                    if self.show_preview(text):
                        pyperclip.copy(text)
                        self.status = "Copied!"
                        self.logger.info("Text copied to clipboard")
                    else:
                        self.status = "Discarded"
                        self.logger.info("Text discarded by user")
                else:
                    # Auto copy
                    pyperclip.copy(text)
                    self.status = "Copied!"
                    self.logger.info("Text copied to clipboard")
                
                # Save transcription if enabled
                if self.config.get('save_transcriptions', False):
                    self.save_transcription(text)
            else:
                self.status = "Transcription failed"
                self.logger.error("Transcription failed")
        else:
            self.status = "Recording too short"
            self.logger.warning(f"Recording too short: {duration:.1f}s")
        
        self.display_ui()
    
    def save_transcription(self, text: str):
        """Save transcription to file
        
        Args:
            text: Transcribed text to save
        """
        try:
            folder = self.config.get('transcription_folder', './transcriptions')
            os.makedirs(folder, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(folder, f"transcription_{timestamp}.txt")
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(text)
            
            self.logger.info(f"Transcription saved to: {filename}")
            
        except Exception as e:
            self.logger.error(f"Error saving transcription: {e}")
    
    def play_beep(self, frequency: int = 1000, duration: int = 100):
        """Play a beep sound (Windows only)
        
        Args:
            frequency: Frequency in Hz
            duration: Duration in milliseconds
        """
        try:
            if sys.platform == 'win32':
                import winsound
                winsound.Beep(frequency, duration)
        except Exception:
            pass  # Silently fail if sound not available
    
    def run(self):
        """Main application loop"""
        try:
            # Get API key
            self.api_key = self.get_api_key()
            
            # Initialize transcriber
            self.transcriber = DeepgramTranscriber(
                self.api_key,
                self.config,
                self.logger
            )
            
            # Display initial UI
            self.display_ui()
            
            # Start keyboard listener
            with keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release
            ) as listener:
                listener.join()
            
        except KeyboardInterrupt:
            print("\nShutting down...")
        except Exception as e:
            self.logger.exception(f"Fatal error: {e}")
            print(f"\nError: {e}")
            input("Press Enter to exit...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        self.logger.info("Shutting down application")
        
        if self.recorder:
            self.recorder.cleanup()
        
        if self.logger:
            self.logger.close()
        
        print("\nGoodbye!")


def main():
    """Main entry point"""
    app = DictationApp()
    app.run()


if __name__ == "__main__":
    main()