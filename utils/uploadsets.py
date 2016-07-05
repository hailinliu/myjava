# !/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import uuid
from PIL import Image


def random_filename():
    """生成伪随机文件名"""
    return str(uuid.uuid4())


def open_image(file_storage):
    """打开图像"""
    image = Image.open(file_storage)
    print image
    # 此处是为了修复一个bug：cannot write mode P as JPEG
    # 解决方法来自：https://github.com/smileychris/easy-thumbnails/issues/95
    # if image.mode != "RGB":
    #     image = image.convert("RGB")
    return image


def save_image(image, upload_set, image_type, file_storage):
    """保存图片
    保存到upload_set对应的文件夹中
    文件后缀使用file_storage中文件名的后缀
    """
    ext = os.path.splitext(file_storage)[1]
    filename = '%s%s' % (random_filename(), ext)
    # 若不存在此目录，则创建之
    if not os.path.isdir(upload_set):
        os.makedirs(upload_set)
    path = os.path.join(upload_set, filename)

    if image_type == 'avatar':
        # 居中裁剪
        w, h = image.size
        if w > h:
            border = h
            avatar_crop_region = ((w - border) / 2, 0, (w + border) / 2, border)
        else:
            border = w
            avatar_crop_region = (0, (h - border) / 2, border, (h + border) / 2)
        image = image.crop(avatar_crop_region)
        # 缩放
        max_border = 100
        image = image.resize((max_border, max_border), Image.ANTIALIAS)
        # print filename.split(".")[0]
        thumb_filename = '%s%s' % (filename.split(".")[0] + "_s", ext)
        path2 = os.path.join(upload_set, thumb_filename)
        image.save(path2)
        filename = thumb_filename

    return filename


def process_avatar(file_storage, upload_set, max_border):
    """将上传的头像进行居中裁剪、缩放，然后保存"""
    image = open_image(file_storage)
    # 居中裁剪
    w, h = image.size
    if w > h:
        border = h
        avatar_crop_region = ((w - border) / 2, 0, (w + border) / 2, border)
    else:
        border = w
        avatar_crop_region = (0, (h - border) / 2, border, (h + border) / 2)
    image = image.crop(avatar_crop_region)
    # 缩放
    if border > max_border:
        image = image.resize((max_border, max_border), Image.ANTIALIAS)
    filename = save_image(image, upload_set, 0, file_storage)
    return filename


def process_question(file_storage, image_type, upload_set):
    """将上传的问题图片进行居中裁剪、缩放，然后保存"""
    image = open_image(file_storage)
    filename = save_image(image, upload_set, image_type, file_storage)
    return filename
