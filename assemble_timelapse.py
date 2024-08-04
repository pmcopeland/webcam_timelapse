import boto3
import cv2
import numpy as np
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# AWS S3 configuration
BUCKET_NAME = 'pmc-timelapses'
LOCAL_IMAGE_DIR = './images'
TIMELAPSE_VIDEO_PATH = './timelapse.mp4'
FRAME_RATE = 30 # FPS
OUTPUT_VIDEO_DURATION = 180 # Seconds

def list_images_in_s3(bucket_name):
    s3 = boto3.client('s3')
    images = []
    continuation_token = None

    # Only retrieve the latest (roughtly) frame_rate*duration number of images
    while True:
        if continuation_token:
            response = s3.list_objects_v2(Bucket=bucket_name, ContinuationToken=continuation_token)
        else:
            response = s3.list_objects_v2(Bucket=bucket_name)

        if 'Contents' in response:
            for obj in response['Contents']:
                images.append((obj['Key'], obj['LastModified']))

        if response.get('IsTruncated'):  # Check if there are more objects to retrieve
            continuation_token = response.get('NextContinuationToken')
        else:
            break

    # Sort the images by last modified time in descending order
    images.sort(key=lambda x: x[1], reverse=True)

    # Return only the latest frame_rate*duration number of images
    images = images[:FRAME_RATE*OUTPUT_VIDEO_DURATION]

    return images

def download_image(s3, bucket_name, image_key, local_dir):
    local_path = os.path.join(local_dir, os.path.basename(image_key))
    if not image_exists_localy(image_key, local_dir):
        s3.download_file(bucket_name, image_key, local_path)
        print(f"Downloaded {image_key} to {local_path}")
    else:
        print(f"Skipped {image_key}, already exists at {local_path}")

def image_exists_localy(image_key, local_dir):
    local_path = os.path.join(local_dir, os.path.basename(image_key))
    return os.path.exists(local_path)

def filter_already_downloaded_images(images, local_dir):
    new_images = [(image_key, last_modified) for image_key, last_modified in images if not image_exists_localy(image_key, local_dir)]
    old_images = [(image_key, last_modified) for image_key, last_modified in images if image_exists_localy(image_key, local_dir)]
    return new_images, old_images


def download_images(bucket_name, images, local_dir):
    s3 = boto3.client('s3')
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
    
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(download_image, s3, bucket_name, image_key, local_dir) for image_key, _ in images]
        for future in as_completed(futures):
            future.result()

def create_timelapse_video(local_dir, images, video_path, frame_rate):
    images = sorted(images, key=lambda x: x[1])
    if not images:
        print("No images found.")
        return

    # Read the first image to get the dimensions
    first_image_path = os.path.join(local_dir, os.path.basename(images[0][0]))
    first_image = cv2.imread(first_image_path)
    height, width, layers = first_image.shape

    # Initialize the video writer with H.264 codec
    fourcc = cv2.VideoWriter_fourcc(*'H264')
    video = cv2.VideoWriter(video_path, fourcc, frame_rate, (width, height))

    for image_key, _ in images:
        image_path = os.path.join(local_dir, os.path.basename(image_key))
        frame = cv2.imread(image_path)
        video.write(frame)
        print(f"Added {image_path} to the video.")

    video.release()

    # Optimize the video for web streaming using ffmpeg
    optimized_video_path = video_path.replace('.mp4', '_optimized.mp4')
    os.system(f'ffmpeg -i {video_path} -vcodec libx264 -crf 23 -preset fast {optimized_video_path} -y')
    print(f"Timelapse video created and optimized for web streaming at {optimized_video_path}")

    # Delete the original video
    os.remove(video_path)
    print(f"Original video deleted: {video_path}")

def main():
    print("Listing images in S3 bucket...")
    images = list_images_in_s3(BUCKET_NAME)

    # trim images
    # get last (output_video_length*frame_rate) images
    images = images[-OUTPUT_VIDEO_DURATION*FRAME_RATE:]

    images, filteredOutImages  = filter_already_downloaded_images(images, LOCAL_IMAGE_DIR)

    if images:
        start_time = images[-1][1].strftime('%Y-%m-%d %H:%M:%S')
        end_time = images[-0][1].strftime('%Y-%m-%d %H:%M:%S')
    else:
        print(f"No images available in the S3 bucket {BUCKET_NAME}.")


    inputQuestion = f"""
Filtered out \033[41m{len(filteredOutImages)}\033[0m images that were already downloaded.
\033[42m{len(images)}\033[0m images to download. \n
\033[44m{start_time}\033[0m to \033[44m{end_time}\033[0m \n
Do you want to continue? (y/n):"""

    user_input = input(inputQuestion)

    if user_input.lower() == "y":
        print("Downloading images from S3...")
        download_images(BUCKET_NAME, images, LOCAL_IMAGE_DIR)

        print("Creating timelapse video...")
        create_timelapse_video(LOCAL_IMAGE_DIR, images, TIMELAPSE_VIDEO_PATH, FRAME_RATE)
    else:
        print("Timelapse creation cancelled.")

if __name__ == "__main__":
    main()