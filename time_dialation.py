import yaml
import time

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

def main(file_path, min_freq, max_freq, step):
    # Read the YAML file to get the current frequency
    with open(file_path, 'r') as file:
        data = yaml.safe_load(file)
    
    if 'settings' in data and 'FREQUENCY' in data['settings']:
        current_frequency = data['settings']['FREQUENCY']
    else:
        print("FREQUENCY key not found under settings in the YAML file.")
        return
    
    direction = -1  # 1 for increment, -1 for decrement

    while True:
        # Sleep for the current frequency
        print(f"Sleeping for {current_frequency} seconds...")
        time.sleep(current_frequency)
        
        # Update the frequency
        current_frequency += direction * step

        #
        
        # Reverse direction if limits are reached
        if current_frequency >= max_freq or current_frequency <= min_freq:
            direction *= -1
        
        # Update the frequency in the YAML file
        update_frequency(file_path, current_frequency)


if __name__ == '__main__':
    original_frequency = get_original_frequency('settings.yaml')
    print(f"Original FREQUENCY: {original_frequency}")
    try:
        main('settings.yaml', min_freq=5, max_freq=60, step=0.5)
    except Exception as e:
         # Reset the frequency to its original value
        update_frequency('settings.yaml', original_frequency)
        print(f"An error occurred: {e}")
    finally:
        # Reset the frequency to its original value
        update_frequency('settings.yaml', original_frequency)