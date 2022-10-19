【Python】SQLite3でinsertするときキャストする

　preperd statementとして値を渡されたとき、その型に応じてSQLite3の型へキャストする。

<!-- more -->

# ブツ

* [リポジトリ][]

[リポジトリ]:https://github.com/ytyaru/Python.sqlite3.row_factory.cast.insert.20221018161507
[DEMO]:https://ytyaru.github.io/Python.sqlite3.row_factory.cast.insert.20221018161507/

## 実行

```sh
NAME='Python.sqlite3.row_factory.cast.insert.20221018161507'
git clone https://github.com/ytyaru/$NAME
cd $NAME/src
./run.py
./test.py
```

# 目的

　Pythonの変数をSQLite3へinsertするとき値の型が所定のものだったら以下のようにキャストする。

Python型|SQLite3型|SQLite3制約
--------|---------|-----------
`bool`|`INTEGER`|`check(c=0 or c=1)`
`datetime`|`TEXT`|`check(regexp('\d{4,}[\-/]\d{2}[\-/]\d{2} \d{2}:\d{2}:\d{2}', c))`, UTC標準時

　preperd statementとしてSQL文内の`?`に与える値を渡されたとき、その型に応じてSQLite3の型へキャストする。

# コード抜粋

## キャスト

```python
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
```

　`to_sql`がキモ。他のメソッドはそれを呼び出しているだけ。`sqlite3.row_factory`が返す行の型としてのタプルや複数行分としてのリストを分解して`to_sql`を呼び出している。

　日付の書式f"{v:%Y-%m-%d %H:%M:%S}"はSQLite3の日付書式である。日付書式にはISO-8601があるが、SQLite3日付書式のほうがメリットが大きい。たとえば`CURRENT_TIMESTAMP`と文字列比較できるし、SQLite3内の日付関係の関数`datetime()`等にも渡せる。SQLite3文脈内において日付型テキストをISO-8601に変換せず比較や計算ができる。タイムゾーン情報がない分だけデータ量も少なくて済む。

## insert

　新たに`insert`メソッドを作った。引数は表名とデータ。列名は不要。すべての列に対して挿入する想定だから。

```python
def inserts(self, table_name, params): ...
```

　すなわち以下のようなinsert文を作る。

```sql
insert into 表名 values(?,?,?...表がもつ列の数だけ?付与);
```

　これをPythonのsqlite3標準ライブラリから呼び出すと以下のようになる。

```sql
sqlite3.connect.execute("insert into users values(?,?)", (0,'A'))
sqlite3.connect.executemany("insert into users values(?,?)", [(0,'A'),(1,'B')])
```

　これをなるだけ簡単に呼び出せるようラップしたのが`insert`メソッド。表名と値を渡すだけでいい。`insert into ...`の文は書かなくていい。細かい構文を忘れていいし、列の数だけ`?`を書く不毛な処理も書かずに済む。

　さらに渡されたデータをSQLite3に最適化した型へキャストする。対象は`bool`と`datetime`のみ。それ以外はそのまま渡す。

　これらを実装したのが以下。

```python
class NtLite:
    def _cast_exec(self, sql, params): return self.exec(sql, CastPy.to_sql_by_row(params))
    def _cast_execm(self, sql, params): return self.execm(sql, CastPy.to_sql_by_rows(params))
    def _insert_sql(self, table_name, params): return f"insert into {table_name} values ({','.join('?' * len(params))})"
    def insert(self, table_name, params): return self._cast_exec(self._insert_sql(table_name, params), params)
    def inserts(self, table_name, params): return self._cast_execm(self._insert_sql(table_name, params), params)
```

# 疑問

　Decimal型もおそらく

# 課題

　日付型のキャストについて不備がある。タイムゾーンが考慮されていない。SQLite3側はUTC標準時を想定しているが、Python側ではローカル日時がデフォルトである。UTC標準時にするにはそのタイムゾーン情報を渡す必要がある。他にもUTC時刻とローカル時刻の変換や、Pythonの`datetime.fromisoformat()`がISO-8601の末尾`Z`形式に対応していないなどの罠が色々ある。

　Pythonにおける日付型の問題を解決して確実にUTC標準時を渡せるようにしたい。そのためのコードを書きたい。

