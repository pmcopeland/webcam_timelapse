import cv2
import os
import boto3
from datetime import datetime, timedelta, timezone, time
import math
import time as time_module
import yaml
import pytz
from tabulate import tabulate
import traceback
import sqlite3

# Define the images directory
images_dir = './images'

# SQL db
conn = sqlite3.connect('timelapse.db')

# Define the Central Time Zone
central = pytz.timezone('US/Central')

previous_times = {}

# Load environment variables
BUCKET_NAME = os.getenv('WEBCAMTIMELAPSE_BUCKET_NAME')
if not BUCKET_NAME:
    raise ValueError("No BUCKET_NAME environment variable set")


def load_settings():
    global MAX_RUNTIME_HOURS, IMAGE_RETENTION_HOURS, FREQUENCY
    global SUNRISE_TIME, SUNSET_TIME, NIGHT_BRIGHTNESS, DAY_BRIGHTNESS
    global SHOW_CAMERA_SETTINGS, SHOW_TIMESTAMP, SAVE_LOCAL_LATEST_IMG, SAVE_S3
    global SHOW_TIMING, ENABLED, SAVE_SQLITE

    with open('settings.yaml', 'r') as f:
        config = yaml.safe_load(f)

    settings = config['settings']
    debug = config['debug']

    MAX_RUNTIME_HOURS = settings['MAX_RUNTIME_HOURS']
    IMAGE_RETENTION_HOURS = settings['IMAGE_RETENTION_HOURS']
    FREQUENCY = settings['FREQUENCY']
    SUNRISE_TIME = central.localize(datetime.strptime(settings['SUNRISE_TIME'], '%H:%M')).time()
    SUNSET_TIME = central.localize(datetime.strptime(settings['SUNSET_TIME'], '%H:%M')).time()
    NIGHT_BRIGHTNESS = settings['NIGHT_BRIGHTNESS']
    DAY_BRIGHTNESS = settings['DAY_BRIGHTNESS']
    ENABLED = settings['ENABLED']
    
    SHOW_CAMERA_SETTINGS = debug['SHOW_CAMERA_SETTINGS']
    SHOW_TIMESTAMP = debug['SHOW_TIMESTAMP']
    SHOW_TIMING = debug['SHOW_TIMING']
    SAVE_LOCAL_LATEST_IMG = debug['SAVE_LOCAL_LATEST_IMG']
    SAVE_S3 = debug['SAVE_S3']
    SAVE_SQLITE = debug['SAVE_SQLITE']

def initialize_camera():
    load_settings()
    print("Initializing camera...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Cannot open webcam")
        raise IOError("Cannot open webcam")

    cap.set(cv2.CAP_PROP_GAIN, 215)


    print("Camera initialized successfully.")
    return cap

def initialize_database(db_path='timelapse.db', conn=None):
    global SESSION_ID
    if conn is None:
        conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS frames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            file_name TEXT,
            brightness INTEGER,
            contrast INTEGER,
            saturation INTEGER,
            gain INTEGER,
            white_balance_temperature INTEGER,
            frequency INTEGER,
            timelapse_session TEXT,
            FOREIGN KEY (timelapse_session) REFERENCES timelapse_sessions(session_id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS timelapse_sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time DATETIME,
            end_time DATETIME
        )
    ''')

    cursor.execute('''
                   INSERT INTO timelapse_sessions (start_time)
                   VALUES (?)
                   ''', (datetime.now(),))
    
    SESSION_ID = cursor.lastrowid

    conn.commit()

def insert_frame_database(timestamp, brightness, contrast, saturation, gain, white_balance_temperature, file_name, frequency, db_path='timelapse.db'):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO frames (timestamp, brightness, contrast, saturation, gain, white_balance_temperature, file_name, frequency, timelapse_session)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, brightness, contrast, saturation, gain, white_balance_temperature, file_name, frequency, SESSION_ID))
    conn.commit()
    conn.close()

def close_session_database(db_path='timelapse.db', conn=None):
    if conn is None:
        conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE timelapse_sessions
        SET end_time = ?
        WHERE session_id = ?
    ''', (datetime.now(), SESSION_ID))
    conn.commit()
    conn.close()


