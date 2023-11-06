import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
from moviepy.editor import VideoFileClip, vfx, ImageClip, concatenate_videoclips
from proglog import ProgressBarLogger

# Custom Proglog logger
class TkProgressBarLogger(ProgressBarLogger):
    def __init__(self, progress_var, max_value):
        self.progress_var = progress_var
        self.max_value = max_value
        super().__init__()

    def callback(self, **changes):
        if 'index' in changes:
            self.progress_var.set(changes['index'] / self.max_value * 100)

    def bars_callback(self, bar, attr, value, old_value=None):
        if attr == 'index':
            percentage = (value / self.bars[bar]['total']) * 100
            self.progress_var.set(percentage)

# File selection function
def select_file(title, filetypes):
    return filedialog.askopenfilename(title=title, filetypes=filetypes)

# File extension validation function
def validate_file_extension(file_path, valid_extensions):
    _, ext = os.path.splitext(file_path)
    return ext.lower() in valid_extensions

# Main application class
class VideoProcessorApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Video Processing')
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, expand=True, padx=20, pady=20)
        self.show_dialogs()

    def show_dialogs(self):
        try:
            video_path = select_file('Select a video file', [('Video files', '*.mp4 *.mkv *.avi *.mov *.flv')])
            if not video_path or not validate_file_extension(video_path, ['.mp4', '.mkv', '.avi', '.mov', '.flv']):
                raise ValueError('Unsupported video file format.')

            image_path = select_file('Select an image file to insert (skip if not needed)', [('Image files', '*.jpg *.jpeg *.png *.bmp *.gif')])
            if image_path and not validate_file_extension(image_path, ['.jpg', '.jpeg', '.png', '.bmp', '.gif']):
                raise ValueError('Unsupported image file format.')

            self.process_video(video_path, image_path)
        except ValueError as e:
            messagebox.showerror('Error', str(e))

    def process_video(self, video_path, image_path):
        # Start the video processing in a separate thread
        threading.Thread(target=self._process_video_thread, args=(video_path, image_path)).start()

    def _process_video_thread(self, video_path, image_path):
        # This method will be executed in a separate thread
        try:
            clip = VideoFileClip(video_path)
            if image_path:
                image_clip = ImageClip(image_path).set_duration(0.01)
                clip = concatenate_videoclips([image_clip, clip])

            video_duration = clip.duration
            if video_duration > 139.98:
                speedup_factor = video_duration / 139.98
                adjusted_clip = clip.fx(vfx.speedx, speedup_factor)
                logger = TkProgressBarLogger(self.progress_var, 100)
                adjusted_filename = os.path.splitext(video_path)[0] + '_adjusted.mp4'
                adjusted_clip.write_videofile(adjusted_filename, logger=logger)
                clip.close()
                if image_path:
                    image_clip.close()
                self.root.after(0, lambda: messagebox.showinfo('완료', f'조절된 동영상이 {adjusted_filename}로 저장되었습니다.'))
                self.root.after(0, self.root.destroy)  # Close the main window and exit the program
            else:
                self.root.after(0, lambda: messagebox.showinfo('정보', '동영상의 길이가 이미 139초 이하입니다.'))
                self.root.after(0, self.root.destroy)  # Close the main window and exit the program
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror('Error', str(e)))

# Run the application
if __name__ == '__main__':
    root = tk.Tk()
    app = VideoProcessorApp(root)
    root.mainloop()
