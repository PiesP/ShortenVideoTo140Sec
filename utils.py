import datetime
from tkinter import filedialog

VIDEO_FILE_TYPES = [("Video files", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv *.mpeg *.mpg *.webm *.ogg")]
IMAGE_FILE_TYPES = [("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tif *.tiff *.webp")]

def select_file(file_types):
    return filedialog.askopenfilename(filetypes=file_types)

def get_current_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")
