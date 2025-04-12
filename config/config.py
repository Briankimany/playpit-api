
import os
from pathlib import Path
import json

current_location = os.path.abspath('.')
config_file = Path("config.json")

if not config_file.exists():
    current_location = os.path.abspath('.')
    home_dir =  Path(current_location).home()

    CONTENT_LOCATION = input("Where to place CONTENT folder: ")
    if CONTENT_LOCATION == '':
        CONTENT_LOCATION=  home_dir /'APP-DATA'
    else:
        CONTENT_LOCATION = Path(CONTENT_LOCATION)/'APP-DATA'


    DATABASE_LOCATION = CONTENT_LOCATION / "databasev1.db"
    USER_DB_LOCATION = CONTENT_LOCATION / "users.db"
    SECURE_UTILS_LOCATION = CONTENT_LOCATION / "secure_utils.pkl"

    UPLOAD_DIR = CONTENT_LOCATION / 'UPLOADS'
    UPLOAD_DIR.mkdir(parents=True , exist_ok = True)
    LOG_DIR = CONTENT_LOCATION / "LOGS"

    ENV_LOCATION = CONTENT_LOCATION / '.env'
    DATA_BASE_FILE_TYPES = [['.mp4' , '.mkv','.avi'] ,
                                        ['.zip' , '.tar' , '.nfo' , '.url' , '.iso' , '.torrent' , '.bin' , '.exe' , '.url' , '.bat']]

    DISPLAY_NO_IMAGE_CONTENT = True

    PROFILES_DIR = CONTENT_LOCATION / 'PROFILE_PICS'
    PROFILES_DIR.mkdir(parents = True , exist_ok = True)
    LOG_DIR.mkdir(parents=True , exist_ok=True)

    REMOTE_LINK = "https://h27iwn67fk4s.connect.remote.it/series"

    TIME_LIMIT = 120

    data = {'CONTENT_LOCATION':str(CONTENT_LOCATION),
            'DATABASE_LOCATION':str(DATABASE_LOCATION),
            'USER_DB_LOCATION':str(USER_DB_LOCATION),
            'UPLOAD_DIR':str(UPLOAD_DIR),
            'ENV_LOCATION':str(ENV_LOCATION),
            'DATA_BASE_FILE_TYPES':DATA_BASE_FILE_TYPES,
            'DISPLAY_NO_IMAGE_CONTENT':DISPLAY_NO_IMAGE_CONTENT,
            'PROFILES_DIR':str(PROFILES_DIR),
            'REMOTE_LINK':REMOTE_LINK,
            'TIME_LIMIT':TIME_LIMIT ,
            "VERIFICATION_SERVER_ADDRES":"http://10.0.0.1:5006/pay",
            "SECURE_UTILS_LOCATION":str(SECURE_UTILS_LOCATION.absolute()),
            "LOG_DIR":str(LOG_DIR)}

    with open(config_file , 'w') as file:
        json.dump(data , file , indent=0)


class ConfigClass:
    def __init__(self) -> None:
        with open(config_file , 'r') as file:
            data = json.load(file)
        for key , value in data.items():
            if key  not in  ('DATA_BASE_FILE_TYPES' ,'DISPLAY_NO_IMAGE_CONTENT','REMOTE_LINK' ,'TIME_LIMIT' ,
                             'VERIFICATION_SERVER_ADDRES','INTASEND_API_ADDRESS','DELAYED_PAYMENT_ADDRESS'):
                value = Path(value)
            setattr( self ,key , value)

