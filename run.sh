#!/bin/bash
echo "Starting LORA Trainer..."

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "Error: pip is not installed. Please install Python and pip first."
    exit 1
fi

# Check if requirements are installed
echo "Checking requirements..."
pip freeze | grep -i opencv-python > /dev/null || MISSING=1
pip freeze | grep -i pillow > /dev/null || MISSING=1
pip freeze | grep -i gradio > /dev/null || MISSING=1
pip freeze | grep -i python-dotenv > /dev/null || MISSING=1
pip freeze | grep -i fal-client > /dev/null || MISSING=1
pip freeze | grep -i requests > /dev/null || MISSING=1
pip freeze | grep -i numpy > /dev/null || MISSING=1

# Install requirements if needed
if [ ! -z "$MISSING" ]; then
    echo "Some requirements are missing. Installing now..."
    pip install -r requirements.txt
else
    echo "All requirements are installed."
fi

# Run the application
python lora_trainer.py