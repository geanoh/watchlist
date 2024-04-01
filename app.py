from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import url_for, request, redirect, flash
from markupsafe import escape
from flask import render_template
import os
import sys
import click
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user
from flask_login import login_required, logout_user, current_user

WIN = sys.platform.startswith('win')
if WIN:  # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:  # 否则使用四个斜线
    prefix = 'sqlite:////'

app = Flask(__name__)


# flash() 函数在内部会把消息存储到 Flask 提供的 session 对象里。session 用来在请求间存储数据，它会把数据签名后存储到浏览器的 Cookie 中，所以我们需要设置签名所需的密钥：
# 这个密钥的值在开发时可以随便设置。基于安全的考虑，在部署时应该设置为随机字符，且不应该明文写在代码里， 在部署章节会详细介绍。
app.config['SECRET_KEY']= 'dev' # 等同于 app.secret_key = 'dev'

app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
# 在扩展类实例化前加载配置
db = SQLAlchemy(app)

name = 'Geanoh'
movies = [
    {'title' : 'My Neighbor Totoro', 'year' : '1988'},
    {'title' : 'Dead Poets Society', 'year' : '1989'},
    {'title' : 'A Perfect World', 'year' : '1993'},
    {'title' : 'Leon', 'year' : '1994'},
    {'title' : 'Mahjong', 'year' : '1996'},
    {'title' : 'Swallowtail Butterfly', 'year' : '1996'},
    {'title' : 'King of Comedy', 'year' : '1999'},
    {'title' : 'WALL-E', 'year' : '2008'},
    {'title' : 'The Pork of Music', 'year' : '2012'},
]

# 模板上下文处理函数
# 这个函数返回的变量（以字典键值对的形式）将会统一注入到每一个模板的上下文环境中，因此可以直接在模板中使用。
@app.context_processor
def inject_user(): # 函数名可以任意修改
    user = User.query.first()
    return dict(user=user) # 需要返回字典，等同于 return {'user': user}

# 404 错误处理函数
@app.errorhandler(404) # 传入要处理的错误代码
def page_not_found(e): # 接受异常对象作为参数
    user = User.query.first()
    return render_template('404.html'), 404 # 返回模板和状态码

# 对于 GET 请求，返回渲染后的页面；对于 POST 请求，则获取提交的表单数据并保存。
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST': # 判断是否是POST请求
        if not current_user.is_authenticated:   # 如果当前用户未认证
            return redirect(url_for('index'))   # 重定向到主页
        # 获取表单数据
        title = request.form.get('title') # 传入表单对应输入字段的name值
        year = request.form.get('year')
        # 验证数据
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.') # 显示错误提示
            return redirect(url_for('index')) # 重定义回主页
        # 保存表单数据到数据库
        movie = Movie(title=title, year=year) # 创建记录
        db.session.add(movie) # 添加到数据库会话
        db.session.commit() # 提交数据库会话
        flash('Item created.') # 显示成功创建的提示
        return redirect(url_for('index')) # 重定向回主页
    
    movies = Movie.query.all() # 读取所有电影记录
    return render_template('index.html', movies=movies)

# @app.route('/')
# @app.route('/index')
# @app.route('/home')
# def hello():
#     return '<h1>Hello Totoro!</h1><img src="http://helloflask.com/totoro.gif">'

@app.route('/user/<name>')
def user_page(name):
    return f'User: {escape(name)}'

@app.route('/test')
def test_url_for():
    print(url_for('hello'))
    print(url_for('user_page', name='jane'))
    print(url_for('user_page', name='alex'))
    print(url_for('test_url_for'))
    print(url_for('test_url_for', num=2))
    return 'Test page'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('Invalid input.')
            return redirect(url_for('login'))
        
        user = User.query.first()
        # 验证用户名和密码是否一致
        if username == user.username and user.validate_password(password):
            login_user(user) # 登入用户
            flash('Login success.')
            return redirect(url_for('index')) # 重定向到主页
        
        flash('Invalid username or password.') # 如果验证失败，显示错误消息
        return redirect(url_for('login'))   # 重定向回登录界面
    
    return render_template('login.html')

