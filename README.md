# Deepgram Nova-3 Medical Transcription Tool

A portable, push-to-talk medical dictation tool that uses Deepgram's Nova-3 Medical API for accurate real-time transcription. The transcribed text is automatically copied to your clipboard for easy pasting into medical records, notes, or any application.

## Features

- **Push-to-Talk**: Hold CTRL to record, release to transcribe
- **Medical-Optimized**: Uses Deepgram Nova-3 Medical model for accurate medical terminology
- **Instant Clipboard**: Transcribed text automatically copied to clipboard
- **Preview Mode**: Optionally review text before copying
- **Completely Portable**: Single .exe file, no installation required
- **Privacy-First**: HIPAA-friendly logging with text redaction
- **Configurable**: JSON configuration for customization
- **IT-Friendly**: Designed to work within enterprise IT policies

## Quick Start (No Python Required!)

### Option 1: Download Pre-Built Executable ⭐ RECOMMENDED

1. **Download the latest release:**
   - Go to [Releases](https://github.com/praxeo/dg_speech/releases)
   - Download `deepgram_dictation_windows.zip`
   - Extract to any folder

2. **Run the application:**
   - Double-click `deepgram_dictation.exe`
   - Enter your Deepgram API key
   - Start dictating with CTRL!

**No Python, no installation, no dependencies required!**

### Option 2: Build from Source (Requires Python)

If you want to modify the code or build it yourself:

#### 1. Get a Deepgram API Key
- Sign up at [https://deepgram.com](https://deepgram.com)
- Create an API key with access to Nova-3 Medical model

#### 2. Install Python (if not installed)
- Download from [python.org](https://www.python.org/downloads/)
- During installation, check "Add Python to PATH"

#### 3. Build the Executable

```bash
# Install dependencies
pip install -r requirements.txt

# Build the executable
python build.py
```

The executable will be created in the `dist/` folder.

## How to Use

1. **First Run**:
   - Double-click `deepgram_dictation.exe`
   - Enter your Deepgram API key when prompted
   - Choose whether to save the key (encrypted) for future use

2. **Using the Tool**:
   - Hold CTRL (left or right) to start recording
   - Speak clearly into your microphone
   - Release CTRL to stop recording and transcribe
   - The text is automatically copied to your clipboard
   - Paste (Ctrl+V) anywhere you need the text

## Controls

| Key | Action |
|-----|--------|
| **CTRL** | Hold to record (push-to-talk) |
| **P** | Toggle preview mode on/off |
| **L** | Toggle logging on/off |
| **ESC** | Exit application |

### Preview Mode
- **When ON**: Shows transcribed text before copying
  - Press ENTER to copy to clipboard
  - Press ESC to discard
- **When OFF**: Automatically copies to clipboard

## Configuration

Edit `config.json` in the same directory as the executable:

```json
{
  "api_key": "",                    // Encrypted API key (set via app)
  "push_to_talk_key": "ctrl",       // Options: ctrl, alt, shift, f1-f12
  "preview_mode": true,              // Show text before copying
  "auto_punctuation": true,          // Automatic punctuation
  "model": "nova-3-medical",         // Deepgram model
  "language": "en-US",               // English locales: en, en-US, en-AU, en-CA, en-GB, en-IE, en-IN, en-NZ
  "save_transcriptions": false,      // Save to text files
  "transcription_folder": "./transcriptions",
  "sound_feedback": true,            // Beep on start/stop
  "min_recording_duration": 0.5,     // Minimum seconds
  "max_recording_duration": 300,     // Maximum seconds (5 min)
  "logging": {
    "enabled": false,                // Enable logging
    "level": "INFO",                 // DEBUG, INFO, WARNING, ERROR
    "file": "./logs/dictation.log",
    "max_size_mb": 10,
    "keep_days": 7,
    "console_output": false,
    "privacy_mode": true             // Redact text from logs
  }
}
```

## Privacy & Security

- **No Installation**: Runs from a single portable executable
- **Local Operation**: All processing happens on your machine
- **Encrypted Storage**: API keys are encrypted when saved
- **Privacy Mode**: Logs can redact transcribed text (HIPAA-friendly)
- **No Telemetry**: No data collection or tracking

## System Requirements

- **OS**: Windows 10/11 (64-bit)
- **RAM**: 512 MB minimum
- **Disk**: ~15 MB for executable
- **Network**: Internet connection for Deepgram API
- **Audio**: Working microphone

## Troubleshooting

### Windows Defender / Antivirus
If Windows Defender blocks the executable:
1. Click "More info" on the SmartScreen prompt
2. Click "Run anyway"
3. Or add an exclusion in Windows Security settings

### Microphone Issues
- Check Windows Privacy Settings → Microphone
- Ensure the app has microphone permissions
- Test microphone in Windows Sound Settings

### API Connection Issues
- Verify your API key is correct
- Check internet connection
- Enable logging to see detailed errors
- Ensure firewall allows outbound HTTPS (port 443)

### No Audio Recording
- Check if another application is using the microphone
- Restart the application
- Try running as Administrator (if microphone is restricted)

## Downloads

### Latest Release
Download the pre-built executable from the [Releases page](https://github.com/praxeo/dg_speech/releases).

**What's included:**
- `deepgram_dictation.exe` - The standalone executable
- `config.json` - Configuration template
- `README.txt` - Quick start guide

**No Python required!** Just download, extract, and run.

## Building from Source

<details>
<summary>Click to expand build instructions</summary>

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Windows development environment

### Build Steps

1. Clone or download the source code:
   ```bash
   git clone https://github.com/praxeo/dg_speech.git
   cd dg_speech
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the build script:
   ```bash
   python build.py
   ```

4. Find the executable in `dist/deepgram_dictation.exe`

### Optional: UPX Compression
To reduce file size by ~50%:
1. Download UPX from [https://upx.github.io/](https://upx.github.io/)
2. Add UPX to your PATH
3. The build script will automatically compress the executable

</details>

## File Structure

```
deepgram_dictation.exe    # Main executable
config.json              # Configuration file (optional)
logs/                    # Log files (when logging enabled)
  └── dictation.log
transcriptions/          # Saved transcriptions (optional)
  └── transcription_[timestamp].txt
```

## Use Cases

- **Medical Documentation**: Quickly dictate patient notes, observations, and reports
- **Clinical Notes**: Record consultation summaries and treatment plans
- **Research**: Transcribe interviews and observations
- **General Dictation**: Any scenario requiring hands-free text input

## License

This tool is provided as-is for medical professionals and healthcare organizations. Please ensure compliance with your organization's data handling and privacy policies.

## Support

For issues or questions:
1. Enable debug logging in `config.json`
2. Check the `logs/dictation.log` file
3. Review the troubleshooting section above

## Acknowledgments

- Powered by [Deepgram](https://deepgram.com) Nova-3 Medical API
- Built with Python and PyInstaller
