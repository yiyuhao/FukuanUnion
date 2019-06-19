import io
import time
import zipfile
from hashlib import sha1
from urllib import parse

import qrcode
from PIL import Image

QRCODE_SIZE = (716, 716)
BACK_IMG_SIZE = (1417, 1654)
QRCODE_START_HEIGHT = 468
QRCODE_ID_START_HEIGHT = 1218


def auth(timestamp, signature):
    """
    接口请求身份验证

    :param timestamp: 请求时的间戳
    :param signature: 请求接收的signature
    """
    salt = 9999
    sh = sha1()
    sh.update(bytes(str(timestamp + salt), 'utf8'))
    if sh.hexdigest() == signature and abs(time.time() - timestamp) < 120:
        return True
    else:
        return False


def parse_query_string(uri):
    """
    解析get请求的参数
    : params uri: 请求url的参数部分（？后面部分）
    """
    params_dict = {}
    query_dict = parse.parse_qs(uri)
    for key, value in query_dict.items():
        try:
            params_dict[key] = value[0]
        except IndexError:
            # Ignore the key if the value is null
            continue

    return params_dict


def make_qrcode(data, size=None):
    """
    生成正方形的二维码

    :param data: 二维码中存放的数据
    :param size: 二维码尺寸元组 (w, h)
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=3
    )
    qr.add_data(data)
    qr.make(fit=True)
    qr_img = qr.make_image()
    qr_img = qr_img.convert("RGBA")
    if size:
        qr_img = qr_img.resize(size, Image.ANTIALIAS)

    return qr_img


def gen_number(number):
    """生成二维码编号

    Arguments:
        number {int} -- 二维码编号
    """
    if isinstance(number, str):
        number = int(number)
    return f'No.{"%04d"% number}'


class InMemoryZIP(object):
    """
    Create zip file in memory
    """

    def __init__(self):
        """
        create the in-memory file-like object
        """
        self.in_memory_zip = io.BytesIO()

    def append(self, filename_in_zip, file_contents):
        """
        Appends a file with name filename_in_zip and contents of
        file_contents to the in-memory zip.
        """
        # create a handle to the in-memory zip in append mode
        zf = zipfile.ZipFile(self.in_memory_zip, 'a',
                             zipfile.ZIP_DEFLATED, False)

        # write the file to the in-memory zip
        zf.writestr(filename_in_zip, file_contents)

        # mark the files as having been created on Windows
        # so that Unix permissions are not inferred as 0000
        for zfile in zf.filelist:
            zfile.create_system = 0
        return self

    def appendfile(self, file_name, file_path_bytes):
        """
        Read a file with path file_path and append to in-memory zip
        with name file_name.
        """
        self.append(file_name, file_path_bytes)
        return self

    def read(self):
        """
        Returns a string with the contents of the in-memory zip.
        """
        self.in_memory_zip.seek(0)
        return self.in_memory_zip.read()

    def writetofile(self, filename):
        """
        Write the in-memory zip to a file
        """
        f = open(filename, 'wb')
        f.write(self.read())
        f.close()
