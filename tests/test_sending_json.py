import requests

url = "http://127.0.0.1:8000/api/cart/order/"

# payload = {'shop_pk': '1',
#           'user_address_pk': '1',
#           'delivery_pk': '1'}
payload = [

    {'Shop_pk': '1',
     'Shop_picture': 'https://...',
     'Shop_name': 'ZARA',
     'offer_title': 'Le petit Pull',
     'offers_price': '357',
     'Offers_count': '1',
     'ID_Offers': '1'
     },

    {'Shop_pk': '2',
     'Shop_picture': 'https://...',
     'Shop_name': 'ZARA 2',
     'offer_title': 'Le petit Pull 2',
     'offers_price': '111',
     'Offers_count': '222',
     'ID_Offers': '333'
     },
]
headers = {
    'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjUzOTkwNDQ3LCJpYXQiOjE2NDg4MDY0NDcsImp0aSI6IjFjYTc1MzBkZWM2ZjQ3YjNhOTFmNzY5NjY0ZGE3MGNiIiwidXNlcl9pZCI6MX0.CLJ7XDdZ_Wy9dgN05IcAa0C3sx1NBi2nzO7tzRd8nPc',
    'Cookie': 'csrftoken=xIESoRdeGLdZHrfIjn10RnaYnCWPKBaWP9BdHdVkscfBqjcod3Zpmurg4EfXyZfh; qaryb-jwt-access=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNjUzODE1MjcxLCJpYXQiOjE2NDg2MzEyNzEsImp0aSI6IjBmMzU1OTk3YTAzMzQ4NTY5MDkzYjdjMmYxMmNhY2FiIiwidXNlcl9pZCI6MjR9.UhRJMni4IkAG3CkpHE6EDweJagUkYr9i6pbGb_5ReEs; qaryb-jwt-refresh=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTY4MDE2NzI3MSwiaWF0IjoxNjQ4NjMxMjcxLCJqdGkiOiIwOGY3ZTAzNmE4NWQ0ODQ2OWY5OTAyNWY1YTc1OTZjMCIsInVzZXJfaWQiOjI0fQ.uNFixfYsdBXLoQ5MQDsqyawMtKWQ5ICmV6v-dyPyS3U'
}

response = requests.request("POST", url, headers=headers, data=payload, files=[])

print(response.text)
