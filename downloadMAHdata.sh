#!/bin/bash

# Prompt for the URL
read -p "Please enter the download URL: " url

# Define the destination directory
dest_dir="data/ttl/main/mah"

# Create the destination directory if it doesn't exist
mkdir -p "$dest_dir"

# Download the file
echo "Downloading the file..."
curl -L -o downloaded_file.zip "$url"

# Check if the download was successful
if [ $? -ne 0 ]; then
    echo "Error: Failed to download the file. Please check the URL and try again."
    exit 1
fi

# Unpack the zip file
echo "Unpacking the file..."
unzip -o downloaded_file.zip -d "$dest_dir"

# Check if the unzip was successful
if [ $? -ne 0 ]; then
    echo "Error: Failed to unpack the zip file."
    exit 1
fi

# Delete the zip file
rm -f downloaded_file.zip

# Inform the user
echo "The data has been successfully downloaded and unpacked to $dest_dir. All OK!"