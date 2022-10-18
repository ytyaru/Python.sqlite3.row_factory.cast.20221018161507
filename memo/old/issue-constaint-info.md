# 制約の取得について

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

　[stackoverflowにも質問がある][]が、やはり`sqlite_master`表の`create table`文を解析するしかないという。これを解析するのは大変すぎる。よって対応しない。

