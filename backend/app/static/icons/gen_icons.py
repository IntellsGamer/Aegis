from PIL import Image, ImageDraw
import os

svg_path = os.path.join(os.path.dirname(__file__), "icon.svg")
out_dir = os.path.dirname(__file__)

# Rasterize the shield design directly (SVG -> PNG requires cairosvg; draw instead).
def draw_icon(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size
    # rounded rect bg
    d.rounded_rectangle([0, 0, s, s], radius=int(s * 0.22), fill=(15, 23, 42, 255))
    # shield
    def px(f): return int(s * f)
    d.polygon([(px(0.5), px(0.10)), (px(0.81), px(0.22)), (px(0.81), px(0.47)),
               (px(0.81), px(0.66)), (px(0.69), px(0.80)), (px(0.50), px(0.875)),
               (px(0.31), px(0.80)), (px(0.19), px(0.66)), (px(0.19), px(0.47))],
              fill=(6, 182, 212, 255))
    d.polygon([(px(0.50), px(0.22)), (px(0.70), px(0.30)), (px(0.70), px(0.47)),
               (px(0.70), px(0.61)), (px(0.62), px(0.72)), (px(0.50), px(0.78)),
               (px(0.38), px(0.72)), (px(0.30), px(0.61)), (px(0.30), px(0.47))],
              fill=(15, 23, 42, 255))
    # star
    d.polygon([(px(0.50), px(0.31)), (px(0.57), px(0.45)), (px(0.72), px(0.47)),
               (px(0.61), px(0.57)), (px(0.64), px(0.72)), (px(0.50), px(0.64)),
               (px(0.36), px(0.72)), (px(0.39), px(0.57)), (px(0.28), px(0.47)),
               (px(0.43), px(0.45))], fill=(34, 211, 238, 255))
    return img

for size in (192, 512):
    draw_icon(size).save(os.path.join(out_dir, f"icon-{size}.png"))
print("icons generated")
