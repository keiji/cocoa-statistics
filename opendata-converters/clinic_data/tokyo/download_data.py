import csv
import json
import os
import shutil
from urllib import request
from dateutil import parser

from absl import flags, app

FLAGS = flags.FLAGS
flags.DEFINE_string("config_path", None, "Config file path")

flags.DEFINE_string("tmp_path", "/tmp", "Temporary path")
flags.DEFINE_string("output_path", "./test/latest.csv", "Output file path")


def _download_opendata(url):
    name = os.path.basename(url)
    file_path = os.path.join(FLAGS.tmp_path, name)

    req = request.Request(url)

    with request.urlopen(req) as res:
        with open(file_path, 'wb') as fp:
            fp.write(res.read())

        last_modified = parser.parse(res.headers['Last-Modified'])
        return last_modified, file_path


def _load_settings(config_path):
    with open(config_path, mode='r') as fp:
        json_obj = json.load(fp)
        return json_obj["tokyo"]


def _validate(file_path, required_header):
    with open(file_path, mode='r', encoding="utf-8-sig") as fp:
        csv_reader = csv.reader(fp)
        for row in csv_reader:
            print(row)
            return _validate_header(required_header, row)


def _validate_header(required_header, header_row):
    for required_column in required_header:
        if required_column not in header_row:
            return False
    return True


def main(argv):
    del argv  # Unused.

    assert FLAGS.config_path is not None, "Parameter --config_path must be set."
    assert os.path.exists(FLAGS.config_path), FLAGS.config_path + " is not exist."

    settings = _load_settings(FLAGS.config_path)
    url = settings["url"]
    required_headers = settings["required_headers"]

    os.makedirs(os.path.dirname(FLAGS.output_path), exist_ok=True)

    last_modified, file_path = _download_opendata(url)

    assert _validate(file_path, required_headers), "Header validation failed."

    try:
        shutil.move(file_path, FLAGS.output_path)
    finally:
        pass


if __name__ == '__main__':
    app.run(main)
