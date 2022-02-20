import csv
import datetime
import json
import os

from urllib import request
from dateutil import parser

from absl import flags, app
import pandas as pd

FLAGS = flags.FLAGS
flags.DEFINE_string("config_path", None, "Config file path")

flags.DEFINE_string("tmp_path", "/tmp", "Temporary path")
flags.DEFINE_string("output_csv_path", "./test/latest.csv", "Output csv file path")
flags.DEFINE_string("output_json_path", "./test/latest.json", "Output json file path")

# RFC3339
FORMAT_RFC3339 = "%Y-%m-%dT%H:%M:%S.%f%z"

JST = datetime.timezone(datetime.timedelta(hours=9), 'Asia/Tokyo')

#

HEADER1 = [
    None, '医療機関名', '電話番号\n(web予約URL)', '対象者\n（★：小児or妊婦以外対応不可）', None, None, '住所\n区市町村',
    'それ以降の住所', 'コロナ検査方法', None, None,
    '健康\n観察\n（※）', '中和\n抗体薬', '経口\n治療薬',
    '発熱患者等に対する診療・検査対応時間',
    None, None, None, None, None, None, None, None, None, None, None, None, None,
    '対応できる\n外国語', '診療検査日時が祝日の場合', '医療機関名'
]

HEADER2 = [
    None, None, None, '濃厚\n接触者', '小児', '妊婦', None, None, 'PCR', '抗原定量', '抗原定性', None, None, None,
    '月\n（午前）', '月\n（午後）', '火\n（午前）', '火\n（午後）', '水\n（午前）', '水\n（午後）', '木\n（午前）',
    '木\n（午後）', '金\n（午前）', '金\n（午後）', '土\n（午前）', '土\n（午後）', '日\n（午前）', '日\n（午後）', None,
    None, None
]

CHAR_MAP = {
    '\n': '',
    '０': '0',
    '１': '1',
    '２': '2',
    '３': '3',
    '４': '4',
    '５': '5',
    '６': '6',
    '７': '7',
    '８': '8',
    '９': '9',
    'ー': '-',
    '−': '-',
    '—': '-',
    '~': '-',
}


def _convert(string):
    if string is None:
        return None

    result = []
    for c in string:
        if c in CHAR_MAP:
            result.append(CHAR_MAP[c])
        else:
            result.append(c)
    return "".join(result)


def _to_string(val):
    if type(val) == bool:
        return str(val).lower()
    else:
        return str(val)


