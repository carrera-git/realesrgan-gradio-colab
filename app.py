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

def upscale_if_needed(input_path, target_width, target_height, out_path):
    original_w, original_h = get_video_resolution(input_path)
    if original_w >= target_width and original_h >= target_height:
        shutil.copy(input_path, out_path)
        return "✅ 원본 해상도가 충분해 업스케일 생략"
    else:
        subprocess.call([
            "ffmpeg", "-i", input_path,
            "-vf", f"scale={target_width}:{target_height}:flags=lanczos,unsharp=5:5:1.0:5:5:0.0,hqdn3d",
            "-c:v", "libx264", "-preset", "fast", out_path
        ])
        return f"🔼 업스케일 및 보정 적용: {original_w}x{original_h} → {target_width}x{target_height}"

def process_video(input_video, width, height, aspect_mode):
    os.makedirs("input", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    os.makedirs("work", exist_ok=True)

    input_path = "input/input.mp4"
    enhanced_path = "work/enhanced.mp4"
    output_name = get_next_filename()
    output_path = os.path.join("output", output_name)

    # 파일 복사
    shutil.copy(input_video, input_path)
    original_w, original_h = get_video_resolution(input_path)

    # 업스케일 + 화질 보정
    enhance_msg = upscale_if_needed(input_path, width, height, enhanced_path)

    # 후처리 필터
    if aspect_mode == "pad":
        vf_filter = f"scale='min({width},iw*{height}/ih)':'min({height},ih*{width}/iw)':force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
    elif aspect_mode == "crop":
        vf_filter = f"scale='if(gt(a,{width}/{height}),{width},-1)':'if(gt(a,{width}/{height}),-1,{height})',crop={width}:{height}"
    elif aspect_mode == "blurred-fill":
        vf_filter = f"scale='min({width},iw*{height}/ih)':'min({height},ih*{width}/iw)':force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,boxblur=10:1"
    else:
        vf_filter = f"scale={width}:{height}"

    # 최종 변환
    try:
        subprocess.run([
            "ffmpeg", "-i", enhanced_path,
            "-vf", vf_filter,
            "-c:v", "libx264", "-preset", "fast", output_path
        ], check=True)
    except subprocess.CalledProcessError:
        return f"⚠️ 처리 실패: 원본 해상도 또는 비율이 요청한 출력에 적합하지 않음", None, None

    # 해상도 텍스트 + 출력 파일 + 원본 프리뷰
    info = f"📏 원본 해상도: {original_w}x{original_h}\n{enhance_msg}"
    return info, input_path, output_path

demo = gr.Interface(
    fn=process_video,
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
    title="🎞 AI 영상 업스케일 + 비율 처리 + 화질 보정 + 자동 파일명",
    allow_flagging="never"
)

demo.launch(share=True)
