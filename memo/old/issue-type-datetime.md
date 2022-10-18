# 日付型

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

## 問題

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

　これはUTC時刻である。深夜3時に実行したわけではない。実行したとき日本時刻では`12:11:42`だった。しかしそれをUTC時刻に直され9時間前のものになり`03:11:42`と出た。このようにSQLite3の時刻はUTCが基本である。

　UTC時刻なのは構わない。ローカル日時に変換すれば日本での時刻を計算できる。ただ、書式のせいでUTCなのかローカル時刻なのか判断できない。SQLite3の中で日付型ならいいが、単なるテキストなのでなおさら。

　もしISO-8601形式なら`yyyy-MM-ddTHH:mm:ssZ`のように末尾に`Z`をつけることでUTC標準時であることを示していた所。

SQLite3|ISO-8601
-------|--------
`yyyy-MM-dd HH:mm:ss`|`yyyy-MM-ddTHH:mm:ssZ`

　なぜSQLite3はこのような書式なのか知らないが、おそらくデータ量が少なく、人に理解しやすい形式ということなのだろう。

　SQLite3で保存するとき、どの書式にすべきか。

書式|メリット
----|--------
`yyyy-MM-dd HH:mm:ss`|SQLiteの`CURRENT_TIMESTAMP`結果と変換せず比較できる
`yyyy-MM-ddTHH:mm:ssZ`|ISO-8601形式に対応したプログラミング言語ならすぐキャストできる

　今回は前者のSQLite形式にしたほうが良いと判断した。

　一見ISO-8601形式のほうが良さげに見えるが、もしSQL文脈内だけでサクッと集計したいと思ったときSQLite日付書式のほうが便利。たとえば以下のように記事の公開日時をセットした`published`列があったとする。これを現在日時と比較してそれ以下なら公開する、といったことができる。ようするに日付のテキスト書式を統一しておけば、わざわざ書式変換せずとも比較できる。

```sql
published <= CURRENT_TIMESTAMP
```

　もし`published`列の日付書式を末尾`Z`など他の形式にしていたら、以下のようにSQLite3の日付形式に直してから比較する必要がある。

```sql
strftime('%Y-%m-%d %H:%M:%S', published) <= CURRENT_TIMESTAMP
```

　日付計算が必要な場合はもっと煩雑になる。たとえば以下のように現在日時から3日前のデータのみ対象にしたいとき等。もし書式が統一されていれば`strftime`関数を使う必要はない。

```sql
datetime(CURRENT_TIMESTAMP, '-3 days') < published
```
```sql
datetime(CURRENT_TIMESTAMP, '-3 days') < strftime('%Y-%m-%d %H:%M:%S', published)
```

　こうした面倒をなくすためにSQLiteの日付形式で保存するのが得策だと考えた。

　ただ、SQLiteの日付形式ではUTC時刻なのかローカル日時なのかわからない。むしろタイムゾーン情報がないため、ローカル日時と判断されてしまうだろう。

　SQLite3文脈内では問題ない。ただ、他のプログラミング言語でデータを使い日付型にキャストするとき問題になる。

　そこで以下のようにSQLite3日付書式をISO-8601書式に変換する。方法はスペースを`T`に置換し、末尾に`Z`を付与するだけ。

* `yyyy-MM-dd HH:mm:ss`→`yyyy-MM-ddTHH:mm:ssZ`

　ISO-8601形式には柔軟性があり同じ時刻であっても別の表記ができる。たとえば末尾`Z`のUTC標準時はほかにも`+00:00`や`-00:00`,`+00:00:00`等と書ける。

　とはいえ、これらの書式すべてに対応するのは面倒なので末尾`Z`形式に統一したい。

　しかしここで残念なお知らせ。Pythonは標準でローカル時刻を返すし、末尾`Z`形式に非対応。そこで、PythonでUTC時刻を取得し、代わりの日付書式`+00:00`に変換する必要がある。以下のように。

```python
# SQLite3日付書式データを取得する
published = sqlite3.connect.execute("select published from articles where id=1;").fetchone()[0]

# SQLite3日付書式をPythonのisoformat
pyiso = published.replace(' ', 'T') + '+00:00'

# Pythonの日付型に変換する
datetime.fromisoformat(pyiso)
```

　もしSQLite3にISO-8601形式（末尾`Z`）で保存しても、Pythonではそれに非対応なのでメリットがない。どうせ変換処理を書かねばならないなら、SQLite3に保存するのはSQLite日付書式のほうがいい。

　きっとPythonのサードパーティ製ライブラリを使えば解決できると思うが、わざわざこれだけのために大きなパッケージをインストールするのも嫌。

　他のプログラミング言語では問題ないかもしれない。むしろ他の言語ではタイムゾーンがないためローカル時刻と判断されてしまう。なのでそれぞれPythonと同じような処理を書かねばならなくなるだろう。

　それでもSQLite3日付形式が最善と判断した。SQLite3文脈内で使いやすいし、タイムゾーンデータが不要な分だけデータ量も少なくなるから。

----------------------------------------------------------------------------------























　また、加算、除算などの計算は関数で行う。

```sql
select datetime('2000-01-01', '+1 days', '-4 hours') as datetime;
```
```sql
2000-01-01 20:00:00
```




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