class ClinicInfo:

    @staticmethod
    def parse_web_url(col):
        col = str(col)

        tokens = col.split("\n")
        for token in tokens:
            if token.startswith("http"):
                return token

        return None

    @staticmethod
    def parse_telephone_number(col):
        col = str(col)

        tokens = col.split("\n")
        for token in tokens:
            if token.startswith("0") or token.startswith("０"):
                return token

        return None

    @staticmethod
    def parse_note(col):
        col = str(col)

        tokens = col.split("\n")
        for token in tokens:
            if token.startswith("0") or token.startswith("０"):
                continue
            if token.startswith("http"):
                continue
            return token

        return ""

    @staticmethod
    def parse_target(col):
        if col == "〇":
            return True, False
        elif col == "★":
            return True, True
        else:
            return False, False

    def parse_bool_or_none(col):
        if col == "〇":
            return True
        elif col == "×":
            return False
        else:
            return None

    @staticmethod
    def parse_time(col):
        if type(col) == str:
            return col.replace("\n", "")
        elif type(col) == datetime.time:
            return str(col)
        elif type(col) == float:
            return None
        else:
            return None

    @staticmethod
    def parse_support_language(col):
        if type(col) == str:
            return col
        elif type(col) == float:
            return None
        else:
            return None

    def __init__(self, row):
        self.name = str(row[1])
        self.note = ""

        self.note += ClinicInfo.parse_note(row[2])

        self.web_url = ClinicInfo.parse_web_url(row[2])
        self.telephone = _convert(ClinicInfo.parse_telephone_number(row[2]))

        self.target_close_contact_person, _ = ClinicInfo.parse_target(row[3])
        self.target_child, self.target_child_limited = ClinicInfo.parse_target(row[4])
        self.target_pregnant, self.target_pregnant_limited = ClinicInfo.parse_target(row[5])

        self.address = row[6] + " " + row[7]

        self.test_pcr = ClinicInfo.parse_bool_or_none(row[8])
        self.test_quantitative_antigen = ClinicInfo.parse_bool_or_none(row[9])  # 抗原定量検査
        self.test_qualitative_antigen = ClinicInfo.parse_bool_or_none(row[10])  # 抗原定性検査

        self.health_observation = ClinicInfo.parse_bool_or_none(row[11])
        self.antibody_treatment = ClinicInfo.parse_bool_or_none(row[12])  # 抗体治療薬・中和抗体薬
        self.covid_antiviral_pill = ClinicInfo.parse_bool_or_none(row[13])  # 経口治療薬

        self.monday_am = _convert(ClinicInfo.parse_time(row[14]))
        self.monday_pm = _convert(ClinicInfo.parse_time(row[15]))
        self.tuesday_am = _convert(ClinicInfo.parse_time(row[16]))
        self.tuesday_pm = _convert(ClinicInfo.parse_time(row[17]))
        self.wednesday_am = _convert(ClinicInfo.parse_time(row[18]))
        self.wednesday_pm = _convert(ClinicInfo.parse_time(row[19]))
        self.thursday_am = _convert(ClinicInfo.parse_time(row[20]))
        self.thursday_pm = _convert(ClinicInfo.parse_time(row[21]))
        self.friday_am = _convert(ClinicInfo.parse_time(row[22]))
        self.friday_pm = _convert(ClinicInfo.parse_time(row[23]))
        self.saturday_am = _convert(ClinicInfo.parse_time(row[24]))
        self.saturday_pm = _convert(ClinicInfo.parse_time(row[25]))
        self.sunday_am = _convert(ClinicInfo.parse_time(row[26]))
        self.sunday_pm = _convert(ClinicInfo.parse_time(row[27]))

        self.support_language = ClinicInfo.parse_support_language(row[28])
        self.open_holiday = str(row[29])

    def write_to_csv(self, csv_writer):
        row = [
            self.name,
            self.telephone, self.web_url,
            self.target_close_contact_person, self.target_child, self.target_pregnant,
            self.target_child_limited, self.target_pregnant_limited,
            self.address,
            self.test_pcr, self.test_quantitative_antigen, self.test_qualitative_antigen,
            self.health_observation, self.antibody_treatment, self.covid_antiviral_pill,
            self.monday_am, self.monday_pm,
            self.tuesday_am, self.tuesday_pm,
            self.wednesday_am, self.wednesday_pm,
            self.thursday_am, self.thursday_pm,
            self.friday_am, self.friday_pm,
            self.saturday_am, self.saturday_pm,
            self.sunday_am, self.sunday_pm,
            self.support_language,
            self.open_holiday,
            self.note,
        ]
        row = list(map(lambda val: _to_string(val) if val is not None else "", row))
        csv_writer.writerow(row)

    def to_dict(self):
        return {
            "name": self.name,
            "address": self.address,
            "contact": {
                "telephone": self.telephone,
                "web_url": self.web_url,
            },
            "target": {
                "close_contact_person": self.target_close_contact_person,
                "child": self.target_child,
                "pregnant": self.target_pregnant,
                "child_limited": self.target_child_limited,
                "pregnant_limited": self.target_pregnant_limited,
            },
            "test": {
                "pcr": self.test_pcr,
                "quantitative_antigen": self.test_quantitative_antigen,
                "qualitative_antigen": self.test_qualitative_antigen
            },
            "health_observation": self.health_observation,
            "antibody_treatment": self.antibody_treatment,
            "covid_antiviral_pill": self.covid_antiviral_pill,
            "office hours": {
                "monday": {
                    "am": {
                        "text": self.monday_am
                    },
                    "pm": {
                        "text": self.monday_pm
                    },
                },
                "tuesday": {
                    "am": {
                        "text": self.tuesday_am
                    },
                    "pm": {
                        "text": self.tuesday_pm
                    },
                },
                "wednesday": {
                    "am": {
                        "text": self.wednesday_am
                    },
                    "pm": {
                        "text": self.wednesday_pm
                    },
                },
                "thursday": {
                    "am": {
                        "text": self.thursday_am
                    },
                    "pm": {
                        "text": self.thursday_pm
                    },
                },
                "friday": {
                    "am": {
                        "text": self.friday_am
                    },
                    "pm": {
                        "text": self.friday_pm
                    },
                },
                "saturday": {
                    "am": {
                        "text": self.saturday_am
                    },
                    "pm": {
                        "text": self.saturday_pm
                    },
                },
                "sunday": {
                    "am": {
                        "text": self.sunday_am
                    },
                    "pm": {
                        "text": self.sunday_pm
                    },
                },
                "holiday": self.open_holiday,
            },
            "support_languages": [
                self.support_language,
            ],
            "note": self.note,
        }


