from DataClass.UserBase import Userbase


class Admin(Userbase):
    def __init__(self, uid, username, age, email, password='00000000', permission_level=0):
        super().__init__(uid, username, age, email, password, permission_level)


    def __str__(self):
        return f'{self.uid} {self.username} {self.password} {self.permission_level} {self.age} {self.emails}'