@app.route('/logout')
@login_required # 用于视图保护
def logout():
    logout_user()   # 登出用户
    flash('Goodbye.')
    return redirect(url_for('index'))   # 重定向回首页

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']

        if not name or len(name) > 20:
            flash('Invalid input.')
            return redirect(url_for('settings'))
        
        current_user.name = name
        # current_user 会返回当前登录用户的数据库记录对象
        # 等同于下面的用法
        # user = User.query.first()
        # user.name = name
        db.session.commit()
        flash('Settings updated.')
        return redirect(url_for('index'))
    
    return render_template('settings.html')

# 数据库模型
# class User(db.Model):  # 表名将会是 user（自动生成，小写处理）
#     id = db.Column(db.Integer, primary_key=True)  # 主键
#     name = db.Column(db.String(20))  # 名字

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    username = db.Column(db.String(20))  # 用户名
    password_hash = db.Column(db.String(128))  # 密码散列值

    def set_password(self, password):  # 用来设置密码的方法，接受密码作为参数
        self.password_hash = generate_password_hash(password)  # 将生成的密码保持到对应字段

    def validate_password(self, password):  # 用于验证密码的方法，接受密码作为参数
        return check_password_hash(self.password_hash, password)  # 返回布尔值



class Movie(db.Model):  # 表名将会是 movie
    id = db.Column(db.Integer, primary_key=True)  # 主键
    title = db.Column(db.String(60))  # 电影标题
    year = db.Column(db.String(4))  # 电影年份


# 自定义命令
@app.cli.command() # 注册为命令，可以传入 name 参数来自定义命令
@click.option('--drop', is_flag=True, help='Create after drop.') # 设置选项
def initdb(drop):
    """Initialize the database."""
    if drop:    # 判断是否输入选项
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.') # 输出提示信息

@app.cli.command()
def forge():
    """ Generate fake data. """
    db.create_all()

    # 全局的两个变量移动到这个函数内
    name = 'Echo Sue'
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]

    user = User(name=name)
    db.session.add(user)
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)
    
    db.session.commit()
    click.echo('Done')

# 创建一个用于显示编辑页面和处理编辑表单提交请求的视图函数
@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required # 登录保护
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    if request.method == 'POST': # 处理编辑表单的提交请求
        title = request.form['title']
        year = request.form['year']

        if not title or not year or len(year) != 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect(url_for('edit', movie_id=movie_id)) # 重定向会对应的编辑页面
        
        movie.title = title # 更新标题
        movie.year = year # 更新年份
        db.session.commit() # 提交数据库会话
        flash('Item updated.')
        return redirect(url_for('index')) # 重定向会主页

    return render_template('edit.html', movie=movie) # 传入被编辑的电影记录

# 创建一个视图函数执行删除操作
@app.route('/movie/delete/<int:movie_id>', methods=['POST']) # 限定只接受POST请求
@login_required # 登录保护
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id) # 获取电影记录
    db.session.delete(movie) # 删除对应的记录
    db.session.commit() # 提交数据库会话
    flash('Item deleted.')
    return redirect(url_for('index')) # 重定向回主页

@app.cli.command()
@click.option('--username', prompt=True, help='The username used to login.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
    """Create user."""
    db.create_all()

    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)  # 设置密码
    else:
        click.echo('Creating user...')
        user = User(username=username, name='Admin')
        user.set_password(password)  # 设置密码
        db.session.add(user)

    db.session.commit()  # 提交数据库会话
    click.echo('Done.')

login_manager = LoginManager(app)   # 实例化扩展类
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id): # 创建用户加载回调函数，接受用户ID作为参数
    user = User.query.get(int(user_id)) # 用 ID 作为User模型的主键查询对应的用户
    return user     # 返回用户的对象