import base64

def encode_image(image_file):
    """
    图片文件转Base64字符串
    """
    return base64.b64encode(image_file.read()).decode('utf-8')
