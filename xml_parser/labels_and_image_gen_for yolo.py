import pandas as pd
import os
from annotation import parse_xml
import sys
import re
import shutil

def process_excel_to_text(excel_file_path, data_df, char):
    """
    Reads an Excel file, processes SOP-UIDs, and creates text files with corresponding data.
    
    Parameters:
    excel_file_path (str): Path to the Excel file containing names and UIDs
    data_df (pd.DataFrame): DataFrame containing the data to be written to text files
    """
    
    try:
        # Check if Excel file exists
        if not os.path.exists(excel_file_path):
            raise FileNotFoundError(f"Excel file not found: {excel_file_path}")
            
            
        # Read the Excel file
        try:
            source_df = pd.read_excel(excel_file_path)
        except Exception as e:
            raise Exception(f"Error reading Excel file: {str(e)}")
        
        # Create output directory with full path
        current_dir = os.path.dirname(os.path.abspath(_file_))
        output_dir = os.path.join(current_dir, 'output_files_1')
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            print(f"Output directory created/verified at: {output_dir}")
        except Exception as e:
            raise Exception(f"Error creating output directory: {str(e)}")
        
        # Process each row in the source Excel file
        for index, row in source_df.iterrows():
            try:
                filename = str(row.iloc[0])  # First column as filename
                sop_uid = str(row.iloc[1])   # Second column as SOP-UID
                
                # Sanitize filename to remove invalid characters
                filename = "".join('_' if c == '/' else c for c in filename if c.isalnum() or c in (' ', '-', '_','/'))
                
                # Find corresponding data in data_df
                matching_data = data_df[data_df['SOP-UID'] == sop_uid]
                
                if not matching_data.empty:
                    # Create text file with absolute path
                    file_path = os.path.join(output_dir, f"{filename}.txt")
                    
                    try:
                        # Write data to text file
                        with open(file_path, 'w') as f:
                            # Write header
                            f.write(f"SOP-UID: {sop_uid}\n")
                            f.write("-" * 50 + "\n\n")
                            # Write all columns from matching data
                            for column in matching_data.columns:
                                value = matching_data[column].iloc[0]
                                column_size = matching_data[column].size  # same result, number of elements
                                try:
                                #print(column)
                                    if column == 'Nodule ID' and matching_data[column].iloc[0] == char[column].iloc[0]:
                                        val = char['malig'].iloc[0]
                                        # print(val)
                                        f.write(f"Label: {val}\n")
                                    if column == 'Nodule ID' and matching_data[column].iloc[1] == char[column].iloc[1]:
                                        val = char['malig'].iloc[1]
                                        # print(val)
                                        f.write(f"Label: {val}\n")
                                    if column == 'Nodule ID' and matching_data[column].iloc[2] == char[column].iloc[2]:
                                        val = char['malig'].iloc[1]
                                        # print(val)
                                        f.write(f"Label: {val}\n")
                                except:
                                    for i in range(column_size):
                                #print(column)
                                        if column == 'Nodule ID' and matching_data[column].iloc[i] == char[column].iloc[i]:
                                            val = char['malig'].iloc[i]
                                            # print(val)
                                            f.write(f"Label: {val}\n")
                                f.write(f"{column}: {value}\n")
                        print(f"Successfully created file: {file_path}")
                    except Exception as e:
                        print(f"Error writing to file {filename}.txt: {str(e)}")
                    
                # else:
                #     print(f"No matching data found for SOP-UID: {sop_uid}")
                    
            except Exception as e:
                print(f"Error processing row {index}: {str(e)}")
                
                continue  # Continue with next row even if current one fails
                
    except Exception as e:
        print(f"Critical error: {str(e)}")
        # Exit with error code


def extract_nodule_info(input_directory, output_directory, filename, image_width=512, image_height=512):
    input_path = os.path.join(input_directory, filename)
    
    # Check if file exists
    if not os.path.exists(input_path):
        print(f"Error: The file {filename} does not exist in the input directory.")
        return
    
    with open(input_path, 'r') as file:
        content = file.read()

    # Extract Label (if it's missing, set it to 0)
    label_match = re.search(r'Label: (\d+)', content)
    if label_match:
        label = int(label_match.group(1))
        # If the label is not 0, set it to 1
        if label != 0:
            label = 1
    else:
        # If label is missing, set it to 0
        label = 0

    # Extract Centroid
    centroid_match = re.search(r'ROI Centroid: \((\d+\.\d+), (\d+\.\d+)\)', content)
    if centroid_match:
        centroid = (float(centroid_match.group(1)), float(centroid_match.group(2)))
    else:
        # Extract List of ROI points and use the first one as centroid if available
        roi_points_match = re.search(r'List of ROI points: \[\((\d+), (\d+)\)\]', content)
        if roi_points_match:
            # Extract and parse the first ROI point
            roi_point = (int(roi_points_match.group(1)), int(roi_points_match.group(2)))
            centroid = roi_point  # Use this as centroid
        else:
            # If neither centroid nor ROI points are found, reject the file
            print(f"Error: Centroid or ROI points missing in the file {filename}. No output file will be created.")
            return

    # Set default width and height as 10 if label is 0 or centroid is present
    if label == 0:
        width = height = 10
    else:
        # Extract ROI Rectangle and calculate width and height
        rectangle_match = re.search(r'ROI Rectangle: \((\d+), (\d+), (\d+), (\d+)\)', content)
        if rectangle_match:
            x1, y1, x2, y2 = map(int, rectangle_match.groups())
            width = x2 - x1
            height = y2 - y1
        else:
            width = height = 10  # Default if rectangle is missing

    # Normalize values for YOLO
    normalized_x_center = centroid[0] / image_width
    normalized_y_center = centroid[1] / image_height
    normalized_width = width / image_width
    normalized_height = height / image_height

    # Prepare output file path
    output_filename = f"{filename.split('.')[0]}.txt"
    output_path = os.path.join(output_directory, output_filename)

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    # Write the extracted and scaled data in a single line, space-separated
    with open(output_path, 'w') as output_file:
        output_file.write(f"{label} {normalized_x_center} {normalized_y_center} {normalized_width} {normalized_height}\n")
    
    print(f"Extracted data saved to {output_path}")

