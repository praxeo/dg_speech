"""
Build script for creating standalone Windows executable
Uses PyInstaller to bundle all dependencies
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def clean_build_folders():
    """Remove old build artifacts"""
    folders = ['build', 'dist', '__pycache__']
    for folder in folders:
        if os.path.exists(folder):
            print(f"Cleaning {folder}...")
            shutil.rmtree(folder)
    
    # Remove .spec file if exists
    spec_file = "deepgram_dictation.spec"
    if os.path.exists(spec_file):
        os.remove(spec_file)


def build_executable():
    """Build the executable using PyInstaller"""
    
    print("=" * 50)
    print("Building Deepgram Medical Dictation Tool")
    print("=" * 50)
    
    # Clean old builds
    clean_build_folders()
    
    # PyInstaller command with optimizations
    command = [
        sys.executable, "-m", "PyInstaller",
        
        # Single file executable
        "--onefile",
        
        # Console application (not windowed)
        "--console",
        
        # Name of the executable
        "--name", "deepgram_dictation",
        
        # Icon (optional - create .ico file if needed)
        # "--icon", "icon.ico",
        
        # Clean build
        "--clean",
        
        # Paths to search for imports
        "--paths", ".",
        
        # Hidden imports that PyInstaller might miss
        "--hidden-import", "websocket",
        "--hidden-import", "pynput.keyboard._win32",
        "--hidden-import", "pynput.mouse._win32",
        
        # Exclude unnecessary modules to reduce size
        "--exclude-module", "matplotlib",
        "--exclude-module", "numpy",
        "--exclude-module", "pandas",
        "--exclude-module", "scipy",
        "--exclude-module", "PIL",
        "--exclude-module", "tkinter",
        "--exclude-module", "PyQt5",
        "--exclude-module", "PyQt6",
        "--exclude-module", "PySide2",
        "--exclude-module", "PySide6",
        
        # Optimization level
        "-O", "2",
        
        # Main script
        "deepgram_dictation.py"
    ]
    
    # Add Windows-specific options
    if sys.platform == "win32":
        command.extend([
            # Windows UAC settings (no admin required)
            "--uac-admin", "False",
            
            # Version information (optional)
            # "--version-file", "version_info.txt",
        ])
    
    print("Running PyInstaller...")
    print(" ".join(command))
    
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(result.stdout)
        
        if result.stderr:
            print("Warnings:", result.stderr)
        
        print("\nBuild successful!")
        
        # Get executable path
        exe_path = Path("dist") / "deepgram_dictation.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"Executable created: {exe_path}")
            print(f"  Size: {size_mb:.1f} MB")
            
            # Copy config template to dist folder
            copy_config_template()
            
            # Optional: Apply UPX compression
            if check_upx_available():
                compress_with_upx(exe_path)
        
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed: {e}")
        print(e.stdout)
        print(e.stderr)
        sys.exit(1)


def copy_config_template():
    """Copy configuration template to dist folder"""
    config_src = "config.json"
    config_dst = Path("dist") / "config.json"
    
    # Create template if it doesn't exist
    if not os.path.exists(config_src):
        create_config_template()
    
    if os.path.exists(config_src):
        shutil.copy2(config_src, config_dst)
        print("Config template copied to dist folder")


def create_config_template():
    """Create a configuration template file"""
    import json
    from config_manager import ConfigManager
    
    config = ConfigManager.DEFAULT_CONFIG.copy()
    
    # Clear sensitive data
    config["api_key"] = ""
    
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    
    print("Configuration template created")


def check_upx_available():
    """Check if UPX is available for compression"""
    try:
        result = subprocess.run(["upx", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def compress_with_upx(exe_path):
    """Compress executable with UPX
    
    Args:
        exe_path: Path to the executable
    """
    print("\nApplying UPX compression...")
    
    try:
        # UPX command with best compression
        command = [
            "upx",
            "--best",  # Best compression
            "--lzma",  # Use LZMA compression
            str(exe_path)
        ]
        
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(result.stdout)
        
        # Check new size
        new_size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"Compressed to: {new_size_mb:.1f} MB")
        
    except subprocess.CalledProcessError as e:
        print(f"Warning: UPX compression failed: {e}")
        print("Executable will work but won't be compressed")
    except FileNotFoundError:
        print("UPX not found. Skipping compression.")
        print("To enable compression, install UPX: https://upx.github.io/")


def create_readme():
    """Create README file for distribution"""
    readme_content = """
# Deepgram Medical Dictation Tool

## Quick Start

1. **First Run**:
   - Double-click `deepgram_dictation.exe`
   - Enter your Deepgram API key when prompted
   - The key can be saved (encrypted) for future use

2. **How to Use**:
   - Hold CTRL (left or right) to record
   - Release CTRL to stop and transcribe
   - Text is automatically copied to clipboard

3. **Controls**:
   - CTRL: Push-to-talk recording
   - P: Toggle preview mode
   - L: Toggle logging
   - ESC: Exit application

4. **Configuration** (Optional):
   - Edit `config.json` to customize settings
   - Modify push-to-talk key, model, language, etc.

5. **Preview Mode**:
   - When enabled: Review text before copying
   - ENTER to copy, ESC to discard
   - When disabled: Auto-copy to clipboard

## Requirements

- Windows 10/11
- Microphone access
- Internet connection
- Deepgram API key (get at https://deepgram.com)

## Troubleshooting

- If Windows Defender blocks the app, click "More info" → "Run anyway"
- For microphone issues, check Windows privacy settings
- Logs are saved in `logs/` folder when logging is enabled

## Support

For issues or questions, check the logs folder or enable debug logging in config.json
"""
    
    readme_path = Path("dist") / "README.txt"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content.strip())
    
    print("README created")


def main():
    """Main build process"""
    
    # Check if running on Windows
    if sys.platform != "win32":
        print("Warning: This build script is optimized for Windows.")
        print("The executable will be built but may not work correctly on non-Windows systems.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)
    
    # Check for required files
    required_files = ["deepgram_dictation.py", "config_manager.py", "logger.py"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"Error: Missing required files: {missing_files}")
        sys.exit(1)
    
    # Build the executable
    build_executable()
    
    # Create distribution README
    create_readme()
    
    print("\n" + "=" * 50)
    print("Build Complete!")
    print("=" * 50)
    print("\nDistribution files in 'dist' folder:")
    print("  - deepgram_dictation.exe")
    print("  - config.json (template)")
    print("  - README.txt")
    print("\nTo use:")
    print("1. Copy the 'dist' folder contents to any location")
    print("2. Run deepgram_dictation.exe")
    print("3. Enter your Deepgram API key")
    print("4. Hold CTRL to dictate!")


if __name__ == "__main__":
    main()