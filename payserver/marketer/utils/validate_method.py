import re


def validate_phone(phone):
    REGEX_MOBILE = '^1[3-9]\d{9}$'
    if re.match(REGEX_MOBILE, phone):
        return phone
    else:
        return None

