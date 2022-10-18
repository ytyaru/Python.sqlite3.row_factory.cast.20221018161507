【Python】SQLite3のselect結果をtuple,sqlite3.Row,namedtuple,dataclassで返すラッパー

　行の型を4種から選べるようにした。また、表名・列名を取得するAPIを追加した。

<!-- more -->

# ブツ

* [リポジトリ][]

[リポジトリ]:https://github.com/ytyaru/Python.sqlite3.row_factory.tuple.sqlite3row.namedtuple.dataclass.__getitem__.20221017181058
[DEMO]:https://ytyaru.github.io/Python.sqlite3.row_factory.tuple.sqlite3row.namedtuple.dataclass.__getitem__.20221017181058/
[sqlite3]:https://docs.python.org/ja/3/library/sqlite3.html
[row_factory]:https://docs.python.org/ja/3/library/sqlite3.html#sqlite3.Connection.row_factory
[sqlite3.Row]:https://docs.python.org/ja/3/library/sqlite3.html#sqlite3.Row
[__getitem__]:https://docs.python.org/ja/3/reference/datamodel.html#object.__getitem__
[cursor.description]:https://docs.python.org/ja/3/library/sqlite3.html#sqlite3.Cursor.description
[namedtuple]:https://docs.python.org/ja/3/library/collections.html#collections.namedtuple
[dataclass]:https://docs.python.org/ja/3/library/dataclasses.html
[mypy]:https://github.com/python/mypy


## 実行

```sh
NAME='Python.sqlite3.row_factory.tuple.sqlite3row.namedtuple.dataclass.__getitem__.20221017181058'
git clone https://github.com/ytyaru/$NAME
cd $NAME/src
./test.py
```

## コード例

```python
#!/usr/bin/env python3
# coding: utf8
import os
from ntlite import NtLite
path = 'my.db'
if os.path.isfile(path): os.remove(path)
db = NtLite(path)
db.exec("create table users(id integer, name text);")
db.execm("insert into users values(?,?);", [(0,'A'),(1,'B')])
assert 2 == db.get("select count(*) num from users;").num
rows = db.gets("select * from users;")
assert 0   == rows[0].id
assert 'A' == rows[0].name
assert 1   == rows[1].id
assert 'B' == rows[1].name

assert 0   == rows[0]['id']
assert 'A' == rows[0]['name']
assert 1   == rows[1]['id']
assert 'B' == rows[1]['name']

assert 0   == rows[0][0]
assert 'A' == rows[0][1]
assert 1   == rows[1][0]
assert 'B' == rows[1][1]
```

## import

```python
from ntlite import NtLite
```

## new

```python
db = NtLite() # :memory:
```
```python
db = NtLite('./db/my.sqlite3')
```
```python
db = NtLite('./db/my.sqlite3', RowTypes.dataclass)
```
```python
db = NtLite(path='./db/my.sqlite3', row_type=RowTypes.dataclass)
```

# 前回との差異

* 行の型を4種から選べるようにした
* 表名・列名を取得するAPIを追加した

## 行の型を4種から選べるようにした

`RowTypes`|列の取得方法
----------|------------
`tuple`|`row[0]`
`sqlite3row`([sqlite3.Row][])|`row[0]`, `row['col_name']`
`namedtuple`|`row[0]`, `row.col_name`, `row['col_name']`
`dataclass`|`row[0]`, `row.col_name`, `row['col_name']`

　デフォルトは`namedtuple`。

### 行型パラメータ

　`RowTypes`の`namedtuple`と`dataclass`はパラメータを持っている。

　以下の2つはパラメータを持っている。

```python
RowTypes.namedtuple(not_getitem=True)
```

```python
RowTypes.namedtuple(not_getitem=True, not_slot=True, not_frozen=True)
```

　それぞれ効果は次の通り。

parameter|namedtuple|dataclass
---------|----------|---------
`not_getitem`=`True`|`['col_name']`で参照不可|`[0]`や`['col_name']`で参照不可
`not_slot`=`True`|-|新しいプロパティを登録できなくなる
`not_frozen`=`True`|-|ミュータブルになる（プロパティに値をセットできるようになる）