def process_multiple_files(input_directory, output_directory):
    # Get all .txt files in the input directory
    for filename in os.listdir(input_directory):
        if filename.endswith('.txt'):
            extract_nodule_info(input_directory, output_directory, filename)

def rename_and_move_images(input_directory, output_directory):
    # Check if the output directory exists, if not create it
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Walk through all folders in the input directory
    for root, dirs, files in os.walk(input_directory):
        for file in files:
            # Check if the file is a .jpg image
            if file.endswith('.jpg'):
                # Get the parent folder's name
                parent_folder_name = os.path.basename(root)
                
                # Construct the new filename as "parentfolder_originalname.jpg"
                new_filename = f"{parent_folder_name}_{file}"
                
                # Create the full path for the input file
                input_file_path = os.path.join(root, file)
                
                # Create the full path for the output file
                output_file_path = os.path.join(output_directory, new_filename)
                
                # Copy the image to the output directory with the new name
                shutil.copy(input_file_path, output_file_path)
                print(f"Copied and renamed {file} to {new_filename}")
    
def sync_folders(input_folder_1, input_folder_2):
    # Get all base names (without extensions) of files in both folders
    files_in_folder_1 = [os.path.splitext(file)[0] for file in os.listdir(input_folder_1) if os.path.isfile(os.path.join(input_folder_1, file))]
    files_in_folder_2 = [os.path.splitext(file)[0] for file in os.listdir(input_folder_2) if os.path.isfile(os.path.join(input_folder_2, file))]

    # Find files in folder 1 that are not in folder 2
    files_to_delete_from_folder_1 = [file for file in files_in_folder_1 if file not in files_in_folder_2]
    
    # Find files in folder 2 that are not in folder 1
    files_to_delete_from_folder_2 = [file for file in files_in_folder_2 if file not in files_in_folder_1]

    # Delete extra files in folder 1
    for file in files_to_delete_from_folder_1:
        # Get full path to the file in folder 1 (with extension)
        file_path_1 = os.path.join(input_folder_1, file + os.path.splitext(next(f for f in os.listdir(input_folder_1) if os.path.splitext(f)[0] == file))[1])
        if os.path.exists(file_path_1):
            os.remove(file_path_1)
            print(f"Deleted {file_path_1} from folder 1")

    # Delete extra files in folder 2
    for file in files_to_delete_from_folder_2:
        # Get full path to the file in folder 2 (with extension)
        file_path_2 = os.path.join(input_folder_2, file + os.path.splitext(next(f for f in os.listdir(input_folder_2) if os.path.splitext(f)[0] == file))[1])
        if os.path.exists(file_path_2):
            os.remove(file_path_2)
            print(f"Deleted {file_path_2} from folder 2")

# Example usage
if __name__ == "__main__":
    _file_="/home/aiims/tumor/"
    try:
        # Get the current script's directory
        script_dir = os.path.dirname(_file_)
        # Construct full path to Excel file
        excel_file = os.path.join(script_dir, "dicom_file_sop_uid_data.xlsx")
        INPUT_FOLDER = "/home/aiims/Downloads/TCIA_LIDC-IDRI_20200921/LIDC-IDRI"
        # Iterate through all patient directories
        patients = os.listdir(INPUT_FOLDER)
        patients.sort()
        preprocessed_scans=[]
        patient_names=[]
        final=[]
        for patient in patients:
            patient_path = os.path.join(INPUT_FOLDER, patient)
            try:
                data_df, char = parse_xml(patient_path)
            except Exception as e:
                print(f"Error parsing XML: {str(e)}")
                continue
    
        # Process the files
            process_excel_to_text(excel_file, data_df, char)
               
    except Exception as e:
        print(f"Program execution failed: {str(e)}")
        sys.exit(1)

    # after processing to excel then further preprocess them to get the output labels satisfying the constraints for yolo model
    input_directory = "/home/aiims/output_files_1"  # Replace with the actual input directory path
    output_directory = "/home/aiims/tumor/xml_parsing/labels_set2"  # Replace with the actual output directory path
    process_multiple_files(input_directory, output_directory)

    # after that now put the images required in a sepearte folder for preprocessing
    # Example usage
    input_images= "/home/aiims/Downloads/Preprocessed_CT_Scans"  # Replace with the actual input directory path
    output_images = "/home/aiims/tumor/xml_parsing/datas_set2"  # Replace with the actual output directory path
    rename_and_move_images(input_images, output_images)

    # now sync the images to the labels by only keepin those images whose labels are present 
    # Example usage
    folder_1 = "/home/aiims/tumor/xml_parsing/datas_set2"  # Replace with the actual folder path 1
    folder_2 = "/home/aiims/tumor/xml_parsing/labels_set2"  # Replace with the actual folder path 2
    sync_folders(folder_1, folder_2)