def capture_frame(cap):

    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame")
        raise IOError("Failed to capture frame")

    # BUFFER FLUSH (TEST)
    for i in range(60):
        cap.read()

    return frame

def calculate_brightness(current_time):
    # Convert times to seconds since midnight
    def time_to_seconds(t):
        return t.hour * 3600 + t.minute * 60 + t.second

    current_seconds = time_to_seconds(current_time)
    sunrise_seconds = time_to_seconds(SUNRISE_TIME)
    sunset_seconds = time_to_seconds(SUNSET_TIME)

    # Define transition duration (1 hour)
    transition_duration = 3600  # 1 hour in seconds

    # Calculate the duration of day and night
    day_duration = sunset_seconds - sunrise_seconds
    night_duration = 24 * 3600 - day_duration

    if sunrise_seconds - transition_duration <= current_seconds <= sunrise_seconds + transition_duration:
        # Morning transition
        transition_progress = (current_seconds - (sunrise_seconds - transition_duration)) / (2 * transition_duration)
        brightness = NIGHT_BRIGHTNESS + (DAY_BRIGHTNESS - NIGHT_BRIGHTNESS) * (0.5 * (1 + math.sin(math.pi * (transition_progress - 0.5))))
    elif sunset_seconds - transition_duration <= current_seconds <= sunset_seconds + transition_duration:
        # Evening transition
        transition_progress = (current_seconds - (sunset_seconds - transition_duration)) / (2 * transition_duration)
        brightness = DAY_BRIGHTNESS + (NIGHT_BRIGHTNESS - DAY_BRIGHTNESS) * (0.5 * (1 + math.sin(math.pi * (transition_progress - 0.5))))
    elif sunrise_seconds + transition_duration < current_seconds < sunset_seconds - transition_duration:
        # Daytime
        brightness = DAY_BRIGHTNESS
    else:
        # Nighttime
        brightness = NIGHT_BRIGHTNESS

    return brightness

import cv2

def add_timestamp_to_frame(frame, timestamp, position='bottom-left'):

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.6
    font_thickness = 2
    margin = 5
    text_color = (255, 255, 255)
    background_color = (0, 0, 0)

    text_size, _ = cv2.getTextSize(timestamp, font, font_scale, font_thickness)
    text_width, text_height = text_size

    if position == 'top-left':
        text_x, text_y = margin, margin + text_height
    elif position == 'top-right':
        text_x, text_y = frame.shape[1] - text_width - margin, margin + text_height
    elif position == 'bottom-left':
        text_x, text_y = margin, frame.shape[0] - margin
    elif position == 'bottom-right':
        text_x, text_y = frame.shape[1] - text_width - margin, frame.shape[0] - margin
    else:
        raise ValueError("Invalid position. Choose from 'top-left', 'top-right', 'bottom-left', 'bottom-right'.")

    cv2.rectangle(frame, (text_x - margin, text_y + margin), 
                  (text_x + text_width + margin, text_y - text_height - margin), 
                  background_color, -1)
    cv2.putText(frame, timestamp, (text_x, text_y), font, font_scale, text_color, font_thickness, cv2.LINE_AA)

    return frame

