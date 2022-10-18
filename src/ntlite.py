import sqlite3
from collections import namedtuple
import dataclasses
import inspect
RowTypes = namedtuple('RowTypes', 'tuple row namedtuple dataclass', defaults=(0,1,2,3))()
class RowType: pass
RowType.row_factory = None
class TupleRowType(RowType): pass
class Sqlite3RowType(RowType): pass
Sqlite3RowType.row_factory = sqlite3.Row
class NamedTupleRowType(RowType):
    def __init__(self, not_getitem=False): self._not_getitem = not_getitem
    def row_factory(self, cursor, row):
        row_type = self.new_row_type(cursor)
        if not self._not_getitem: row_type = self.set_getitem(row_type)
        return row_type(*row)
    def new_row_type(self, cursor): return namedtuple('Row', list(map(lambda d: d[0], cursor.description)))
    def set_getitem(self, row_type):
        def getitem(self, key):
            if isinstance(key, str): return getattr(self, key)
            else: return super(type(self), self).__getitem__(key)
        row_type.__getitem__ = getitem
        return row_type
class DataClassRowType(RowType):
    def __init__(self, not_getitem=False, not_slots=False, not_frozen=False):
        self._not_getitem = not_getitem
        self._not_slots = not_slots
        self._not_frozen = not_frozen
    def row_factory(self, cursor, row):
        row_type = self.new_row_type(cursor)
        if not self._not_getitem: row_type = self.set_getitem(row_type)
        return row_type(*row)
    def new_row_type(self, cursor):
        return dataclasses.make_dataclass('Row', list(tuple(map(lambda d: d[0], cursor.description))), slots=not self._not_slots, frozen=not self._not_frozen)

    def set_getitem(self, row_type):
        def getitem(self, key):
            if isinstance(key, str): return getattr(self, key)
            elif isinstance(key, int): return getattr(self, list(self.__annotations__.keys())[key])
            else: raise TypeError('The key should be int or str type.')
        row_type.__getitem__ = getitem
        return row_type
# NtLiteのコンストラクタ引数row_typeにセットする値はこのRowTypesが持ついずれかのプロパティを渡す
RowTypes = namedtuple('RowTypes', 'tuple sqlite3 namedtuple dataclass', defaults=(TupleRowType, Sqlite3RowType, NamedTupleRowType, DataClassRowType))()
class NtLite:
    def __init__(self, path=':memory:', row_type:RowTypes=RowTypes.namedtuple):
        self._path = path
        self._row_type = row_type
        self.RowType = row_type
        self._con = sqlite3.connect(path)
        self._set_row_factory()
        self._cur = self._con.cursor()
    def __del__(self): self._con.close()
    def table_names(self): return tuple([row.name for row in self.gets("select name from sqlite_master where type='table';")])
    def column_names(self, table_name): return tuple([row.name for row in self.table_info(table_name)])
    def table_info(self, table_name): return self.gets(f"PRAGMA table_info('{table_name}');")
    def table_xinfo(self, table_name): return self.gets(f"PRAGMA table_xinfo('{table_name}');")
    def exec(self, sql, params=()): return self.con.execute(sql, params)
    def execm(self, sql, params=()): return self.con.executemany(sql, params)
    def execs(self, sql): return self.con.executescript(sql)
    def get(self, sql, params=()): return self.exec(sql, params).fetchone()
    def gets(self, sql, params=()): return self.exec(sql, params).fetchall()
    def _cast_exec(self, sql, params): return self.exec(sql, CastPy.to_sql_by_row(params))
    def _cast_execm(self, sql, params): return self.execm(sql, CastPy.to_sql_by_rows(params))
    def _insert_sql(self, table_name, params): return f"insert into {table_name} values ({','.join('?' * len(params))})"
    def insert(self, table_name, params): return self._cast_exec(self._insert_sql(table_name, params), params)
    def inserts(self, table_name, params): return self._cast_execm(self._insert_sql(table_name, params), params)
    #def insert(self, sql, params): return self._cast_exec(sql, params)
    #def update(self, sql, params): return self._cast_exec(sql, params)
    #def update(self, table_name, params, id): return self._cast_exec(f"update {table_name} set どうにかして表の全列名を取得する where id=?", params)
    #def updates(self, sql, params): return self._cast_execm(sql, params)
       
    def commit(self): return self.con.commit()
    def rollback(self): return self.con.rollback()
    @property
    def con(self): return self._con
    @property
    def cur(self): return self._cur
    @property
    def path(self): return self._path
    @property
    def RowType(self): return self._row_type
    @RowType.setter
    def RowType(self, v):
        if inspect.isclass(v):
            if issubclass(v, RowType):
                self._row_type = v() # 型が渡されたらデフォルトコンストラクタで生成したインスタンスをセットする
                return
        self._row_type = v if issubclass(type(v), RowType) else NamedTupleRowType()
    def _set_row_factory(self):
        self._con.row_factory = self._row_type.row_factory if issubclass(type(self._row_type), RowType) else NamedTupleRowType().row_factory

import re
from datetime import datetime
class CastPy:
    @classmethod
    def to_sql(cls, v):
        if isinstance(v, bool): return '1' if v else '0'
        elif isinstance(v, datetime): return f"{v:%Y-%m-%d %H:%M:%S}"
        else: return v
    @classmethod
    def to_sql_by_row(cls, row):
        if isinstance(row, tuple): return tuple([cls.to_sql(col) for col in row])
        else: return row
    @classmethod
    def to_sql_by_rows(cls, rows):
        if isinstance(rows, list): return [cls.to_sql_by_row(row) for row in rows]
        else: return rows

