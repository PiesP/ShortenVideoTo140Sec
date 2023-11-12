import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
from moviepy.editor import VideoFileClip, vfx
from PIL import Image
from plyer import notification
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

class OptionSelector:
    def __init__(self, parent):
        self.parent = parent
        self.selector_window = tk.Toplevel(parent)
        self.selector_window.title('Select an Option')
        self.selector_window.geometry('300x100')

        ttk.Button(self.selector_window, text='Shorten Video to under 140 seconds', command=lambda: self.process_option(1)).pack(fill=tk.X, expand=True, padx=20, pady=5)
        ttk.Button(self.selector_window, text='Convert to WebP', command=lambda: self.process_option(2)).pack(fill=tk.X, expand=True, padx=20, pady=5)
        ttk.Button(self.selector_window, text='Cancel', command=self.cancel_option_selector).pack(fill=tk.X, expand=True, padx=20, pady=5)

    def process_option(self, choice):
        self.selector_window.withdraw()
        if choice == 1:
            app = VideoProcessorApp(self.parent, choice)
            app.show_dialogs_with_image_selection()
        elif choice == 2:
            app = VideoProcessorApp(self.parent, choice)
            app.show_dialogs()

    def cancel_option_selector(self):
        self.selector_window.destroy()

class VideoProcessorApp:
    def __init__(self, root, user_choice):
        self.root = root
        self.user_choice = user_choice
        self.root.title('Video Processing App')
        self.root.geometry('300x100')
        self.root.deiconify()

        self.status_var = tk.StringVar()
        self.status_label = tk.Label(root, textvariable=self.status_var)
        self.status_label.pack(fill=tk.X, expand=True, padx=20, pady=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, expand=True, padx=20, pady=5)

        self.cancel_button = ttk.Button(root, text="Cancel", command=self.cancel_processing)
        self.cancel_button.pack(fill=tk.X, expand=True, padx=20, pady=5)

        self.cancel_event = threading.Event()

    def show_dialogs_with_image_selection(self):
        video_path = select_file('Select a video file', [('Video files', '*.mp4 *.mkv *.avi *.mov *.flv')])
        image_path = None

        if messagebox.askyesno("Image Selection", "Do you want to select an image file?"):
            image_path = select_file('Select an image file', [('Image files', '*.jpg *.jpeg *.png *.gif')])

        if video_path and validate_file_extension(video_path, ['.mp4', '.mkv', '.avi', '.mov', '.flv']):
            if image_path is None or validate_file_extension(image_path, ['.jpg', '.jpeg', '.png', '.gif']):
                self.process_video_shorten(video_path, image_path)
            else:
                messagebox.showerror('Error', 'Unsupported image file format.')
        else:
            messagebox.showerror('Error', 'Unsupported video file format or no video file was selected.')

    def show_dialogs(self):
        video_path = select_file('Select a video file', [('Video files', '*.mp4 *.mkv *.avi *.mov *.flv')])
        if video_path and validate_file_extension(video_path, ['.mp4', '.mkv', '.avi', '.mov', '.flv']):
            if self.user_choice == 1:
                self.process_video_shorten(video_path)
            elif self.user_choice == 2:
                self.process_video_to_webp(video_path)
        else:
            messagebox.showerror('Error', 'Unsupported video file format or no file was selected.')

    def cancel_processing(self):
        self.cancel_event.set()
        self.status_var.set('Processing cancelled.')
        self.cancel_button.config(state=tk.DISABLED)
        self.root.destroy()

    def show_dialogs_with_image_selection(self):
        video_path = select_file('Select a video file', [('Video files', '*.mp4 *.mkv *.avi *.mov *.flv')])
        
        image_path = select_file('Select an image file (optional)', [('Image files', '*.jpg *.jpeg *.png *.gif')])

        if video_path and validate_file_extension(video_path, ['.mp4', '.mkv', '.avi', '.mov', '.flv']):
            if not image_path or validate_file_extension(image_path, ['.jpg', '.jpeg', '.png', '.gif']):
                self.process_video_shorten(video_path, image_path)
            else:
                messagebox.showerror('Error', 'Unsupported image file format.')
        else:
            messagebox.showerror('Error', 'Unsupported video file format or no video file was selected.')

    def process_video_shorten(self, video_path, image_path=None):
        if image_path:
            pass
        threading.Thread(target=self._process_video_shorten_thread, args=(video_path,)).start()

    def process_video_to_webp(self, video_path):
        self.cancel_event.clear()
        threading.Thread(target=self._process_video_to_webp_thread, args=(video_path,)).start()

    def _process_video_shorten_thread(self, video_path):
        adjusted_filename = os.path.splitext(video_path)[0] + '_shortened.mp4'
        try:
            clip = VideoFileClip(video_path)

            video_duration = clip.duration
            if video_duration > 139.98:
                speedup_factor = video_duration / 139.98
                adjusted_clip = clip.fx(vfx.speedx, speedup_factor)

                logger = self.setup_logger()
                self.write_video_file(adjusted_clip, adjusted_filename, logger)
            else:
                self.root.after(0, lambda: messagebox.showinfo('Info', 'No processing was needed.'))
            self.root.after(0, self.finish_processing)

        except Exception as e:
            self.handle_video_processing_error(e, adjusted_filename)

        finally:
            self.cleanup_resources(clip, None)

    def _process_video_to_webp_thread(self, video_path):
        try:
            clip = VideoFileClip(video_path)
            frames = [Image.fromarray(frame) for frame in clip.iter_frames()]

            total_frames = len(frames)
            webp_output_path = os.path.splitext(video_path)[0] + '.webp'

            self.status_var.set('Converting video to WebP...')
            for i in range(total_frames):
                if self.cancel_event.is_set():
                    self.root.after(0, lambda i=i: self.update_progress(i, total_frames))
                    return
                progress = (i + 1) / total_frames * 100
                self.progress_var.set(progress)
                self.status_var.set(f'Converting video to WebP: {progress:.2f}%')

            if not self.cancel_event.is_set():
                frames[0].save(webp_output_path, save_all=True, append_images=frames[1:], loop=0, duration=int(1000 / clip.fps), format='webp')
                self.root.after(0, lambda: messagebox.showinfo('Info', f'Video converted to WebP: {webp_output_path}'))
                self.root.after(0, self.finish_processing)

        except Exception as e:
            self.handle_video_processing_error(e, webp_output_path)
        finally:
            self.cleanup_resources(clip, None)

    def update_progress(self, current_frame, total_frames):
        progress = (current_frame + 1) / total_frames * 100
        self.progress_var.set(progress)
        self.status_var.set(f'Converting video to WebP: {progress:.2f}%')

    def cancel_processing(self):
        self.cancel_event.set()
        self.status_var.set('Processing cancelled.')
        self.cancel_button.config(state=tk.DISABLED)
        self.root.destroy()

    def setup_logger(self):
        return TkProgressBarLogger(self.progress_var, 100, self.status_var, self.cancel_event)

    def write_video_file(self, clip, filename, logger):
        try:
            video_bitrate = '1400k'
            audio_bitrate = '128k'
            frames_per_second = 24
            ffmpeg_params = ['-c:v', 'h264_nvenc', '-preset', 'fast']
            clip.write_videofile(filename, fps=frames_per_second, bitrate=video_bitrate, audio_bitrate=audio_bitrate, logger=logger, ffmpeg_params=ffmpeg_params)
        except Exception as e:
            print(f"Failed to write video file: {e}")
            raise

    def handle_video_processing_error(self, error, filename):
        error_message = str(error)
        self.root.after(0, lambda: messagebox.showerror('Error', error_message, master=self.root))
        self.attempt_cleanup_incomplete_file(filename)
        self.root.after(0, self.safe_destroy)

    def finish_processing(self):
        self.show_notification("Video Processing Completed", "Your video has been processed successfully.")
        self.safe_destroy()

    def show_notification(self, title, message):
        notification.notify(
            title=title,
            message=message,
            app_name='Video Processing App',
            timeout=10
        )

    def safe_destroy(self):
        self.root.destroy()

    def attempt_cleanup_incomplete_file(self, filename):
        if os.path.exists(filename):
            try:
                os.remove(filename)
                self.root.after(0, lambda: messagebox.showinfo('Info', 'Cancelled and cleaned up incomplete video file.'))
            except Exception as e:
                error_message = f'Failed to delete incomplete video file: {e}'
                self.root.after(0, lambda: messagebox.showerror('Error', error_message))
        else:
            self.root.after(0, lambda: messagebox.showinfo('Info', 'No incomplete file found to delete.'))

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
    root.title('Main Application')
    root.geometry('300x100')
    root.withdraw()

    OptionSelector(root)

    root.mainloop()
