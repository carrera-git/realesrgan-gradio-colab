import gradio as gr
import os
import shutil
import subprocess

def upscale_video(input_video, scale):
    os.makedirs("input", exist_ok=True)
    os.makedirs("output", exist_ok=True)

    input_path = "input/input.mp4"
    output_path = "output/output.mp4"

    # Gradio에서 받은 파일은 경로(str)로 전달됨
    shutil.copy(input_video, input_path)

    # 임시: ffmpeg로 업스케일 시뮬레이션
    subprocess.call([
        "ffmpeg", "-i", input_path,
        "-vf", f"scale=iw*{scale}:ih*{scale}",
        "-c:v", "libx264", "-preset", "fast", output_path
    ])

    return output_path

demo = gr.Interface(
    fn=upscale_video,
    inputs=[
        gr.File(label="Input Video (mp4)", file_types=[".mp4"]),
        gr.Slider(1, 4, value=2, step=1, label="Upscale Factor")
    ],
    outputs=gr.Video(label="Upscaled Video"),
    title="Real-ESRGAN Style Video Upscaler",
    allow_flagging="never"
)

demo.launch(share=True)
