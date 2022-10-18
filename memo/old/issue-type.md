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

