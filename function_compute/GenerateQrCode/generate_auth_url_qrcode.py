import io

from urllib.request import quote

from common import auth, make_qrcode, parse_query_string


def gen_auth_url_qrcode(environ, start_response):
    """
    函数计算入口
    接口参数（get）:
        scenario_type: marketer / merchant / alipay
        state: 微信重定向参数
        timestamp: 时间戳
        signature: 时间戳计算的加密值
        redirect_url: 微信重定向url
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

    timestamp = int(params_dict.get('timestamp', 0))
    signature = params_dict.get('signature')
    scenario_type = params_dict.get('scenario_type', '')
    state = params_dict.get('state', '')
    redirect_url = params_dict.get('redirect_url', '')
    version = params_dict.get('version', '')

    if auth(timestamp, signature):
        bytes_data = generate_auth_url_qrcode(scenario_type=scenario_type,
                                              state=state,
                                              env=env,
                                              version=version,
                                              redirect_url=redirect_url)
    else:
      bytes_data = b''
      
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
    
    
def generate_auth_url_qrcode(scenario_type, state, env, version,
                             redirect_url=None):
    """
    生成一张授权二维码(微信、支付宝)
    :param scenario_type: marketer / merchant / alipay
    :param state: 微信重定向参数
    :param env: 环境变量
    :param version: api版本
    :param redirect_url: 微信重定向url
    :return: qrcode bytes
    """
    scenario = {
        'marketer': 'wx4897f192a4e54979',
        'merchant': 'wx3f75ca357f606548',
        'alipay_test': '2016091800543597',
        'alipay_prod': '2016071401615878',
        'user_test': 'wx550ba0dd3e19d5f6',
    }

    redirect_url_map = {
        'test': 'http://api-alpha.mishitu.com/',
        'prod': 'http://api.mishitu.com/'
    }

    if version and not redirect_url:
        version = '/{}'.format(version)

    redirect_map = {
        'marketer': 'api/marketer{}/get-merchant-wechat-info/'.format(version),
        'merchant': 'api/merchant{}/add_cashier/wechat_auth_redirect/'.format(version),
        'alipay': 'api/marketer{}/get-merchant-alipay-info/'.format(version)
    }

    if not redirect_url:
        if state.startswith('alipay_'):
            redirect_url = redirect_url_map[env] + redirect_map['alipay']
        elif state.startswith('marketer_'):
            redirect_url = redirect_url_map[env] + redirect_map['marketer']
        else:
            redirect_url = redirect_url_map[env] + redirect_map['merchant']

    # url encode the redirect_url
    redirect_url = quote(redirect_url, safe='')

    if state.startswith('alipay_'):
        auth_host = 'https://openauth.alipay.com'
        if env == 'test':
            auth_host = 'https://openauth.alipaydev.com'
        auth_url = ('{}/oauth2/publicAppAuthorize.htm?app_id={}&scope=auth_user'
                    '&state={}&redirect_uri={}'.format(auth_host,
                                                       scenario[scenario_type],
                                                       state,
                                                       redirect_url))
    else:
        auth_url = ('https://open.weixin.qq.com/connect/oauth2/authorize?'
                    'appid={}&redirect_uri={}&response_type=code&'
                    'scope=snsapi_userinfo&state={}'
                    '#wechat_redirect'.format(scenario[scenario_type],
                                              redirect_url,
                                              state))
    
    # 生成授权二维码
    img = make_qrcode(auth_url)
    
    buf = io.BytesIO()
    img.save(buf, 'png')
    
    return buf.getvalue()

