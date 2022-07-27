DEBUG = False
SECRET_KEY = "123456"

MONGODB_SETTINGS = {
    "db": "demo",
    "host": "127.0.0.1",
    "port": 27017,
}


class Email():
    MAIL_SERVER = 'smtp.qq.com'   # 使用的邮箱服务器
    MAIL_PORT = 465            # 端口   支持SSL一般为465，默认为25
    MAIL_USE_SSL = True        # 是否支持SSL
    MAIL_USE_TLS = False       # 是否支持TLS
    MAIL_DEFAULT_SENDER = '469453368@qq.com'   # 默认发件人
    MAIL_USERNAME = '469453368@qq.com'   # 用户名
    MAIL_PASSWORD = 'kidktaipsfxmbidi'  # 163邮箱客户端授权码，不是登录密码
    MAIL_SUPPRESS_SEND = 'False'