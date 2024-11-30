# Preprocessing steps
Leverages the fact that CT scans have HU units which is characterization of different radiodensity levels that help in cleaning the data by removing the data of parts such as bones etc leaving with a cleaner image of lungs which is then used to processing.
# Preprocessing visualiztion
Helps to visualize what happens while preprocessing when viewing in a 3D form
# Image segregation for cnn 
Uses the data to classify the images into cancerous and non cancerous for cnn model
# Labels and image gen for yolo
Processes the xml file for each slice of all the patient to generate a txt file containing the data in a format needed by the yolo model and ensures that the images are also present in another folder
...