　デフォルトはすべて`False`。できるだけ列参照しやすくパフォーマンスが高いセッティングにしたつもり。

　`namedtuple`は最初から新プロパティ登録不可かつイミュータブルである。ふつうDBのselect結果ではそれで問題ない。パフォーマンス的にもそのほうがよい。なのでdataclassもそうした。もしPythonのdataclassのデフォルトと同じにしたいなら`not_*`系フラグをすべて`True`にすればいい。

　`NtLite`を生成するときは以下のように渡す。

```python
db = NtLite(row_type=RowTypes.namedtuple(not_getitem=True))
db = NtLite(row_type=RowTypes.dataclass(not_getitem=True, not_slot=True, not_frozen=True))
```

　`NtLite.RowType`で後からセットすることもできる。

```python
db = NtLite()
db.RowType = RowTypes.dataclass(not_getitem=True)
```

## 表名・列名を取得するAPIを追加した

```python
#!/usr/bin/env python3
# coding: utf8
from ntlite import NtLite
db = NtLite()
db.exec("create table users(id integer, name text, age integer);")
db.exec("create table jobs(id integer, name text);")
assert ('users','jobs') == db.table_names()
assert ('id','name','age') == db.column_names('users')
```

# 課題

## 型について

　せっかくdataclassで型情報をセットできるのだからDBで取得してそれに応じたPython型にしたい。しかしあまりにも問題が多すぎる。

　まず、SQLite3のデータ型はとても少なく以下5種しかない。

SQLite3の型|意味
-----------|----
`INTEGER`|整数
`REAL`|浮動小数点数
`TEXT`|テキスト
`BLOB`|バイナリ
`NULL`|NULL

　もしPythonの型にキャストするなら以下のようになるだろう。

Python型|SQLite3型
--------|---------
`int`|`INTEGER`
`float`|`REAL`
`str`|`TEXT`
`bytes`|`BLOB`
`None`|`NULL`
`bool`|`INTEGER` + `check(c=0 or c=1)`
`datetime`|`TEXT` + `check(regexp('\d{4,}[\-/]\d{2}[\-/]\d{2}T\d{2}:\d{2}:\d{2}Z', c))`

　SQLite3では真偽型や日付型がない。よってそれぞれ`INTEGER`,`TEXT`に制約をつけて代用する。

### 日付型

　問題は以下の3つがそれぞれ微妙に異なることである。

* SQLite3における日付の書式
* ISO-8601における日付の書式
* Pythonにおける日付の書式

文脈|日付の書式|日時
----|----------|----
SQLite3|`yyyy-MM-dd HH:mm:ss`|UTC標準時
[ISO-8601][]|`yyyy-MM-ddTHH:mm:ssZ`等|UTC標準時,タイムゾーン
[Python][datetime.fromisoformat]|`YYYY-MM-DD[*HH[:MM[:SS[.fff[fff]]]][+HH:MM[:SS[.ffffff]]]]`|ローカル日時

[ISO-8601]:https://ja.wikipedia.org/wiki/ISO_8601
[datetime.fromisoformat]:https://docs.python.org/ja/3/library/datetime.html#datetime.datetime.fromisoformat
[]:https://docs.python.org/ja/3/library/datetime.html#datetime.date.fromisoformat

　さらに細かく分類すると大体以下のような感じ。ただし文脈によって微妙に書式が異なる。

型|書式
--|----
`date`|`yyyy-MM-dd`
`time`|`HH:mm:ss`
`datetime`|`yyyy-MM-dd HH:mm:ss`

　SQLite3での日付はUTCが基本。たとえば現在日時を出力する`CURRENT_TIMESTAMP`は以下。

```sql
select CURRENT_TIMESTAMP;
```
```sh
2022-10-18 03:11:42
```

