import numpy as np 
import pandas as pd 
import pydicom
import os
import scipy.ndimage
import matplotlib.pyplot as plt
import cv2 
from PIL import Image

from skimage import measure, morphology
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from scipy.ndimage import gaussian_filter

#--------------------------------------------------------------------------------------------------------------

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

#--------------------------------------------------------------------------------------------------------------

def load_scan(path):
    slices = [
        (pydicom.read_file(os.path.join(path, s)), s[:-4])  # Remove .dcm extension
        for s in os.listdir(path) if s.endswith('.dcm')
    ]
    
    # Sort slices by ImagePositionPatient[2]
    slices.sort(key=lambda x: float(x[0].ImagePositionPatient[2]))
    
    # Calculate slice thickness
    try:
        slice_thickness = np.abs(slices[0][0].ImagePositionPatient[2] - slices[1][0].ImagePositionPatient[2])
    except:
        slice_thickness = np.abs(slices[0][0].SliceLocation - slices[1][0].SliceLocation)
        
    # Set SliceThickness for each slice
    for s, name in slices:
        s.SliceThickness = slice_thickness
        s.FileName = name  # Attach the filename without extension

    return slices

#--------------------------------------------------------------------------------------------------------------

def resample(image, scan, new_spacing=[1,1,1]):
    # Determine current pixel spacing
    
    slice_thickness = scan[0].SliceThickness
    pixel_spacing = scan[0].PixelSpacing
    
    # Ensure pixel_spacing is a numpy array
    if isinstance(pixel_spacing, list):
        pixel_spacing = np.array(pixel_spacing)
    elif isinstance(pixel_spacing, np.ndarray):
        # Ensure pixel_spacing is a 1D array
        if pixel_spacing.ndim != 1:
            raise ValueError("PixelSpacing should be a 1D numpy array or a list")

    # Convert slice_thickness to numpy array
    slice_thickness_array = np.array([slice_thickness])

    # Concatenate slice_thickness_array and pixel_spacing
    spacing = np.concatenate((slice_thickness_array, pixel_spacing))

    # Convert to float32 for consistency
    spacing = spacing.astype(np.float32)
    

    resize_factor = spacing / new_spacing
    new_real_shape = image.shape * resize_factor
    new_shape = np.round(new_real_shape)
    real_resize_factor = new_shape / image.shape
    new_spacing = spacing / real_resize_factor
    
    image = scipy.ndimage.zoom(image, real_resize_factor, mode='nearest')
    
    return image, new_spacing 

#--------------------------------------------------------------------------------------------------------------

def normalize(image):
    MIN_BOUND = -1000.0
    MAX_BOUND = 400.0
    image = (image - MIN_BOUND) / (MAX_BOUND - MIN_BOUND)
    image[image > 1] = 1.
    image[image < 0] = 0.
    return image

#--------------------------------------------------------------------------------------------------------------

def get_pixels_hounds(slices):
    image = np.stack([s.pixel_array for s in slices])
    image = image.astype(np.int16)
    image[image == -2000] = 0

    for slice_number in range(len(slices)):
        intercept = slices[slice_number].RescaleIntercept
        slope = slices[slice_number].RescaleSlope
        if slope != 1:
            image[slice_number] = slope * image[slice_number].astype(np.float64)
            image[slice_number] = image[slice_number].astype(np.int16)
        image[slice_number] += np.int16(intercept)

    # Normalize the image
    image = normalize(image)
    
    # Optionally apply zero centering (be cautious with this for CT scans)
    # image = zero_center(image)

    # Apply Gaussian filter for smoothing
    image = gaussian_filter(image, sigma=1)

    return np.array(image, dtype=np.float32)

#--------------------------------------------------------------------------------------------------------------

def largest_label_volume(im, bg=-1):
    vals, counts = np.unique(im, return_counts=True)

    counts = counts[vals != bg]
    vals = vals[vals != bg]

    if len(counts) > 0:
        return vals[np.argmax(counts)]
    else:
        return None

#--------------------------------------------------------------------------------------------------------------

