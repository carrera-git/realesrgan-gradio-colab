# /content/realesrgan-gradio-colab/inference_realesrgan.py
import os
import cv2
import torch
from realesrgan import RealESRGANer
from basicsr.archs.rrdbnet_arch import RRDBNet

# 모델 경로
model_path = 'weights/RealESRGAN_x4plus.pth'

# 디바이스 설정
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 최신 버전 기준 RRDBNet 파라미터명으로 수정
model = RRDBNet(
    num_in_ch=3,
    num_out_ch=3,
    num_feat=64,
    num_block=23,
    num_grow_ch=32
)

# 업샘플러 구성
upsampler = RealESRGANer(
    scale=4,
    model_path=model_path,
    model=model,
    tile=0,
    tile_pad=10,
    pre_pad=0,
    half=False,
    device=device
)

# 프레임 폴더 설정
input_dir = 'frames_in'
output_dir = 'frames_out'
os.makedirs(output_dir, exist_ok=True)

# 프레임 순회하며 업스케일
for fname in sorted(os.listdir(input_dir)):
    if fname.endswith('.png'):
        img_path = os.path.join(input_dir, fname)
        img = cv2.imread(img_path, cv2.IMREAD_COLOR)
        if img is None:
            print(f"❌ 이미지 로드 실패: {img_path}")
            continue
        try:
            output, _ = upsampler.enhance(img, outscale=4)
            out_path = os.path.join(output_dir, fname.replace('.png', '_out.png'))
            cv2.imwrite(out_path, output)
        except Exception as e:
            print(f"⚠️ 처리 중 에러: {fname} → {e}")
