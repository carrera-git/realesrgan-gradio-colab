import gradio as gr
import os
import shutil
import subprocess
import cv2

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

def upscale_video(input_video, width, height, aspect_mode):
    os.makedirs("input", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("enhanced", exist_ok=True)

    input_path = "input/input.mp4"
    enhanced_path = "enhanced/enhanced.mp4"
    output_name = get_next_filename()
    output_path = os.path.join("output", output_name)

    shutil.copy(input_video, input_path)

    original_w, original_h = get_video_resolution(input_path)

    # 프리뷰용 해상도 표시
    preview_msg = f"📏 원본 해상도: {original_w}x{original_h}"

    # AI 필터 흉내 (sharpen + denoise)
    subprocess.call([
        "ffmpeg", "-i", input_path,
        "-vf", "unsharp=5:5:1.0:5:5:0.0,hqdn3d",
        "-c:v", "libx264", "-preset", "fast", enhanced_path
    ])

    # 필터 조합
    if aspect_mode == "pad":
        vf_filter = f"scale='min({width},iw*{height}/ih)':'min({height},ih*{width}/iw)':force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
    elif aspect_mode == "crop":
        vf_filter = f"scale='if(gt(a,{width}/{height}),{width},-1)':'if(gt(a,{width}/{height}),-1,{height})',crop={width}:{height}"
    elif aspect_mode == "blurred-fill":
        vf_filter = f"scale='min({width},iw*{height}/ih)':'min({height},ih*{width}/iw)':force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,boxblur=10:1"
    else:
        vf_filter = f"scale={width}:{height}"

    # 최종 리사이즈 시도
    try:
        subprocess.run([
            "ffmpeg", "-i", enhanced_path,
            "-vf", vf_filter,
            "-c:v", "libx264", "-preset", "fast", output_path
        ], check=True)
    except subprocess.CalledProcessError:
        return "⚠️ 변환 실패! 요청된 해상도보다 원본이 작을 수 있어요.", None

    return preview_msg, output_path

demo = gr.Interface(
    fn=upscale_video,
    inputs=[
        gr.File(label="Input Video (mp4)", file_types=[".mp4"]),
        gr.Number(label="Output Width (예: 1920)"),
        gr.Number(label="Output Height (예: 1080)"),
        gr.Radio(["pad", "crop", "blurred-fill"], label="Aspect Ratio Mode")
    ],
    outputs=[
        gr.Textbox(label="Original Resolution"),
        gr.Video(label="Final Output")
    ],
    title="🎥 AI Video Enhancer + Aspect Ratio Options + Preview",
    allow_flagging="never"
)

demo.launch(share=True)