def segment_lung_mask(image, fill_lung_structures=True):
    
    # Not actually binary, but 1 and 2. 
    # 0 is treated as background, which we do not want
    binary_image = np.array(image > 0.3, dtype=np.int8)+1
    labels = measure.label(binary_image)
    
    # Pick the pixel in the very corner to determine which label is air.
    #   Improvement: Pick multiple background labels from around the patient
    #   More resistant to "trays" on which the patient lays cutting the air 
    #   around the person in half
    background_label = labels[0,0,0]
    
    #Fill the air around the person
    binary_image[background_label == labels] = 2
    
    # Method of filling the lung structures (that is superior to something like 
    # morphological closing)
    if fill_lung_structures:
        # For every slice we determine the largest solid structure
        for i, axial_slice in enumerate(binary_image):
            axial_slice = axial_slice - 1
            labeling = measure.label(axial_slice)
            l_max = largest_label_volume(labeling, bg=0)
            
            if l_max is not None: #This slice contains some lung
                binary_image[i][labeling != l_max] = 1

    binary_image -= 1 #Make the image actual binary
    binary_image = 1-binary_image # Invert it, lungs are now 1
    
    # Remove other air pockets insided body
    labels = measure.label(binary_image, background=0)
    l_max = largest_label_volume(labels, bg=0)
    if l_max is not None: # There are air pockets
        binary_image[labels != l_max] = 0

    return binary_image

#--------------------------------------------------------------------------------------------------------------

def process_patient(patient_folder):
    patient_correct_folder = find_folder_with_max_files(patient_folder)
    patient = load_scan(patient_correct_folder)
    
    slices= [pixel[0] for pixel in patient]
    # Convert the DICOM slices to pixel data
    patient_pixels = get_pixels_hounds(slices)
    
    # Resample the pixel data
    #pix_resampled, spacing = resample(first_patient_pixels, first_patient, [1, 1, 1])
    
    # Segment the lung mask
    segmented_lungs = segment_lung_mask(patient_pixels, False)
    file_name=[fname[1]for fname in patient]
    return segmented_lungs,file_name

#--------------------------------------------------------------------------------------------------------------

def to_jpg(pixel_array):
    # Read the DICOM file
    pixel_array = pixel_array.astype(np.float32)

    # Normalize the pixel values to [0, 255]
    pixel_array = (pixel_array - np.min(pixel_array)) / (np.max(pixel_array) - np.min(pixel_array)) * 255
    pixel_array = pixel_array.astype(np.uint8)

    # If the array has more than one channel, convert to grayscale
    if pixel_array.ndim == 2:  # Single channel (already grayscale)
        img = Image.fromarray(pixel_array)
    elif pixel_array.ndim == 3:  # Multi-channel (RGB or others)
        # Convert to grayscale
        img = Image.fromarray(pixel_array).convert("L")  # "L" mode for grayscale
    else:
        raise ValueError("Unsupported image shape: {}".format(pixel_array.shape))

    return img

#--------------------------------------------------------------------------------------------------------------

INPUT_FOLDER = "/home/aiims/tumor/xml_parsing/LIDC-IDRI"
OUTPUT_FOLDER = "/home/aiims/tumor/Preprocessed_CT_Scans" 

# Ensure output directory exists
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
# Iterate through all patient directories
patients = os.listdir(INPUT_FOLDER)
patients.sort()
preprocessed_scans=[]
patient_names=[]

for patient in patients:
    patient_path = os.path.join(INPUT_FOLDER, patient)
    if os.path.isdir(patient_path):  # Ensure it's a directory
        patient_scans,scan_file=process_patient(patient_path)
        combined_scans = [(patient_scans[i], scan_file[i]) for i in range(len(scan_file))]
    preprocessed_scans.append(combined_scans)
    patient_names.append(patient)

for name, combined_scans in zip(patient_names, preprocessed_scans):
    # Create a folder for each patient in the output directory
    patient_folder = os.path.join(OUTPUT_FOLDER, name)
    os.makedirs(patient_folder, exist_ok=True)
    
    # Loop through combined scans to save each scan as a JPEG
    for scan, filename in combined_scans:
        img=to_jpg(scan)

        # Construct the full file path for saving
        file_name = os.path.join(patient_folder, f"{filename}.jpg")

        # Save the image
        img.save(file_name)

        print(f"Saved {file_name}")
