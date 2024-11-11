import logging
import numpy as np
import pandas as pd
import xml.etree.ElementTree as etree
import os
import nodule_structs as nod_str
from utils import find_folder_with_max_files, string_to_dict
# logging.getLogger().setLevel(logging.INFO)

NS = {'nih': 'http://www.nih.gov'} # Namespace for the xml file(Same for all files)

# ------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------

def parse_xml(dirname, use_pandas=True):
    output_file = use_pandas and os.path.join(dirname, 'annotation.csv') or None
    output_file1 = use_pandas and os.path.join(dirname, 'char_list.csv') or None

    if use_pandas and os.path.isfile(output_file):
        logging.info(f"Loading annotations from file {output_file}")
        annotations = pd.read_csv(output_file)  # Load DataFrame
        char_list = pd.read_csv(output_file1)  # Load DataFrame
        logging.info("Load annotations complete")

    else:
        logging.info("Reading annotations")
        annotations = []
        char_list = []
        dirname = find_folder_with_max_files(dirname)
        xml_file = find_xml_file(dirname)
        logging.info(f"XML file parsed: {xml_file}")
        annotations, char_list = parse(xml_file)
    if use_pandas and not os.path.isfile(output_file):
        logging.info(f"Saving annotations to file {output_file}")
        df = pd.DataFrame(annotations)  # Convert to DataFrame
        df1 = pd.DataFrame(char_list)  # Convert to DataFrame
        df.to_csv(output_file, index=False)  # Save as CSV file
        df1.to_csv(output_file1, index=False)  # Save as CSV file
    return annotations, char_list

# ------------------------------------------------------------------------------------------------------

def find_xml_file(root):
    xml_file = ''
    count = 0
    for root, _, files in os.walk(root):
        for f in files:
            if not f.endswith('.xml'):
                continue
            else:
                xml_file = os.path.join(root, f)
                count+=1
    if count!=1:
        print("None or more than one XML files found")
        return None            
    return xml_file

# ------------------------------------------------------------------------------------------------------

def parse(xml_filename):
    logging.info(f"Parsing {xml_filename}")
    annotations = []
    nodule_character_list = []
    tree = etree.parse(xml_filename)
    root = tree.getroot()
    radiologist_no = 0
    for read_session in root.findall('nih:readingSession', NS):
        radiologist_no+=1
        rad_annotation = nod_str.RadAnnotation()
        rad_annotation.version = read_session.find('nih:annotationVersion', NS).text
        rad_annotation.id = read_session.find('nih:servicingRadiologistID', NS).text
        nodule_nodes = read_session.findall('nih:unblindedReadNodule', NS) # List all normal and small nodules
        non_nodules = read_session.findall('nih:nonNodule', NS) # List all non-nodules
        # print(len(nodule_nodes))
        # [print(f"Node: {node}\n") for node in nodule_nodes]
        
        for node in nodule_nodes:
            nodule = parse_nodule(node)
            if nodule.is_small:
                rad_annotation.small_nodules.append(nodule)
            else:
                rad_annotation.nodules.append(nodule)

        for node in non_nodules:
            nodule = parse_non_nodule(node)
            rad_annotation.non_nodules.append(nodule)
        # annotations.append(rad_annotation)
        N = rad_annotation.nodules
        S = rad_annotation.small_nodules
        NN = rad_annotation.non_nodules
        for i in range (len(N)):
            for j in range(len(N[i].rois)):
                annotations.append({"Radiologist No.": radiologist_no, "Nodule Type": "N", "No.": i+1, "Nodule ID": N[i].id, "Inclusion": str(N[i].rois[j].inclusion) , "Z-Coordinate": N[i].rois[j].z, "SOP-UID": N[i].rois[j].sop_uid, "No. of ROI points": len(N[i].rois[j].roi_xy) , "List of ROI points": str(N[i].rois[j].roi_xy), "ROI Centroid": N[i].rois[j].roi_centroid, "ROI Rectangle": N[i].rois[j].roi_rect})
        for i in range (len(S)):
            for j in range(len(S[i].rois)):
                annotations.append({"Radiologist No.": radiologist_no, "Nodule Type": "S", "No.": i+1, "Nodule ID": S[i].id, "Inclusion": str(S[i].rois[j].inclusion) , "Z-Coordinate": S[i].rois[j].z, "SOP-UID": S[i].rois[j].sop_uid, "No. of ROI points": len(S[i].rois[j].roi_xy) , "List of ROI points": str(S[i].rois[j].roi_xy), "ROI Centroid": "NA", "ROI Rectangle": "NA"})
        for i in range (len(NN)):
            for j in range(len(NN[i].rois)):
                annotations.append({"Radiologist No.": radiologist_no, "Nodule Type": "NN","No.": i+1, "Nodule ID": NN[i].id, "Inclusion": str(NN[i].rois[j].inclusion) , "Z-Coordinate": NN[i].rois[j].z, "SOP-UID": NN[i].rois[j].sop_uid, "No. of ROI points": len(NN[i].rois[j].roi_xy) , "List of ROI points": str(NN[i].rois[j].roi_xy), "ROI Centroid": "NA", "ROI Rectangle": "NA"})
        for i in range (len(N)):
            nodule_character_list.append({"Radiologist No.": radiologist_no, "Nodule Type": "N", "No.": i+1, "Nodule ID": N[i].id} | string_to_dict(N[i].characteristics.__str__()))
    return annotations, nodule_character_list

