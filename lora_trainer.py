import os
import sys
import cv2
import zipfile
import subprocess
import base64
from pathlib import Path
import gradio as gr
import numpy as np
from PIL import Image
import fal_client
import requests
from dotenv import load_dotenv
import glob
import shutil
import json

# Load environment variables
load_dotenv()
FAL_API_KEY = os.getenv("FAL_KEY")

if not FAL_API_KEY:
    print("Warning: FAL_KEY not found in .env file")

# Create persistent directories
FRAMES_DIR = os.path.join(os.getcwd(), "frames")
RESIZED_DIR = os.path.join(os.getcwd(), "resized")
SELECTED_DIR = os.path.join(os.getcwd(), "selected")

# Ensure directories exist
os.makedirs(FRAMES_DIR, exist_ok=True)
os.makedirs(RESIZED_DIR, exist_ok=True)
os.makedirs(SELECTED_DIR, exist_ok=True)

# Function to extract frames from videos
def extract_frames(video_folder, output_folder=FRAMES_DIR, interval=15):
    """Extract frames from videos at specified interval in seconds"""
    os.makedirs(output_folder, exist_ok=True)
    video_files = []
    
    for ext in ["*.mp4", "*.mov", "*.avi", "*.mkv"]:
        video_files.extend(glob.glob(os.path.join(video_folder, ext)))
    
    # Clear output folder first
    for file in os.listdir(output_folder):
        file_path = os.path.join(output_folder, file)
        if os.path.isfile(file_path):
            os.unlink(file_path)
    
    extracted_frames = []
    
    print(f"Found {len(video_files)} video files")
    for video_file in video_files:
        video_name = os.path.splitext(os.path.basename(video_file))[0]
        print(f"Processing video: {video_name}")
        
        cap = cv2.VideoCapture(video_file)
        
        if not cap.isOpened():
            print(f"Error opening video file: {video_file}")
            continue
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps
        
        print(f"Video duration: {duration:.2f}s, FPS: {fps:.2f}")
        
        # Calculate frame interval based on time
        frame_interval = int(fps * interval)
        
        current_frame = 0
        frame_num = 0
        while current_frame < frame_count:
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = cap.read()
            
            if not ret:
                break
                
            frame_filename = os.path.join(output_folder, f"{video_name}_frame_{frame_num}.jpg")
            cv2.imwrite(frame_filename, frame)
            extracted_frames.append(frame_filename)
            
            current_frame += frame_interval
            frame_num += 1
            
        cap.release()
        print(f"Extracted {frame_num} frames from {video_name}")
    
    return extracted_frames

# Function to resize and crop images to 1024x1024
def resize_images(input_images, output_folder=RESIZED_DIR, name_prefix="image_"):
    """Resize and crop images to 1024x1024 and rename them sequentially"""
    os.makedirs(output_folder, exist_ok=True)
    
    # Clear output folder first
    for file in os.listdir(output_folder):
        file_path = os.path.join(output_folder, file)
        if os.path.isfile(file_path):
            os.unlink(file_path)
    
    resized_images = []
    
    for i, img_path in enumerate(input_images, 1):
        try:
            img = Image.open(img_path)
            
            # Crop to square (center crop)
            width, height = img.size
            size = min(width, height)
            left = (width - size) // 2
            top = (height - size) // 2
            right = left + size
            bottom = top + size
            img = img.crop((left, top, right, bottom))
            
            # Resize to 1024x1024
            img = img.resize((1024, 1024), Image.LANCZOS)
            
            # Save with new name
            output_path = os.path.join(output_folder, f"{name_prefix}{i}.jpg")
            img.save(output_path, quality=95)
            resized_images.append(output_path)
            
        except Exception as e:
            print(f"Error processing image {img_path}: {str(e)}")
    
    return resized_images

# Function to create a zip file of selected images
def create_zip_file(image_paths, output_zip):
    """Create a zip file containing the selected images"""
    with zipfile.ZipFile(output_zip, 'w') as zipf:
        for img_path in image_paths:
            zipf.write(img_path, os.path.basename(img_path))
    return output_zip

# Function to upload zip file and get URL
def upload_zip(zip_path):
    """Upload zip file and return URL"""
    return fal_client.upload_file(zip_path)

