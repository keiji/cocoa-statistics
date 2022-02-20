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

HEADER = [
    "\ufeff検索キー", "公開用_医療機関ID",
    "医療機関名", "正規化住所", "経度", "緯度", "郵便番号",
    "電話番号", "オンライン予約用ページアドレス",
    "相談センター等からの紹介",
    "自院患者", "濃厚接触者", "小児", "妊婦",
    "区市町村", "行政コード",
    "大字", "それ以降の住所", "ビル名・階数・部屋番号",
    "PCR", "抗原定量", "抗原定性", "鼻咽頭", "鼻腔", "唾液", "その他",
    "月（午前）", "月（午後）",
    "火（午前）", "火（午後）",
    "水（午前）", "水（午後）",
    "木（午前）", "木（午後）",
    "金（午前）", "金（午後）",
    "土（午前）", "土（午後）",
    "日（午前）", "日（午後）",
    "対応できる外国語", "診療検査日時が祝日の場合",
    "それ以降の住所"
]


def _download_opendata(url):
    name = os.path.basename(url)
    file_path = os.path.join(FLAGS.tmp_path, name)

    req = request.Request(url)

    with request.urlopen(req) as res:
        with open(file_path, 'wb') as fp:
            fp.write(res.read())

        last_modified = parser.parse(res.headers['Last-Modified'])
        return last_modified, file_path


def _load_endpoint_url(config_path):
    with open(config_path, mode='r') as fp:
        json_obj = json.load(fp)
        return json_obj["tokyo"]["url"]


def _validate(file_path):
    with open(file_path, mode='r') as fp:
        csv_reader = csv.reader(fp)
        for row in csv_reader:
            print(row)
            return row == HEADER


def main(argv):
    del argv  # Unused.

    assert FLAGS.config_path is not None, "Parameter --config_path must be set."
    assert os.path.exists(FLAGS.config_path), FLAGS.config_path + " is not exist."

    url = _load_endpoint_url(FLAGS.config_path)

    os.makedirs(os.path.dirname(FLAGS.output_path), exist_ok=True)

    last_modified, file_path = _download_opendata(url)

    assert _validate(file_path), "Header validation failed."

    try:
        shutil.move(file_path, FLAGS.output_path)
    finally:
        pass


if __name__ == '__main__':
    app.run(main)
