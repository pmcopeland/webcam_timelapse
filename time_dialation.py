import yaml
import time

def update_frequency(file_path, new_frequency):
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
        
        # Reverse direction if limits are reached
        if current_frequency >= max_freq or current_frequency <= min_freq:
            direction *= -1
        
        # Update the frequency in the YAML file
        update_frequency(file_path, current_frequency)


main('settings.yaml', min_freq=10, max_freq=60, step=1)