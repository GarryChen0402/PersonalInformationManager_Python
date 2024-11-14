class Userbase(object):
    def __init__(self, uid, username, age, email, password='00000000', permission_level=-1):
        self.uid = uid
        self.username = username
        self.age = age
        self.password = password
        self.emails = []
        self.emails.append(email)
        self.permission_level = permission_level