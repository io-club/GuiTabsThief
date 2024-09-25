import os
import json
from pathlib import Path

def organize_songs(directory):
    # Walk through the directory structure
    for root, dirs, files in os.walk(directory, topdown=False):
        for file in files:
            if file.endswith('.pdf'):
                # Get the full path of the file
                file_path = Path(root) / file
                # Extract the song name without extension
                song_name = file_path.stem

                # Create a new directory with the song name
                new_dir = Path(directory) / song_name
                new_dir.mkdir(parents=True, exist_ok=True)

                # Move the PDF file into the new directory
                new_file_path = new_dir / file
                file_path.rename(new_file_path)

                # Create the info.json file
                tags = list(Path(root).relative_to(directory).parts)
                info = {
                    "name": song_name,
                    "tags": tags
                }

                # Save info.json in the new song directory
                info_path = new_dir / 'info.json'
                with open(info_path, 'w') as json_file:
                    json.dump(info, json_file, indent=4)

                # Check if the original directory is empty and delete it if so
                original_dir = file_path.parent
                if not any(original_dir.iterdir()):
                    original_dir.rmdir()

                    # Continue deleting parent directories if they're empty
                    while original_dir != Path(directory):
                        parent = original_dir.parent
                        if not any(parent.iterdir()):
                            parent.rmdir()
                            original_dir = parent
                        else:
                            break

# Example usage
# Replace 'some_directory_path' with the path of your directory
organize_songs(input('Enter root path: '))
