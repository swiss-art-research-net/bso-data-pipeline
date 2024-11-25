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

# Unpack only the content of the SARI directory directly into the destination directory
echo "Unpacking the file..."
unzip -o downloaded_file.zip "SARI/*" -d "$dest_dir"

# Check if the unzip was successful
if [ $? -ne 0 ]; then
    echo "Error: Failed to unpack the zip file."
    rm -f downloaded_file.zip
    exit 1
fi

# Move the files out of the SARI subdirectory into the destination directory root
mv "$dest_dir/SARI/"* "$dest_dir"
rmdir "$dest_dir/SARI"

# Rename .ttl files with spaces in their names
echo "Renaming .ttl files with spaces in their names..."
for file in "$dest_dir"/*.ttl; do
    if [[ "$file" == *" "* ]]; then
        mv "$file" "${file// /_}"
    fi
done

# Delete the zip file
rm -f downloaded_file.zip

# Inform the user
echo "The data from the SARI directory has been successfully downloaded, unpacked to $dest_dir, and .ttl files with spaces have been renamed."