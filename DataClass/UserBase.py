class Userbase(object):
    def __init__(self, uid:str, username:str, age:int, password:str ='00000000', permission_level:int =-1):
        self.uid = uid
        self.username = username
        self.age = age
        self.password = password
        self.emails = []
        self.permission_level = permission_level



    def __str__(self):
        return f'{self.uid}\t{self.username}\t\t\t{self.password}\t{self.permission_level}\t\t\t\t\t{self.age}\t\t\t{self.emails}'

    def add_email(self, email:str):
        self.emails.append(email)

    def set_password(self, password:str):
        self.password = password


