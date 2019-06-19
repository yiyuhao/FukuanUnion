from registry.cn-hangzhou.aliyuncs.com/mixadx/payunion_payweb_base

LABEL maintainer "Mixadx"

# Mount the files
add payweb /opt/sourcecode/payweb
add operation /opt/sourcecode/operation
volume ['/dockerdata']

# Create the necessary folders
run mkdir -p /dockerdata/log/supervisor
run mkdir -p /opt/www/PAYUNION_PAYWEB/payweb/

#Copy configs
run cp -r /opt/sourcecode/operation/dockerfiles/payunion_payweb/config /opt/www/PAYUNION_PAYWEB/

# Include the necessary code
run cp -r /opt/sourcecode/payweb/* /opt/www/PAYUNION_PAYWEB/payweb/

# Setup nginx
run echo "daemon off;" >> /etc/nginx/nginx.conf
run cp /opt/www/PAYUNION_PAYWEB/config/nginx/payunion_payweb.conf /etc/nginx/sites-enabled/payunion_payweb.conf
run rm -f /etc/nginx/sites-enabled/default

expose 80
cmd ["nginx"]
