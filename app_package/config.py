import os
from pb_config import ConfigLocal, ConfigDev, ConfigProd

match os.environ.get('FLASK_CONFIG_TYPE'):
    case 'dev':
        config = ConfigDev()
        print('- PhotosBackupAPI/app_pacakge/config: Development')
    case 'prod':
        config = ConfigProd()
        print('- PhotosBackupAPI/app_pacakge/config: Production')
    case _:
        config = ConfigLocal()
        print('- PhotosBackupAPI/app_pacakge/config: Local')