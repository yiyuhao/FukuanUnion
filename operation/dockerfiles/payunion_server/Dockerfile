from registry.cn-hangzhou.aliyuncs.com/mixadx/payunion_server_base

LABEL maintainer "Mixadx"

#************************************************************************************************************************
#******************************************Start of Environment Variables************************************************
#************************************************************************************************************************
ENV GLOBAL_ENV_FOR_DYNACONF "PAYUNION"

ENV PAYUNION_IS_DEBUG "@bool True"
# Options are ['dev','test','prod']
ENV PAYUNION_ENV "test"


ENV PAYUNION_MYSQL_HOST ""
ENV PAYUNION_MYSQL_PORT "@int 3306"
ENV PAYUNION_MYSQL_DBNAME ""
ENV PAYUNION_MYSQL_USER ""
ENV PAYUNION_MYSQL_PASSWORD ""

ENV PAYUNION_REDIS_HOST ""
ENV PAYUNION_REDIS_PORT "@int 6379"
ENV PAYUNION_REDIS_PASSWORD ""

# 七牛 key
ENV PAYUNION_QINIU_ACCESS_KEY ""
ENV PAYUNION_QINIU_SECRET_KEY ""
ENV PAYUNION_QINIU_BUCKET_NAME ""
ENV PAYUNION_QINIU_BUCKET_DOMAIN ""

# 微信公众号appid,secret，服务器配置token
ENV PAYUNION_SUBSCRIPTION_ACCOUNT_APP_ID_USER ""
ENV PAYUNION_SUBSCRIPTION_ACCOUNT_APP_ID_MERCHANT ""
ENV PAYUNION_SUBSCRIPTION_ACCOUNT_APP_ID_MARKETER ""

ENV PAYUNION_SUBSCRIPTION_ACCOUNT_SECRET_USER ""
ENV PAYUNION_SUBSCRIPTION_ACCOUNT_SECRET_MERCHANT ""
ENV PAYUNION_SUBSCRIPTION_ACCOUNT_SECRET_MARKETER ""

ENV PAYUNION_SUBSCRIPTION_ACCOUNT_TOKEN_USER ""
ENV PAYUNION_SUBSCRIPTION_ACCOUNT_TOKEN_MERCHANT ""
ENV PAYUNION_SUBSCRIPTION_ACCOUNT_TOKEN_MARKETER ""

# 银行卡加密KEY
ENV PAYUNION_SECRET_KEY ""
# 微信openid加密/解密 秘钥
ENV PAYUNION_OPENID_AES_KEY ""

ENV PAYUNION_CLIENT_MINI_APP_ID ""
ENV PAYUNION_CLIENT_MINI_APP_SECRET ""

# 商户端小程序
ENV PAYUNION_MERCHANT_MINA_APP_ID ""
ENV PAYUNION_MERCHANT_MINA_APP_SECRET ""

# 邀请端小程序
ENV PAYUNION_MARKETER_MINA_APP_ID ""
ENV PAYUNION_MARKETER_MINA_APP_SECRET ""

ENV PAYUNION_WECHAT_MERCHANT_ID ""
ENV PAYUNION_WECHAT_MERCHANT_API_KEY ""
ENV PAYUNION_WECHAT_MERCHANT_CERT ""
ENV PAYUNION_WECHAT_MERCHANT_CERT_KEY ""
ENV PAYUNION_WECHAT_PUBLIC_KEY ""

ENV PAYUNION_ALIPAY_APP_ID ""
ENV PAYUNION_ALIPAY_APP_PRIVATE_KEY ""
ENV PAYUNION_ALIPAY_APP_PUBLIC_KEY ""
ENV PAYUNION_ALIPAY_PUBLIC_KEY ""

# 容联云短信
ENV PAYUNION_RLYSMS_APP_ID ""
ENV PAYUNION_RLYSMS_ACCOUNT_SID ""
ENV PAYUNION_RLYSMS_AUTH_TOKEN ""

# 讯飞语音合成
ENV PAYUNION_XUNFEI_API_ID ""
ENV PAYUNION_XUNFEI_API_KEY ""

# 百度语音合成
ENV PAYUNION_BAIDU_API_KEY ""
ENV PAYUNION_BAIDU_SECRET_KEY ""

# 阿里云市场
ENV PAYUNION_ALIYUN_APPCODE ""
ENV PAYUNION_ALIYUN_APP_KEY ""
ENV PAYUNION_ALIYUN_APP_SECRET ""


# 服务器之间验证请求合法性secret_token 配置
ENV PAYUNION_INTERNAL_AUTH_TOKEN_CONFIG_REFRESH_TOKEN ""


#************************************************************************************************************************
#******************************************End of Environment Variables************************************************
#************************************************************************************************************************


# Mount the files
add payserver /opt/sourcecode/payserver
add operation /opt/sourcecode/operation
volume ['/dockerdata']

# Create the necessary folders
run mkdir -p /dockerdata/log/payserver
run mkdir -p /dockerdata/log/supervisor

# Setup django application
run mkdir -p /opt/www/PAYUNION_SERVER
run cp -r /opt/sourcecode/operation/dockerfiles/payunion_server/config /opt/www/PAYUNION_SERVER/

# Include the necessary code
run cp -r /opt/sourcecode/payserver /opt/www/PAYUNION_SERVER/

run echo "yes" | python /opt/www/PAYUNION_SERVER/payserver/manage.py collectstatic

# Setup supervisor
run rm -f /etc/supervisor/supervisord.conf
run mkdir -p /etc/supervisor/conf.d/
run cp /opt/www/PAYUNION_SERVER/config/supervisor/supervisord.conf /etc/supervisor/supervisord.conf
run cp /opt/www/PAYUNION_SERVER/config/supervisor/supervisor-app.conf /etc/supervisor/conf.d/supervisor-app.conf

expose 80
run chmod 777 /opt/www/PAYUNION_SERVER/config/startup.sh
cmd ["/opt/www/PAYUNION_SERVER/config/startup.sh", "-bash"]
