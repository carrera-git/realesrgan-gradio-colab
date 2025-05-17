import gradio as gr
import os
import shutil
import subprocess
from datetime import datetime

# 자동 번호 파일
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

def upscale_video(input_video, width, height, aspect_mode):
    os.makedirs("input", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("enhanced", exist_ok=True)

    input_path = "input/input.mp4"
    enhanced_path = "enhanced/enhanced.mp4"
    output_name = get_next_filename()
    output_path = os.path.join("output", output_name)

    # 파일 복사
    shutil.copy(input_video, input_path)

    # 간이 화질 보정 (sharpen + denoise 흉내)
    subprocess.call([
        "ffmpeg", "-i", input_path,
        "-vf", "unsharp=5:5:1.0:5:5:0.0,hqdn3d",  # sharpen + denoise
        "-c:v", "libx264", "-preset", "fast", enhanced_path
    ])

    # 아스팩트 처리 필터 구성
    if aspect_mode == "pad":
        vf_filter = f"scale='min({width},iw*{height}/ih)':'min({height},ih*{width}/iw)':force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
    elif aspect_mode == "crop":
        vf_filter = f"scale='if(gt(a,{width}/{height}),{width},-1)':'if(gt(a,{width}/{height}),-1,{height})',crop={width}:{height}"
    elif aspect_mode == "blurred-fill":
        vf_filter = f"scale='min({width},iw*{height}/ih)':'min({height},ih*{width}/iw)':force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,boxblur=10:1"
    else:
        vf_filter = f"scale={width}:{height}"

    # 최종 출력
    subprocess.call([
        "ffmpeg", "-i", enhanced_path,
        "-vf", vf_filter,
        "-c:v", "libx264", "-preset", "fast", output_path
    ])

    return output_path

demo = gr.Interface(
    fn=upscale_video,
    inputs=[
        gr.File(label="Input Video (mp4)", file_types=[".mp4"]),
        gr.Number(label="Output Width (e.g., 1920)"),
        gr.Number(label="Output Height (e.g., 1080)"),
        gr.Radio(["pad", "crop", "blurred-fill"], label="Aspect Ratio Mode")
    ],
    outputs=gr.Video(label="Final Enhanced Video"),
    title="AI Video Enhancer + Aspect Ratio Handler",
    allow_flagging="never"
)

demo.launch(share=True)
