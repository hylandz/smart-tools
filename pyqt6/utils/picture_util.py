from PIL import Image


def png_to_ico(png_path, ico_path, sizes=None):
    if sizes is None:
        sizes = [(32, 32), (64, 64), (128, 128), (256, 256)]

    im = Image.open(png_path)
    im.save(ico_path,format="ICO",sizes=sizes)


if __name__ == '__main__':
    png_p = r"E:\code\pyqt6-gui\jt808\assets\icons\notification.png"
    ico_p = r"E:\code\pyqt6-gui\jt808\assets\icons\notification.ico"
    try:
        png_to_ico(png_p, ico_p, sizes=[(32, 32)])
        print("转换成功")
    except Exception as e:
        print(str(e))
