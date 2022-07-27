import os
from flask import Flask, request, render_template, Response, jsonify, redirect, url_for
from face_train import Dataset, Model
import cv2
import tensorflow as tf
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_mongoengine import MongoEngine
from flask_paginate import Pagination, get_page_parameter
import json
from models import *
from tensorflow.python.keras.backend import set_session
from createfold import CreateFolder
from bson import ObjectId
import re
from flask_script import Manager, Shell
from flask_mail import Mail, Message
from threading import Thread
import random


app = Flask(__name__, template_folder="templates", static_folder="static")

# 导入模块
session = tf.Session()
graph = tf.get_default_graph()
set_session(session)
model = Model()
model.load_model(file_path='./model/aggregate.face.model.h5')

# 导入登录配置
app.config.from_object("config")

loginmanager = LoginManager(app)
loginmanager.session_protection = "strong"
loginmanager.login_view = "login"
loginmanager.init_app(app)

db = MongoEngine(app)


@loginmanager.user_loader
def get_user(user_id):
    return User.objects(id=user_id).first()


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


@app.route("/")
@login_required
def index():
    if current_user.nickname == "manager":
        return render_template("index_manager.html")
    else:
        return render_template("index.html")


@app.route("/index_manager")
@login_required
def index_manage():
    if current_user.username == "0000000000":
        return render_template("index_manager.html")
    else:
        return render_template("index.html")


@app.route("/sign_in_log_manager")
@login_required
def sign_in_log_manager():
    return render_template("sign_in_log_manager.html")


@app.route("/to_update_manager")
@login_required
def to_update_manager():
    username = request.args.get('id')
    return render_template("update_manager.html", username=username)


# 注册功能实现
@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    elif request.method == "POST":
        err_msg = {
            "result": "NO"
        }
        param = json.loads(request.data.decode("utf-8"))
        gender = param.get("gender", "")
        username = param.get("username", "")
        password = param.get("password", "")
        nickname = param.get("nickname", "")
        email = param.get("email", "")
        age = param.get("age", "")
        phone = param.get("phone", "")
        birthday = param.get("birthday", "")
        if not username:
            err_msg["msg"] = "缺少账号"
            return jsonify(err_msg)
        if len(username) != 9:
            err_msg["msg"] = "账号长度需为9位数"
            return jsonify(err_msg)
        if not password:
            err_msg["msg"] = "缺少密码"
            return jsonify(err_msg)
        a = re.compile(r'[0-9a-zA-Z]{6,20}')
        if a.fullmatch(password) is None:
            err_msg["msg"] = "密码只能包含数字和字母，切为6~20位数"
            return jsonify(err_msg)
        if re.match("^(?:(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])).*$", password) is None:
            err_msg["msg"] = "密码必须包含大小写字母和数字"
            return jsonify(err_msg)
        if not nickname:
            err_msg["msg"] = "缺少用户名"
            return jsonify(err_msg)
        if len(nickname) > 10:
            err_msg["msg"] = "用户名长度要小于10"
            return jsonify(err_msg)
        if not email:
            err_msg["msg"] = "缺少邮箱"
            return jsonify(err_msg)
        if not age:
            err_msg["msg"] = "缺少年龄"
            return jsonify(err_msg)
        if not phone:
            err_msg["msg"] = "缺少用手机号"
            return jsonify(err_msg)
        if len(phone) != 11:
            err_msg["msg"] = "无效手机号"
            return jsonify(err_msg)
        user = User.objects(username=username)
        if not user:
            user = User(gender=gender, username=username, nickname=nickname, email=email, age=age, phone=phone,
                        birthday=birthday, avatar="")
            user.hash_password(password)
            return jsonify({
                "result": "OK"
            })
        else:
            err_msg["msg"] = "用户已经注册"
            return jsonify(err_msg)


# 注册功能实现(end)


