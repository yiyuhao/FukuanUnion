import io
import json
from urllib import parse

import requests
from PIL import Image, ImageDraw, ImageFont

from common import (auth, make_qrcode, InMemoryZIP, gen_number, QRCODE_SIZE,
                     BACK_IMG_SIZE, QRCODE_ID_START_HEIGHT,
                     QRCODE_START_HEIGHT)


def gen_qrcode(environ, start_response):
    """
    函数计算入口
    接口参数：
        uuids: uuid 数组
        url: 二维码背景
    """
    context = environ['fc.context']
    request_uri = environ['fc.request_uri']
    for k, v in environ.items():
        if k.startswith("HTTP_"):
            # process custom request headers
            pass
    # do something here

    try:
        request_body_size = int(environ.get('CONTENT_LENGTH', 0))
    except (ValueError):
        request_body_size = 0
    request_body_bytes = environ['wsgi.input'].read(request_body_size)
    request_body = parse.unquote(request_body_bytes.decode('utf8'))

    env = environ['env']
    body_dic = json.loads(request_body)
    uuids = body_dic['uuids']
    url = body_dic['url']
    timestamp = int(body_dic['timestamp'])
    signature = body_dic['signature']

    if auth(timestamp, signature):
        bytes_data = generate_qrcode(uuids=uuids, env=env, url=url)
    else:
        bytes_data = b''

    # response status
    status = '200 OK'
    if not bytes_data:
        status = '403 FORBIDDEN'
    response_headers = [
        ('Content-type', 'application/octet-stream'),
        ('Content-Disposition', "attachment; filename={}".format("qrcode.zip")),
        ('Content-Length', len(bytes_data))
    ]
    start_response(status, response_headers)

    return [bytes_data]


def generate_qrcode(uuids, env, url=None):
    """
    生成二维码压缩包
    :param uuids: uuid 数组
    :param url: 二维码背景
    :param env: 当前环境
    :return: 二维码压缩包bytes
    """
    if not uuids:
        return b''

    default_url = ('https://ss1.mvpalpha.muchbo.com/payunion/'
                   'c3a531a5-9610-43d5-bdcc-0cd782eba491.jpg')

    pay_url_map = {
        'prod': 'http://api.mishitu.com/api/user/payment/entry?uuid={}',
        'test': 'http://api-alpha.mishitu.com/api/user/payment/entry?uuid={}',
    }

    # 背景图片url
    url = url if url else default_url

    # 背景图片
    resp = requests.get(url)
    f = io.BytesIO(resp.content)
    back_img = Image.open(f)

    if back_img.mode != 'RGBA':
        back_img = back_img.convert('RGBA')
        back_img = back_img.resize(BACK_IMG_SIZE, Image.ANTIALIAS)

    # 生成一个内存zip对象
    imz = InMemoryZIP()

    for item in uuids:
        # 二维码data
        data = pay_url_map[env].format(item[1])

        # 生成扫码区
        img = make_qrcode(data, QRCODE_SIZE)

        # 卡片
        cav_img = Image.new('RGBA', BACK_IMG_SIZE, (220, 220, 220))
        # 给卡片增加背景图片
        cav_img = Image.alpha_composite(cav_img, back_img)
        img_w, _ = img.size
        cav_img_w, _ = cav_img.size
        width_start = int((cav_img_w - img_w) / 2)

        # 将二维码添加到背景
        cav_img.paste(img, (width_start, QRCODE_START_HEIGHT))

        # 将编号插入背景图
        number = gen_number(item[0])
        draw = ImageDraw.Draw(cav_img)
        fnt = ImageFont.truetype("msyh.ttf", size=64, encoding='utf-8')
        fnt_width, _ = draw.textsize(number, fnt)
        if fnt_width > cav_img_w:
            font_width = 0
        else:
            font_width = int((cav_img_w - fnt_width) / 2)

        draw.text((font_width, QRCODE_ID_START_HEIGHT), number, font=fnt,
                  fill='#fff')

        buf = io.BytesIO()
        cav_img.save(buf, 'png')
        imz.appendfile('{}.jpg'.format(str(item[1])), buf.getvalue())

    return imz.read()
