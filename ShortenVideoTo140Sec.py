import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import os
from concurrent.futures import ThreadPoolExecutor
import threading
import time

class VideoProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Video Processing App')
        self.root.geometry('300x100')

        self.status_var = tk.StringVar()
        self.status_label = tk.Label(root, textvariable=self.status_var)
        self.status_label.pack(fill=tk.X, expand=True, padx=20, pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, expand=True, padx=20, pady=5)

        self.cancel_button = ttk.Button(root, text="Cancel", command=self.cancel_processing)
        self.cancel_button.pack(fill=tk.X, expand=True, padx=20, pady=5)

        self.cancel_requested = False
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.future = None
        self.processing_completed = False

        self.show_dialogs()

    def show_dialogs(self):
        try:
            video_path = self.select_file('Select a video file', [('Video files', '*.mp4 *.mkv *.avi *.mov *.flv')])
            if not video_path:
                self.root.destroy()
                return

            if not self.validate_file_extension(video_path, ['.mp4', '.mkv', '.avi', '.mov', '.flv']):
                raise ValueError('Unsupported video file format.')

            image_path = self.select_file('Select an image file to insert (skip if not needed)', [('Image files', '*.jpg *.jpeg *.png *.bmp *.gif')])
            if image_path and not self.validate_file_extension(image_path, ['.jpg', '.jpeg', '.png', '.bmp', '.gif']):
                raise ValueError('Unsupported image file format.')
            elif not image_path:
                image_path = None

            self.log_status("Processing started.")
            self.future = self.executor.submit(self.process_video, video_path, image_path)

        except ValueError as e:
            messagebox.showerror('Error', str(e))

    def select_file(self, title, filetypes):
        return filedialog.askopenfilename(title=title, filetypes=filetypes)

    def validate_file_extension(self, file_path, valid_extensions):
        _, ext = os.path.splitext(file_path)
        return ext.lower() in valid_extensions

    def process_video(self, video_path, image_path):
        adjusted_filename = os.path.splitext(video_path)[0] + '_adjusted.mp4'
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception("Error: Could not open video file.")

            width, height, frame_count = self.get_video_properties(cap)
            out = self.prepare_output_video(adjusted_filename, width, height, image_path)

            self.process_frames(cap, out, frame_count)
            self.finalize_video_processing(cap, out)

            if not self.cancel_requested:
                self.processing_completed = True
                self.root.destroy()
        except Exception as e:
            self.log_status(f"Error: {str(e)}")

    def get_video_properties(self, cap):
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        return width, height, frame_count

    def prepare_output_video(self, adjusted_filename, width, height, image_path):
        out = cv2.VideoWriter(adjusted_filename, cv2.VideoWriter_fourcc(*'mp4v'), 30, (width, height))
        if image_path:
            image = cv2.imread(image_path)
            image = cv2.resize(image, (width, height), interpolation=cv2.INTER_CUBIC)
            out.write(image)
        return out

    def process_frames(self, cap, out, frame_count):
        for current_frame in range(frame_count):
            if self.cancel_requested:
                self.log_status("Processing cancelled.")
                break

            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)
            self.update_progress((current_frame / frame_count) * 100)

        self.finalize_video_processing(cap, out)

    def cancel_processing(self):
        self.cancel_requested = True
        if self.future:
            self.future.cancel()
        self.status_var.set('Processing cancelled.')
        self.cancel_button.config(state=tk.DISABLED)

        threading.Thread(target=self.wait_and_force_close, daemon=True).start()

    def wait_and_force_close(self):
        time.sleep(10)
        if not self.processing_completed:
            self.root.destroy()

    def finalize_video_processing(self, cap, out):
        cap.release()
        if out is not None:
            out.release()
        self.log_status("Video processing finalized.")

    def update_progress(self, progress_percentage):
        self.progress_var.set(progress_percentage)

    def log_status(self, message):
        self.status_var.set(message)
        print(message)

if __name__ == '__main__':
    root = tk.Tk()
    try:
        app = VideoProcessorApp(root)
        root.mainloop()
    except Exception as e:
        print(f"An error occurred: {str(e)}")
