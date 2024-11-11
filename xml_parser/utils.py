import os
import glob
import shutil
def create_folder(directory, folder_name):
    """
    Creates a folder with the specified name in the given directory.
    
    Parameters:
    - directory: The path to the directory where the folder should be created.
    - folder_name: The name of the folder to create.
    
    Returns:
    - path: The full path to the created folder.
    """
    # Combine the directory and folder name
    path = os.path.join(directory, folder_name)
    
    # Create the folder if it doesn't already exist
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Folder '{folder_name}' created at '{directory}'.")
    else:
        print(f"Folder '{folder_name}' already exists at '{directory}'.")
    
    return path

def find_folder_with_max_files(folder_path):
    max_files = 0
    max_files_folder = None

    # Walk through the folder tree
    for root, dirs, files in os.walk(folder_path):
        # If this folder contains files and not just sub-folders
        if files:
            num_files = len(files)
            # Update if this folder has more files than the current max
            if num_files > max_files:
                max_files = num_files
                max_files_folder = root

    return max_files_folder

def delete_files(dirname, file_name):
    # Find all files with the specified name in the folder's subfolders
    for folder in os.listdir(dirname):
        f = os.path.join(dirname, folder)
        file_to_delete = glob.glob(os.path.join(f, file_name))
        print(file_to_delete)
    # Delete each file
        os.remove(file_to_delete[0]) if file_to_delete else None
    print("Files deleted successfully.")
    return None

def delete_folder(dirname, folder_name):
    # Find all files with the specified name in the folder's subfolders
    for folder in os.listdir(dirname):
        f = os.path.join(dirname, folder)
        folder_to_delete = os.path.join(f, folder_name)
        print(folder_to_delete)
    # Delete each file
        shutil.rmtree(folder_to_delete) if os.path.exists(folder_to_delete) else None
    print(f"Folder {folder_name} deleted successfully.")
    return None

def string_to_dict(string):
    pairs = [item.strip() for item in string.split(",")]

    # Creating the def string_to_dict():e dictionary
    dictionary = {}
    for pair in pairs:
        key, value = pair.split(": ")
        dictionary[key.strip()] = int(value.strip())

    return dictionary
