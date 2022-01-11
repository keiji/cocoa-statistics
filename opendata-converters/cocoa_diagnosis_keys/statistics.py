import datetime

# RFC3339
FORMAT_RFC3339 = "%Y-%m-%dT%H:%M:%S.%f%z"

EN_INTERVAL_WINDOW = 60 * 10

JST = datetime.timezone(datetime.timedelta(hours=9), 'Asia/Tokyo')


def _rolling_start_interval_number_to_date(rolling_start_interval_number):
    epoch = rolling_start_interval_number * EN_INTERVAL_WINDOW
    return datetime.datetime.fromtimestamp(epoch).astimezone(JST)


class StatisticsData:
    created = -1
    rolling_start_interval_number = -1
    key_count = 0
    valid_key_count = 0
    invalid_key_data_count = 0
    invalid_transmission_risk_level_key_count = 0
    invalid_report_type_key_count = 0
    invalid_days_since_onset_of_symptoms_key_count = 0
    has_not_report_type_count = 0
    has_not_days_since_onset_of_symptoms_count = 0
    transmission_risk_level_distribution = {}
    report_type_distribution = {}
    days_since_onset_of_symptoms_distribution = {}

    def __init__(self):
        self.key_count = 0
        self.valid_key_count = 0
        self.invalid_key_data_count = 0
        self.invalid_transmission_risk_level_key_count = 0
        self.invalid_report_type_key_count = 0
        self.invalid_days_since_onset_of_symptoms_key_count = 0
        self.transmission_risk_level_distribution = {}
        for level in range(7 + 1):
            self.transmission_risk_level_distribution[level] = 0

        self.report_type_distribution = {}
        for type in range(6 + 1):
            self.report_type_distribution[type] = 0

        self.days_since_onset_of_symptoms_distribution = {}
        for day in range(-14, 14 + 1):
            self.days_since_onset_of_symptoms_distribution[day] = 0

    def __str__(self):
        return "StatisticsData( \n" \
               "created: %d, \n" \
               "rolling_start_interval_number: %d, \n" \
               "rolling_start_interval_number_date: %s, \n" \
               "key_count: %d, \n" \
               "valid_key_count: %d, \n" \
               "invalid_key_data_count: %d, \n" \
               "invalid_transmission_risk_level_key_count: %d, \n" \
               "invalid_report_type_key_count: %d, \n" \
               "invalid_days_since_onset_of_symptoms_key_count: %d, \n" \
               "has_not_report_type_count: %d, \n" \
               "has_not_days_since_onset_of_symptoms_count: %d, \n" \
               "transmission_risk_level_distribution: %s, \n" \
               "report_type_distribution: %s, \n" \
               "days_since_onset_of_symptoms_distribution: %s, \n" \
               ")" % (self.created,
                      self.rolling_start_interval_number,
                      _rolling_start_interval_number_to_date(self.rolling_start_interval_number).strftime(
                          FORMAT_RFC3339),
                      self.key_count,
                      self.valid_key_count,
                      self.invalid_key_data_count,
                      self.invalid_transmission_risk_level_key_count,
                      self.invalid_report_type_key_count,
                      self.invalid_days_since_onset_of_symptoms_key_count,
                      self.has_not_report_type_count, self.has_not_days_since_onset_of_symptoms_count,
                      self.transmission_risk_level_distribution,
                      self.report_type_distribution,
                      self.days_since_onset_of_symptoms_distribution,
                      )

    @staticmethod
    def compare(l, r):
        if l.created < r.created:
            return 1
        if l.created > r.created:
            return -1

        if l.rolling_start_interval_number < r.rolling_start_interval_number:
            return 1
        if l.rolling_start_interval_number > r.rolling_start_interval_number:
            return -1

        return 0

    @staticmethod
    def write_header_to_csv(csv_writer):
        csv_writer.writerow([
            "created",
            "rolling_start_interval_number",
            "rolling_start_interval_number_date",
            "key_count",
            "valid_key_count",
            "invalid_key_data_count",
            "invalid_transmission_risk_level_key_count",
            "invalid_report_type_key_count",
            "invalid_days_since_onset_of_symptoms_key_count",
            "has_not_report_type_count",
            "has_not_days_since_onset_of_symptoms_count",
            "transmission_risk_level_unused_count",
            "transmission_risk_level_low_count",
            "transmission_risk_level_standard_count",
            "transmission_risk_level_high_count",
            "transmission_risk_level_confirmed_clinical_diagnosis_count",
            "transmission_risk_level_negative_case_count",
            "transmission_risk_level_recursive_case_count",
            "report_type_unknown_count",
            "report_type_confirmed_test_count",
            "report_type_confirmed_clinical_diagnosis_count",
            "report_type_self_reported_count",
            "report_type_recursive_count",
            "report_type_revoked_count",
            "days_since_onset_of_symptoms_-14_count",
            "days_since_onset_of_symptoms_-13_count",
            "days_since_onset_of_symptoms_-12_count",
            "days_since_onset_of_symptoms_-11_count",
            "days_since_onset_of_symptoms_-10_count",
            "days_since_onset_of_symptoms_-9_count",
            "days_since_onset_of_symptoms_-8_count",
            "days_since_onset_of_symptoms_-7_count",
            "days_since_onset_of_symptoms_-6_count",
            "days_since_onset_of_symptoms_-5_count",
            "days_since_onset_of_symptoms_-4_count",
            "days_since_onset_of_symptoms_-3_count",
            "days_since_onset_of_symptoms_-2_count",
            "days_since_onset_of_symptoms_-1_count",
            "days_since_onset_of_symptoms_0_count",
            "days_since_onset_of_symptoms_+1_count",
            "days_since_onset_of_symptoms_+2_count",
            "days_since_onset_of_symptoms_+3_count",
            "days_since_onset_of_symptoms_+4_count",
            "days_since_onset_of_symptoms_+5_count",
            "days_since_onset_of_symptoms_+6_count",
            "days_since_onset_of_symptoms_+7_count",
            "days_since_onset_of_symptoms_+8_count",
            "days_since_onset_of_symptoms_+9_count",
            "days_since_onset_of_symptoms_+10_count",
            "days_since_onset_of_symptoms_+11_count",
            "days_since_onset_of_symptoms_+12_count",
            "days_since_onset_of_symptoms_+13_count",
            "days_since_onset_of_symptoms_+14_count",
        ])

    def write_to_csv(self, csv_writer):
        csv_writer.writerow([
            self.created,
            self.rolling_start_interval_number,
            _rolling_start_interval_number_to_date(self.rolling_start_interval_number).strftime(FORMAT_RFC3339),
            self.key_count,
            self.valid_key_count,
            self.invalid_key_data_count,
            self.invalid_transmission_risk_level_key_count,
            self.invalid_report_type_key_count,
            self.invalid_days_since_onset_of_symptoms_key_count,
            self.has_not_report_type_count,
            self.has_not_days_since_onset_of_symptoms_count,
            self.transmission_risk_level_distribution[0],
            self.transmission_risk_level_distribution[1],
            self.transmission_risk_level_distribution[2],
            self.transmission_risk_level_distribution[3],
            self.transmission_risk_level_distribution[4],
            self.transmission_risk_level_distribution[5],
            self.transmission_risk_level_distribution[6],
            self.report_type_distribution[0],
            self.report_type_distribution[1],
            self.report_type_distribution[2],
            self.report_type_distribution[3],
            self.report_type_distribution[4],
            self.report_type_distribution[5],
            self.days_since_onset_of_symptoms_distribution[-14],
            self.days_since_onset_of_symptoms_distribution[-13],
            self.days_since_onset_of_symptoms_distribution[-12],
            self.days_since_onset_of_symptoms_distribution[-11],
            self.days_since_onset_of_symptoms_distribution[-10],
            self.days_since_onset_of_symptoms_distribution[-9],
            self.days_since_onset_of_symptoms_distribution[-8],
            self.days_since_onset_of_symptoms_distribution[-7],
            self.days_since_onset_of_symptoms_distribution[-6],
            self.days_since_onset_of_symptoms_distribution[-5],
            self.days_since_onset_of_symptoms_distribution[-4],
            self.days_since_onset_of_symptoms_distribution[-3],
            self.days_since_onset_of_symptoms_distribution[-2],
            self.days_since_onset_of_symptoms_distribution[-1],
            self.days_since_onset_of_symptoms_distribution[0],
            self.days_since_onset_of_symptoms_distribution[+1],
            self.days_since_onset_of_symptoms_distribution[+2],
            self.days_since_onset_of_symptoms_distribution[+3],
            self.days_since_onset_of_symptoms_distribution[+4],
            self.days_since_onset_of_symptoms_distribution[+5],
            self.days_since_onset_of_symptoms_distribution[+6],
            self.days_since_onset_of_symptoms_distribution[+7],
            self.days_since_onset_of_symptoms_distribution[+8],
            self.days_since_onset_of_symptoms_distribution[+9],
            self.days_since_onset_of_symptoms_distribution[+10],
            self.days_since_onset_of_symptoms_distribution[+11],
            self.days_since_onset_of_symptoms_distribution[+12],
            self.days_since_onset_of_symptoms_distribution[+13],
            self.days_since_onset_of_symptoms_distribution[+14],
        ])
