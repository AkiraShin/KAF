import asyncio  # 异步 I/O
import logging  # 日志记录
import aiomysql  # 连接数据库MySQL


def log(sql, args=()):
    logging.info('SQL:%s' % sql)
    # info(msg, *args, **kwargs)msg 是消息格式字符串


async def create_pool(loop, **kw):
    logging.info('create database connection pool...')
    global __pool  # 私有变量
    __pool = await aiomysql.create_pool(  # 创建连接池
        host=kw.get('host', 'localhost'),#获取key=host的值,不存在返回localhost
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset', 'utf8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
        loop=loop
    )

    # SQL.connect参数
    # 字符串参数 host： 数据库服务所在的主机的地址。 默认为“localhost”
    # 字符串参数 user：登录数据库的用户名
    # 字符串参数 password：对应用户名的密码
    # 字符串参数 db: 要使用的数据库， 如果没有指定不会使用其他的，报错。
    # 整型参数 port：MySQL服务使用的端口，一般默认的就可以(3306).
    # 字符串参数 unix_socket：可选的，你可以使用一个unix的socket，而不是一个TCP/IP。
    # 字符串参数 charset： 指定你想要使用的编码格式，例如“utf8”。
    # 参数 sql_model：默认使用的SQL模式，例如“NO_BACKSLASH_ESCAPES”
    # 参数 read_default_file： 指定读取[client]部分的my.cnf文件。
    # 参数 conv：使用指定编码器替代默认编码器，通常用来定制一些类型。 具体参考pymysql.converters
    # 参数 user_unicode： 是否使用默认的unicode字符串
    # 参数 client_flag： 自定义发送给mysql的flag，从pymysql.constants.CLIENT中可以找到相应的值。
    # 参数 cursorclass：自定义使用的游标类
    # 参数 str init_command：连接建立的时候执行的SQL初始化语句。
    # 参数 connect_timeout：连接中抛出异常前的保持时间。
    # 字符串参数 read_default_group：从配置文件中读取的分组信息
    # 布尔参数 no_delay：禁止使用socket连接的纳格算法
    # 参数 autocommit：自动提交模式，指定为None使用默认的值(default: False)
    # 参数 loop：异步循环事件的实例，或者指定为None使用默认的实例。
    # return：返回值是一个连接的实例


async def select(sql, args, size=None):
    log(sql, args)  # 前面定义的log函数
    global __pool
    with (await __pool) as conn:
        cur = await conn.cursor(aiomysql.DictCursor)  # 返回字典(dict)表示的记录

        # execute(self, query, args):执行单条sql语句,接收的参数为sql语句本身和使用的参数列表,返回值为受影响的行数
        # REPLACE ( string_expression , string_pattern , string_replacement )3换下1中所有的2
        # SQL语句的占位符是?，而MySQL的占位符是%s，select()函数在内部自动替换。注意要始终坚持使用带参数的SQL，而不是自己拼接SQL字符串，这样可以防止SQL注入攻击。
        await cur.execute(sql.replace('?', '%s'), args or ())
        if size:
            # fetchmany(self, size=None):接收size条返回结果行.如果size的值大于返回的结果行的数量,则会返回cursor.arraysize条数据
            rs = await cur.fetchmany(size)
        else:
            rs = await cur.fetchall()
        await cur.close()
        logging.info('rows returned: %s' % len(rs))
        return rs


async def execute(sql, args):
    log(sql)
    with (await __pool) as conn:
        try:
            cur = await conn.cursor()
            await cur.execute(sql.replace('?', '%s'), args)
            affected = cur.rowcount  # rowcount随着每次fetch而累计,表示从cursor中提取的记录数目
            await cur.close()
        except BaseException:
            raise
        return affected


def create_args_string(num):
    L = []
    for _ in range(num):
        L.append('?')  # L内添加?用于sql占位
    return ', '.join(L)


class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):#cls表示类本身，self表示实例
        # 排除Model类本身
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)#创建type类的class
        # 获取table名称
        tableName = attrs.get('__table__', None) or name
        logging.info('found model: %s (table: %s)' % (name, tableName))
        # 获取所有Field和主key_name
        mappings = dict()
        fields = []
        primaryKey = None
        for k, v in attrs.items():#返回可遍历的(键, 值) 元组数组
            if isinstance(v, Field):
                logging.info('found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    # 找到主键
                    if primaryKey:
                        raise RuntimeError(
                            'Duplicate primary key for field: %s' % k)
                    primaryKey = k
                else:
                    fields.append(k)
        if not primaryKey:
            raise RuntimeError('Primary key not found.')
        for k in mappings.keys():
            attrs.pop(k)
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))
        attrs['__mappings__'] = mappings  # 保存属性和列的映射关系
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primaryKey  # 主键属性名
        attrs['__fields__'] = fields  # 除主键外的属性名
        # 构造默认的SQL的SELECT,INSERT,UPDATE和DELETE语句
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (
            primaryKey, ', '.join(escaped_fields), tableName)  # 用', '连接escape_fields
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ', '.join(
            escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ', '.join(
            map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (
            tableName, primaryKey)
        return type.__new__(cls, name, bases, attrs)


class Model(dict, metaclass=ModelMetaclass):
    def __init__(self, **kw):
        super(Model, self).__init__(**kw)  # super()调用父类(超类)避免重复调用，查找顺序问题

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)  # 查找self里的key属性，无则设为None

    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' %
                              (key, str(value)))
                setattr(self, key, value)
        return value

    @classmethod  # 装饰器的self变为cls，self表示一个实例，cls表示类本身
    async def findAll(cls, where=None, args=None, **kw):
        # find objects by where clause
        sql = [cls.__select__]  # cls可调用类属性、类方法和对象
        if where:
            sql.append('where')
            sql.append(where)
        if args is None:
            args = []
        orderBy = kw.get('orderBy', None)  # get()函数返回指定键的值,不存在返回None
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)
        limit = kw.get('limit', None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?, ?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        rs = await select(' '.join(sql), args)
        return [cls(**r) for r in rs]  # 调用Model(dict)返回将select得到的字典创建的model类

    @classmethod
    async def findNumber(cls, selectField, where=None, args=None):
        # find number by select and where
        sql = ['select %s _num_ from `%s`' % (selectField, cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = await select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['_num_']

    @classmethod
    async def find(cls, pk):
        # find object by primary key
        rs = await select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    async def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        if rows != 1:
            logging.warning(
                'failed to insert record: affected rows: %s' % rows)

    async def update(self):
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = await execute(self.__update__, args)
        if rows != 1:
            logging.warning(
                'failed to update by primary key: affected rows: %s' % rows)

    async def remove(self):
        args = [self.getValue(self.__primary_key__)]
        rows = await execute(self.__delete__, args)
        if rows != 1:
            logging.warning(
                'failed to remove by primary key: affected rows: %s' % rows)


class Field(object):  # Field增加一个default参数可以让ORM自己填入缺省值,缺省值可以作为函数对象传入,调用save()时自动计算
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)


class StringField(Field):
    def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
        super().__init__(name, ddl, primary_key, default)


class BooleanField(Field):
    def __init__(self, name=None, default=False):
        super().__init__(name, 'boolean', False, default)


class IntegerField(Field):
    def __init__(self, name=None, primary_key=False, default=0):
        super().__init__(name, 'bigint', primary_key, default)


class FloatField(Field):
    def __init__(self, name=None, primary_key=False, default=0.0):
        super().__init__(name, 'real', primary_key, default)


class TextField(Field):
    def __init__(self, name=None, default=None):
        super().__init__(name, 'text', False, default)
