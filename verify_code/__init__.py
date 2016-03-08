# -*- coding: utf-8 -*-
# 导入三个模块
from PIL import Image, ImageDraw, ImageFont
import random
import math
from StringIO import StringIO
import os.path


def make(text):
    width = 85
    height = 25
    bgcolor = (200, 200, 200)
    image = Image.new('RGB', (width, height), bgcolor)
    newImage = Image.new('RGB', (width, height), bgcolor)

    font_file = os.path.join(os.path.dirname(__file__), 'CANDARAB.TTF')
    font = ImageFont.truetype(font_file, 25)

    draw = ImageDraw.Draw(image)
    for i in range(len(text)):
        _rand = random.randint(1, 3)
        if _rand == 1:
            _red = random.randint(0, 200)
            fontcolor = (_red, 0, 0)
        if _rand == 2:
            _gree = random.randint(0, 200)
            fontcolor = (0, _gree, 0)
        if _rand == 3:
            _blue = random.randint(0, 200)
            fontcolor = (0, 0, _blue)

        draw.text((i * 18, 0), text[i], font=font, fill=fontcolor)
    del draw
    # 保存原始版本
    # image.save('1234_1.jpeg')
    '''演示扭曲，需要新建一个图片对象'''
    # 新图片

    # load像素
    newPix = newImage.load()
    pix = image.load()
    offset = 5
    for y in range(0, height):
        # offset += 1
        for x in range(0, width):
            # 新的x坐标点
            newx = x + offset
            # 你可以试试如下的效果
            # newx = x + math.sin(float(y)/10)*10
            if newx < width:
                # 把源像素通过偏移到新的像素点
                newPix[newx, y] = pix[x, y]
    # 保存扭曲后的版本
    # newImage.save('1234_2.jpeg')
    '''形变一下'''
    # x1 = ax+by+c
    # y1 = dx+ey+f
    # newImage = image.transform((width+30,height+10), Image.AFFINE, (1,-0.3,0,-0.1,1,0))
    # newImage.save('1234_3.jpeg')
    '''画干扰线，别画太多，免得用户都看不清楚'''
    # 创建draw，画线用
    draw = ImageDraw.Draw(newImage)
    # 线的颜色
    linecolor = (100, 200, 200)
    for i in range(0, 5):
        # 都是随机的
        x1 = random.randint(0, width)
        x2 = random.randint(0, width)
        y1 = random.randint(0, height)
        y2 = random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], linecolor)

        # 保存到本地
    # newImage.save('/home/perolchen/1234.jpeg')
    f = StringIO()
    newImage.save(f, 'GIF')
    v = f.getvalue()
    f.close()
    return v


if __name__ == '__main__':
    make('4208')
