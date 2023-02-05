import json
import os.path
import os

def get_settings():
    settings_file_path = os.path.join(os.path.dirname(__file__), "settings.json")
    settings_file = open(settings_file_path, "r")
    data = json.load(settings_file)
    return json.dumps(data)

if __name__ == "__main__":
    data = get_settings()
    print(data)