　これはUTC時刻である。日本時刻では`12:11:42`だった。しかしそれをUTC時刻に直され9時間前のものになった。このようにSQLite3の時刻はUTCが基本である。

　また、日付の書式は`yyyy-MM-dd HH:mm:ss`となる。これはISO-8601形式とわずかに異なる。

SQLite3|ISO-8601
-------|--------
`yyyy-MM-dd HH:mm:ss`|`yyyy-MM-ddTHH:mm:ssZ`

　なぜこのような書式なのか知らないが、おそらくデータ量が少なく、人に理解しやすい形式なのだろう。



　ただ、SQLite3の記述だとUTC時刻なのかローカル時刻なのか見分けがつかない。なので末尾に`Z`を付与してUTC時刻であることを明示するISO-8601形式にする。このテキストをそのまま取得すれば、ISO-8601テキストに対応したライブラリがあるプログラミング言語なら簡単にUTC時刻であることも識別できるし日付型に変換してくれる。

　ただ、ISO-8601形式には柔軟性があり同じ時刻であっても別の表記ができる。たとえば末尾`Z`のUTC標準時はほかにも`+00:00`や`-00:00`,`+00:00:00`等と書ける。

　とはいえ、これらの書式すべてに対応したテキストをSQLite側で許すのは得策でなはない。表記を単一に固定してしまえば単純に文字列だけで大小比較することができる。これならキャストせずSQL内だけでソートや大小比較、同値判定することができる。よって日付型の書式は末尾`Z`で統一するのが最善だと考える。

　動作確認として以下のようなSQLを実行した。

```sql
create table users(birth datetime check(regexp('\d{4,}[\-/]\d{2}[\-/]\d{2}T\d{2}:\d{2}:\d{2}Z', birth)));
insert into users values('2000-01-01T00:00:00Z');
insert into users values('2000-01-01T00:00:00+00:00');
```
```sh
Runtime error: CHECK constraint failed: regexp('\d{4,}[\-/]\d{2}[\-/]\d{2}T\d{2}:\d{2}:\d{2}Z', birth) (19)
```

　前者の`insert`文はOK。後者の`insert`文はチェック制約違反エラー。想定通り。

　また、加算、除算などの計算は関数で行う。

```sql
select datetime('2000-01-01', '+1 days', '-4 hours') as datetime;
```
```sql
2000-01-01 20:00:00
```

　詳細は[SQLite function datetime][]参照。

[SQLite function datetime]:https://www.sqlite.org/lang_datefunc.html

　Pythonではデフォルトのままだとローカル時刻が取得される。UTC時刻を取得するときは以下。

```python
from datetime import timezone, datetime, timedelta
dt_utc = datetime(2020, 11, 1, 8, tzinfo=timezone.utc)
```

　残念なことにPythonの日付書式はタイムゾーンが`+00:00`形式にしか対応しておらず`Z`形式には非対応。なので末尾`Z`形式の日付型がきたら`+00:00`に置換してやる必要がある。

```python
from datetime import timezone, datetime, timedelta
dt_utc = datetime.fromisoformat('2000-01-01T00:00:00Z') # NG
dt_utc = datetime.fromisoformat('2000-01-01T00:00:00+00:00:00') # OK
```

　Python 3.9からは以下のようなタイムゾーン専用クラスが用意された。ただしタイムゾーンデータは頻繁に更新されるためOSが持っているデータに依存するらしい。

```python
from zoneinfo import ZoneInfo
LOS_ANGELES = ZoneInfo("America/Los_Angeles")
```

### 真偽値
　

　真偽値でも試す。

```sql
create table t(is_male bool check(is_male=0 or is_male=1));
insert into t values(0);
insert into t values(1);
insert into t values(2);
```
```sql
Runtime error: CHECK constraint failed: is_male=0 or is_male=1 (19)
```

　`0`,`1`までは成功するが`2`でチェック制約違反となる。

　SQLite3は型を柔軟にキャストするので、以下のように文字列としてセットしても数値になる。なぜかSQLite3の公式ドキュメントではこれを自画自賛している。

