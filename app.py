import gradio as gr
import os
import shutil
import subprocess
import cv2
import math

for folder in ["input", "frames_in", "frames_out", "output", "weights"]:
    os.makedirs(folder, exist_ok=True)

def get_video_resolution(path):
    cap = cv2.VideoCapture(path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return width, height

def extract_frames(video_path):
    subprocess.call([
        "ffmpeg", "-y", "-i", video_path,
        "frames_in/frame_%05d.png"
    ])

def run_realesrgan():
    subprocess.call([
        "python", "inference_realesrgan.py",
        "-n", "RealESRGAN_x4plus",
        "-i", "frames_in",
        "-o", "frames_out",
        "--outscale", "4",
        "--model_path", "weights/RealESRGAN_x4plus.pth"
    ])

def reassemble_video(output_path, fps=30):
    subprocess.call([
        "ffmpeg", "-y", "-framerate", str(fps),
        "-i", "frames_out/frame_%05d_out.png",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", output_path
    ])

def upscale_and_format(input_video, width, height, aspect_mode):
    input_path = "input/input.mp4"
    output_path = "output/result.mp4"

    shutil.copy(input_video, input_path)
    original_w, original_h = get_video_resolution(input_path)

    extract_frames(input_path)
    run_realesrgan()
    reassemble_video("temp_upscaled.mp4")

    input_aspect = original_w / original_h
    target_aspect = width / height

    if aspect_mode == "pad":
        vf = f"scale=w='min({width},iw*{height}/ih)':h='min({height},ih*{width}/iw)':force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
    elif aspect_mode == "crop":
        if input_aspect > target_aspect:
            ih = height
            iw = math.ceil(height * input_aspect)
        else:
            iw = width
            ih = math.ceil(width / input_aspect)
        x = f"(in_w-{width})/2"
        y = f"(in_h-{height})/2"
        vf = f"scale={iw}:{ih},crop={width}:{height}:{x}:{y}"
    elif aspect_mode == "blurred-fill":
        vf = f"split[main][bg];[bg]scale={width}:{height},boxblur=20[blur];[main]scale='min({width},iw*{height}/ih)':'min({height},ih*{width}/iw)':force_original_aspect_ratio=decrease[scaled];[blur][scaled]overlay=(W-w)/2:(H-h)/2"
    else:
        vf = f"scale={width}:{height}"

    subprocess.call([
        "ffmpeg", "-y", "-i", "temp_upscaled.mp4",
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", output_path
    ])

    return f"{original_w}x{original_h} → {width}x{height}", input_path, output_path

demo = gr.Interface(
    fn=upscale_and_format,
    inputs=[
        gr.File(label="🎞 입력 영상(mp4)", file_types=[".mp4"]),
        gr.Number(label="📏 출력 가로", value=1080),
        gr.Number(label="📏 출력 세로", value=1920),
        gr.Radio(["pad", "crop", "blurred-fill"], label="비율 조정 방식", value="pad")
    ],
    outputs=[
        gr.Textbox(label="변환 정보"),
        gr.Video(label="원본"),
        gr.Video(label="결과")
    ],
    title="🔼 Real-ESRGAN 업스케일 + 비율 조정",
    allow_flagging="never"
)

demo.launch(share=True)
