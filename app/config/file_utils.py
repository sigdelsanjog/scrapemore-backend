import os

temp = 'temp'
def create_temp_folder(directory=temp):
    """Check if the temp directory exists, create it if not."""
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory
