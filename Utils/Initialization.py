import os
import shutil
from .Configuration import *


def init_folder():
    if not os.path.exists(DATA_ROOT_PATH):
        print('The main directory of the data will be created.!')
        os.makedirs(DATA_ROOT_PATH)
    for key,value in SUB_DIR.items():
        if not os.path.exists(os.path.join(DATA_ROOT_PATH,value)):
            print(f'The subdir of {key} not found! It will be created.')
            os.makedirs(os.path.join(DATA_ROOT_PATH,value))

def restore_initial_settings():
    user_check = input('Do you want to restore the initial settings? (y/n) ')
    if user_check == 'y':
        shutil.rmtree(DATA_ROOT_PATH)
    else:
        print('Restore Initial Settings Cancelled!')



if __name__ == '__main__':
    restore_initial_settings()
    init_folder()
