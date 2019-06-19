from registry.cn-hangzhou.aliyuncs.com/mixadx/payunion_admin_base

LABEL maintainer "Mixadx"

# Mount the files
add padmin /opt/sourcecode/padmin
add operation /opt/sourcecode/operation
volume ['/dockerdata']

# Create the necessary folders
run mkdir -p /dockerdata/log/supervisor
run mkdir -p /opt/www/PAYUNION_ADMIN/padmin/public/

#Copy configs
run cp -r /opt/sourcecode/operation/dockerfiles/payunion_admin/config /opt/www/PAYUNION_ADMIN/

# Include the necessary code
run cp -r /opt/sourcecode/padmin/public/* /opt/www/PAYUNION_ADMIN/padmin/public/

# Setup nginx
run echo "daemon off;" >> /etc/nginx/nginx.conf
run cp /opt/www/PAYUNION_ADMIN/config/nginx/payunion_admin.conf /etc/nginx/sites-enabled/payunion_admin.conf
run rm -f /etc/nginx/sites-enabled/default

expose 80
cmd ["nginx"]
