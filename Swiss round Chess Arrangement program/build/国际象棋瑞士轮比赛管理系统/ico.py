from PIL import Image

# 将 PNG 转换为 ICO
def png_to_ico(png_path, ico_path, sizes=[(16,16), (32,32), (48,48), (64,64)]):
    img = Image.open(png_path)
    # ICO 格式需要 RGBA 模式
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    img.save(ico_path, format='ICO', sizes=sizes)

# 使用
png_to_ico('icon.png', 'icon.ico')