def add_previous_timing(frame, times_list, position='top-right'):
    # Safely format the duration, replacing None with a placeholder
    def format_duration(duration):
        return f"{duration:.2f}s" if duration is not None else "N/A"

    times_text = "--- PREVIOUS FRAME ---\n\n\n" + "\n\n".join([f"{task}: {format_duration(duration)}" for task, duration in times_list])
    
    # Define font and text properties
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.4
    font_thickness = 1
    margin = 5
    text_color = (255, 255, 255)
    background_color = (0, 0, 0)

    # Split the times text into lines
    lines = times_text.split('\n')
    
    # Calculate the maximum text width of all lines
    max_text_width = 0
    for line in lines:
        text_size, _ = cv2.getTextSize(line, font, font_scale, font_thickness)
        max_text_width = max(max_text_width, text_size[0])

    # Calculate the size of the text box
    text_height = text_size[1] * len(lines)
    
    # Determine the position of the text box
    if position == 'top-left':
        text_x, text_y = margin, margin + text_height
    elif position == 'top-right':
        text_x, text_y = frame.shape[1] - max_text_width - margin, margin + text_height
    elif position == 'bottom-left':
        text_x, text_y = margin, frame.shape[0] - margin
    elif position == 'bottom-right':
        text_x, text_y = frame.shape[1] - max_text_width - margin, frame.shape[0] - margin
    else:
        raise ValueError("Invalid position argument")

    # Draw the background rectangle
    cv2.rectangle(frame, (text_x - margin, text_y - text_height - margin), 
                  (text_x + max_text_width + margin, text_y + margin), background_color, cv2.FILLED)
    
    # Draw each line of text
    for i, line in enumerate(lines):
        line_y = text_y - (len(lines) - i - 1) * text_size[1]
        cv2.putText(frame, line, (text_x, line_y), font, font_scale, text_color, font_thickness)

    return frame

def calculate_times(times):
    # Create a list to hold the times
    times_list = []

    # Helper function to safely calculate time differences
    def safe_time_diff(start, end):
        if start is not None and end is not None:
            return round(end - start, 2)
        return None

    # Add times to the list with checks
    times_list.append(["Load settings", safe_time_diff(times['load_settings'][0], times['load_settings'][1])])
    times_list.append(["Calculate brightness", safe_time_diff(times['calculate_brightness'][0], times['calculate_brightness'][1])])
    times_list.append(["Set brightness", safe_time_diff(times['set_brightness'][0], times['set_brightness'][1])])
    times_list.append(["Capture frame", safe_time_diff(times['capture_frame'][0], times['capture_frame'][1])])

    if times["add_timestamp"]:
        times_list.append(["Add timestamp", safe_time_diff(times['add_timestamp'][0], times['add_timestamp'][1])])
    if times["add_camera_settings"]:
        times_list.append(["Add camera settings", safe_time_diff(times['add_camera_settings'][0], times['add_camera_settings'][1])])
    if times["save_frame"]:
        times_list.append(["Save frame", safe_time_diff(times['save_frame'][0], times['save_frame'][1])])
    if times["upload_to_s3"]:
        times_list.append(["Upload to S3", safe_time_diff(times['upload_to_s3'][0], times['upload_to_s3'][1])])
    if times["delete_old_images"]:
        times_list.append(["Delete old images from S3", safe_time_diff(times['delete_old_images'][0], times['delete_old_images'][1])])
    if times["add_prev_timing"]:
        times_list.append(["Add previous timing", safe_time_diff(times['add_prev_timing'][0], times['add_prev_timing'][1])])

    return times_list

def format_times_table(times_list, loop_duration, FREQUENCY, deviation, adjusted_sleep_duration):
    # Add additional information to the times list
    times_list.append(["Total loop duration", loop_duration])
    times_list.append(["Target", FREQUENCY])
    times_list.append(["Deviation from frequency", deviation])
    times_list.append(["Adjusted sleep duration", adjusted_sleep_duration])

    output = ""

    # build multiline string
    for k, v in times_list:
        if v is not None:
            output += f"{k}: {round(v, 2)}\n"

    return output

def save_frame(frame, images_dir):

    image_path = os.path.join(images_dir, 'last.jpg')
    cv2.imwrite(image_path, frame)

    return image_path

def upload_to_s3(image_path, timestamp):

    s3 = boto3.client('s3')
    with open(image_path, "rb") as data:
        s3.upload_fileobj(data, 'pmc-timelapses', f'{timestamp.replace(":", "").replace(" ", "_")}.jpg')


def delete_old_images_from_s3():

    s3 = boto3.client('s3')
    retention_period = datetime.now(timezone.utc) - timedelta(hours=IMAGE_RETENTION_HOURS)
    
    objects = s3.list_objects_v2(Bucket=BUCKET_NAME)
    if 'Contents' in objects:
        for obj in objects['Contents']:
            obj_time = obj['LastModified']
            if obj_time < retention_period:
                s3.delete_object(Bucket=BUCKET_NAME, Key=obj['Key'])



