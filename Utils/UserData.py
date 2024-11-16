import os

from sqlalchemy.testing.pickleable import User

from DataClass import *
from Utils.Configuration import *

def save_all_users(users_data:list): # 将 users_data 保存在 user_data.txt 文件中
    save_path = str(os.path.join(DATA_ROOT_PATH, SUB_DIR['USER_DIR']))
    with open(os.path.join(save_path, TEXT_FILE['USER_FILE']), 'w') as f:
        for u in users_data:
            f.write(f'{u}\n')

def load_all_users(): # 从 user_data.txt 文件中读取 user 数据
    user_data_path = os.path.join(DATA_ROOT_PATH, SUB_DIR['USER_DIR'], TEXT_FILE['USER_FILE'])
    users_list = []
    with open(user_data_path, 'r') as f:
        lines = f.readlines()
    for line in lines:
        print(line)
        user_pre_data = line.replace('\n', '').replace('\t', ' ').split(' ')
        print(len(user_pre_data))
        # print(user_pre_data)
        # print(user_pre_data[5])
        emails = eval(user_pre_data[5])
        if user_pre_data[3] == '0':
            single_user = Admin(user_pre_data[0], user_pre_data[1], int(user_pre_data[4]), user_pre_data[2], int(user_pre_data[3]))
            for email in emails:
                single_user.add_email(email)
            users_list.append(single_user)
        elif user_pre_data[3] == '2':
            single_user = CommonUser(user_pre_data[0], user_pre_data[1], int(user_pre_data[4]), user_pre_data[2],
                                int(user_pre_data[3]))
            for email in emails:
                single_user.add_email(email)
            users_list.append(single_user)
    return users_list

def register_new_user(uid):
    print('-' * 42 + 'Register New User' + '-' * 41)
    name = input('Please Input Your Username:')
    age = input('Please Input Your Age(Optional): ')
    if age == '':
        age = 0
    password1 = input('Please Input Your Password (Required): ')
    password2 = input('Please Confirm Your Password (Required): ')
    if password1 != password2:
        print('Passwords do not match!')
        return
    new_user = CommonUser(uid, name, int(age), password1)
    temp_email = input("Please Enter Your Email Address(Optional): ")
    while temp_email != '':
        new_user.add_email(temp_email)
        temp_email = input("Please Enter Your Email Address(Optional): ")
    print('User Registered!')
    print('-' * 100)
    return new_user

if __name__ == '__main__':
    user = register_new_user('00001')
    print(user)