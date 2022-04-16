import os
import re
import pandas as pd
from sklearn.model_selection import train_test_split

from URLAnalyser.constants import DATA_DIRECTORY
from URLAnalyser.utils import url_is_valid
from URLAnalyser.data.host import get_host
from URLAnalyser.data.host import host_registrar
from URLAnalyser.data.host import host_country
from URLAnalyser.data.host import host_server_count
from URLAnalyser.data.host import host_date
from URLAnalyser.data.host import host_speed
from URLAnalyser.data.host import host_latency
from URLAnalyser.data.content import get_content
from URLAnalyser.data.content import content_type
from URLAnalyser.data.content import content_redirect
from URLAnalyser.data.content import content_content


def _load_file(filename, path):
    if filename in os.listdir(path):
        df = pd.read_csv(os.path.join(path, filename), header=None, names=["name"])
        df = df.dropna()
        return df


def _save_file(df, filename, path):
    df.to_csv(os.path.join(path, filename), index=False)


def _load_lexical(sample_rate, use_cache, path, is_keras):
    if "whitelist.txt" in os.listdir(path) and "blacklist.txt" in os.listdir(path):
        benign = _load_file("whitelist.txt", path)
        malicious = _load_file("blacklist.txt", path)

        benign.insert(1, 'class', 0)
        malicious.insert(1, 'class', 1)

        urls = pd.concat([benign, malicious])
        urls = urls.sample(frac=sample_rate) if is_keras else urls.sample(n=20000)

        urls["name"] = urls["name"].apply(lambda x: re.sub(r"https?://(www\.)?", "", x))
        urls["is_valid"] = False
        return urls
    return None


def _load_host(sample_rate, use_cache, path, is_keras):
    # If cache enabled, try load from their first
    if use_cache and "host.csv" in os.listdir(path):
        return _load_file("host.csv", path)

    # Initialise host df with lexical values
    host = _load_lexical(sample_rate, use_cache, path, is_keras)
    if host is None:
        return None

    # Remove urls that are not valid
    host["is_valid"] = host["name"].apply(lambda x: url_is_valid(x))
    host = host[host.is_valid]

    # Extract host based information from sites
    host["info"] = host['name'].apply(lambda x: get_host(x))
    host["registrar"] = host['info'].apply(lambda x: host_registrar(x))
    host["location"] = host['info'].apply(lambda x: host_country(x))
    host["server_count"] = host['info'].apply(lambda x: host_server_count(x))
    host["creation_date"] = host['info'].apply(lambda x: host_date(x, "creation_date"))
    host["updated_date"] = host['info'].apply(lambda x: host_date(x, "updated_date"))
    host["expiration_date"] = host['info'].apply(lambda x: host_date(x, "expiration_date"))
    host["speed"] = host['name'].apply(lambda x: host_speed(x))
    host["latency"] = host['name'].apply(lambda x: host_latency(x))

    # Remove extra info column at the end
    host.drop(["info"], axis=1, inplace=True)
    return host


def _load_content(sample_rate, use_cache, path, is_keras):
    # If cache enabled, try load from their first
    if use_cache and "host.csv" in os.listdir(path):
        return _load_file("host.csv", path)

    # Initialise content df with lexical values
    content = _load_lexical(sample_rate, use_cache, path, is_keras)
    if content is None:
        return None

    # Remove urls that are not valid
    content["is_valid"] = content["name"].apply(lambda x: url_is_valid(x))
    content = content[content.is_valid]

    # Extract content based information from sites
    content["info"] = content['name'].apply(lambda x: get_content(x))
    content["type"] = content['info'].apply(lambda x: content_type(x))
    content["is_redirect"] = content['info'].apply(lambda x: content_redirect(x))
    content["content"] = content['info'].apply(lambda x: content_content(x))

    # Remove extra info column at the end
    content.drop(["info"], axis=1, inplace=True)
    return content


def _load_method(dataset_name):
    if dataset_name == 'lexical':
        return _load_lexical
    if dataset_name == 'host':
        return _load_host
    if dataset_name == 'content':
        return _load_content


def load_url_data(dataset_name, sample_rate=1, use_cache=True, is_keras=False):
    load_method = _load_method(dataset_name)
    path = os.path.join(DATA_DIRECTORY, "urls")

    url_data = load_method(sample_rate, use_cache, path, is_keras)
    _save_file(url_data, dataset_name + ".csv", path)

    url_data.drop(["is_valid"], inplace=True, axis=1)
    url_data.reset_index(inplace=True, drop=True)
    return url_data


def get_train_test_data(url_dataframe):
    y = url_dataframe['class']
    x = url_dataframe.drop(['class'], axis=1)
    return train_test_split(x, y, test_size=0.2)
