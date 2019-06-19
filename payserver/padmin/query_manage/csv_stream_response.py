# -*- coding: utf-8 -*-
#
#   Project: payunion
#   Author: zhaopengfei
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.
import codecs
from io import BytesIO

from django.http import JsonResponse, StreamingHttpResponse
from django.utils.encoding import escape_uri_path


def out_put_csv(rows, out_file_name='output.csv'):
    
    def get_then_clear_io_string(io_string_ojb):
        io_string_ojb.seek(0)
        data = io_string_ojb.read()
        io_string_ojb.seek(0)
        io_string_ojb.truncate()
        return data
    
    def generate_csv(rows):
        output = BytesIO()
        output.write(bytearray([0xFF, 0xFE]))
        for row in rows:
            row_data = codecs.encode("\t".join(row) + "\n", "utf-16le")
            output.write(row_data)
            yield get_then_clear_io_string(output)
        output.close()

    resp = StreamingHttpResponse(generate_csv(rows))
    resp["Content-Type"] = "application/vnd.ms-excel; charset=utf-16le"
    resp['Content-Disposition'] = "attachment; filename*=utf-8''{}".format(escape_uri_path(out_file_name))
    resp["Content-Transfer-Encoding"] = "binary"
    return resp
