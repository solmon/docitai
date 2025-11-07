#!/bin/sh

# Description: This script builds the current project and specified libraries,
# then moves their wheel files to the current project's dist folder. It exits on failure.

# Get the current directory (the service's directory)
CURRENT_DIR=$(pwd)

# Function to handle errors and exit the script with an error message
handle_error() {
    echo "$1"
    exit 1
}

# Function to silently delete a directory if it exists
delete_dist_folder() {
    if [ -d "$1" ]; then
        echo "Deleting existing dist folder in $1..."
        rm -rf "$1" || handle_error "Failed to delete dist folder in $1."
    fi
}

# Delete existing dist folder in the current project (if it exists)
delete_dist_folder "$CURRENT_DIR/dist"

# Build the current project
echo "Building the current project at $CURRENT_DIR..."
uv build --wheel -o dist || handle_error "Failed to build the current project at $CURRENT_DIR."

# Base path to the libraries
LIBS_DIR="$CURRENT_DIR/../../libs"

# Iterate through each library name provided as arguments
for LIB_NAME in "$@"; do
    # Construct the full path to the library directory and resolve it to absolute path
    LIB_DIR=$(realpath "$LIBS_DIR/$LIB_NAME")

    # Check if the library directory exists
    if [ ! -d "$LIB_DIR" ]; then
        handle_error "Directory $LIB_DIR does not exist. Exiting."
    fi

    # Delete existing dist folder in the library directory (if it exists)
    delete_dist_folder "$LIB_DIR/dist"

    # Navigate to the library directory
    echo "Navigating to $LIB_DIR..."
    cd "$LIB_DIR" || handle_error "Failed to navigate to $LIB_DIR. Exiting."

    # Build the library
    echo "Building $LIB_NAME at $LIB_DIR..."
    uv build --wheel -o dist || handle_error "Failed to build $LIB_NAME at $LIB_DIR. Exiting."

    # Ensure the dist directory exists in the current project
    mkdir -p "$CURRENT_DIR/dist"

    # Locate the generated wheel file in the library's dist folder
    WHL_FILE=$(ls dist/*.whl 2>/dev/null)

    # Check if a wheel file was generated
    if [ -z "$WHL_FILE" ]; then
        handle_error "No wheel file found in $LIB_DIR/dist for $LIB_NAME. Exiting."
    fi

    # Move the wheel file to the current project's dist folder
    mv "$WHL_FILE" "$CURRENT_DIR/dist/" || handle_error "Failed to move $WHL_FILE to $CURRENT_DIR/dist. Exiting."

    echo "Successfully built and moved $LIB_NAME to dist."
done

# Copy uv.lock and .python-version from the root directory
ROOT_DIR="$CURRENT_DIR/../.."
for FILE in "uv.lock" ".python-version"; do
  if [ -f "$ROOT_DIR/$FILE" ]; then
    cp "$ROOT_DIR/$FILE" "$CURRENT_DIR/dist/" || handle_error "Failed to copy $FILE to $CURRENT_DIR/dist. Exiting."
    echo "Copied $FILE to dist."
  else
    echo "Warning: $FILE not found in $ROOT_DIR. Skipping."
  fi
done

# Return to the original directory (where the script was invoked)
cd "$CURRENT_DIR" || exit

echo "Task completed successfully."
