# /content/realesrgan-gradio-colab/inference_realesrgan.py
import os
import cv2
import torch
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

model_path = 'weights/RealESRGAN_x4plus.pth'
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# 업스케일러 로드
model = RRDBNet(num_in_ch=3, num_out_ch=3, nf=64, nb=23, gc=32, scale=4)
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

# 프레임 업스케일링
input_dir = 'frames_in'
output_dir = 'frames_out'
os.makedirs(output_dir, exist_ok=True)

for fname in sorted(os.listdir(input_dir)):
    if fname.endswith('.png'):
        img_path = os.path.join(input_dir, fname)
        img = cv2.imread(img_path, cv2.IMREAD_COLOR)
        output, _ = upsampler.enhance(img, outscale=4)
        out_path = os.path.join(output_dir, fname.replace('.png', '_out.png'))
        cv2.imwrite(out_path, output)