def _download_opendata(url):
    name = os.path.basename(url)
    file_path = os.path.join(FLAGS.tmp_path, name)

    req = request.Request(url)

    with request.urlopen(req) as res:
        with open(file_path, 'wb') as fp:
            fp.write(res.read())

        last_modified = parser.parse(res.headers['Last-Modified'])
        return last_modified, file_path


def _is_validate(row, header):
    for index, col in enumerate(row):
        header_col = header[index]
        if header_col is None:
            continue

        if col != header_col:
            return False
    return True


def _parse(file_path):
    df = pd.read_excel(file_path, sheet_name=0)

    # validation
    validation_header1 = _is_validate(df.values[1], HEADER1)
    validation_header2 = _is_validate(df.values[2], HEADER2)

    if not validation_header1 and not validation_header2:
        print("Validation failed")
        return False

    clinic_infos = list()

    for index, row in enumerate(df.values[3:]):
        info = ClinicInfo(row)
        clinic_infos.append(info)

    return clinic_infos


def _write_to_csv_header(writer):
    writer.writerow([
        "医療機関名",
        "電話番号", "Web予約URL",
        "対象者（濃厚接触者）", "対象者（小児）", "対象者（妊婦）",
        "対象者は小児に限定", "対象者は妊婦に限定",
        "所在地",
        "検査方法（PCR）", "検査方法（抗原定量）", "検査方法（抗原定性）",
        "健康観察", "中和抗体薬", "経口治療薬",
        "発熱患者等に対する診療・検査対応時間（月曜日・午前）", "発熱患者等に対する診療・検査対応時間（月曜日・午後）",
        "発熱患者等に対する診療・検査対応時間（火曜日・午前）", "発熱患者等に対する診療・検査対応時間（火曜日・午後）",
        "発熱患者等に対する診療・検査対応時間（水曜日・午前）", "発熱患者等に対する診療・検査対応時間（水曜日・午後）",
        "発熱患者等に対する診療・検査対応時間（木曜日・午前）", "発熱患者等に対する診療・検査対応時間（木曜日・午後）",
        "発熱患者等に対する診療・検査対応時間（金曜日・午前）", "発熱患者等に対する診療・検査対応時間（金曜日・午後）",
        "発熱患者等に対する診療・検査対応時間（土曜日・午前）", "発熱患者等に対する診療・検査対応時間（土曜日・午後）",
        "発熱患者等に対する診療・検査対応時間（日曜日・午前）", "発熱患者等に対する診療・検査対応時間（日曜日・午後）",
        "対応できる外国語",
        "診療検査日が祝日の場合",
        "備考",
    ])


def _save_as_csv(clinic_infos, output_path):
    with open(output_path, mode='w') as fp:
        writer = csv.writer(fp)
        _write_to_csv_header(writer)
        for info in clinic_infos:
            info.write_to_csv(writer)


def _save_as_json(clinic_infos, output_path, last_modified):
    clinic_infos_dict_list = list(map(lambda clinic_info: clinic_info.to_dict(), clinic_infos))
    json_obj = {
        "clinic_list": clinic_infos_dict_list,
        "last_modified": last_modified.strftime(FORMAT_RFC3339),
    }

    text = json.dumps(json_obj, ensure_ascii=False, indent=4)
    print(text)

    with open(output_path, mode='w') as fp:
        json.dump(json_obj, fp, ensure_ascii=False)


def _load_endpoint_url(config_path):
    with open(config_path, mode='r') as fp:
        json_obj = json.load(fp)
        return json_obj["tokyo"]["url"]


def main(argv):
    del argv  # Unused.

    assert FLAGS.config_path is not None, "Parameter --config_path must be set."
    assert os.path.exists(FLAGS.config_path), FLAGS.config_path + " is not exist."

    url = _load_endpoint_url(FLAGS.config_path)

    os.makedirs(os.path.dirname(FLAGS.output_csv_path), exist_ok=True)
    os.makedirs(os.path.dirname(FLAGS.output_json_path), exist_ok=True)

    last_modified, file_path = _download_opendata(url)

    try:
        clinic_infos = _parse(file_path)
        _save_as_csv(clinic_infos, FLAGS.output_csv_path)
        _save_as_json(clinic_infos, FLAGS.output_json_path, last_modified)
    finally:
        pass


if __name__ == '__main__':
    app.run(main)
