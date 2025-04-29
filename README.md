 # LORA Trainer

This application automates the process of extracting frames from videos, resizing them, and training a LORA model using the FAL API.

## Features

- Extract frames from videos at specified intervals
- Resize and crop images to 1024x1024
- Web interface for selecting images for training
- Integration with FAL API for LORA model training
- Automatic download of trained model files

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project directory and add your FAL API key:
   ```
   FAL_KEY=your_fal_api_key
   ```

## Usage

1. Run the application:
   ```
   python lora_trainer.py
   ```

2. In the web interface:
   - Enter the path to the folder containing your videos
   - Set the frame extraction interval (in seconds)
   - Provide a prefix for the renamed images
   - Click "Process Videos" to extract and resize frames
   - Select images for training by clicking on them in the gallery
   - Configure LORA training parameters
   - Click "Train LORA Model" to start training

3. After training completes, the model files will be downloaded to your current directory.

## Requirements

- Python 3.7+
- OpenCV
- Pillow
- Gradio
- FAL Client

## Notes

- Training may take several minutes depending on the number of images and training steps
- The application creates temporary directories for processing
- Selected images are automatically zipped and uploaded to FAL for training