# 登录功能实现
@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    elif request.method == "POST":
        err_msg = {
            "result": "NO"
        }
        param = json.loads(request.data.decode("utf-8"))
        username = param.get("username", "")
        password = param.get("password", "")
        if not username:
            err_msg["msg"] = "缺少用户名"
            return jsonify(err_msg)
        if not password:
            err_msg["msg"] = "缺少密码"
            return jsonify(err_msg)
        user = User.objects(username=username).first()
        user_manager = User_Manager.objects(username=username).first()
        if not user:
            if not user_manager:
                err_msg["msg"] = "用户尚未注册"
                return jsonify(err_msg)
        if user:
            if not user.verify_password(password):
                err_msg["msg"] = "密码错误"
                return jsonify(err_msg)
        else:
            if not user_manager.verify_password(password):
                err_msg["msg"] = "密码错误"
                return jsonify(err_msg)
        if user.username == "0000000000":
            login_user(user)
            return jsonify({
                "result": "OK",
                "next_url": "/index_manager"
            })
        else:
            login_user(user)
            return jsonify({
                "result": "OK",
                "next_url": "/"
            })


# 登录功能实现(end)


# 人脸收集视频流
def face_gain(name):
    path_name = './data/' + name
    catch_pic_num = 200
    CreateFolder(path_name)
    camera = cv2.VideoCapture(0)
    # CreateFolder(path_name)
    # 告诉OpenCV使用人脸识别分类器
    classfier = cv2.CascadeClassifier("./haarcascade/haarcascade_frontalface_alt2.xml")

    # 识别出人脸后要画的边框的颜色，RGB格式
    color = (0, 255, 0)

    num = 0
    while True:
        # Capture frame-by-frame
        success, frame = camera.read()  # read the camera frame
        if not success:
            break
        else:
            grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # 将当前桢图像转换成灰度图像

            # 人脸检测，1.2和2分别为图片缩放比例和需要检测的有效点数
            faceRects = classfier.detectMultiScale(grey, scaleFactor=1.2, minNeighbors=2, minSize=(32, 32))
            if len(faceRects) > 0:  # 大于0则检测到人脸
                for faceRect in faceRects:  # 单独框出每一张人脸
                    x, y, w, h = faceRect
                    if w > 200:

                        # 将当前帧保存为图片
                        img_name = '%s\%d.jpg' % (path_name, num)

                        # image = frame[y - 10: y + h + 10, x - 10: x + w + 10]
                        image = grey[y:y + h, x:x + w]  # 保存灰度人脸图
                        cv2.imwrite(img_name, image)

                        num += 1
                        if num > catch_pic_num:  # 如果超过指定最大保存数量退出循环
                            break

                        # 画出矩形框的时候稍微比识别的脸大一圈
                        cv2.rectangle(frame, (x - 10, y - 10), (x + w + 10, y + h + 10), color, 2)

                        # 显示当前捕捉到了多少人脸图片了，这样站在那里被拍摄时心里有个数，不用两眼一抹黑傻等着
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        cv2.putText(frame, 'num:%d' % num, (x + 30, y + 30), font, 1, (255, 0, 255), 4)

            # 超过指定最大保存数量结束程序
            if num > catch_pic_num:
                break
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result
    cv2.destroyAllWindows()


