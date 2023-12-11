import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
import threading
import datetime
import os
import logging
import subprocess
import re

CREATE_NO_WINDOW = 0x08000000

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

VIDEO_FILE_TYPES = [("Video files", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv *.mpeg *.mpg *.webm *.ogg")]
IMAGE_FILE_TYPES = [("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tif *.tiff *.webp")]

def select_file(file_types):
    return filedialog.askopenfilename(filetypes=file_types)

def get_current_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d%H%M%S")

def execute_ffmpeg_command(cmd):
    try:
        result = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, universal_newlines=True, creationflags=CREATE_NO_WINDOW)
        return result.stderr
    except Exception as e:
        logging.error("FFmpeg command execution failed: %s", e)
        return None

def get_video_duration(video_path):
    stderr = execute_ffmpeg_command(['ffmpeg', '-i', video_path])
    if stderr:
        match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})', stderr)
        if match:
            hours, minutes, seconds = match.groups()
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    return None

def update_ffmpeg_progress(process, progress_var, status_var, total_duration, current_task, root, cancel_event):
    for line in iter(process.stdout.readline, ""):
        if cancel_event.is_set():
            process.terminate()
            break

        match = re.search(r'time=(\d{2}):(\d{2}):(\d{2})', line)
        if match:
            hours, minutes, seconds = map(int, match.groups())
            elapsed_time = hours * 3600 + minutes * 60 + seconds
            progress = (elapsed_time / total_duration) * 100
            root.after(0, lambda: update_progress(progress_var, status_var, progress, current_task))

    process.stdout.close()
    process.wait()
    root.after(0, lambda: update_progress(progress_var, status_var, 100, current_task))

def run_ffmpeg_command(cmd, progress_var, status_var, root, cancel_event, total_duration, current_task):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1, creationflags=CREATE_NO_WINDOW)

    for line in iter(process.stdout.readline, ""):
        if cancel_event.is_set():
            process.terminate()
            break

        match = re.search(r'time=(\d{2}):(\d{2}):(\d{2})', line)
        if match:
            hours, minutes, seconds = map(int, match.groups())
            elapsed_time = hours * 3600 + minutes * 60 + seconds
            progress = (elapsed_time / total_duration) * 100
            root.after(0, lambda: update_progress(progress_var, status_var, progress, current_task))

    process.stdout.close()
    process.wait()
    root.after(0, lambda: update_progress(progress_var, status_var, 100, current_task))

def update_progress(progress_var, status_var, progress, current_task):
    progress_var.set(progress)
    status_var.set(f"Progress of {current_task}: {progress:.2f}%")

def adjust_video_speed(video_path, target_duration, progress_var, status_var, root, cancel_event):
    current_task = "Adjusting video speed"
    status_var.set(f"{current_task} in progress...")
    duration = get_video_duration(video_path)
    if duration is None:
        return False, video_path

    file_name, file_extension = os.path.splitext(video_path)
    output_path = f"{file_name}_{get_current_timestamp()}.mp4"

    if duration > target_duration:
        speed_factor = duration / target_duration
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-filter:v', f"setpts={1/speed_factor}*PTS",
            '-filter:a', f"atempo={speed_factor}" if 0.5 <= speed_factor <= 2 else f"atempo=2,atempo={speed_factor / 2}",
            output_path
        ]
        run_ffmpeg_command(cmd, progress_var, status_var, root, cancel_event, duration, current_task)
        return True, output_path
    else:
        return False, video_path

def resize_image(image_path, video_path, status_var):
    current_task = "Resizing image"
    status_var.set(f"{current_task} in progress...")
    try:
        process = subprocess.Popen(['ffmpeg', '-i', video_path], stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, universal_newlines=True)
        stdout, stderr = process.communicate()
        match = re.search(r'Stream.*Video.* (\d+)x(\d+)', stderr)
        if match:
            width, height = map(int, match.groups())
            file_name, file_extension = os.path.splitext(image_path)
            output_image_path = f"{file_name}_{get_current_timestamp()}{file_extension}"

            with Image.open(image_path) as img:
                img = img.resize((width, height))
                img.save(output_image_path)

            return output_image_path
    except Exception as e:
        logging.error("Error in resizing image: %s", e)
    return image_path

