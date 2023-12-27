from collections.abc import MutableMapping
from urllib.parse import urlencode
import db_requests
import config


async def generate_payment_link(order_id: int, customer_phone: str, product_id: int) -> str:
    """Создаёт и возвращает платёжную ссылку"""
    product = await db_requests.get_course_by_id(product_id)
    linktoform = ''
    secret_key = config.SECRET_PRODAMUS_KEY

    data = {
        'order_id': order_id,
        'customer_phone': customer_phone,
        'customer_email': 'ИМЯ@prodamus.ru',
        'products': [
            {
                'sku': product.id,
                'name': product.title,
                'price': product.price,
                'quantity': '1',

                #  Тип оплаты, с возможными значениями (при необходимости заменить):
                # 	1 - полная предварительная оплата до момента передачи предмета расчёта;
                # 	2 - частичная предварительная оплата до момента передачи 
                #       предмета расчёта;
                # 	3 - аванс;
                # 	4 - полная оплата в момент передачи предмета расчёта;
                # 	5 - частичная оплата предмета расчёта в момент его передачи 
                #       с последующей оплатой в кредит;
                # 	6 - передача предмета расчёта без его оплаты в момент 
                #       его передачи с последующей оплатой в кредит;
                # 	7 - оплата предмета расчёта после его передачи с оплатой в кредит.
                #      (не обязательно, если не указано будет взято из настроек 
                #      Магазина на стороне системы)
                #'paymentMethod': 1
            },
        ],

        #  для интернет-магазинов доступно только действие "Оплата"
        'do': 'pay',
        #  url-адрес для возврата пользователя без оплаты 
        #    (при необходимости прописать свой адрес)
        'urlReturn' : 'https://t.me/oksanakolorist_bot',

        # url-адрес для возврата пользователя при успешной оплате 
        #    (при необходимости прописать свой адрес)
        'urlSuccess': 'https://t.me/oksanakolorist_bot',
        
    }

    # подписываем с помощью кастомной функции sign (см ниже)
    data['signature'] = sign(data, secret_key)

    # компануем ссылку с помощью кастомной функции http_build_query (см ниже)
    link = linktoform + '?' + urlencode(http_build_query(data))

    return link

def sign(data, secret_key):
    import hashlib
    import hmac
    import json

    # переводим все значения data в string c помощью кастомной функции deep_int_to_string (см ниже)
    deep_int_to_string(data)

    # переводим data в JSON, с сортировкой ключей в алфавитном порядке, без пробелом и экранируем бэкслеши
    data_json = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(',', ':')).replace("/", "\\/")

    # создаем подпись с помощью библиотеки hmac и возвращаем ее
    return hmac.new(secret_key.encode('utf8'), data_json.encode('utf8'), hashlib.sha256).hexdigest()

def deep_int_to_string(dictionary):
    for key, value in dictionary.items():
        if isinstance(value, MutableMapping):
            deep_int_to_string(value)
        elif isinstance(value, list) or isinstance(value, tuple):
            for k, v in enumerate(value):
                deep_int_to_string({str(k): v})
        else: dictionary[key] = str(value)
                
def http_build_query(dictionary, parent_key=False):
    items = []
    for key, value in dictionary.items():
        new_key = str(parent_key) + '[' + key + ']' if parent_key else key
        if isinstance(value, MutableMapping):
            items.extend(http_build_query(value, new_key).items())
        elif isinstance(value, list) or isinstance(value, tuple):
            for k, v in enumerate(value):
                items.extend(http_build_query({str(k): v}, new_key).items())
        else:
            items.append((new_key, value))
    return dict(items)
