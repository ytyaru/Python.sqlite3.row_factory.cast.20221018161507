# 真偽値

　真偽値における型問題について。

　SQLite3にbool型はない。よって以下のように`integer`とチェック制約で代用する。

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

　SQLite3は型を柔軟にキャストするので、以下のように文字列としてセットしても数値になる。なぜかSQLite3の公式ドキュメントではこれを自画自賛している。何が便利なのかよくわからない。理解していないと想定外のキャストが発生しバグになるので開発者の負担が大きくなるのでは？

　文字列型で試してみると、数値型にキャストされる。`'0'`,`'1'`ではエラーなく挿入されてしまう。

```sql
insert into t values('0');
insert into t values('1');
insert into t values('2');
```
```sh
Runtime error: CHECK constraint failed: is_male=0 or is_male=1 (19)
```

　先頭に`'0'`を付与した文字列でも同じく数値型に変換されるらしい。

```sql
insert into t values('00');
insert into t values('01');
insert into t values('02');
```
```sh
Runtime error: CHECK constraint failed: is_male=0 or is_male=1 (19)
```

　SQLite3的にはこれがとても便利であり他のRDBMSにない機能だと主張している。

　ところが、型安全がもてはやされている昨今の現状に対応したのか、[STRICT Tables][]なるものができた。

[STRICT Tables]:https://www.sqlite.org/stricttables.html

　これは勝手にテキストを数値にキャストしないようにする仕組みらしい。ただ、今までそれをウリにしてきたので混乱するし、後方互換もなくなる。この[STRICT Tables][]を含んだDBファイルは3.37.0 (2021-11-27)以降のバージョンでないと読み取れない。他のRDBMSとも異なる仕様なのでSQL文共通性がなくなる。よって[STRICT Tables][]を使おうとは今のところ思えない。

