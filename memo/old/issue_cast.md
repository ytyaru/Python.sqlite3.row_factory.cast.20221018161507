# キャスト

　真偽値と日付を各SQL文でキャストしたい。

## insert, update

　Pythonの型からSQLite3の型へキャストしたい。

```python
sql = "insert into users values(?,?,?,?);"
datas = [(0,'A',False,datetime.now()),(1,'B',True,datetime.now())]
sqlite3.connect.execute(sql, datas)
```

```python
sql = "update users set is_male=?, birth=? where id=?;"
datas = [(False,datetime.now(),0),(True,datetime.now(),1)]
sqlite3.connect.execute(sql, datas)
```

## select

　SQLite3の型からPythonの型へキャストしたい。

```python
sql = "select * from users wehre birth < CURRENT_TIMESTAMP;"
rows = sqlite3.connect.execute(sql).fetchall()
rows[0][2] #=> True/False
rows[0][3] #=> datetime() UTC
```

## どうするか

　`sqlite3.connect.execute()`をラップし、渡されたpreperd statementのデータを`datas`で取得して、それが`bool`, `datetime`型だったらキャストする。

```python
insert(sql, datas)
update(sql, datas)
get(sql, datas)
gets(sql, datas)
```


```python
import re
def cast_py_to_sql(self, v):
	if isinstance(v, bool): return '1' if v else '0'
	elif isinstance(v, datetime): return f"{v:%Y/%m/%d %H:%M:%S}"
	else: return v
def cast_py_to_sql_by_row(self, row):
	if isinstance(row, tuple): return tuple([cast_py_to_sql(col) for col in row])
	else: return row
def cast_py_to_sql_by_rows(self, rows):
	if isinstance(rows, list): return [cast_py_to_sql_by_row(row) for row in rows]
	else: return rows
```
```python
def insert(self, sql, datas):
	return sqlite3.connect.execute(sql, cast_py_to_sql_by_rows(datas))
def update(sql, datas):
	return sqlite3.connect.execute(sql, cast_py_to_sql_by_rows(datas))
```

　select文でのキャストは`row_factory`で実装せねばらない。さらに`create table`で定義した列の型も必要。問題は列の型をどうやって取得するか。

```python
get(sql, datas)
gets(sql, datas)
```

　`row_factory`のコールバック関数の引数から、列名は`cursor.description`で取得できるし、値は`row`で取得できる。が、表名が取得できない。そもそも`create table`した表の列を返すとは限らない。たとえば`select CURRENT_TIMESTAMP;`や`select count(*) ...`、GroupByやテーブル結合、副問合せもある。それらの列の型をどう取得するか。

```sql
select typeof(CURRENT_TIMESTAMP);
```
```sql
text
```

　`typeof()`を使うとSQLite3に存在する型名が返る。そうではなく`create table`で定義した型名を返して欲しい。

```sql
create table users(is_male bool check(is_male=0 or is_male=1));
insert into users values(0);
select typeof(is_male) from users;
```
```sql
integer
```

　`pragma_table_info`表を使うと取得できた。

```sql
select name, type from pragma_table_info('users');
```
```sql
is_male|bool
```

　問題はどうやって表名を取得するか。渡されたselect文を解析するしかない。ただ、先述のように定義された表の列をそのまま返すとは限らない。`select 実在する列名`, `from 実在する表名`の形である必要がある。実在する名前以外には関数や別名定義、副問合せなど様々なものがありうる。そういった要素が一切ないときだけ、キャストすることができる。

```python
from datetime import datetime
from decimal import Decimal
def cast_sql_to_py(self, v, typ): # v=値, typ=SQLite3型名
	# 'yyyy-MM-dd HH:mm:ss'のときUTC標準時としてdatetime型にキャストする
	if 'datetime' == typ.lower() and re.fullmatch(r'\d{4,}[\-/]\d{2}[\-/]\d{2} \d{2}:\d{2}:\d{2}', v):
		return datetime.fromisoformat(v.replace(' ', 'T') + '+00:00')
	elif typ.lower() in ['bool', 'boolean']: return bool(v)
	elif 'decimal' == typ.lower(): return Decimal(v)
	elif 'blob' == typ.lower(): return bytes(v)
	else: return v
def cast_sql_to_py_by_row(self, row, types):
	if isinstance(row, tuple): return tuple([cast_sql_to_py(col) for col in row])
	else: return row
def cast_sql_to_py_by_rows(self, rows):
	if isinstance(rows, list): return [cast_sql_to_py_by_row(row) for row in rows]
	else: return rows
```

```sql
def row_factory(self, cursor, row):
	# なんとかしてSQL文を取得し表名を取得し列名を取得する。cursor.descriptionの列名が表に存在する列名であればキャストする。そうでないなら何もしない
	cast_sql_to_py_by_row(list(zip(names, types, row))) # [(列名,型,値),...]
	cast_sql_to_py_by_row(namedtuple('Column','name type value')(name,typ,v)) # [(列名,型,値),...]
```

　これ以上はどうやるのかわからない。実際にコードを書いてみないと。

