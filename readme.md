# Timelapse Setup Guide

This is a python based webcam timelapse controler, timelapse assembler, and even a small vue site to scrub through recent images. 

It uses S3 for file storage, allowing the ~~complexity~~ flexability of modern cloud storage to shine. This is a weekend project kinda thing, really only built for myself. I'm making the assumption that you have your own AWS account, or have access to one and can set up AWS CLI and configure the whole IAM user stuff. 

Anyone who is crazy enough to spend their free time burried in aws documentation is free to enjoy this or contribute.  

This comes with no warranty, ***you're on your own kid***. 

## Prerequisites

- Python 3 installed
- Required Python packages installed (see [`requirements.txt`](requirements.txt) script configured and tested

### Setting Up AWS CLI and IAM User

Before running this application, you need to set up the AWS CLI and create an IAM user with the necessary permissions. Follow these steps:

#### 1. Install AWS CLI

If you haven't already installed the AWS CLI, you can do so by following the instructions [here](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html).

#### 2. Create an IAM User

1. **Log in to the AWS Management Console**.
2. **Navigate to the IAM Console**: Go to the [IAM Console](https://console.aws.amazon.com/iam/).
3. **Create a New User**:
   - Click on `Users` in the sidebar.
   - Click on the `Add user` button.
   - Enter a username (e.g., `webcam-timelapse-user`).
   - Select `Programmatic access` for access type.
   - Click `Next: Permissions`.

4. **Attach Policies**:
   - Choose `Attach existing policies directly`.
   - Search for and select `AmazonS3FullAccess` (or create a custom policy with the necessary permissions).
   - Click `Next: Tags` (optional) and then `Next: Review`.

5. **Create User**:
   - Review the settings and click `Create user`.
   - Note down the `Access key ID` and `Secret access key`. You will need these in the next step.

#### 3. Configure AWS CLI

1. Open a terminal.
2. Run the following command to configure the AWS CLI:

   ```sh
   aws configure
   ```

3. Enter the `Access key ID`, `Secret access key`, `Default region name`, and `Default output format` when prompted.

#### 4. Verify Configuration

To ensure the AWS CLI is configured correctly, you can list your S3 buckets:

```sh
aws s3 ls
```

This should display a list of your S3 buckets.


### Setting the Environment and Service Config

To set the S3 bucket name for a systemd service, you need to define it in the service file. Follow these steps:

1. **Edit the systemd service file**:

   Open your systemd service file, for example, `webcam_timelapse.service`:

   ```sh
   sudo nano /etc/systemd/system/webcam_timelapse.service
   ```

2. **Add the environment variable**:

   Add the `Environment` directive under the `[Service]` section to define the environment variable:

   ```ini
   [Service]
   Environment="WEBCAMTIMELAPSE_BUCKET_NAME=your-bucket-name"
   ExecStart=/usr/bin/python3 /path/to/your/timelapse.py
   Restart=always
   User=your-username
   WorkingDirectory=/path/to/your/project
   ```

   Replace `your-bucket-name` with the actual name of your S3 bucket and `/path/to/your/timelapse.py` with the path to your script.

3. **Reload the systemd daemon**:

   After modifying the service file, reload the systemd daemon to apply the changes:

   ```sh
   sudo systemctl daemon-reload
   ```

4. **Restart the service**:

   Restart the service to ensure it picks up the new environment variable:

   ```sh
   sudo systemctl restart webcam_timelapse.service
   ```

5. **Verify the service status**:

   Check the status of the service to ensure it is running correctly:

   ```sh
   sudo systemctl status webcam_timelapse.service
   ```

By defining the environment variable in the service file, you ensure that it is available to the script when it runs under systemd.

## Troubleshooting

- If the service fails to start, check the logs for more information:

```sh
journalctl -u webcam_timelapse.service
```
Use `-f` to get live trailing logs. 

- To view the latest image look at `images/last.jpg`, if you open the file in vs code (using vs code remote ssh or tunnels if running on headless machine) to watch the image update every time a photo is taken.