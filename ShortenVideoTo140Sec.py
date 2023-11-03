import subprocess
import sys

def install_package(package_name):
    """
    주어진 패키지 이름으로 pip를 사용하여 패키지를 설치합니다.
    """
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package_name])

def validate_file_extension(file_path, valid_extensions):
    """
    주어진 파일 경로의 확장자가 유효한 확장자 목록에 포함되어 있는지 확인합니다.
    """
    _, ext = os.path.splitext(file_path)
    return ext.lower() in valid_extensions

# 필요한 패키지들을 설치합니다.
# install_package('moviepy')
# install_package('tk')

from tkinter import Tk, filedialog
from moviepy.editor import VideoFileClip, vfx, ImageClip, concatenate_videoclips
import os

def select_file(title, filetypes):
    """
    파일 선택 대화상자를 표시하고 선택된 파일의 경로를 반환합니다.
    """
    root = Tk()
    root.withdraw()  # GUI 창을 숨깁니다.
    file_path = filedialog.askopenfilename(title=title, filetypes=filetypes)
    root.destroy()  
    return file_path

# 사용자에게 동영상 파일의 경로를 선택하게 합니다.
video_path = select_file('동영상 파일을 선택하세요', [('동영상 파일', '*.mp4;*.mkv;*.avi;*.mov;*.flv')])

# 동영상 파일의 확장자 검증
valid_video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.flv']
if not validate_file_extension(video_path, valid_video_extensions):
    raise ValueError('지원하지 않는 동영상 파일 형식입니다.')

# 사용자에게 이미지 파일의 경로를 선택하게 합니다. (옵션)
image_path = select_file('삽입할 이미지 파일을 선택하세요 (취소하면 이미지 없이 진행)', [('이미지 파일', '*.jpg;*.jpeg;*.png;*.bmp;*.gif')])

# 이미지 파일의 확장자 검증
if image_path:
    valid_image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']
    if not validate_file_extension(image_path, valid_image_extensions):
        raise ValueError('지원하지 않는 이미지 파일 형식입니다.')

# 동영상을 로드합니다.
clip = VideoFileClip(video_path)

# 이미지 파일을 입력받았다면, 해당 이미지를 0.01초 동안 보여주는 클립을 생성하고, 동영상의 시작 부분에 연결합니다.
if image_path:
    image_clip = ImageClip(image_path).set_duration(0.01)
    clip = concatenate_videoclips([image_clip, clip])

# 동영상의 길이를 확인합니다.
video_duration = clip.duration

if video_duration > 139:
    # 적절한 재생 속도를 계산합니다.
    speedup_factor = video_duration / 139.98
    adjusted_clip = clip.fx(vfx.speedx, speedup_factor)

    # 조절된 동영상을 저장합니다.
    adjusted_filename = os.path.splitext(video_path)[0] + '_adjusted.mp4'
    adjusted_clip.write_videofile(adjusted_filename)
    clip.close()  # 비디오 클립을 닫습니다.
    if image_path:
        image_clip.close()  # 이미지 클립을 닫습니다.
    print(f'조절된 동영상이 {adjusted_filename}로 저장되었습니다.')
else:
    print('동영상의 길이가 이미 139초 이하입니다.')