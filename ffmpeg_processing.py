import subprocess
import datetime
import os
import re
import logging
import tkinter as tk
from tkinter import messagebox

def is_ffmpeg_encoder_available(encoder_name):
    try:
        result = subprocess.run(['ffmpeg', '-encoders'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        if encoder_name in result.stdout:
            return True
        return False
    except Exception as e:
        logging.error("Error checking FFmpeg encoder availability: %s", e)
        return False

def get_video_duration(video_path):
    try:
        stderr = subprocess.run(['ffmpeg', '-i', video_path], stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, universal_newlines=True).stderr
        if stderr:
            match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2}\.\d{2})', stderr)
            if match:
                hours, minutes, seconds = match.groups()
                return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        return None
    except Exception as e:
        logging.error("Error getting video duration: %s", e)
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

def update_progress(progress_var, status_var, progress, current_task):
    progress_var.set(progress)
    if progress >= 100:
        status_var.set("Processing complete. Finalizing...")
    else:
        status_var.set(f"Progress of {current_task}: {progress:.2f}%")

def process_video_ffmpeg(video_path, image_path, target_duration, progress_var, status_var, root, cancel_event, encoder):
    current_task = "Processing video"
    status_var.set(f"{current_task} in progress...")

    try:
        duration = get_video_duration(video_path)
        if duration is None:
            raise Exception("Unable to get video duration")

        file_name_without_ext = os.path.splitext(os.path.basename(video_path))[0]
        output_video_name = f"{file_name_without_ext}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.mp4"
        output_video_path = os.path.join(os.path.dirname(video_path), output_video_name).replace('\\', '/')

        if duration <= target_duration:
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-i', image_path,
                '-c:v', encoder,
                '-movflags', 'faststart',
                '-y', output_video_path
            ]
        else:
            speed_factor = duration / target_duration
            setpts_filter = f"setpts={1/speed_factor}*PTS"
            atempo_filter = ""
            while speed_factor > 2.0:
                atempo_filter += "atempo=2.0,"
                speed_factor /= 2.0
            if speed_factor > 1.0:
                atempo_filter += f"atempo={speed_factor}"

            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-i', image_path,
                '-filter_complex', f"[0:v]{setpts_filter}[v];[0:a]{atempo_filter}[a]",
                '-map', '[v]',
                '-map', '[a]',
                '-movflags', 'faststart',
                '-c:v', encoder,
                '-t', str(target_duration),
                '-y', output_video_path
            ]

        print(cmd)
        logging.info("Executing FFmpeg command: %s", ' '.join(cmd))

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, bufsize=1, creationflags=subprocess.CREATE_NO_WINDOW)

        update_ffmpeg_progress(process, progress_var, status_var, duration, current_task, root, cancel_event)

        if process.returncode != 0:
            raise Exception(f"FFmpeg process failed with exit code {process.returncode}")

        if not os.path.exists(output_video_path):
            raise Exception("Output video file not found after processing")

        return output_video_path
    except Exception as e:
        logging.error("Exception occurred during video processing: %s", e)
        messagebox.showerror("Processing Error", f"An error occurred during video processing: {e}")
        return None

def process_video(video_path, image_path, progress_var, status_var, cancel_event, root, encoder, on_processing_finished):
    try:
        duration = get_video_duration(video_path)
        if duration is None:
            raise Exception("Unable to get video duration")

        target_duration = 139.99 if duration > 139.99 else duration
        output_video_path = process_video_ffmpeg(video_path, image_path, target_duration, progress_var, status_var, root, cancel_event, encoder)

        if cancel_event.is_set():
            messagebox.showinfo("Cancelled", "Process was cancelled")
            return None
        if not output_video_path:
            raise Exception("Video processing returned no output path")

        if not os.path.exists(output_video_path):
            raise Exception("Output video file not found after processing")

        messagebox.showinfo("Completed", f"Video processing completed. Output saved to {output_video_path}")
        on_processing_finished()
        return output_video_path
    except Exception as e:
        logging.error("Exception occurred during video processing: %s", e)
        messagebox.showerror("Processing Error", f"An error occurred during video processing: {e}")
