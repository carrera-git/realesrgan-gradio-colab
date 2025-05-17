import gradio as gr
import os
import subprocess

def upscale_video(input_video, scale):
    os.makedirs("input", exist_ok=True)
    os.makedirs("output", exist_ok=True)
import shutil

input_path = "input/input.mp4"
shutil.copy(input_video.name, input_path)


    # 영상 저장
    input_video.save(input_path)

    # Real-ESRGAN 대신 ffmpeg 업스케일 시뮬레이션
    subprocess.call([
        "ffmpeg", "-i", input_path,
        "-vf", f"scale=iw*{scale}:ih*{scale}",
        "-c:v", "libx264", "-preset", "fast", output_path
    ])

    return output_path

demo = gr.Interface(
    fn=upscale_video,
    inputs=[
        gr.File(label="Input Video (mp4)"),
        gr.Slider(1, 4, value=2, step=1, label="Upscale Factor")
    ],
    outputs=gr.Video(label="Upscaled Video"),
    title="Real-ESRGAN Style Video Upscaler"
)

demo.launch(share=True)