def add_camera_settings_to_frame(frame, cap, position='bottom-right'):

    
    # Retrieve camera settings
    brightness = round(cap.get(cv2.CAP_PROP_BRIGHTNESS))
    contrast = round(cap.get(cv2.CAP_PROP_CONTRAST))
    saturation = round(cap.get(cv2.CAP_PROP_SATURATION))
    gain = round(cap.get(cv2.CAP_PROP_GAIN))
    white_balance_temperature = round(cap.get(cv2.CAP_PROP_WB_TEMPERATURE))

    # Format the settings text
    settings_text = f"Freq: {FREQUENCY}\n\nBrightness: {brightness}\n\nContrast: {contrast:}\n\nSaturation: {saturation:}\n\nGain: {gain:}\n\nWhite Balance: {white_balance_temperature:}"
    
    # Define font and text properties
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.4
    font_thickness = 1
    margin = 5
    text_color = (255, 255, 255)
    background_color = (0, 0, 0)

    
    # Split the settings text into lines
    lines = settings_text.split('\n')
    
    # Calculate the maximum text width of all lines
    max_text_width = 0
    for line in lines:
        text_size, _ = cv2.getTextSize(line, font, font_scale, font_thickness)
        max_text_width = max(max_text_width, text_size[0])

    # Calculate the size of the text box
    text_height = text_size[1] * len(lines)
    
    # Determine the position of the text box
    if position == 'top-left':
        text_x, text_y = margin, margin + text_height
    elif position == 'top-right':
        text_x, text_y = frame.shape[1] - max_text_width - margin, margin + text_height
    elif position == 'bottom-left':
        text_x, text_y = margin, frame.shape[0] - margin
    elif position == 'bottom-right':
        text_x, text_y = frame.shape[1] - max_text_width - margin, frame.shape[0] - margin
    else:
        raise ValueError("Invalid position. Choose from 'top-left', 'top-right', 'bottom-left', 'bottom-right'.")
    
    # Draw the background rectangle
    cv2.rectangle(frame, (text_x - margin, text_y + margin), 
                  (text_x + max_text_width + margin, text_y - text_height - margin), 
                  background_color, -1)
    
    # Overlay each line of text
    for i, line in enumerate(lines):
        y = text_y - (len(lines) - i - 1) * text_size[1]
        cv2.putText(frame, line, (text_x, y), font, font_scale, text_color, font_thickness, cv2.LINE_AA)
    

    return frame

def take_test_image():
    cap = initialize_camera()
    
    try:
        frame = capture_frame(cap)
        
        if SHOW_TIMESTAMP:
            timestamp = datetime.now(timezone.utc).strftime('%Y %m %d_%H %M %S')
            frame = add_timestamp_to_frame(frame, timestamp)
        
        if SHOW_CAMERA_SETTINGS:
            frame = add_camera_settings_to_frame(frame, cap)
        
        image_path = save_frame(frame, images_dir)
        
        if SAVE_S3:
            upload_to_s3(image_path, timestamp)
        

    except Exception as e:
        print(f"An error occurred while taking the test image: {e}")
    finally:
        cap.release()
        print("Camera released after taking test image.")

