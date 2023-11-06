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
        try:
            video_path = select_file('Select a video file', [('Video files', '*.mp4 *.mkv *.avi *.mov *.flv')])
            if video_path and not validate_file_extension(video_path, ['.mp4', '.mkv', '.avi', '.mov', '.flv']):
                raise ValueError('Unsupported video file format.')
            elif not video_path:
                return

            image_path = select_file('Select an image file to insert (skip if not needed)', [('Image files', '*.jpg *.jpeg *.png *.bmp *.gif')])
            if image_path and not validate_file_extension(image_path, ['.jpg', '.jpeg', '.png', '.bmp', '.gif']):
                raise ValueError('Unsupported image file format.')
            elif not image_path:
                image_path = None

            self.process_video(video_path, image_path)
        except ValueError as e:
            messagebox.showerror('Error', str(e))

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
                logger = TkProgressBarLogger(self.progress_var, 100, self.status_var, self.cancel_event)

                if self.cancel_event.is_set():
                    raise Exception("Video processing was cancelled.")

                adjusted_clip.write_videofile(adjusted_filename, logger=logger)

                if self.cancel_event.is_set():
                    raise Exception("Video processing was cancelled.")

                clip.close()
                if image_path:
                    image_clip.close()

                self.root.after(0, lambda: messagebox.showinfo('Complete', f'Adjusted video saved as {adjusted_filename}.'))
                self.root.after(0, self.root.destroy)
            else:
                self.root.after(0, lambda: messagebox.showinfo('Info', 'Video duration is already below 140 seconds.'))
                self.root.after(0, self.root.destroy)
        except Exception as e:
            error_message = str(e)
            self.root.after(0, lambda: messagebox.showerror('Error', error_message))
            if os.path.exists(adjusted_filename):
                try:
                    os.remove(adjusted_filename)
                    self.root.after(0, lambda: messagebox.showinfo('Info', 'Cancelled and cleaned up incomplete video file.'))
                except Exception as cleanup_error:
                    self.root.after(0, lambda: messagebox.showerror('Error', f'Failed to delete incomplete video file: {cleanup_error}'))
            self.root.after(0, self.root.destroy)
        finally:
            clip.close()
            if image_path and 'image_clip' in locals():
                image_clip.close()

    def cancel_processing(self):
        self.cancel_event.set()
        self.status_var.set('Processing cancelled.')
        self.cancel_button.config(state=tk.DISABLED)

if __name__ == '__main__':
    root = tk.Tk()
    app = VideoProcessorApp(root)
    root.mainloop()