# ------------------------------------------------------------------------------------------------------

def parse_nodule(xml_node):  # xml_node is one unblindedReadNodule
    char_node = xml_node.find('nih:characteristics', NS)
    # if no characteristics, it is a smallnodule  i.e. is_small=TRUE
    is_small = (char_node is None or len(char_node) == 0)
    nodule = is_small and nod_str.SmallNodule() or nod_str.NormalNodule()
    nodule.id = xml_node.find('nih:noduleID', NS).text
    if not is_small:
        subtlety = char_node.find('nih:subtlety', NS)
        nodule.characteristics.subtlety = int(subtlety.text)
        nodule.characteristics.internal_struct = \
            int(char_node.find('nih:internalStructure', NS).text)
        nodule.characteristics.calcification = \
            int(char_node.find('nih:calcification', NS).text)
        nodule.characteristics.sphericity = \
            int(char_node.find('nih:sphericity', NS).text)
        nodule.characteristics.margin = \
            int(char_node.find('nih:margin', NS).text)
        nodule.characteristics.lobulation = \
            int(char_node.find('nih:lobulation', NS).text)
        nodule.characteristics.spiculation = \
            int(char_node.find('nih:spiculation', NS).text)
        nodule.characteristics.texture = \
            int(char_node.find('nih:texture', NS).text)
        nodule.characteristics.malignancy = \
            int(char_node.find('nih:malignancy', NS).text)
    xml_rois = xml_node.findall('nih:roi', NS)
    for xml_roi in xml_rois:
        roi = nod_str.NoduleRoi()
        roi.z = float(xml_roi.find('nih:imageZposition', NS).text)
        roi.sop_uid = xml_roi.find('nih:imageSOP_UID', NS).text
        # when inclusion = TRUE ->roi includes the whole nodule
        # when inclusion = FALSE ->roi is drown twice for one nodule
        # 1.ouside the nodule
        # 2.inside the nodule -> to indicate that the nodule has donut hole(the inside hole isnot part of the nodule) but by forcing inclusion to be TRUE, this situation is ignored
        roi.inclusion = (xml_roi.find('nih:inclusion', NS).text == "TRUE")
        edge_maps = xml_roi.findall('nih:edgeMap', NS)
        for edge_map in edge_maps:
            x = int(edge_map.find('nih:xCoord', NS).text)
            y = int(edge_map.find('nih:yCoord', NS).text)
            roi.roi_xy.append([x, y])
        xmax = np.array(roi.roi_xy)[:, 0].max()
        xmin = np.array(roi.roi_xy)[:, 0].min()
        ymax = np.array(roi.roi_xy)[:, 1].max()
        ymin = np.array(roi.roi_xy)[:, 1].min()
        if not is_small:  # only for normalNodules
            roi.roi_rect = (xmin, ymin, xmax, ymax)
            roi.roi_centroid = (
                (xmax + xmin) / 2, (ymax + ymin) / 2)  # center point
        nodule.rois.append(roi)
    return nodule  # is equivalent to unblindedReadNodule(xml element)

# ------------------------------------------------------------------------------------------------------

def parse_non_nodule(xml_node):  # xml_node is one nonNodule
    nodule = nod_str.NonNodule()
    nodule.id = xml_node.find('nih:nonNoduleID', NS).text
    roi = nod_str.NoduleRoi()
    roi.z = float(xml_node.find('nih:imageZposition', NS).text)
    roi.sop_uid = xml_node.find('nih:imageSOP_UID', NS).text
    loci = xml_node.findall('nih:locus', NS)
    for locus in loci:
        x = int(locus.find('nih:xCoord', NS).text)
        y = int(locus.find('nih:yCoord', NS).text)
        roi.roi_xy.append((x, y))
    nodule.rois.append(roi)
    return nodule  # is equivalent to nonNodule(xml element)

# ------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------

# Example usage
# folder_path = '/home/aiims/tumor/xml_parsing/LIDC-IDRI/LIDC-IDRI-0072'
# ann, char = parse_xml(folder_path)
# print(ann.head(), char.head())
