The XML file is defined for each patient and is a part of the LIDC IDRI Consortium dataset, it contains annotations for each patient's nodules by four anonymous radiologists.
The image segregation for cnn helps uses the data to clssify the images into cancerous and non cancerous for cnn model.
The labels and image gen preprocesses the xml file for each slice of all the patient to generate a txt file containing the data in a format needed by the yolomodel and ensures that the images are also present in another folder for yolo model
...
