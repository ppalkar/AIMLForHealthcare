import annotation as ann
import os
import pandas as pd
import numpy as np
import ast
import pydicom
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from utils import create_folder, delete_folder, delete_files

def run_annotations(patient_directory):
    patients_dict = {}
    count = 0
    for folder in os.listdir(patient_directory):
        try:
            f = os.path.join(patient_directory, folder) if folder!='LICENSE' else None
            if (f!=None):
                anno, charac = ann.parse_xml(f)
                # print()
                # print()
                # print(f"ANNOTATION & CHAR LIST for {folder} is completed.", end = '')
                # count+=1
                # print(count,"\n")
                # print()
                patients_dict[folder] = [anno, charac] 
        except Exception as e:
            print(f"Error loading {folder}")
            continue    
            # print()
    return patients_dict    



def bounding_box_create(dicom_directory, folder_name, pat_data):
    pat_1 = pat_data[os.path.basename((dicom_directory))][0]
    dicom_dir = ann.find_folder_with_max_files(dicom_directory)
    output_dir = create_folder(dicom_directory,folder_name)
    #Iterate thrpugh all the rows of the dataframe successfully removing nan rows
    for index, row in pat_1.iterrows():
        # Skip if both SOP-UIeD and Z-Coordinate are NaN
        if pd.isna(row['SOP-UID']) and pd.isna(row['Z-Coordinate']):
            continue
        
        # Convert string values to appropriate types
        try:
            z_coordinate = float(row['Z-Coordinate']) if pd.notna(row['Z-Coordinate']) else None
            inclusion = row['Inclusion'] == True
            roi_centroid = ast.literal_eval(row['ROI Centroid']) if pd.notna(row['ROI Centroid']) and row['ROI Centroid'] != 'nan' else None
            roi_rectangle = ast.literal_eval(row['ROI Rectangle']) if pd.notna(row['ROI Rectangle']) and row['ROI Rectangle'] != 'nan' else None
            # print(roi_rectangle)    
            # print(f"Row {index} successfully parsed.")
        except (ValueError, SyntaxError):
            print(f"Skipping row {index} due to data parsing error.")
            continue
        # Load the DICOM file using the SOP-UID
        dicom_file_path = None
        for root, _, files in os.walk(dicom_dir):
            for file in files:
                if file.lower().endswith('.dcm'):
                    dicom_path = os.path.join(root, file)
                    dicom_data = pydicom.dcmread(dicom_path)

                    # Check if the SOPInstanceUID matches
                    if hasattr(dicom_data, 'SOPInstanceUID') and dicom_data.SOPInstanceUID == row['SOP-UID']:
                        dicom_file_path = dicom_path
                        break
            if dicom_file_path:
                break

        if dicom_file_path is None:
            print(f"DICOM file with SOP-UID {row['SOP-UID']} not found.")
            continue
        
        # Extract the image pixel array
        image = dicom_data.pixel_array

        # Plot the image
        fig, ax = plt.subplots(1)
        ax.imshow(image, cmap='gray')

        # Mark the centroid if it is not None
        if roi_centroid is not None:
            ax.plot(roi_centroid[0], roi_centroid[1], 'ro')  # Mark centroid with a red dot

        # Draw the bounding box if ROI Rectangle is not None
        if roi_rectangle is not None:
            xmin, ymin, xmax, ymax = roi_rectangle
            x = xmin
            y = ymin
            width = xmax - xmin
            height = ymax - ymin
            rect = Rectangle((x, y), width, height, linewidth=1, edgecolor='r', facecolor='none')
            ax.add_patch(rect)

        # Display the marked image
        # plt.title(f"Image with SOP-UID {row['SOP-UID']}")
        # plt.show()
        output_file = os.path.join(output_dir, f"SOP_UID_{row['SOP-UID']}.jpg")
        plt.savefig(output_file, format='jpg')
        plt.close(fig)

        print(f"Saved image: {output_file}")
        return None
#__main___
# dicom_dir = '/home/aiims/tumor/xml_parsing/LIDC-IDRI/LIDC-IDRI-0138'
# folder_name = 'images'
# dirname = "/home/aiims/tumor/xml_parsing/LIDC-IDRI"
# pat_data = run_annotations(dirname)
# print(pat_1.columns.to_list())
# bounding_box_create(dicom_dir, folder_name, pat_data)

# centroid_arr = (pat_data["LIDC-IDRI-0072"][0]["ROI Centroid"]).to_list()
# print(centroid_arr)
# delete_files(dirname, "char_list.csv")
# delete_files(dirname, "annotation.csv")
# delete_folder(dirname, "images")