```sql
insert into t values('0');
insert into t values('1');
insert into t values('2');
```
```sh
Runtime error: CHECK constraint failed: is_male=0 or is_male=1 (19)
```
```sql
insert into t values('00');
insert into t values('01');
insert into t values('02');
```
```sh
Runtime error: CHECK constraint failed: is_male=0 or is_male=1 (19)
```

　しかし型安全がもてはやされている昨今の現状に対応したのか、[STRICT Tables][]なるものができた。

[STRICT Tables]:https://www.sqlite.org/stricttables.html

　これは勝手にテキストを数値にキャストしないようにする仕組みらしい。ただ、今までそれをウリにしてきたので混乱するし、この[STRICT Tables][]を含んだDBファイルは3.37.0 (2021-11-27)以降のバージョンでないと読み取れない。


boolean


``|

## 制約の取得について

　列がもつ制約を取得したかった。けれどそれを簡単に取得する方法がない。`PRAGMA`に[table_info][], [table_xinfo][], [table_list][]があるが、それで取得できる制約は`primary key`, `default`, `not null`のみ。私は`unique`, `check`, `foreign key`も取得したかった。

[table_info]:https://www.sqlite.org/pragma.html#pragma_table_info
[table_xinfo]:https://www.sqlite.org/pragma.html#pragma_table_xinfo
[table_list]:https://www.sqlite.org/pragma.html#pragma_table_list

```sh
sqlite3
```
```sh
sqlite> create table users(id integer primary key, name text not null, is_male integer check(is_male=0 or is_male=1));
sqlite> .headers on
```sh
sqlite> pragma table_info('users');
cid|name|type|notnull|dflt_value|pk
0|id|INTEGER|0||1
1|name|TEXT|1||0
2|is_male|INTEGER|0||0
```
```sh
sqlite> pragma table_xinfo('users');
cid|name|type|notnull|dflt_value|pk|hidden
0|id|INTEGER|0||1|0
1|name|TEXT|1||0|0
2|is_male|INTEGER|0||0|0
```
```sh
sqlite> pragma table_list;
schema|name|type|ncol|wr|strict
main|users|table|3|0|0
main|sqlite_schema|table|5|0|0
temp|sqlite_temp_schema|table|5|0|0
```

　[sqlite_master][]表には`create table`文が含まれている。これを解析すれば取得できると思う。

```sql
sqlite> select * from sqlite_master;
type|name|tbl_name|rootpage|sql
table|users|users|2|CREATE TABLE users(id integer primary key, name text not null, is_male integer check(is_male=0 or is_male=1))
```

　けれど難易度が高い。制約の記法が2種類ある。それぞれに対応した解析をする必要がある。

　1つ目は列ごとに書く方法。

```sql
create table users(
  id integer primary key,
  name text not null,
  is_male integer check(is_male=0 or is_male=1)
);
```

　2つ目は制約ごとに書く方法。この方法は複数の列を関わらせることができる。

```sql
create table users(
  id integer primary key,
  name text not null,
  is_male integer,
  constraint c1 check(is_male=0 or is_male=1);
);
```

　外部キーについても同じ。列ごとに書くのと、制約ごとに書く方法がある。

```sql
create table jobs(
  id integer primary key,
  name text
);
create table human(
  id integer primary key,
  job_id integer references jobs(id)
);
```
```sql
create table human(
  id integer primary key,
  job_id integer,
  foreign key job_id references jobs(id),
);
```

　UNIQUE制約も複数の記法がある。以下以外にも`primary key`にしたら`UNIQUE`になる。

```sql
create table users(
  id integer,
  name text unique
);
```
```sql
create unique index 制約名 on 表名(列名)
```

　[constraint構文][]参照。

[constraint構文]:https://www.sqlite.org/syntax/table-constraint.html
[stackoverflowにも質問がある]:https://stackoverflow.com/questions/9636053/is-there-a-way-to-get-the-constraints-of-a-table-in-sqlite

　これらを解析するのは大変すぎる。よって対応しない。

