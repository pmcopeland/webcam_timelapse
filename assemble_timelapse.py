import boto3
import cv2
import numpy as np
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables
BUCKET_NAME = os.getenv('WEBCAMTIMELAPSE_BUCKET_NAME')
if not BUCKET_NAME:
    raise ValueError("No WEBCAMTIMELAPSE_BUCKET_NAME environment variable set")

LOCAL_IMAGE_DIR = './images'
TIMELAPSE_VIDEO_PATH = './timelapse.mp4'
FRAME_RATE = 15  # FPS
OUTPUT_VIDEO_DURATION = 200 # Seconds

def list_images_in_s3(bucket_name):
    s3 = boto3.client('s3')
    images = []
    continuation_token = None

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

    return images

def download_image(s3, bucket_name, image_key, local_dir):
    local_path = os.path.join(local_dir, os.path.basename(image_key))
    if not os.path.exists(local_path):
        s3.download_file(bucket_name, image_key, local_path)
        print(f"Downloaded {image_key} to {local_path}")
    else:
        print(f"Skipped {image_key}, already exists at {local_path}")

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

def main():
    print("Listing images in S3 bucket...")
    images = list_images_in_s3(BUCKET_NAME)
    if not images:
        print("No images found in the S3 bucket.")
        return

    print("Downloading images from S3...")
    download_images(BUCKET_NAME, images, LOCAL_IMAGE_DIR)

    # trim images
    # get last (output_video_length*frame_rate) images
    images = images[-OUTPUT_VIDEO_DURATION*FRAME_RATE:]

    print("Creating timelapse video...")
    create_timelapse_video(LOCAL_IMAGE_DIR, images, TIMELAPSE_VIDEO_PATH, FRAME_RATE)

if __name__ == "__main__":
    main()