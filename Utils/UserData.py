import os
from DataClass.Admin import *
from Configuration import *

def save_all_users(users:list):
    save_path = str(os.path.join(DATA_ROOT_PATH, SUB_DIR['USER_DIR']))
    with open(os.path.join(save_path, 'user_data.txt'), 'w') as f:
        for user in users:
            f.write(f'{user}\n')


if __name__ == '__main__':
    # a =
    gyc = Admin(0,'gyc', 18, 'gychen0402@foxmail.com')
    print(gyc)
    save_all_users([gyc])