def insert_image_to_video(video_path, image_path, progress_var, status_var, root, cancel_event):
    current_task = "Inserting image"
    status_var.set(f"{current_task} in progress...")
    video_duration = get_video_duration(video_path)
    if video_duration is None:
        return None

    file_name, file_extension = os.path.splitext(video_path)
    output_video_path = f"{file_name}_{get_current_timestamp()}{file_extension}"

    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-i', image_path,
        '-filter_complex', "overlay=enable='eq(n,0)'",
        output_video_path
    ]
    run_ffmpeg_command(cmd, progress_var, status_var, root, cancel_event, video_duration, current_task)
    return output_video_path

def compress_video(input_video_path, progress_var, status_var, root, cancel_event):
    current_task = "Compressing video"
    status_var.set(f"{current_task} in progress...")
    video_duration = get_video_duration(input_video_path)
    if video_duration is None:
        return input_video_path

    file_name, file_extension = os.path.splitext(input_video_path)
    output_video_path = f"{file_name}_compressed_{get_current_timestamp()}{file_extension}"

    cmd = [
        'ffmpeg',
        '-i', input_video_path,
        '-vcodec', 'libx265',
        '-crf', '23',
        output_video_path
    ]
    run_ffmpeg_command(cmd, progress_var, status_var, root, cancel_event, video_duration, current_task)
    return output_video_path

def process_video(video_path, image_path, progress_var, status_var, cancel_event, root):
    video_path_1 = video_path_2 = video_path_3 = image_path_1 = None
    temp_files = []

    try:
        target_duration = 139
        adjusted, video_path_1 = adjust_video_speed(video_path, target_duration, progress_var, status_var, root, cancel_event)
        if cancel_event.is_set(): return
        if adjusted and video_path_1 != video_path:
            temp_files.append(video_path_1)

        if image_path:
            image_path_1 = resize_image(image_path, video_path_1, status_var)
            if cancel_event.is_set(): return
            if image_path_1 != image_path:
                temp_files.append(image_path_1)

            video_path_2 = insert_image_to_video(video_path_1, image_path_1, progress_var, status_var, root, cancel_event)
            if cancel_event.is_set(): return
            if video_path_2 != video_path_1:
                temp_files.append(video_path_2)
        else:
            video_path_2 = video_path_1

        video_path_3 = compress_video(video_path_2, progress_var, status_var, root, cancel_event)
        if cancel_event.is_set(): return
        if video_path_3 != video_path_2:
            temp_files.append(video_path_3)

        if cancel_event.is_set():
            messagebox.showinfo("Cancelled", "Process was cancelled")
            return

        messagebox.showinfo("Completed", f"Video processing completed. Output saved to {video_path_3}")
    except Exception as e:
        logging.error("Exception occurred: %s", e)
        messagebox.showerror("Error", str(e))
    finally:
        for file in temp_files:
            if file and os.path.exists(file) and file != video_path_3:
                os.remove(file)

        root.quit()

def start_processing(video_path, image_path, progress_var, status_var, cancel_event, root):
    if video_path:
        processing_thread = threading.Thread(target=process_video, args=(video_path, image_path, progress_var, status_var, cancel_event, root))
        processing_thread.start()
    else:
        messagebox.showinfo("Cancelled", "Process cancelled by user")
        root.quit()

def main():
    root = tk.Tk()
    root.title("Shorten Video To 140s")
    root.geometry("400x100")

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

    video_path = select_file(VIDEO_FILE_TYPES)
    if not video_path:
        messagebox.showinfo("Cancelled", "No video file selected")
        root.quit()
        return

    image_path = select_file(IMAGE_FILE_TYPES)

    processing_thread = threading.Thread(target=start_processing, args=(video_path, image_path, progress_var, status_var, cancel_event, root))
    processing_thread.daemon = True
    processing_thread.start()

    root.mainloop()

    processing_thread.join()
    root.destroy()

if __name__ == "__main__":
    main()
