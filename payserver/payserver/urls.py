"""payserver URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.urls import include

from config import API_VERSION
from payserver.shared_views import api_version_not_found
from puser.rest import payment_entry

urlpatterns = [
    url(r'^api/admin/', include('padmin.urls')),
    url(r'^api/user/v%d\.%d\.%d/' % API_VERSION['USER'], include('puser.urls')),
    url(r'^api/merchant/v%d\.%d\.%d/' % API_VERSION['MERCHANT'], include('merchant.urls')),
    url(r'^api/marketer/v%d\.%d\.%d/' % API_VERSION['MARKETER'], include('marketer.urls')),

    # payment entry is encoded into the payment qrcode, so it cannot be versioned
    url(r'^api/user/payment/entry', payment_entry.PaymentEntryView.as_view(), name='payment_entry'),
]
