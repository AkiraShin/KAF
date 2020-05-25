import time
import uuid
# UUID通过uuid1时间戳、uuid3名字的MD5散列值、uuid4随机数、uuid5名字的SHA-1散列值来保证生成ID的时间和空间的唯一性，固定大小128bit，编码为32位16进制数字的字符串
from orm import Model, StringField, BooleanField, FloatField, TextField


def next_id():
    # 返回15+32+3=50位字符串(time.time()*1000保留两位小数为15位)，用varchar(50)储存,
    return '%015d%s000' % (int(time.time()*1000), uuid.uuid4().hex)
    # %[(name)][flags][width].[precision]typecode 上面flags=0表示用0填充，width=15表示显示宽度
    # hex将10进制整数转换成16进制并以str表示,在这里hex输出纯字母和数据删去uuid中的-


class User(Model):
    __table__ = 'users'

    id = StringField(primary_key=True, default=next_id,
                     ddl='varchar(50)')  # mysql中的varchar相当于str
    email = StringField(ddl='varchar(50)')
    passwd = StringField(ddl='varchar(50)')
    admin = BooleanField()
    name = StringField(ddl='varchar(50)')
    image = StringField(ddl='varchar(50)')
    created_at = FloatField(default=time.time)


class Blog(Model):
    __table__ = 'blogs'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    name = StringField(ddl='varchar(50)')
    summary = StringField(ddl='varchar(200)')
    content = TextField()
    created_at = FloatField(default=time.time)


class Comment(Model):
    __table__ = 'comments'

    id = StringField(primary_key=True, default=next_id, ddl='varchar(50)')
    blog_id = StringField(ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    content = TextField()
    created_at = FloatField(default=time.time)
