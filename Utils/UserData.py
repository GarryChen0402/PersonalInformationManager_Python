import os
from DataClass.Admin import *
from .Configuration import *

def save_all_users(users_data:list): # 将 users_data 保存在 user_data.txt 文件中
    save_path = str(os.path.join(DATA_ROOT_PATH, SUB_DIR['USER_DIR']))
    with open(os.path.join(save_path, TEXT_FILE['USER_FILE']), 'w') as f:
        for u in users_data:
            f.write(f'{u}\n')

def load_all_users(): # 从 user_data.txt 文件中读取 user 数据
    user_data_path = os.path.join(DATA_ROOT_PATH, SUB_DIR['USER_DIR'], TEXT_FILE['USER_FILE'])
    users_data = []
    with open(user_data_path, 'r') as f:
        lines = f.readlines()
    for line in lines:
        # print(line)
        user_pre_data = line.replace('\n', '').split('\t')
        # print(user_pre_data)
        emails = eval(user_pre_data[5])
        if user_pre_data[3] == '0':
            single_user = Admin(user_pre_data[0], user_pre_data[1], int(user_pre_data[4]), user_pre_data[2], int(user_pre_data[3]))
            for email in emails:
                single_user.add_email(email)
            users_data.append(single_user)
    return users_data

if __name__ == '__main__':
    users = load_all_users()
    for user in users:
        print(type(user))