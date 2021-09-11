import csv
import os
import tempfile
from urllib import request

from absl import flags, app

FLAGS = flags.FLAGS
flags.DEFINE_string("tmp_path", "/tmp", "Temporary Path")
flags.DEFINE_string("output_path", "./test/latest.csv", "Output-file path")

OPENDATA_URL = "https://covid19.mhlw.go.jp/public/opendata/newly_confirmed_cases_daily.csv"


def _download_opendata():
    fd, tmpfile = tempfile.mkstemp(dir=FLAGS.tmp_path, suffix='.csv', text=True)
    req = request.Request(OPENDATA_URL)
    with request.urlopen(req) as res:
        os.write(fd, res.read())
    os.close(fd)
    return tmpfile


def _save(csv_rows):
    with open(FLAGS.output_path, mode='w') as fp:
        writer = csv.writer(fp)
        for row in csv_rows:
            writer.writerow(row)


def main(argv):
    del argv  # Unused.

    dir = os.path.dirname(FLAGS.output_path)
    os.makedirs(dir, exist_ok=True)

    csv_file = _download_opendata()
    try:
        with open(csv_file, 'r') as fp:
            reader = list(csv.reader(fp))
            latest_day = reader[-1][0]
            print(latest_day)

            filtered_rows = filter(lambda row: row[0] == latest_day, reader)
            _save(filtered_rows)
    finally:
        os.remove(csv_file)


if __name__ == '__main__':
    app.run(main)
