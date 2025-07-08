from core.config_dir.logger import log_event


def get_actual_endpoint_set():
    res = set()
    with open('./logs/info_warning_error/app.log', 'r', encoding='utf-8') as f:
        for line in f:
            url = line.split('|')[2].split(':8000')
            if len(url) > 1:
                method, endpoint = url[0].split('http://')[0].strip(), url[1].strip()
                res.add((method, endpoint))
    log_event(f'{res}', level='CRITICAL')
