# ------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------

class RadAnnotation:
    def __init__(self, init=True):
        self.version = None
        self.id = None

        self.nodules = []  # is normalNodule i.e in xml unblindedReadNodule with characteristics info
        self.small_nodules = []  # in xml unblindedReadNodule with no characteristics info
        self.non_nodules = []  # located inside readingSession
        self.initialized = init
        return

    def is_init(self):
        return self.initialized

    def set_init(self, init):
        self.initialized = init
        return

    def __str__(self):
        n_nodules = len(self.nodules)
        n_small_nodules = len(self.small_nodules)
        n_non_nodules = len(self.non_nodules)
        strng = f"Annotation Version {self.version} Radiologist ID {self.id} \n"
        strng += f"#Nodules: {n_nodules}; #SmallNodules: {n_small_nodules}; #NonNodules: {n_non_nodules} \n"

        if (n_nodules > 0):
            strng += f"\n--- Nodules {n_nodules}---\n" 
            for i in range(n_nodules):
                strng += f"NORMAL NODULE: {i+1}"
                strng += str(self.nodules[i])

        if (n_small_nodules > 0):
            strng += f"\n--- Small Nodules {n_small_nodules} ---\n"
            for i in range(n_small_nodules):
                strng += f"SMALL NODULE: {i+1}"
                strng += str(self.small_nodules[i])

        if (n_non_nodules > 0):
            strng += f"\n--- Non Nodules {n_non_nodules} ---\n" 
            for i in range(n_non_nodules):
                strng += f"NON NODULE: {i+1}"
                strng += str(self.non_nodules[i])

        strng += "-" * 79 + "\n"
        return strng

# ------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------

class AnnotationHeader:
    def __init__(
            self):  # 4 elements are not included b/c they don't have data
        # inside
        self.version = None
        self.message_id = None
        self.date_request = None
        self.time_request = None
        self.task_desc = None
        self.series_instance_uid = None
        self.date_service = None
        self.time_service = None
        self.study_instance_uid = None

    def __str__(self):
        str = ("--- XML HEADER ---\n"
               "Version (%s) Message-Id (%s) Date-request (%s) Time-request ("
               "%s) \n"
               "Series-UID (%s)\n"
               "Time-service (%s) Task-descr (%s) Date-service (%s) "
               "Time-service (%s)\n"
               "Study-UID (%s)") % (
                  self.version, self.message_id, self.date_request,
                  self.time_request,
                  self.series_instance_uid, self.time_service, self.task_desc,
                  self.date_service,
                  self.time_service, self.study_instance_uid)
        return str

# ------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------

class IdriReadMessage:
    def __init__(self):
        self.header = AnnotationHeader()
        self.annotations = []

# ------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------

class NoduleRoi:  # is common for nodule and non-nodule
    def __init__(self, z_pos=0., sop_uid=''):
        self.z = z_pos
        self.sop_uid = sop_uid
        self.inclusion = True

        self.roi_xy = []  # to hold list of x,ycords in edgemap(edgmap pairs)
        self.roi_rect = []  # rectangle to hold the roi
        self.roi_centroid = []  # to hold centroid of the roi
        return

    def __str__(self):
        n_pts = len(self.roi_xy)
        str = f"Inclusion {self.inclusion} Z = {self.z} SOP_UID {self.sop_uid} \n ROI points {n_pts}  ::  " 

        if (n_pts > 2):
            str += "[[ %d,%d ]] :: " % (
            self.roi_centroid[0], self.roi_centroid[1])
            str += "(%d, %d), (%d,%d)..." % (
                self.roi_xy[0][0], self.roi_xy[0][1], self.roi_xy[1][0],
                self.roi_xy[1][1])
            str += "(%d, %d), (%d,%d)" % (
                self.roi_xy[-2][0], self.roi_xy[-2][1], self.roi_xy[-1][0],
                self.roi_xy[-1][1])
        else:
            for i in range(n_pts):
                str += f"({self.roi_xy[i][0]}, {self.roi_xy[i][1]}),"
        return str

# ------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------

class Nodule:  # is base class for all nodule types (NormalNodule, SmallNodule and NonNodule)
    def __init__(self):
        self.id = None
        self.rois = []
        self.is_small = False #Will be assigned as True for SmallNodule

    def __str__(self):
        strng = f"--- Nodule ID: {self.id}; Small: {str(self.is_small)} ---\n" 
        strng += self.tostring() + "\n"
        return strng

    def tostring(self):
        pass

# ------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------

# Defined only for Normal Nodules' characteristics assignment
class NoduleCharacteristics:
    def __init__(self):
        self.subtlety = 0
        self.internal_struct = 0
        self.calcification = 0
        self.sphericity = 0
        self.margin = 0
        self.lobulation = 0
        self.spiculation = 0
        self.texture = 0
        self.malignancy = 0
        return

    def __str__(self):
        str = f"subtlty: {self.subtlety}, intstruct: {self.internal_struct}, calci: {self.calcification}, sphere: {self.sphericity}, margin: {self.margin}, lob: {self.lobulation}, spicul: {self.spiculation}, txtur: {self.texture}, malig: {self.malignancy}"
        return str
    
# ------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------

class NormalNodule(Nodule):
    def __init__(self):
        Nodule.__init__(self)
        self.characteristics = NoduleCharacteristics()
        self.is_small = False

    def tostring(self):
        strng = str(self.characteristics)
        strng += "\n"

        for roi in self.rois:
            strng += str(roi) + "\n"  # str calls __str__ of NoduleRoi's class
            # i.e.converting roi to
        return strng  # string to prepare it for printing(it doesn't print it)

# ------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------

class SmallNodule(Nodule):
    def __init__(self):
        Nodule.__init__(self)
        self.is_small = True

    def tostring(self):
        strng = '\n'
        for roi in self.rois:
            strng += str(roi) + "\n"
        return strng

# ------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------

class NonNodule(Nodule):
    def __init__(self):
        Nodule.__init__(self)
        self.is_small = True

    def tostring(self):
        strng = '\n'
        for roi in self.rois:
            strng += str(roi)
        return strng

# ------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------
