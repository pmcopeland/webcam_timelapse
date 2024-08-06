import yaml
import time
import math



def load_settings():
    global MODE

    with open('settings.yaml', 'r') as f:
        config = yaml.safe_load(f)

    settings = config['fun_stuff']['time_dilation']
    
    MODE = settings['mode']

# Function to get the original FREQUENCY value from the YAML file
def get_original_frequency(file_path):
    # Read the YAML file
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    
    # Get the FREQUENCY value under settings
    if 'settings' in data and 'FREQUENCY' in data['settings']:
        return data['settings']['FREQUENCY']
    else:
        print("FREQUENCY key not found under settings in the YAML file.")
        return None

# Function to update the FREQUENCY value in the YAML file
def update_frequency(file_path, new_frequency):
    new_frequency = round(new_frequency)

    # Read the YAML file
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    
    # Update the FREQUENCY value under settings
    if 'settings' in data and 'FREQUENCY' in data['settings']:
        data['settings']['FREQUENCY'] = new_frequency
    else:
        print("FREQUENCY key not found under settings in the YAML file.")
        return
    
    # Write the updated data back to the YAML file
    with open(file_path, 'w') as file:
        yaml.safe_dump(data, file)
    
    print(f"FREQUENCY updated to {new_frequency} in {file_path}")

def calculate_new_frequency(current_value, min_value, max_value, step, mode, angle=None):
    """
    Calculate the new frequency based on the specified mode.
    
    Parameters:
    - current_value: The current frequency value.
    - min_value: The minimum frequency limit.
    - max_value: The maximum frequency limit.
    - step: The step size for incrementing or decrementing.
    - mode: The mode of transition ('linear' or 'sine').
    - angle: The current angle for sine wave calculation (only used in 'sine' mode).
    
    Returns:
    - new_value: The updated frequency value.
    - new_angle: The updated angle (only relevant for 'sine' mode).
    """
    if mode == 'linear':
        direction = 1 if current_value < max_value else -1
        new_value = current_value + direction * step
        if new_value >= max_value or new_value <= min_value:
            direction *= -1
            new_value = current_value + direction * step
        return new_value, None
    
    elif mode == 'sine':
        new_value = (max_value - min_value) / 2 * (math.sin(angle) + 1) + min_value
        new_angle = angle + step
        return new_value, new_angle
    
    else:
        raise ValueError("Invalid mode. Use 'linear' or 'sine'.")

def main(file_path, min_freq, max_freq, step):
    load_settings()


    # Read the YAML file to get the current frequency
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    
    if 'settings' in data and 'FREQUENCY' in data['settings']:
        current_frequency = data['settings']['FREQUENCY']
    else:
        print("FREQUENCY key not found under settings in the YAML file.")
        return
    
    angle = 0  # Initial angle for the sine wave

    while True:

        # Calculate the new frequency
        current_frequency, angle = calculate_new_frequency(current_frequency, min_freq, max_freq, step, MODE, angle)

        print(f"Mode: {MODE}, Frequency: {current_frequency}, Angle: {angle}")
        
        # Update the frequency in the YAML file
        update_frequency(file_path, current_frequency)
        
        time.sleep(current_frequency)

if __name__ == "__main__":
    main('settings.yaml', min_freq=5, max_freq=120, step=0.1)