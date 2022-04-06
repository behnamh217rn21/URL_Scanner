import requests


def get_content(url):
    try:
        return requests.get("http://" + url, timeout=(0.1, 10))
    except BaseException:
        try:
            return requests.get("https://" + url, timeout=(0.1, 10))
        except BaseException:
            return None


def content_type(response):
    return response.headers['Content-Type'] if response is not None else None


def content_redirect(response):
    return response.is_redirect if response is not None else None


def content_content(response):
    return response.content.decode(
        response.apparent_encoding) if response is not None else None
