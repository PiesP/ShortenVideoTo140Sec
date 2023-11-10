import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
from moviepy.editor import VideoFileClip, vfx, ImageClip, concatenate_videoclips
from proglog import ProgressBarLogger

class TkProgressBarLogger(ProgressBarLogger):
    def __init__(self, progress_var, max_value, status_var, cancel_event):
        super().__init__()
        self.progress_var = progress_var
        self.max_value = max_value
        self.status_var = status_var
        self.cancel_event = cancel_event

    def callback(self, **changes):
        if self.cancel_event.is_set():
            raise Exception("Video processing was cancelled by user.")
        if 'index' in changes:
            progress_percentage = changes['index'] / self.max_value * 100
            self.progress_var.set(progress_percentage)
            self.status_var.set(f'Processing... {progress_percentage:.2f}%')

    def bars_callback(self, bar, attr, value, old_value=None):
        if attr == 'index':
            percentage = (value / self.bars[bar]['total']) * 100
            self.progress_var.set(percentage)
            self.status_var.set(f'{bar.capitalize()} processing: {value}/{self.bars[bar]["total"]} ({percentage:.2f}%)')

def select_file(title, filetypes):
    return filedialog.askopenfilename(title=title, filetypes=filetypes)

def validate_file_extension(file_path, valid_extensions):
    _, ext = os.path.splitext(file_path)
    return ext.lower() in valid_extensions

class VideoProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Video Processing App')
        self.root.geometry('300x100')  # Make sure the height accommodates the Cancel button.

        self.status_var = tk.StringVar()
        self.status_label = tk.Label(root, textvariable=self.status_var)
        self.status_label.pack(fill=tk.X, expand=True, padx=20, pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, expand=True, padx=20, pady=5)

        self.cancel_button = ttk.Button(root, text="Cancel", command=self.cancel_processing)
        self.cancel_button.pack(fill=tk.X, expand=True, padx=20, pady=5)

        self.cancel_event = threading.Event()

        self.show_dialogs()

    def show_dialogs(self):
        video_path = select_file('Select a video file', [('Video files', '*.mp4 *.mkv *.avi *.mov *.flv')])
        if not video_path or not validate_file_extension(video_path, ['.mp4', '.mkv', '.avi', '.mov', '.flv']):
            messagebox.showerror('Error', 'Unsupported video file format or no file was selected.')
            return

        image_path = select_file('Select an image file to insert (skip if not needed)', [('Image files', '*.jpg *.jpeg *.png *.bmp *.gif')])
        if image_path and not validate_file_extension(image_path, ['.jpg', '.jpeg', '.png', '.bmp', '.gif']):
            messagebox.showerror('Error', 'Unsupported image file format.')
            return

        self.process_video(video_path, image_path)

    def process_video(self, video_path, image_path):
        threading.Thread(target=self._process_video_thread, args=(video_path, image_path)).start()

    def _process_video_thread(self, video_path, image_path):
        adjusted_filename = os.path.splitext(video_path)[0] + '_adjusted.mp4'
        try:
            clip = VideoFileClip(video_path)
            if image_path:
                image_clip = ImageClip(image_path).set_duration(0.01)
                clip = concatenate_videoclips([image_clip, clip])

            video_duration = clip.duration
            if video_duration > 139.98:
                speedup_factor = video_duration / 139.98
                adjusted_clip = clip.fx(vfx.speedx, speedup_factor)

                logger = self.setup_logger()
                self.write_video_file(adjusted_clip, adjusted_filename, logger)
                
            elif image_path:
                logger = self.setup_logger()
                clip = concatenate_videoclips([ImageClip(image_path), clip])
                clip.write_videofile(adjusted_filename, logger=logger)

            else:
                self.root.after(0, lambda: messagebox.showinfo('Info', 'No processing was needed.'))

        except Exception as e:
            self.handle_video_processing_error(e, adjusted_filename)

        finally:
            self.cleanup_resources(clip, image_path)

    def setup_logger(self):
        return TkProgressBarLogger(self.progress_var, 100, self.status_var, self.cancel_event)

    def write_video_file(self, clip, filename, logger):
        try:
            clip.write_videofile(filename, fps=24, bitrate="1400k", logger=logger)
        except Exception as e:
            print(f"Failed to write video file: {e}")
            raise

    def handle_video_processing_error(self, error, filename):
        error_message = str(error)
        self.root.after(0, lambda: messagebox.showerror('Error', error_message))
        self.attempt_cleanup_incomplete_file(filename)

    def attempt_cleanup_incomplete_file(self, filename):
        try:
            os.remove(filename)
            self.root.after(0, lambda: messagebox.showinfo('Info', 'Cancelled and cleaned up incomplete video file.'))
        except Exception as cleanup_error:
            self.root.after(0, lambda: messagebox.showerror('Error', f'Failed to delete incomplete video file: {cleanup_error}'))

    def cleanup_resources(self, clip, image_path):
        clip.close()
        if image_path and 'image_clip' in locals():
            locals()['image_clip'].close()

    def cancel_processing(self):
        self.cancel_event.set()
        self.status_var.set('Processing cancelled.')
        self.cancel_button.config(state=tk.DISABLED)

if __name__ == '__main__':
    root = tk.Tk()
    app = VideoProcessorApp(root)
    root.mainloop()
