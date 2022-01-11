import base64
import csv
import datetime
import itertools
import json
import os
import tempfile
import zipfile
from functools import cmp_to_key
from itertools import groupby
from urllib import request

from absl import flags, app

import protobuf.temporary_exposure_key_export_pb2 as tek_export
from statistics import StatisticsData, _rolling_start_interval_number_to_date, EN_INTERVAL_WINDOW

FLAGS = flags.FLAGS
flags.DEFINE_string("tmp_path", "/tmp/cocoa_diagnosis_keys", "Temporary Path")
flags.DEFINE_string("output_path", "./v1/cocoa_diagnosis_keys/latest.csv", "Output-file path")

COCOA_DIAGNOSIS_KEYS_LIST_URL = os.environ['COCOA_DIAGNOSIS_KEYS_LIST_URL']

FILENAME_EXPORT_BIN = "export.bin"
BIN_HEADER = "EK Export v1    "
BIN_HEADER_BYTES_LENGTH = len(BIN_HEADER.encode(encoding='utf-8'))


class Entry:
    url = None
    created = -1
    zip_file_path = None
    diagnosis_keys = None

    def __init__(self, url, created, zip_file_path):
        self.url = url
        self.created = created
        self.zip_file_path = zip_file_path


def _download_diagnosis_keys_list():
    fd, tmpfile = tempfile.mkstemp(dir=FLAGS.tmp_path, suffix='.json', text=True)
    req = request.Request(COCOA_DIAGNOSIS_KEYS_LIST_URL)
    with request.urlopen(req) as res:
        os.write(fd, res.read())
    os.close(fd)
    return tmpfile


def _download_diagnosis_keys(row):
    url = row["url"]
    created = row["created"]
    filename = url.split("/")[-1]
    file_path = os.path.join(FLAGS.tmp_path, filename)
    entry = Entry(url, created, file_path)
    if os.path.exists(file_path):
        print("%s already exist." % file_path)
        return entry

    with open(file_path, 'wb') as fp:
        req = request.Request(url)
        with request.urlopen(req) as res:
            fp.write(res.read())
    return entry


def _get_diagnosis_keys_file(entry):
    zip_file_path = entry.zip_file_path
    assert zipfile.is_zipfile(zip_file_path), "%s doesn't seem valid ZIP file." % zip_file_path

    with zipfile.ZipFile(zip_file_path, "r") as zip:
        zip.extract(FILENAME_EXPORT_BIN, FLAGS.tmp_path)

    return os.path.join(FLAGS.tmp_path, FILENAME_EXPORT_BIN)


def _get_diagnosis_keys(bin_file_path):
    with open(bin_file_path, 'rb') as fp:
        # strip header
        fp.seek(BIN_HEADER_BYTES_LENGTH)

        diagnosis_keys = tek_export.TemporaryExposureKeyExport()
        diagnosis_keys.ParseFromString(fp.read())

        return diagnosis_keys


def _rolling_period_to_timedelta(rolling_period):
    epoch = rolling_period * EN_INTERVAL_WINDOW
    return datetime.timedelta(seconds=epoch)


def _print(diagnosis_keys):
    print(diagnosis_keys.start_timestamp)
    print(diagnosis_keys.end_timestamp)
    print(diagnosis_keys.region)
    print(diagnosis_keys.batch_num)
    print(diagnosis_keys.batch_size)
    for key in diagnosis_keys.keys:
        print(key.transmission_risk_level)
        print(_rolling_start_interval_number_to_date(key.rolling_start_interval_number))
        print(_rolling_period_to_timedelta(key.rolling_period))

        if not key.HasField("report_type"):
            print("Field report_type not exist.")
        else:
            print(key.report_type)

        if not key.HasField("days_since_onset_of_symptoms"):
            print("Field days_since_onset_of_symptoms not exist.")
        else:
            print(key.days_since_onset_of_symptoms)

    print(diagnosis_keys.revised_keys)


def _is_valid_transmission_risk_level_key(key):
    # https://developer.apple.com/documentation/exposurenotification/enexposureinfo/3583716-transmissionrisklevel
    if key.transmission_risk_level >= 0 or key.transmission_risk_level <= 7:
        return True, ""

    return False, "value transmission_risk_level %d" % key.report_type


def _is_valid_report_type_key(key):
    # https://developer.apple.com/documentation/exposurenotification/endiagnosisreporttype
    if key.report_type >= 0 or key.report_type <= 5:
        return True, ""

    return False, "value report_type %d is invalid." % key.report_type


