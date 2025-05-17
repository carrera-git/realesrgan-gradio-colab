# ⚠️ 이 코드는 Google Colab 전용입니다
# 1. Real-ESRGAN 설치 및 모델 다운로드
# 2. 영상 프레임 추출 → 프레임별 AI 업스케일 → 영상 재조합
# 3. 결과물 crop/pad 처리 후 출력

import gradio as gr
import os
import shutil
import subprocess
import cv2
import math

# 초기 디렉토리 구성
for folder in ["input", "work", "frames_in", "frames_out", "output"]:
    os.makedirs(folder, exist_ok=True)

# 파일명 카운터 관리
counter_file = "counter.txt"
if not os.path.exists(counter_file):
    with open(counter_file, "w") as f:
        f.write("0")

def get_next_filename():
    with open(counter_file, "r+") as f:
        count = int(f.read().strip()) + 1
        f.seek(0)
        f.write(str(count))
        f.truncate()
    return f"output_{count:03d}.mp4"

def get_video_resolution(path):
    cap = cv2.VideoCapture(path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return width, height

def run_realesrgan_on_frames():
    # 프레임 단위 이미지들을 AI 업스케일
    subprocess.call([
        "python", "inference_realesrgan.py",
        "-n", "RealESRGAN_x4plus",
        "-i", "frames_in",
        "-o", "frames_out",
        "--outscale", "4"
    ])

def extract_frames(video_path):
    subprocess.call([
        "ffmpeg", "-y", "-i", video_path,
        "frames_in/frame_%05d.png"
    ])

def reassemble_video(output_path, fps=30):
    subprocess.call([
        "ffmpeg", "-y", "-framerate", str(fps),
        "-i", "frames_out/frame_%05d_out.png",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", output_path
    ])

def upscale_video(input_video, width, height, aspect_mode):
    input_path = "input/input.mp4"
    enhanced_path = "work/enhanced.mp4"
    output_name = get_next_filename()
    output_path = f"output/{output_name}"

    shutil.copy(input_video, input_path)

    original_w, original_h = get_video_resolution(input_path)

    # 1단계: 프레임 추출 → Real-ESRGAN 처리 → 영상 재조립
    extract_frames(input_path)
    run_realesrgan_on_frames()
    reassemble_video(enhanced_path)

    input_aspect = original_w / original_h
    target_aspect = width / height

    if aspect_mode == "pad":
        vf_filter = f"scale=w='min({width},iw*{height}/ih)':h='min({height},ih*{width}/iw)':force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
    elif aspect_mode == "crop":
        if input_aspect > target_aspect:
            intermediate_h = height
            intermediate_w = math.ceil(height * input_aspect)
        else:
            intermediate_w = width
            intermediate_h = math.ceil(width / input_aspect)
        x_offset = f"(in_w-{width})/2"
        y_offset = f"(in_h-{height})/2"
        vf_filter = f"scale={intermediate_w}:{intermediate_h},crop={width}:{height}:{x_offset}:{y_offset}"
    elif aspect_mode == "blurred-fill":
        vf_filter = f"split[main][bg];[bg]scale={width}:{height},boxblur=20[blurred];[main]scale='min({width},iw*{height}/ih)':'min({height},ih*{width}/iw)':force_original_aspect_ratio=decrease[scaled];[blurred][scaled]overlay=(W-w)/2:(H-h)/2"
    else:
        vf_filter = f"scale={width}:{height}"

    subprocess.call([
        "ffmpeg", "-y", "-i", enhanced_path,
        "-vf", vf_filter,
        "-c:v", "libx264", "-preset", "fast", output_path
    ])

    info = f"📏 원본 해상도: {original_w}x{original_h}\n🎨 Real-ESRGAN 적용 완료"
    return info, input_path, output_path

demo = gr.Interface(
    fn=upscale_video,
    inputs=[
        gr.File(label="Input Video (mp4)", file_types=[".mp4"]),
        gr.Number(label="Output Width (예: 1920)"),
        gr.Number(label="Output Height (예: 1080)"),
        gr.Radio(["pad", "crop", "blurred-fill"], label="Aspect Ratio Mode")
    ],
    outputs=[
        gr.Textbox(label="처리 정보"),
        gr.Video(label="📥 원본 프리뷰"),
        gr.Video(label="📤 결과 영상")
    ],
    title="🎞 Real-ESRGAN + Crop/Pad 완전체 (Colab 전용)",
    allow_flagging="never"
)

demo.launch(share=True)
