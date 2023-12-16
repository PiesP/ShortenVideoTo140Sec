import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import datetime
import os
import logging
import ffmpeg_processing

ENCODER = None
CREATE_NO_WINDOW = 0x08000000

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

VIDEO_FILE_TYPES = [("Video files", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv *.mpeg *.mpg *.webm *.ogg")]
IMAGE_FILE_TYPES = [("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tif *.tiff *.webp")]

def select_file(file_types):
    return filedialog.askopenfilename(filetypes=file_types)

def get_current_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")

def start_processing(video_path, image_path, progress_var, status_var, cancel_event, root):
    if video_path:
        processing_thread = threading.Thread(target=ffmpeg_processing.process_video, args=(video_path, image_path, progress_var, status_var, cancel_event, root, ENCODER))
        processing_thread.start()
    else:
        messagebox.showinfo("Cancelled", "Process cancelled by user")
        root.quit()

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import ffmpeg_processing

def main():
    global ENCODER
    root = tk.Tk()
    root.title("Shorten Video To 140s")
    root.geometry("400x100")

    if not ffmpeg_processing.is_ffmpeg_encoder_available('hevc_nvenc'):
        if not ffmpeg_processing.is_ffmpeg_encoder_available('libx265'):
            messagebox.showerror("Error", "Neither 'hevc_nvenc' nor 'libx265' encoders are available. Please install 'libx265' to proceed.")
            root.quit()
            return
        else:
            ENCODER = 'libx265'
    else:
        ENCODER = 'hevc_nvenc'

    progress_var = tk.DoubleVar()
    status_var = tk.StringVar(value="Displaying the progress status here.")

    status_label = tk.Label(root, textvariable=status_var)
    status_label.pack()

    progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100)
    progress_bar.pack(fill=tk.X, padx=10, pady=5)

    cancel_event = threading.Event()

    def on_cancel():
        cancel_event.set()

    cancel_button = tk.Button(root, text="Cancel", command=on_cancel)
    cancel_button.pack()

    video_path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv *.mpeg *.mpg *.webm *.ogg")])
    image_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tif *.tiff *.webp")])

    if not video_path:
        messagebox.showinfo("Cancelled", "No video file selected")
        root.quit()
        return

    def on_processing_finished():
        if root.winfo_exists():
            root.quit()

    processing_thread = threading.Thread(
        target=ffmpeg_processing.process_video, 
        args=(video_path, image_path, progress_var, status_var, cancel_event, root, ENCODER, on_processing_finished)
    )
    processing_thread.start()

    root.mainloop()

    if root.winfo_exists():
        root.destroy()

if __name__ == "__main__":
    main()