def main():
    global previous_times
    
    current_time = datetime.now(timezone.utc)
    print(f"[{current_time.isoformat()}] Starting main process...")
    cap = initialize_camera()
    start_time = datetime.now(timezone.utc)

    if SAVE_SQLITE:
        initialize_database(conn=conn)


    try:
        while (datetime.now(timezone.utc) - start_time) < timedelta(hours=MAX_RUNTIME_HOURS):
            load_settings_start = time_module.time()
            load_settings()
            load_settings_end = time_module.time()
            

            loop_start_time = time_module.time()
            current_time = datetime.now(timezone.utc)
            
            calculate_brightness_start = time_module.time()
            brightness = calculate_brightness(datetime.now())
            calculate_brightness_end = time_module.time()
            
            set_brightness_start = time_module.time()
            cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness)
            set_brightness_end = time_module.time()
            
            capture_frame_start = time_module.time()
            frame = capture_frame(cap)
            capture_frame_end = time_module.time()

            if SHOW_TIMESTAMP:
                add_timestamp_start = time_module.time()
                image_timestamp = datetime.now().strftime('%m/%d/%Y %H:%M')
                frame = add_timestamp_to_frame(frame, image_timestamp)
                add_timestamp_end = time_module.time()

            if SHOW_TIMING:
                add_timing_start = time_module.time()
                frame = add_previous_timing(frame, previous_times)
                add_timing_end = time_module.time()
            
            if SHOW_CAMERA_SETTINGS:
                add_camera_settings_start = time_module.time()
                frame = add_camera_settings_to_frame(frame, cap)
                add_camera_settings_end = time_module.time()

            if SAVE_LOCAL_LATEST_IMG:
                save_frame_start = time_module.time()
                image_path = save_frame(frame, images_dir)
                save_frame_end = time_module.time()

            if SAVE_S3:
                upload_to_s3_start = time_module.time()
                file_timestamp = datetime.now(timezone.utc).strftime('%Y %m %d_%H %M %S')
                upload_to_s3(image_path, file_timestamp)
                upload_to_s3_end = time_module.time()

            if SAVE_SQLITE:
                save_sqlite_start = time_module.time()
                insert_frame_database(datetime.now(), brightness, cap.get(cv2.CAP_PROP_CONTRAST), cap.get(cv2.CAP_PROP_SATURATION), cap.get(cv2.CAP_PROP_GAIN), cap.get(cv2.CAP_PROP_WB_TEMPERATURE), file_timestamp, FREQUENCY)
                save_sqlite_end = time_module.time()


            if (current_time - start_time).seconds % 3600 < FREQUENCY:
                delete_old_images_start = time_module.time()
                delete_old_images_from_s3()
                delete_old_images_end = time_module.time()

            loop_end_time = time_module.time()
            loop_duration = loop_end_time - loop_start_time
            deviation = loop_duration - FREQUENCY

            adjusted_sleep_duration = max(0, FREQUENCY - loop_duration)

            times = {
                "load_settings": (load_settings_start, load_settings_end),
                "calculate_brightness": (calculate_brightness_start, calculate_brightness_end),
                "set_brightness": (set_brightness_start, set_brightness_end),
                "capture_frame": (capture_frame_start, capture_frame_end),
                "add_timestamp": (add_timestamp_start, add_timestamp_end) if SHOW_TIMESTAMP else (None, None),
                'add_prev_timing': (add_timing_start, add_timing_end) if SHOW_TIMING else (None, None),
                "add_camera_settings": (add_camera_settings_start, add_camera_settings_end) if SHOW_CAMERA_SETTINGS else (None, None),
                "save_frame": (save_frame_start, save_frame_end) if SAVE_LOCAL_LATEST_IMG else (None, None),
                "upload_to_s3": (upload_to_s3_start, upload_to_s3_end) if SAVE_S3 else (None, None),
                "save_sqlite": (save_sqlite_start, save_sqlite_end) if SAVE_SQLITE else (None, None),
                "delete_old_images": (delete_old_images_start, delete_old_images_end) if (current_time - start_time).seconds % 3600 < FREQUENCY else (None, None),
            }
            times_list = calculate_times(times)
            formatted_table = format_times_table(times_list, loop_duration, FREQUENCY, deviation, adjusted_sleep_duration)
            print("████████████████████████████████████████████████████████████████████████")
            print(f" [{datetime.now(timezone.utc).isoformat()}] Loop completed.")
            print(formatted_table)
            
            previous_times = times_list
            
            time_module.sleep(adjusted_sleep_duration)

        else:
            print("⚠ ⚠ ⚠ CAMERA DISABLED ⚠ ⚠ ⚠")
            time_module.sleep(1)

            

    except Exception as e:
        close_session_database()
        print(f"[{datetime.now(timezone.utc).isoformat()}] An error occurred: {e}")
        traceback.print_exc()
    finally:
        cap.release()
        close_session_database()
        print(f"[{datetime.now(timezone.utc).isoformat()}] Camera released after main process.")

if __name__ == "__main__":
    main()