"""Constants of the Pulsar nixie clock integration."""

from datetime import timedelta

DOMAIN = "pulsar_nixie"
MANUFACTURER = "Pulsar"
MODEL = "Nixie clock"

UPDATE_INTERVAL = timedelta(seconds=30)

# The POSIX time zones the clock offers, with the labels of its configuration page
TIME_ZONES: dict[str, str] = {
    "GMT10": "(GMT-10:00) Hawaii",
    "AKST9AKDT,M3.2.0,M11.1.0": "(GMT-09:00) Alaska",
    "GMT9": "(GMT-09:00)",
    "PST8PDT,M3.2.0,M11.1.0": "(GMT-08:00) Los Angeles, Vancouver",
    "GMT8": "(GMT-08:00)",
    "MST7": "(GMT-07:00) Arizona",
    "MST7MDT,M3.2.0,M11.1.0": "(GMT-07:00) Denver",
    "CST6": "(GMT-06:00) Guadalajara, Mexico City, Monterrey, Saskatchewan",
    "CST6CDT,M3.2.0,M11.1.0": "(GMT-06:00) Chicago, Winnipeg",
    "EST5EDT,M3.2.0,M11.1.0": "(GMT-05:00) New York, Indiana (East)",
    "AST4ADT,M3.2.0,M11.1.0": "(GMT-04:00) Atlantic Time (Canada)",
    "GMT3": "(GMT-03:00) Buenos Aires, Georgetown",
    "GMT2": "(GMT-02:00)",
    "GMT1": "(GMT-01:00)",
    "GMT0": "(GMT) Greenwich Mean Time",
    "GMT0BST,M3.5.0/1,M10.5.0": "(GMT) Dublin, Edinburgh, Lisbon, London",
    "CET-1CEST,M3.5.0,M10.5.0/3": "(GMT+01:00) Berlin, Copenhagen, Paris, Prague, Rome",
    "EET-2EEST,M3.5.0/3,M10.5.0/4": "(GMT+02:00) Athens, Vilnius, Bucharest, Sofia",
    "IST-2IDT,M3.4.4/26,M10.5.0": "(GMT+02:00) Jerusalem",
    "GMT-3": "(GMT+03:00)",
    "GMT-4": "(GMT+04:00) Baku, Tbilisi, Yerevan",
    "GMT-5": "(GMT+05:00)",
    "GMT-6": "(GMT+06:00)",
    "GMT-7": "(GMT+07:00)",
    "CST-8": "(GMT+08:00) Shanghai, Beijing",
    "JST-9": "(GMT+09:00) Tokyo",
    "KST-9": "(GMT+09:00) Seoul",
    "ACST-9:30ACDT,M10.1.0,M4.1.0/3": "(GMT+09:30) Adelaide",
    "AEST-10AEDT,M10.1.0,M4.1.0/3": "(GMT+10:00) Canberra, Melbourne, Sydney",
    "AEST-10": "(GMT+10:00) Brisbane",
}
