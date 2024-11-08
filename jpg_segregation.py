import pydicom
from PIL import Image
import os
import glob
import shutil
import pandas as pd
import numpy as np
from all_annotations_main import run_annotations
from utils import create_folder, find_folder_with_max_files
import re

def cancer_nodes_zpos(folder_path):
    data_dict = run_annotations(folder_path)
    # print(data_dict.keys())
    # print(data_dict.items())
    new_dict = {}
    for key in data_dict.keys():
        df, char = data_dict[key]
        field = "Nodule Type"
        filtered_df = df[df[field] == 'N']
        # print(filtered_df.head()) if key == "LIDC-IDRI-0203" else None
        # Extract each column from the filtered rows into separate lists
        value1_list = filtered_df['Z-Coordinate'].tolist()
        value2_list = filtered_df['SOP-UID'].tolist()
        new_dict[key] = (value1_list, value2_list)
    # print(new_dict["LIDC-IDRI-0203"][0])
    return new_dict

def Cancerous_slices():
    """
    Gives a list of cancerous slices from all the files
    """
    # Ensure output directories exist
    dirname = "/home/aiims/tumor/xml_parsing/LIDC-IDRI"
    node_dict = cancer_nodes_zpos(dirname)
    patient_folder_list = node_dict.keys()
    list_of_cancerous_slices=[]
    for patient_folder_name in patient_folder_list:
        patient_folder = os.path.join(dirname, patient_folder_name)    
        dicom_folder = find_folder_with_max_files(patient_folder)
        sopuid_list = node_dict[patient_folder_name][1]
        for file_path in glob.glob(os.path.join(dicom_folder, "*.dcm")):
            dicom_file = pydicom.dcmread(file_path)

            # Get the SOPInstanceUID for the current file
            sop_uid = dicom_file.SOPInstanceUID if 'SOPInstanceUID' in dicom_file else None

            # Determine if this file matches one of the target SOPInstanceUIDs
            if sop_uid in sopuid_list:
                list_of_cancerous_slices.append(file_path)
    return list_of_cancerous_slices
    
# Regular expression to capture LIDC-IDRI-XXXX and X-XXX
pattern = r'LIDC-IDRI-(\d{4})\/.*?\/(\d+-\d+)(?=\.dcm)'
list_of_slices=Cancerous_slices()

# Extracting the required parts
results = []
for path in list_of_slices:
    match = re.search(pattern, path)
    if match:
        lidc_idri = f"LIDC-IDRI-{match.group(1)}"
        x_xxx = match.group(2)
        new_path = os.path.join(lidc_idri, x_xxx)  
        results.append((lidc_idri, x_xxx, new_path))
        
results.sort(key=lambda x: x[0])

INPUT_FOLDER = "/home/aiims/tumor/Preprocessed_CT_Scans" 

expected_files = [os.path.join(INPUT_FOLDER, f"{new_path}.jpg") for _, _, new_path in results]
patients = os.listdir(INPUT_FOLDER)
patients.sort()
preprocessed_scans=[]
patient_names=[]

create_folder("/home/aiims/tumor/xml_parsing/sanidhya", "cancerous_jpg")
create_folder("/home/aiims/tumor/xml_parsing/sanidhya", "non_cancerous_jpg") 
a=1
b=1
for patient in patients:
    patient_path = os.path.join(INPUT_FOLDER, patient)
    if os.path.isdir(patient_path):  # Ensure it's a directory
        for file_name in os.listdir(patient_path):
            # Create the full file path
            
            file_path = os.path.join(patient_path, file_name) 
            if file_path in expected_files:
                    # Create the destination path in the output folder
                output_folder = "/home/aiims/tumor/xml_parsing/sanidhya/cancerous_jpg"
                output_path = os.path.join(output_folder,f"{a}.jpg")
                a+=1
                shutil.copy(file_path, output_path)
                
            else:
                output_folder = "/home/aiims/tumor/xml_parsing/sanidhya/non_cancerous_jpg"
                output_path = os.path.join(output_folder, f"{b}.jpg")
                b+=1
                shutil.copy(file_path, output_path)
                
        print("DICOM files have been organized into matching and non-matching folders.")
       

