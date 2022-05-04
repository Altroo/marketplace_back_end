from datetime import datetime
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


def generate_order_id(user_pk):
    dt = datetime.now()
    ts = datetime.timestamp(dt)
    str_ts = str(ts)
    str_ts_s = str_ts.split('.')
    timestamp = str_ts_s[0][6:]
    uid = urlsafe_base64_encode(force_bytes(user_pk))
    print('{}-{}'.format(timestamp, uid))


if __name__ == '__main__':
    generate_order_id(1)
