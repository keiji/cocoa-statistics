import csv
import unittest

import io

from statistics import StatisticsData


def _dummy_statistics_keys():
    statistics_data = StatisticsData()
    statistics_data.created = 1
    statistics_data.rolling_start_interval_number = 2
    statistics_data.key_count = 3
    statistics_data.invalid_transmission_risk_level_key_count = 4
    statistics_data.invalid_report_type_key_count = 5
    statistics_data.invalid_days_since_onset_of_symptoms_key_count = 6
    statistics_data.invalid_key_data_count = 7
    statistics_data.valid_key_count = 8
    statistics_data.has_not_days_since_onset_of_symptoms_count = 9
    statistics_data.has_not_report_type_count = 10

    for key in range(8):
        statistics_data.transmission_risk_level_distribution[key] = 100 + key

    for key in range(6):
        statistics_data.report_type_distribution[key] = 1000 + key

    for key in range(-14, 15):
        statistics_data.days_since_onset_of_symptoms_distribution[key] = 10000 + key

    statistics_data.comment = "this is comment"

    return statistics_data


class TestStatisticsData(unittest.TestCase):

    def test_csv(self):
        expected_csv = "1,2,1970-01-01T09:20:00.000000+0900,3,8,7,4,5,6,10,9,100,101,102,103,104,105,106,1000,1001,1002,1003,1004,1005,9986,9987,9988,9989,9990,9991,9992,9993,9994,9995,9996,9997,9998,9999,10000,10001,10002,10003,10004,10005,10006,10007,10008,10009,10010,10011,10012,10013,10014,this is comment\r\n"

        string_io = io.StringIO()
        writer = csv.writer(string_io)

        _dummy_statistics_keys().write_to_csv(writer)

        self.assertEqual(expected_csv, string_io.getvalue())