# Function to train LORA model
def train_lora(images_url, trigger_phrase="ohwx", steps=1000, learning_rate=0.00115, 
              training_style="subject", face_crop=True):
    """Train LORA model using FAL API"""
    
    def on_queue_update(update):
        if isinstance(update, fal_client.InProgress):
            for log in update.logs:
                print(log["message"])
    
    result = fal_client.subscribe(
        "fal-ai/turbo-flux-trainer",
        arguments={
            "images_data_url": images_url,
            "trigger_phrase": trigger_phrase,
            "steps": steps,
            "learning_rate": learning_rate,
            "training_style": training_style,
            "face_crop": face_crop
        },
        with_logs=True,
        on_queue_update=on_queue_update,
    )
    
    return result

# Function to get base64 encoded image
def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

# Gradio interface
def create_interface():
    # State variables
    class AppState:
        def __init__(self):
            self.extracted_frames = []
            self.resized_images = []
            self.selected_images = []
            self.training_result = None
    
    state = AppState()
    
    # Define CSS for better scrolling
    custom_css = """
    .gradio-gallery {
        min-height: 200px; /* Prevent collapsing when empty */
        border: 1px solid #444; /* Add border for clarity */
        border-radius: 5px;
    }
    """
    
    # Build the interface
    with gr.Blocks(title="LORA Trainer", css=custom_css) as app:
        gr.Markdown("# LORA Model Trainer")
        
        with gr.Accordion("Step 1: Process Videos", open=True):
            with gr.Row():
                video_folder = gr.Textbox(label="Video Folder Path", placeholder="Path to folder containing videos")
                interval = gr.Number(label="Frame Interval (seconds)", value=15, minimum=1)
                name_prefix = gr.Textbox(label="Image Name Prefix", value="image_of_", placeholder="Prefix for renamed images")
            
            process_btn = gr.Button("Process Videos")
            process_output = gr.Textbox(label="Processing Status")
        
        with gr.Accordion("Step 2: Select Images for Training", open=True):
            gr.Markdown("Click on images in the 'Available Images' panel to select/deselect them. Selected images will appear in the 'Selected Images' panel.")
            
            # Define the two panels
            with gr.Row(equal_height=False):
                with gr.Column(scale=1, min_width=400):
                    gr.Markdown("### Available Images")
                    source_gallery = gr.Gallery(
                        label="Source Images",
                        show_label=False,
                        columns=3,
                        object_fit="contain",
                        elem_id="source_gallery",
                        allow_preview=True
                    )
                    
                with gr.Column(scale=1, min_width=400):
                    gr.Markdown("### Selected Images")
                    selected_gallery = gr.Gallery(
                        label="Selected Images",
                        show_label=False,
                        columns=3,
                        object_fit="contain",
                        elem_id="selected_gallery",
                        allow_preview=True
                    )
                    selection_status = gr.Textbox(label="Selection Status", value="No images selected")
                    with gr.Row():
                        select_all_btn = gr.Button("Select All")
                        clear_selection_btn = gr.Button("Clear Selection")
            
            # Store selected indices
            selected_indices = gr.State([])
        
        with gr.Accordion("Step 3: Train LORA Model", open=True):
            with gr.Row():
                trigger_word = gr.Textbox(label="Trigger Word", value="ohwx", placeholder="Trigger word for the model")
                steps = gr.Number(label="Training Steps", value=1000, minimum=100)
                learning_rate = gr.Number(label="Learning Rate", value=0.00115, minimum=0.0001)
            
            with gr.Row():
                training_style = gr.Radio(label="Training Style", choices=["subject", "style"], value="subject")
                face_crop = gr.Checkbox(label="Face Crop", value=True)
            
            train_btn = gr.Button("Train LORA Model")
            train_output = gr.Textbox(label="Training Result")
        
        def process_videos(video_folder, interval, name_prefix):
            if not os.path.exists(video_folder):
                return "Video folder does not exist", [], [], []
            
            # Extract frames
            state.extracted_frames = extract_frames(video_folder, FRAMES_DIR, int(interval))
            
            if not state.extracted_frames:
                return "No frames extracted from videos", [], [], []
            
            # Resize images
            state.resized_images = resize_images(state.extracted_frames, RESIZED_DIR, name_prefix)
            
            # Create gallery items
            gallery_items = []
            for img_path in state.resized_images:
                gallery_items.append((img_path, os.path.basename(img_path)))
            
            return (
                f"Frames extracted and resized successfully. Found {len(state.resized_images)} images. "
                f"Click on images to select them for training.",
                gallery_items,
                [], # Clear selected gallery
                [] # Clear selected indices
            )
        
        def toggle_selection(evt: gr.SelectData, current_indices):
            # Make sure current_indices is a list
            if current_indices is None:
                current_indices = []
            
            # Get the index of the selected image
            selected_idx = evt.index
            
            # Toggle the selection
            if selected_idx in current_indices:
                current_indices.remove(selected_idx)
            else:
                current_indices.append(selected_idx)
            
            # Update selected gallery
            selected_items = []
            for idx in sorted(current_indices):
                if idx < len(state.resized_images):
                    img_path = state.resized_images[idx]
                    selected_items.append((img_path, os.path.basename(img_path)))
            
            # Update selected directory
            update_selected_directory(current_indices)
            
            # Update status text
            status = f"Selected {len(current_indices)} images for training. Files copied to '{SELECTED_DIR}' folder."
            
            return current_indices, selected_items, status
        
        def select_all():
            # Select all images
            all_indices = list(range(len(state.resized_images)))
            
            # Update selected gallery
            selected_items = []
            for idx in all_indices:
                img_path = state.resized_images[idx]
                selected_items.append((img_path, os.path.basename(img_path)))
            
            # Update selected directory
            update_selected_directory(all_indices)
            
            # Update status text
            status = f"Selected all {len(all_indices)} images for training. Files copied to '{SELECTED_DIR}' folder."
            
            return all_indices, selected_items, status
        
        def clear_selection():
            # Clear selection
            # Update selected directory
            update_selected_directory([])
            
            # Update status text
            status = "Selection cleared. No images selected for training."
            
            return [], [], status
        
        def update_selected_directory(indices):
            # Reset the selected directory
            for file in os.listdir(SELECTED_DIR):
                file_path = os.path.join(SELECTED_DIR, file)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            
            # Copy selected images to the selected directory
            state.selected_images = []
            for idx in indices:
                if idx < len(state.resized_images):
                    img_path = state.resized_images[idx]
                    dest_path = os.path.join(SELECTED_DIR, os.path.basename(img_path))
                    shutil.copy2(img_path, dest_path)
                    state.selected_images.append(dest_path)
        
        def train_model(trigger_word, steps, learning_rate, training_style, face_crop):
            if not state.selected_images:
                return "No images selected for training. Please select at least one image."
            
            # Create a zip file of selected images
            zip_path = os.path.join(os.getcwd(), "training_images.zip")
            create_zip_file(state.selected_images, zip_path)
            
            # Upload zip file
            try:
                zip_url = upload_zip(zip_path)
                
                # Train LORA model
                result = train_lora(
                    zip_url, 
                    trigger_phrase=trigger_word,
                    steps=int(steps),
                    learning_rate=float(learning_rate),
                    training_style=training_style,
                    face_crop=face_crop
                )
                
                state.training_result = result
                
                # Download files
                lora_file_path = os.path.join(os.getcwd(), "lora_weights.safetensors")
                config_file_path = os.path.join(os.getcwd(), "lora_config.json")
                
                with open(lora_file_path, 'wb') as f:
                    f.write(requests.get(result["diffusers_lora_file"]["url"]).content)
                
                with open(config_file_path, 'wb') as f:
                    f.write(requests.get(result["config_file"]["url"]).content)
                
                return f"LORA training completed! Files downloaded to:\n- {lora_file_path}\n- {config_file_path}"
                
            except Exception as e:
                return f"Error during training: {str(e)}"
        
        # Connect process button
        process_btn.click(
            process_videos, 
            inputs=[video_folder, interval, name_prefix], 
            outputs=[process_output, source_gallery, selected_gallery, selected_indices]
        )
        
        # Connect image selection
        source_gallery.select(
            toggle_selection,
            inputs=[selected_indices],
            outputs=[selected_indices, selected_gallery, selection_status]
        )
        
        # Connect select all button
        select_all_btn.click(
            select_all,
            inputs=None,
            outputs=[selected_indices, selected_gallery, selection_status]
        )
        
        # Connect clear selection button
        clear_selection_btn.click(
            clear_selection,
            inputs=None,
            outputs=[selected_indices, selected_gallery, selection_status]
        )
        
        # Connect train button
        train_btn.click(
            train_model, 
            inputs=[trigger_word, steps, learning_rate, training_style, face_crop], 
            outputs=[train_output]
        )
    
    return app

# Run the application
if __name__ == "__main__":
    app = create_interface()
    app.launch(share=True)