import io

import requests
from PIL import Image, ImageDraw, ImageFont

from common import (make_qrcode, parse_query_string, gen_number,
                    QRCODE_SIZE, BACK_IMG_SIZE, QRCODE_START_HEIGHT,
                    QRCODE_ID_START_HEIGHT)


def gen_signal_qrcode(environ, start_response):
    """
    函数计算入口
    接口参数(get)：
        uuid: 付款码uuid
        id: 付款码id
        url:  背景图片url
    """
    context = environ['fc.context']
    request_uri = environ['fc.request_uri']

    for k, v in environ.items():
        if k.startswith("HTTP_"):
            # process custom request headers
            pass

    # do something here
    env = environ['env']
    params_str = request_uri.split('?')[-1]
    params_dict = parse_query_string(params_str)

    uuid = params_dict.get('uuid', '')
    url = params_dict.get('url', '')
    id = params_dict.get('id', '')

    # 直接不验证
    bytes_data = generate_signal_qrcode(uuid=uuid, env=env, id=id, url=url)

    # response status
    status = '200 OK'
    if not bytes_data:
        status = '403 FORBIDDEN'
    response_headers = [
        ('Content-type', 'image/png'),
        ('Content-Disposition', "attachment; filename={}".format("qrcode.png"))
    ]
    start_response(status, response_headers)

    return [bytes_data]


def generate_signal_qrcode(uuid='', id=None, env='', url=None):
    """
    生成一张商户付款二维码
    :param uuid: 付款码uuid
    :param id: 付款码id
    :param env: 环境变量
    :param url:  背景图片url
    :return:  qrcode bytes
    """
    if not uuid and not id and not env:
        return b''

    pay_url_map = {
        'prod': 'http://api.mishitu.com/api/user/payment/entry?uuid={}',
        'test': 'http://api-alpha.mishitu.com/api/user/payment/entry?uuid={}',
    }

    default_url = ('https://ss-alpha.mishitu.com/payunion/'
                   'f8743e3e-52d1-48d2-9b7f-3e0a8415536d.jpg')
    url = url if url else default_url

    # 背景图片
    resp = requests.get(url)
    f = io.BytesIO(resp.content)
    back_img = Image.open(f)

    if back_img.mode != 'RGBA':
        back_img = back_img.convert('RGBA')
        back_img = back_img.resize(BACK_IMG_SIZE, Image.ANTIALIAS)

    # 生成二维码链接
    data = pay_url_map[env].format(uuid)

    # 生成二维码扫码区
    img = make_qrcode(data, QRCODE_SIZE)

    # 卡片
    cav_img = Image.new('RGBA', BACK_IMG_SIZE, (220, 220, 220))

    # 给卡片增加背景图片
    cav_img = Image.alpha_composite(cav_img, back_img)
    img_w, _ = img.size
    cav_img_w, _ = cav_img.size
    w = int((cav_img_w - img_w) / 2)
    cav_img.paste(img, (w, QRCODE_START_HEIGHT))

    # 生成画布
    draw = ImageDraw.Draw(cav_img)

    # 写入编号
    number = gen_number(id)
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

    return buf.getvalue()