@app.route('/video_feed2')
@login_required
def video_feed2():
    return Response(face_gain(current_user.nickname), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/put_data')
@login_required
def index2():
    return render_template('face_gain_main.html')


# 人脸收集视频流(end)


# @app.route("/put_data", methods=["GET", "POST"])
# @login_required
# def gain_face():
#     if request.method == "POST":
#         imgdata = request.form.get("myimg")
#         num = request.form.get("num")
#         name = request.form.get("name")
#         # 判断是否存在文件夹，不存在则创建一个
#         if not os.path.exists("./data/" + name):
#             os.mkdir("./data/" + name)
#
#         img_base64_data = base64.b64decode(imgdata)
#         # # 将img_base64_data写入.jpg文件中
#         with open("./data/" + name + "/" + num + ".jpg", "wb") as f:
#             f.write(img_base64_data)
#
#         classfier = cv2.CascadeClassifier("D:\\Users\\lhk\\PycharmProjects\\Face_recongnize\\haarcascade"
#                                           "\\haarcascade_frontalface_alt2.xml")
#
#         frame = cv2.imread("./data/" + name + "/" + num + ".jpg")
#         grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # 将当前桢图像转换成灰度图像
#         faceRects = classfier.detectMultiScale(grey, scaleFactor=1.2, minNeighbors=2, minSize=(32, 32))
#         # print(faceRects)
#         if len(faceRects) > 0:  # 大于0则检测到人脸
#             for faceRect in faceRects:  # 单独框出每一张人脸
#                 x, y, w, h = faceRect
#                 if w >= 170:
#                     # 保存当前图片
#                     img_name = '%s\%d.jpg' % (
#                         "D:\\Users\\lhk\\PycharmProjects\\Face_recongnize\\data\\" + name, int(num))
#
#                     # image = frame[y - 10: y + h + 10, x - 10: x + w + 10]
#                     image = grey[y:y + h, x:x + w]  # 保存灰度人脸图
#                     cv2.imwrite(img_name, image)
#                     print(num, "图片存储成功")
#                 else:
#                     os.remove("./data/" + name + "/" + num + ".jpg")
#                     print("请靠近摄像头重新拍照")
#                     break
#
#     return render_template("face_gain.html")


# 视频流实现函数
def gen_frames():
    camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cascade_path = "./haarcascade/haarcascade_frontalface_alt2.xml"
    color = (0, 255, 0)
    face_name = ''
    while True:
        # 读取视频的每一帧
        success, frame = camera.read()
        if not success:
            camera.release()
            cv2.destroyAllWindows()
            break
        else:
            frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            cascade = cv2.CascadeClassifier(cascade_path)
            faceRects = cascade.detectMultiScale(frame_gray, scaleFactor=1.2, minNeighbors=2, minSize=(32, 32))
            if len(faceRects) > 0:
                for faceRect in faceRects:
                    x, y, w, h = faceRect
                    # 截取脸部图像提交给模型识别这是谁
                    image = frame[y: y + h, x: x + w]
                    # 解决flask调用模块预测错误
                    with graph.as_default():
                        set_session(session)
                        faceID = model.face_predict(image)
                    cv2.rectangle(frame, (x - 10, y - 10), (x + w + 10, y + h + 10), color, thickness=2)
                    # face_id判断
                    for i in range(len(os.listdir('./data/'))):
                        # print("已录人名：" + str(os.listdir('./data/')))
                        if i == faceID:
                            # 文字提示是谁
                            cv2.putText(frame, os.listdir('./data/')[i],
                                        (x + 30, y + 30),  # 坐标
                                        cv2.FONT_HERSHEY_SIMPLEX,  # 字体
                                        1,  # 字号
                                        (255, 0, 255),  # 颜色
                                        2)  # 字的线宽
                            face_name = str(os.listdir('./data/')[i])
            ret, buffer = cv2.imencode('.jpg', frame)
            # 将该帧格式化为响应块，内容类型为image/jpeg
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # 逐帧显示并显示结果
            yield face_name
    cv2.destroyAllWindows()


@app.route('/video_feed')
@login_required
def video_feed():
    # 视频流路由。将其放在img标签的src属性中

    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/face_recognize')
@login_required
def face_recongnize():
    """视频流页面"""
    gen = gen_frames()
    next(gen)
    name = next(gen)
    if name == '':
        return render_template('face_recognition.html',
                               user="face recognize defeat ,please refresh and try again",
                               flag=0)
    else:
        return render_template('face_recognition.html',
                               user=name,
                               text="face recognize successfully",
                               flag=1)
# 视频流实现函数(end)


@app.route('/backtoindex')
def back_to_index():
    return render_template('index.html')


# index中iframe跳转
@app.route("/home")
@login_required
def home():
    return render_template("home.html")


@app.route("/personal_info")
@login_required
def personal_info():
    return render_template("personal_info.html")


@app.route("/get_sign_in_log", methods=["POST", "GET"])
@login_required
def get_sign_in_log():
    if request.method == "POST":
        time = Time.objects(name=current_user.username)
        return jsonify(time)


@app.route("/sign_in_log")
@login_required
def sign_in_log():
    return render_template("sign_in_log.html")


@app.route("/manage_users")
@login_required
def manage_users():
    return render_template("manage_users.html")


# index中iframe跳转（end）


# 更新用户信息
# @app.route("/update_name", methods=["POST", "GET"])
# @login_required
# def update_name():
#     if request.method == "POST":
#         param = json.loads(request.data.decode("utf-8"))
#         new_name = param.get("new_name", "")
#         user = User.objects(nickname=current_user.nickname).first()
#         user.nickname = new_name
#         user.save()
#         return jsonify({"result": "OK"})


@app.route("/update_birthday", methods=["POST", "GET"])
@login_required
def update_birthday():
    if request.method == "POST":
        param = json.loads(request.data.decode("utf-8"))
        new_birthday = param.get("new_birthday", "")
        username = param.get("username", "")
        user = User.objects(username=username).first()
        user.birthday = new_birthday
        user.save()
        return jsonify({"result": "OK"})


@app.route("/update_gender", methods=["POST", "GET"])
@login_required
def update_gender():
    if request.method == "POST":
        param = json.loads(request.data.decode("utf-8"))
        new_gender = param.get("new_gender", "")
        username = param.get("username", "")
        user = User.objects(username=username).first()
        user.gender = new_gender
        user.save()
        return jsonify({"result": "OK"})


@app.route("/update_age", methods=["POST", "GET"])
@login_required
def update_age():
    if request.method == "POST":
        param = json.loads(request.data.decode("utf-8"))
        new_age = param.get("new_age", "")
        username = param.get("username", "")
        user = User.objects(username=username).first()
        user.age = new_age
        user.save()
        return jsonify({"result": "OK"})


# app.config['MAIL_SUPPRESS_SEND'] = False    # 发送邮件，为True则不发送
# app.config['MAIL_SERVER'] = 'smtp.qq.com'   # 邮箱服务器
# app.config['MAIL_PORT'] = 465               # 端口
# app.config['MAIL_USE_SSL'] = True           # 重要，qq邮箱需要使用SSL
# app.config['MAIL_USE_TLS'] = False          # 不需要使用TLS
# app.config['MAIL_USERNAME'] = '469453368@qq.com'  # 填邮箱
# app.config['MAIL_PASSWORD'] = 'kidktaipsfxmbidi'      # 填授权码
# app.config['MAIL_DEFAULT_SENDER'] = '469453368@qq.com'  # 填邮箱，默认发送者
manager = Manager(app)
mail = Mail(app)


def generate_verification_code():
    code_list = []
    for i in range(10):  # 0-9 number
        code_list.append(str(i))
    for i in range(65, 91):  # A-Z
        code_list.append(chr(i))
    for i in range(97, 123):  # a-z
        code_list.append(chr(i))
    myslice = random.sample(code_list, 6)
    verification_code = ''.join(myslice)  # list to string
    return verification_code


# 异步发送邮件
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


code = ''


@app.route('/send_code', methods=["POST", "GET"])
@login_required
def send_code():
    code = generate_verification_code()
    msg = Message(subject='验证码',
                  sender="",  # 需要使用默认发送者则不用填
                  recipients=[current_user.email],
                  body='您的验证码是：%s' % code
                  )
    # 邮件内容会以文本和html两种格式呈现，而你能看到哪种格式取决于你的邮件客户端。
    thread = Thread(target=send_async_email, args=[app, msg])
    thread.start()
    return jsonify(code)


@app.route("/update_password", methods=["POST", "GET"])
@login_required
def update_password():
    if request.method == "POST":
        param = json.loads(request.data.decode("utf-8"))
        new_password = param.get("new_password", "")
        username = param.get("username", "")
        sendCode = param.get("sendCode", "")
        againPassword = param.get("againPassword", "")
        if sendCode != code:
            return jsonify({"result": "Code is error"})
        a = re.compile(r'[0-9a-zA-Z]{6,20}')
        if a.fullmatch(new_password) is None:
            return jsonify({"result": "密码只能包含英文和数字"})
        if re.match("^(?:(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])).*$", new_password) is None:
            return jsonify({"result": "密码必须包含大小写字母和数字"})
        if new_password != againPassword:
            return jsonify({"result": "两次输入密码不一致"})
        user = User.objects(username=username).first()
        user.hash_password(new_password)
        return jsonify({"result": "OK"})


@app.route("/update_email", methods=["POST", "GET"])
@login_required
def update_email():
    if request.method == "POST":
        param = json.loads(request.data.decode("utf-8"))
        new_email = param.get("new_email", "")
        username = param.get("username", "")
        user = User.objects(username=username).first()
        user.email = new_email
        user.save()
        return jsonify({"result": "OK"})


@app.route("/update_phone", methods=["POST", "GET"])
@login_required
def update_phone():
    if request.method == "POST":
        param = json.loads(request.data.decode("utf-8"))
        new_phone = param.get("new_phone", "")
        username = param.get("username", "")
        if len(new_phone) != 11:
            return jsonify({"result": "电话号码无效"})
        user = User.objects(username=username).first()
        user.phone = new_phone
        user.save()
        return jsonify({"result": "OK"})


@app.route("/update_avatar", methods=["POST", "GET"])
@login_required
def update_avatar():
    if request.method == "POST":
        param = json.loads(request.data.decode("utf-8"))
        new_avatar = param.get("new_avatar", "")
        username = param.get("username", "")
        user = User.objects(username=username).first()
        user.avatar = new_avatar
        user.save()
        return jsonify({"result": "OK"})


# 更新用户信息(end)


# 签到获取时间模块并保存
@app.route("/sign_in", methods=["POST", "GET"])
@login_required
def sign_in():
    if request.method == "GET":
        return render_template("index.html")
    elif request.method == "POST":
        err_msg = {
            "result": "NO"
        }
        time_date = json.loads(request.data.decode("utf-8"))
        name = time_date.get("name", "")
        year = str(time_date.get("year", ""))
        month = str(time_date.get("month", ""))
        date = str(time_date.get("date", ""))
        hour = str(time_date.get("hour", ""))
        minute = str(time_date.get("minute", ""))
        second = str(time_date.get("second", ""))
        time = Time.objects(name=name, year=year, month=month, date=date)
        if name == current_user.nickname:
            if not time:
                time = Time(name=current_user.username,
                            year=year,
                            month=month,
                            date=date,
                            hour=hour,
                            minute=minute,
                            second=second,
                            nickname=current_user.nickname)
                time.save()
                return jsonify({"result": "OK"})
            else:
                err_msg["msg"] = "You had sign in today"
                return jsonify(err_msg)
        else:
            err_msg["msg"] = "The face does not match the user"
            return jsonify(err_msg)


# 签到获取时间模块并保存(end)


@app.route("/get_users", methods=["POST", "GET"])
@login_required
def get_user():
    users = User.objects.all()
    return jsonify(users)


@app.route("/delete_manager", methods=["POST", "GET"])
@login_required
def delete_manager():
    if request.method == "GET":
        return render_template("index_manager.html")
    elif request.method == "POST":
        date = json.loads(request.data.decode("utf-8"))
        username = date.get("username", "")
        user = User.objects(username=username).first()
        time = Time.objects(name=username).all()
        user_comment = UserComment.objects(name=username).all()
        user_comment.delete()
        time.delete()
        user.delete()
        return jsonify({"result": "OK"})


@app.route("/update_manager", methods=["POST", "GET"])
@login_required
def update_manager():
    if request.method == "GET":
        return render_template("index_manager.html")
    elif request.method == "POST":
        date = json.loads(request.data.decode("utf-8"))
        username = date.get("username", "")
        user = User.objects(username=username).first()
        return render_template("update_manager.html", username=user.username)


@app.route("/get_user_info", methods=["POST", "GET"])
@login_required
def get_user_info():
    if request.method == "GET":
        return render_template("home.html")
    elif request.method == "POST":
        date = json.loads(request.data.decode("utf-8"))
        username = date.get("username", "")
        user = User.objects(username=username).first()
        return jsonify(user)


@app.route("/check_sign_in", methods=["POST", "GET"])
@login_required
def check_sign_in():
    if request.method == "POST":
        time = json.loads(request.data.decode("utf-8"))
        year = str(time.get("year", ""))
        month = str(time.get("month", ""))
        date = str(time.get("date", ""))
        userSignLog = Time.objects(year=year, month=month, date=date).all()
        userList = []
        for i in range(len(userSignLog)):
            userList.append(userSignLog[i].name)
        user = User.objects(username__nin=userList).all()
        return jsonify(
            user=user,
            userSignLog=userSignLog
        )


@app.route('/user_comment')
@login_required
def user_comment():
    return render_template("user_comment.html")


@app.route('/get_data', methods=['POST'])
@login_required
def get_data():
    comment = UserComment.objects().all()
    limit = int(request.form.get("pageSize"))
    page = int(request.form.get("currentPage"))
    start = (page - 1) * limit
    end = page * limit if len(comment) > page * limit else len(comment)
    ret = [{"comment": comment[i]} for i in range(start, end)]
    return {"data": ret, "count": len(comment)}


@app.route('/submit_comment', methods=["POST", "GET"])
@login_required
def submit_comment():
    commentDate = json.loads(request.data.decode("utf-8"))
    textArea = commentDate.get("textArea", "")
    year = str(commentDate.get("year", ""))
    month = str(commentDate.get("month", ""))
    date = str(commentDate.get("date", ""))
    hour = str(commentDate.get("hour", ""))
    minute = str(commentDate.get("minute", ""))
    comment = UserComment(name=current_user.username,
                          info=textArea,
                          year=year,
                          month=month,
                          date=date,
                          hour=hour,
                          minute=minute,
                          nickname=current_user.nickname,
                          avatar=current_user.avatar)
    comment.save()
    return jsonify("ok")


@app.route('/get_comment_info', methods=["POST", "GET"])
@login_required
def get_comment_info():
    date = json.loads(request.data.decode("utf-8"))
    userReplay = UserReplay.objects(userId=date).all()
    return jsonify(userReplay)


@app.route('/put_comment_info', methods=["POST", "GET"])
@login_required
def put_comment_info():
    err_msg = {
        "result": "NO"
    }
    date = json.loads(request.data.decode("utf-8"))
    userId = date.get("id", "")
    print()
    commentInput = date.get("commentInput", "")
    userReplay = UserReplay(userId=userId,
                            content=commentInput,
                            name=current_user.nickname,
                            avatar=current_user.avatar,
                            userIdBack="",
                            userNameBack="",
                            )
    userReplay.save()
    err_msg["result"] = "ok"
    userReplay = UserReplay.objects(userId=userId).all()
    err_msg["msg"] = userReplay
    return jsonify(err_msg)


@app.route('/put_replay_info', methods=["POST", "GET"])
@login_required
def put_replay_info():
    date = json.loads(request.data.decode("utf-8"))
    userId = date.get("id", "")
    userIdBack = date.get("replayId", "")
    commentInput = date.get("commentInput", "")
    userReplay = UserReplay.objects(id=ObjectId(userIdBack)).first()
    userReplay2 = UserReplay(userId=userId,
                             avatar=current_user.avatar,
                             name=current_user.nickname,
                             content=commentInput,
                             userIdBack=userIdBack,
                             userNameBack=userReplay.name
                             )
    userReplay2.save()
    return jsonify("ok")


if __name__ == "__main__":
    app.run()


# ne – 不等于≠
# lt – 小于<
# lte – 小于等于≤
# gt – 大于>
# gte – 大于等于 ≥
# not – 否定一个标准的检查，需要用在其他操作符之前(e.g. Q(age__not__mod=5))
# in – 值在 list 中
# nin – 值不在 list 中
# mod – value % x == y, 其中 x 和 y 为给定的值
# all – list 里面所有的值
# size – 数组的大小
# exists – 存在这个值

# exact – 字符串型字段完全匹配这个值
# iexact – 字符串型字段完全匹配这个值（大小写敏感）
# contains – 字符串字段包含这个值
# icontains – 字符串字段包含这个值（大小写敏感）
# startswith – 字符串字段由这个值开头
# istartswith – 字符串字段由这个值开头（大小写敏感）
# endswith – 字符串字段由这个值结尾
# iendswith – 字符串字段由这个值结尾（大小写敏感）
# match – 执行 $elemMatch 操作，所以你可以使用一个数组中的 document 实例