def _is_valid_days_since_onset_of_symptoms_key(key):
    # https://developers.google.com/android/exposure-notifications/meaningful-exposures
    if key.days_since_onset_of_symptoms >= -14 or key.days_since_onset_of_symptoms <= 14:
        return True, ""

    return False, "value days_since_onset_of_symptoms %d is invalid." % key.days_since_onset_of_symptoms


def _is_valid_temporary_exposure_key_key(key):
    # Temporary Exposure Key
    # The use of 16-byte keys limits the server and device requirements for transferring and storing
    # Diagnosis Keys while preserving low false-positive probabilities.
    # https://blog.google/documents/69/Exposure_Notification_-_Cryptography_Specification_v1.2.1.pdf/
    if len(key.key_data) == 16:
        return True, ""

    return False, "key_data %s length %d is invalid." % (base64.b64encode(key.key_data), len(key.key_data))


def _statistics_keys(created, rolling_start_interval_number, keys):
    statistics_data = StatisticsData()
    statistics_data.created = created
    statistics_data.rolling_start_interval_number = rolling_start_interval_number

    for key in keys:
        statistics_data.key_count += 1

        is_valid_key = True

        messages = []

        is_valid, message = _is_valid_transmission_risk_level_key(key)
        if not is_valid:
            statistics_data.invalid_transmission_risk_level_key_count += 1
            is_valid_key = False
            messages.append(message)

        is_valid, message = _is_valid_report_type_key(key)
        if not is_valid:
            statistics_data.invalid_transmission_risk_level_key_count += 1
            is_valid_key = False
            messages.append(message)

        is_valid, message = _is_valid_days_since_onset_of_symptoms_key(key)
        if not is_valid:
            statistics_data.invalid_transmission_risk_level_key_count += 1
            is_valid_key = False
            messages.append(message)

        is_valid, message = _is_valid_temporary_exposure_key_key(key)
        if not is_valid:
            statistics_data.invalid_key_data_count += 1
            is_valid_key = False
            messages.append(message)

        statistics_data.comment = "|".join(messages)

        if is_valid_key:
            statistics_data.valid_key_count += 1

        statistics_data.transmission_risk_level_distribution[key.transmission_risk_level] += 1

        if key.HasField("report_type"):
            statistics_data.report_type_distribution[key.report_type] += 1
        else:
            statistics_data.has_not_report_type_count += 1

        if key.HasField("days_since_onset_of_symptoms"):
            statistics_data.days_since_onset_of_symptoms_distribution[key.days_since_onset_of_symptoms] += 1
        else:
            statistics_data.has_not_days_since_onset_of_symptoms_count += 1

    return statistics_data


def _statistics(diagnosis_keys_entries):
    statistics_list = []

    for created, entries in groupby(diagnosis_keys_entries, key=lambda entry: entry.created):
        print("%d" % created)

        # Extract keys
        keys = list(itertools.chain.from_iterable((map(lambda entry: entry.diagnosis_keys.keys, entries))))

        for rolling_start_interval_number, keys in groupby(keys, key=lambda key: key.rolling_start_interval_number):
            print("    %d" % rolling_start_interval_number)
            statistics_data = _statistics_keys(created, rolling_start_interval_number, keys)
            statistics_list.append(statistics_data)

    return statistics_list


def main(argv):
    del argv  # Unused.

    dir = os.path.dirname(FLAGS.output_path)
    os.makedirs(dir, exist_ok=True)

    os.makedirs(FLAGS.tmp_path, exist_ok=True)

    print("Start")

    list_file_path = _download_diagnosis_keys_list()

    diagnosis_keys_entries = []
    with open(list_file_path) as fp:
        json_obj = json.load(fp)
        for row in json_obj:
            diagnosis_keys_entries.append(_download_diagnosis_keys(row))

    for entry in diagnosis_keys_entries:
        diagnosis_keys_file_path = _get_diagnosis_keys_file(entry)
        entry.diagnosis_keys = _get_diagnosis_keys(diagnosis_keys_file_path)
        os.remove(diagnosis_keys_file_path)

    # Statistics
    statistics_list = _statistics(diagnosis_keys_entries)
    sorted(statistics_list, key=cmp_to_key(StatisticsData.compare))

    with open(FLAGS.output_path, mode='w') as fp:
        writer = csv.writer(fp)
        StatisticsData.write_header_to_csv(writer)
        for statistics_data in statistics_list:
            statistics_data.write_to_csv(writer)

    print("Clean...")
    os.remove(list_file_path)

    print("Done.")


if __name__ == '__main__':
    app.run(main)
