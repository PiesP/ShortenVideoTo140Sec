import subprocess
import datetime
import os
import re
import logging
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import threading
import tempfile

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_ffmpeg_command(command):
    try:
        return subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, encoding='utf-8')
    except FileNotFoundError:
        return None

def is_ffmpeg_installed():
    return run_ffmpeg_command(['ffmpeg', '-version']) is not None

def is_ffmpeg_encoder_available(encoder_name):
    result = run_ffmpeg_command(['ffmpeg', '-encoders'])
    return result is not None and encoder_name in result.stdout

def get_video_duration(video_path):
    if not os.path.exists(video_path):
        logging.error("Video file does not exist: %s", video_path)
        return None

    result = run_ffmpeg_command(['ffmpeg', '-i', video_path])
    if result and result.stderr:
        match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})', result.stderr)
        if match:
            hours, minutes, seconds = match.groups()
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    return None

def get_video_resolution(video_path):
    result = run_ffmpeg_command(['ffmpeg', '-i', video_path])
    if result and result.stderr:
        match = re.search(r'Stream #.*: Video:.* (\d{3,4})x(\d{3,4})', result.stderr)
        if match:
            return match.groups()
    return None, None

def create_image_video(image_path, resolution, temp_dir, progress_var, encoder):
    width, height = resolution
    temp_video_path = os.path.join(temp_dir, "temp_image_video.mp4")
    cmd = [
        'ffmpeg', '-loop', '1', '-i', image_path, 
        '-f', 'lavfi', '-i', 'anullsrc',
        '-c:v', encoder, '-t', '0.1', '-s', f'{width}x{height}', 
        '-c:a', 'aac', '-shortest',
        '-pix_fmt', 'yuv420p', temp_video_path
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    progress_var.set(33)
    return temp_video_path

def add_image_video_to_beginning(image_video_path, video_path, temp_dir, progress_var, encoder):
    temp_combined_video_path = os.path.join(temp_dir, "temp_combined_video.mp4")
    cmd = [
        'ffmpeg', '-i', image_video_path, '-i', video_path, 
        '-filter_complex',
        '[0:v][0:a][1:v][1:a] concat=n=2:v=1:a=1 [v][a]',
        '-c:v', encoder, '-map', '[v]', '-map', '[a]', 
        temp_combined_video_path
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    progress_var.set(66)
    return temp_combined_video_path

def safe_tkinter_update(root, func, *args, **kwargs):
    root.after(0, lambda: func(*args, **kwargs))

def update_ffmpeg_progress(process, progress_var, status_var, current_task, root, cancel_event, total_duration):
    try:
        while True:
            line = process.stdout.readline()
            if not line:
                break

            if 'time=' in line:
                time_match = re.search(r'time=(\d{2}):(\d{2}):(\d{2}\.\d{2})', line)
                if time_match:
                    hours, minutes, seconds = map(int, time_match.groups())
                    elapsed_time = hours * 3600 + minutes * 60 + seconds
                    progress = (elapsed_time / total_duration) * 34 + 66
                    safe_tkinter_update(root, update_progress, progress_var, status_var, min(max(progress, 66), 100), current_task)

            if cancel_event.is_set():
                process.terminate()
                break

    finally:
        process.stdout.close()
        process.wait()
        safe_tkinter_update(root, update_progress, progress_var, status_var, 100, current_task)

def update_progress(progress_var, status_var, progress, current_task):
    progress_var.set(progress)
    status_var.set(f"Progress of {current_task}: {progress:.2f}%")

def has_audio_stream(video_path):
    result = run_ffmpeg_command(['ffmpeg', '-i', video_path])
    if result and result.stderr:
        return 'Audio: ' in result.stderr
    return False

def prepare_ffmpeg_command(video_path, original_video_path, encoder, target_duration):
    duration = get_video_duration(video_path)
    if duration is None:
        raise Exception("Unable to get video duration")

    file_name_without_ext = os.path.splitext(os.path.basename(original_video_path))[0]
    output_video_name = f"{file_name_without_ext}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
    output_video_path = os.path.join(os.path.dirname(original_video_path), output_video_name).replace('\\', '/')

    cmd = ['ffmpeg', '-i', video_path]

    video_filters = []
    video_filters.append('scale=1280:720:force_original_aspect_ratio=decrease')

    if duration > target_duration:
        speed_factor = duration / target_duration
        setpts_filter = f"setpts={1/speed_factor}*PTS"
        atempo_filter = "atempo=1.0"
        while speed_factor > 2.0:
            atempo_filter += ",atempo=2.0"
            speed_factor /= 2.0
        if speed_factor > 1.0:
            atempo_filter += f",atempo={speed_factor}"

        video_filters.append(setpts_filter)
        audio_filter = atempo_filter

        cmd.extend(['-filter_complex', f"[0:v]{','.join(video_filters)}[v];[0:a]{audio_filter}[a]", '-map', '[v]', '-map', '[a]'])
    else:
        cmd.extend(['-vf', ','.join(video_filters)])

    cmd.extend(['-c:v', encoder, '-movflags', 'faststart', '-y', output_video_path])
    return cmd, output_video_path

def process_video_ffmpeg(video_path, original_video_path, progress_var, status_var, root, cancel_event, encoder, target_duration):
    current_task = "Processing video"
    status_var.set(f"{current_task} in progress...")

    try:
        cmd, output_video_path = prepare_ffmpeg_command(video_path, original_video_path, encoder, target_duration)
        with tempfile.NamedTemporaryFile(delete=False) as temp_progress_file:
            cmd.extend(['-progress', temp_progress_file.name])

        logging.info("Executing FFmpeg command: %s", ' '.join(cmd))
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, encoding='utf-8', bufsize=1, creationflags=subprocess.CREATE_NO_WINDOW)
        
        progress_thread = threading.Thread(target=update_ffmpeg_progress, args=(process, progress_var, status_var, current_task, root, cancel_event, target_duration))
        progress_thread.start()
        stdout, stderr = process.communicate()
        progress_thread.join()

        exit_code = process.returncode
        if exit_code != 0:
            logging.error("FFmpeg process failed with exit code %d", exit_code)
            logging.error("FFmpeg command: %s", ' '.join(cmd))
            logging.error("FFmpeg output: %s", stderr.strip())
            raise Exception(f"FFmpeg process failed with exit code {exit_code}")

        if not os.path.exists(output_video_path):
            raise Exception("Output video file not found after processing")

        progress_var.set(100)  # Update progress to 3/3
        return output_video_path
    except subprocess.CalledProcessError as e:
        logging.error("FFmpeg process error: %s", str(e))
        messagebox.showerror("Processing Error", f"FFmpeg process error: {e}")
        return None
    except Exception as e:
        logging.error("Exception occurred during video processing: %s", e)
        messagebox.showerror("Processing Error", f"An error occurred during video processing: {e}")
        return None

def process_video(video_path, image_path, progress_var, status_var, cancel_event, root, encoder, on_processing_finished):
    try:
        resolution = get_video_resolution(video_path)
        if resolution == (None, None):
            raise Exception("Unable to get video resolution")

        with tempfile.TemporaryDirectory() as temp_dir:
            image_video_path = create_image_video(image_path, resolution, temp_dir, progress_var, encoder)
            combined_video_path = add_image_video_to_beginning(image_video_path, video_path, temp_dir, progress_var, encoder)

            target_duration = 139.9
            output_video_path = process_video_ffmpeg(combined_video_path, video_path, progress_var, status_var, root, cancel_event, encoder, target_duration)

        if cancel_event.is_set():
            messagebox.showinfo("Cancelled", "Process was cancelled")
            return

        if not output_video_path:
            raise Exception("Video processing returned no output path")

        messagebox.showinfo("Completed", f"Video processing completed. Output saved to {output_video_path}")
        on_processing_finished()
    except Exception as e:
        logging.error("Exception occurred during video processing: %s", e)
        messagebox.showerror("Processing Error", f"An error occurred during video processing: {e}")
