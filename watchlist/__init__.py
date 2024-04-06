import os
import sys

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

WIN = sys.platform.startswith('win')
if WIN:  # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:  # 否则使用四个斜线
    prefix = 'sqlite:////'

app = Flask(__name__)
# flash() 函数在内部会把消息存储到 Flask 提供的 session 对象里。session 用来在请求间存储数据，它会把数据签名后存储到浏览器的 Cookie 中，所以我们需要设置签名所需的密钥：
# 这个密钥的值在开发时可以随便设置。基于安全的考虑，在部署时应该设置为随机字符，且不应该明文写在代码里， 在部署章节会详细介绍。
app.config['SECRET_KEY']= os.getenv('SECRET_KEY', 'dev') # 等同于 app.secret_key = 'dev'
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(os.path.dirname(app.root_path), os.getenv('DATABASE_FILE', 'data.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控

db = SQLAlchemy(app)
login_manager = LoginManager(app)   # 实例化扩展类

@login_manager.user_loader
def load_user(user_id): # 创建用户加载回调函数，接受用户ID作为参数
    from watchlist.models import User
    user = User.query.get(int(user_id)) # 用 ID 作为User模型的主键查询对应的用户
    return user     # 返回用户的对象

login_manager.login_view = 'login'

@app.context_processor
def inject_user():
    from watchlist.models import User
    user = User.query.first()
    return dict(user=user)

from watchlist import views, errors, commands