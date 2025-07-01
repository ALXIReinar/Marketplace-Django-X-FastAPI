from random import randint


def get_urls_plan():
    arr = [
           ('GET', '/api/favorites/?limit=20&offset=0'),
           ('POST', '/api/products/?limit=60&offset=0'),
           ('POST', '/api/users/passw/forget_passw'),
           ('POST', '/api/chats/get_file/local'),
           ('PUT', '/api/chats/set_readed'),
           ('POST', '/api/bg_tasks/ext_prd/lvl3'),
           ('GET', '/docs'), ('GET', '/openapi.json'),
           ('POST', '/api/products/elastic/search?limit=40&offset=0'),
           ('GET', '/api/orders/'),
           ('GET', '/.well-known/appspecific/com.chrome.devtools.json'),
           ('POST', '/api/chats/send_file/s3'),
           ('GET', '/api/products/77_3?in_front_cache=false'),
           ('PUT', '/api/chats/commit_msg'),
           ('PUT', '/api/users/logout'),
           ('GET', '/api/bg_tasks/wqweerrt'),
           ('POST', '/api/bg_tasks/ext_prd/lvl1'),
           ('DELETE', '/api/bg_tasks/crons/delete_chat-messages'),
           ('POST', '/api/products/elastic/bulk_docs'),
           ('GET', '/api/orders/purchased?limit=40&offset=0'),
           ('PUT', '/api/bg_tasks/crons/s3_fs-manager'),
           ('GET', '/favicon.ico'), ('DELETE', '/api/bg_tasks/crons/flush_refresh-tokens'),
           ('GET', '/api/chats/get_ws_token'),
           ('PUT', '/api/products/elastic/index_up/123'),
           ('POST', '/api/bg_tasks/ext_prd/lvl2'),
           ('GET', '/api/chats/?limit=30&offset=0'),
           ('PUT', '/api/users/passw/set_new_passw'),
           ('POST', '/api/chats/send_file/local'),
           ('POST', '/api/users/login'),
           ('PUT', '/api/bg_tasks/s3_upload/saving?file_path=12'),
           ('GET', '/api/products/bg_lvl3/77'),
           ('POST', '/api/chats/bulk_presigned_urls'),
           ('POST', '/api/bg_tasks/email_check'),
           ('POST', '/api/chats/send_message'),
           ('GET', '/api/users/passw/compare_confirm_code?reset_token=2134546&code=34566778'),
           ('GET', '/api/orders/sections?status=true&limit=60&offset=0'),
           ('POST', '/api/users/profile/seances')
    ]
    random_ip = []
    for i in range(len(arr)):
        ip_quarts = tuple(str(randint(0, 255)) for _ in range(4))
        ip = '.'.join(ip_quarts) + ', '
        random_ip.append(ip)
    res = [(meth, endpoint, ip) for (meth, endpoint), ip in zip(arr, random_ip)]
    return res
