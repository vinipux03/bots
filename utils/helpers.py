# utils/helpers.py

import json

def load_json_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_user_gender_form(gender):
    return "дорогой" if gender == "male" else "дорогая"
