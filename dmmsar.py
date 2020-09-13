#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
指定されたIDやURLでDMMから作品一覧を取得し、ウィキテキストを作成する。


書式:
dmmsar.py (-A|-S|-L|-K|-U) [キーワード ...] [オプション...]


DMMから女優、シリーズ、メーカー、あるいはレーベルのID(DMMで割り当てて
いるやつ)を直接指定してその全作品の素人系総合wiki用ウィキテキストを
まとめて作成する。
作品一覧だけを取得したり、ファイルから読み込むこともできる。

デフォルトでイメージビデオ、総集編、復刻盤、DMM/数量限定、アウトレット
製品は除外を試みる(-m オプションで調整可)。ただしすべて除外できるとは
限らない。
総集編の判別は:
・品番のプレフィクスがあらかじめ登録されている総集編のものと一致
・ジャンルに総集編がある
・タイトルに「総集編」「BEST」などの関連ワードがある
・タイトルに「10人/名」以上/「10本番/SEX」以上/「20(連)発/射」以上/
「4時間」以上/「240分」以上/「10組」以上/「n選」のうち2つ以上含まれている
・収録時間が約4時間以上(200分超)なら総集編しかなさそうなメーカーである
ただし、タイトルに「撮りおろし/下ろし/卸し」が含まれていれば除外しない。
実際に撮りおろしが含まれていてもタイトルにそれが書いてないと除外してしまう。


注意:
一度取得したページはキャッシュされ(一部のページを除く)、Wikiなら
最大2時間、それ以外は24時間はそれを利用する。
内部でサイトごとにアクセスに5秒の間隔を置いている。
この間隔を短く/無くしたりして短時間に大量の情報を取得した場合、
(D)DoS攻撃とみなされて通報されるかもしれないので注意。


引数:
キーワード(ID/URL/品番/ファイルパス)
    -A/-S/-K/-L を指定した場合は取得するそれのIDか、その一覧ページの
    URLを指定する。
    -U を指定した場合はDMMの任意の作品一覧ページのURLを指定する。
    --cid を指定した場合は cid の範囲を指定する(--cid オプションを参照)。

    IDはDMM上でそれぞれでの一覧を表示した時にそのURLからわかる(id=)。
    IDを複数指定した場合、それらをまとめて1つの一覧を作成する。
    これは改名しているがDMM上で統合されていない女優の作品一覧の作成を
    想定しているため。

    -i/-w を指定した場合はファイルのパスを指定する。パスが指定されない
    場合は標準入力から読み込む。


オプション:
-A, --actress (女優IDで一覧取得)
-S, --series  (シリーズIDで一覧取得)
-L, --label   (レーベルIDで一覧取得)
-K, --maker   (メーカーIDで一覧取得)
-U, --url     (指定したURLのページからそのまま取得)
    検索方法。どれか一つだけ指定できる。
    -A/-S/-K/-L で女優/シリーズ/メーカー/あるいはレーベルのいずれかの
    DMM上のID(またはURL)指定で一覧を取得する。
    キーワードに女優/シリーズ/レーベル/メーカー一覧ページのURLを指定
    すると -A/-S/-L/-K を自動判定する。
    -U では、指定されたURLのページからそのまま取得する。

-i, --from-tsv
    作品情報の一覧をインポートファイル(TSV)から取得する。

    インポートファイル形式:
    --tsv 指定で出力される一覧の形式に情報を追加するイメージ。タブ区切り。

    ファイルフォーマット:
    <カラム> <内容>
        0*   DMM作品ページのURL
        1*   タイトル
        2    品番
        3    出演者[,出演者 ...] (書式は dmm2ssw.py の -a オプション参照)
        4    出演者数
        5    監督[,監督 ...]
        6    備考 (NOTE)[,備考...] (要素ごとにカンマ区切り)
    *:必須

    タイトルとURLは必須。ただしタイトルの先頭に __ (アンダースコア2個)を
    つけておくと最終的に出力されるウィキテキストには使用されず、DMM上の
    タイトルが採用されるので、一意の文字列であれば何でも良い。
    レコードあたりタブが3個以上あれば他の情報はなくてもよい。
    文字列がなくてもタブがあるだけで「データのないカラム」があると
    みなされる。

-w, --from-wiki
    素人総合wikiの表形式のウィキテキストから取得する。
    wikiとDMM上の情報をマージできる。
    セルが結合されている表には未対応。

--cid
    作成する作品のDMM上の品番(cid)を直接指定する。
    キーワードの第一引数に"{}"が含まれる場合は、引数を
    "品番の基底文字列" "開始番号" "終了番号" ["ステップ"]
    とみなす。
    例) dmmsar.py -L --cid "h_244saba{}" "080" "085"
    ⇒ cid=h_244saba080,081,082,083,084,085の情報を取得する。
    {} が含まれない場合は単に品番の羅列とみなし、それぞれの情報を
    取得する。
    指定した品番の作品ページが見つからなかったら発売前の作品とみなし
    DMMへのリンクは作成する。
    --service が指定されていない場合DVDセル版(dvd)とみなす。
    -U 指定時はこのオプションは指定できない。

--cid-l
    --cid と同じだが、指定した品番の作品ページが見つからない場合は
    発売されなかったあるいは発売中止になったものとしてリンクを作成
    しない。

-o, --out ファイル名のベース
    指定されたファイルに出力する。未指定時は標準出力に出力する。
    ウィキテキストを作成した場合、実際に出力されるファイル名は、
    女優ページ用なら
     識別子 + _actress + ページ数 + 拡張子
    レーベル/シリーズ一覧ページ用なら
     識別子 + _table + ページ数 + 拡張子
    となる。
    また、--split (デフォルトは200) の件数ごとに番号を付けてファイルを
    分ける。
    例) moodyz.wiki ⇒ moodyz_table.1.wiki

-r, --replace
    出力ファイル名と同名のファイルが存在する場合それを上書きする。

-t, --table
    女優ページ用ではなく、一覧ページ用に表形式でウィキテキストを
    出力する。2個以上指定すると両方を作成する。
    --tsv と同時に指定できない。

--tsv
    ウィキテキストを作成せず、作品名とページURLの一覧(タブ区切り)を
    出力する。
    これで出力した一覧(を修正したもの)を -i オプションの入力とできる。
    -t/-tt と同時に指定できない。

--service {dvd,rental,video,ama,all}
    検索するサービスの種類を指定する。指定できるのは以下のうちどれか
    一つ。
     dvd     DVD通販 (-A/-S/-K/-L のデフォルト)
     rental  DVDレンタル
     video   動画-ビデオ
     ama     動画-素人
    -U/-i/-w を指定した場合は無視される。
    キーワードにURLが与えられていれば指定不要。

-m, --disable-omit
    イメージビデオを除外しない。2個指定すると総集編作品も、3個
    指定するとアウトレットも、4個指定すると復刻盤も、5個指定すると
    限定盤も除外しない。
    除外もれ/除外しないもれが発生する場合もある。

--start-pid 品番(例:JMD-112)
    データ作成開始品番。一覧取得後、この品番とプレフィクスが同じで
    番号がこれ以上のものが見つかればそれ以降のものだけ作成する。
    大文字小文字は区別しない。
    DMM作品ページのURL(cid=)から品番を自動作成しているが、URLの
    cidが実際の品番と異なることがあり、このとき抜けやズレが発生する
    場合がある。
    より厳密にチェックする場合は --start-pid-s オプションを使用する。

--start-pid-s 品番(例:JMD-112)
    --start-pid をより厳密にチェックする。
    作品ごとに作品ページを見に行くので開始品番を見つけるまでの時間が
    よりかかる。

--start-cid DMM上の品番(例:15jmd112so)
    --start-pid と似ているが、DMM上の品番でチェックする。
    DMM上の品番とは、DMMサイト上でDMMが割り振った品番のこと。
    大文字小文字は区別しない。
    DMM作品ページのURL(cid=)から品番を取得しているが、URLのcidが
    実際の品番と異なることがあり、このとき抜けやズレが発生する場合が
    ある。

-e, --last-pid 品番
    Wiki上ですでに作成済みの作品の最後の品番。一覧取得後、この品番が
    みつかるまでスキップし、そのつぎの作品以降を作成する。
    大文字小文字は区別しない。
    DMM作品ページのURL(cid=)から品番を自動作成しているが、URLの
    cidが実際の品番と異なることがあり、このとき抜けやズレが発生する
    場合がある。
    より厳密にチェックする場合は --last-pid-s オプションを使用する。

--last-cid DMM上の品番(例:15jmd112so)
    --last-pid と似ているが、DMM上の品番でチェックする。
    DMM上の品番とは、DMMサイト上でDMMが割り振った品番のこと。
    大文字小文字は区別しない。
    DMM作品ページのURL(cid=)から品番を取得しているが、URLのcidが
    実際の品番と異なることがあり、このとき抜けやズレが発生する場合が
    ある。

--start-date YYYYMMDD
    データ作成開始日。発売/貸出/配信開始日がこの指定日以降のものだけ
    作成する。

--existings-html Wiki一覧ページのURL/HTML [URL/HTML ...]
    Wikiの一覧ページを読み込み、まだWikiに追加されていない作品情報のみ
    作成する。

--filter-pid フィルターパターン
    品番がフィルターパターン(Python正規表現)にマッチしたものだけ作成する。
    大文字小文字は区別しない。
    DMM作品ページのURLから品番を取得しているが、URLのcidが実際の品番と
    異なることがあり、このとき抜けやズレが発生する場合がある。
    より厳密にチェックする場合は --filter-pid-s オプションを使用する。

--filter-pid-s フィルターパターン
    --filter-pid をより厳密にチェックする。
    作品ごとに作品ページを見に行くのでより時間がかかる。

--filter-cid フィルターパターン
    DMM上の品番(cid)がフィルターパターン(Python正規表現)にマッチした
    ものだけ作成する。大文字小文字は区別しない。
    DMM作品ページのURLから品番を取得しているが、URLのcidが実際の品番と
    異なることがあり、このとき抜けやズレが発生する場合がある。

--filter-title フィルターパターン
    作品名がフィルターパターン(Python正規表現)にマッチしたものだけ
    作成する。大文字小文字は区別しない。

--not-in-series
    シリーズ化されていない作品のみ作成する(-L/-K/-U 指定時のみ)。
    見つかったシリーズ名の一覧を最後に出力する。

--row 行番号
    表形式を作成する時の最初のデータのみなし行位置。10件毎のヘッダー
    挿入やページ分割はこの値を基準に決定される。

--pages-last ページ数
    DMM上で一覧ページを、新着順にこのページ数分だけデータを取得し
    作成する。1ページあたり120件。
    --start-pid/--start-cid が指定された場合、該当する pid、cid を
    発見したページ+1ページがこの値を下回った場合はそこで取得を停止する。

--join-tsv ファイル [ファイル ...] (TSV)
    DMMから得た作品と(URLが)同じ作品がファイル内にあった場合、
    DMMからは取得できなかった情報がファイル側にあればそれで補完する
    (NOTEも含む)。
    ファイル形式については -i オプションの「インポートファイル形式」参照。

--join-wiki ウィキテキスト [ウィキテキスト ...] (一覧ページの表形式)
    DMMから得た作品と(URLが)同じ作品がウィキテキスト内にあった場合、
    DMMからは取得できなかった情報がウィキテキスト側にあればそれで
    補完する(NOTEも含む)。
    セルが結合されている表には未対応。

--join-html Wiki一覧ページのURL/HTML [URL/HTML ...] (一覧ページのHTML)
    DMMから得た作品と(URLが)同じ作品が、Wikiの一覧ページにあった場合、
    DMMからは取得できなかった情報がWiki側にあればそれで補完する
    (NOTEも含む)。
    一覧ページを保存したHTMLのファイルでも可。
    セルが結合されている表には未対応。

--hunter
    --join-*オプション指定と同時にこのオプションを指定すると
    作品タイトルは補完ファイル内のものを優先する。ただし
    補完ファイル内の作品タイトルが「__」ではじまる場合は無視され
    DMMのものが採用される。

--sort-key {release,pid,title}
    出力する時の並び替えキー。
    デフォルトは品番順(pid)

-d, --add-dir-col
    DIRECTORカラムを出力する。
    -t/-tt オプションが与えられた時用。

--note 文字列
    女優ページ用なら最後に、一覧ページの表形式ならNOTEカラムに
    文字列を追加する。
    全作品に同じ文字列
    データは固定の文字列と以下の変数を指定できる。
    これら変数はウィキテキスト作成時に対応する文字列に展開される。
    @{media}  メディアの種類
    @{time}   収録時間
    @{series} シリーズ名
    @{maker}  メーカー名
    @{label}  レーベル名
    @{cid}    DMM上の品番

--add-column [カラム名[:データ] [カラム名[:データ] ...]]
    表形式に任意のカラムを追加する。
    -t/-tt を指定しない場合は無視される。
    書式はカラム名のあとに : とともに各カラム内に出力するデータを
    指定できる。
    データの書式は --note オプションと同じ。

-s, --series-link [シリーズ一覧ページ名]
    作成する女優ページ用ウィキテキストのシリーズ一覧ページへの
    リンクを強制的に追加・変更する。

-l, --label-link [レーベル一覧ページ名]
    作成する女優ページ用ウィキテキストのレーベル一覧ページへの
    リンクを強制的に追加・変更する。

--linklabel 一覧ページへのリンクのラベル名
    作品一覧ページへのリンクの表示名(「レーベル一覧」「シリーズ一覧」
    など)をここで指定した文字列に置き換える。

--hide-list
    女優ページ用ウィキテキストにシリーズ/レーベル一覧へのリンクを
    追加しない。

--pid-regex パターン 置換文字列
    -t/-tt/-w を指定した場合のみ有効。
    dmm2ssw.py で行う品番の自動置き換えパターンでは対応できない場合用。
    作品のDMM上での品番情報(cid=)がパターン(python正規表現)に
    マッチしたら置換文字列で置き換える。
    マッチング時英字の大文字・小文字は区別しないが、マッチした場合
    すべて大文字化される。
    一部のイレギュラーなレーベルについては個別に対応している
    (dmm2ssw.pyの説明参照)。

--subtitle-regex パターン 置換文字列
    -t/-tt を指定した場合のみ有効。
    このオプションが指定されると、タイトルの文字列をを元に引数に従って
    副題を生成する。
    パターン(python正規表現)にマッチしたものを置換文字列で置き換える。
    マッチしなかったら何もしない。

--disable-series-guide
    メーカー/レーベル一覧ページ(表形式)でのシリーズ作品のシリーズ一覧
    ページへのガイドを追加しない

--without-header
    先頭にヘッダ情報を出力しない。
    -w を指定した時は無視される。

--split ページあたりのタイトル数
    出力されるタイトル数がページあたりのタイトル数を超えるたび、空行と
    ヘッダを挿入する。
    デフォルトは200。
    0を指定するとヘッダ挿入を行わない。
    --without-header 指定時は無視される(0と同じ)。

-f, --disable-follow-redirect
    取得した出演者名のwikiページがリダイレクトページかどうか
    チェックしない。
    指定しない場合チェックし、そうであればリダイレクト先へのリンクを
    取得して付加する。
    詳細はdmm2ssw.pyの説明参照。

--enable-check-smm
    このオプションが与えられるとDMM上に出演者情報がないときにSMMを検索する。
    (https://supermediamall.com/ のドメイン移行及び仕様変更のため現在動作未確認)

--check-rental
    レンタル先行メーカーなのにレンタル版以外が指定されていた場合
    レンタル版のリリース情報をチェックしてレンタルが早ければ
    そちらに置き換える。
    デフォルトの挙動はdmm2ssw.pyと逆。

--disable-check-related'
    他メディアやサービスの情報収集を行わない。

--disable-check-listpage
    Wiki上の実際の一覧ページを探さない。

--disable-check-bd
    デフォルトでは、Blu-ray版製品だったとき、DVD版がないか確認し、
    DVD版があればBlu-ray版の情報は作成しない(DVD版の方で備考として
    Blu-ray版へのリンクを付記する)が、このオプションが与えられると
    それを行わず、DVD版と同様に(DVD版があれば両方を)作成する。

--fastest
    処理時間に影響する(ウェブページへアクセスする)あらゆる補助処理を
    行わない。

--recheck
    「ページが見つからない」とキャッシュされているページを
    再チェックする。

-c, --copy
    作成したウィキテキストをクリップボードへコピーする。
    Python モジュール pyperclip が必要。

-b, --browser
    ページ名が確定している場合その名前のWikiページを開く。
    --tsv など、ページ名が解決できない場合は無視される。

-C, --clear-cache
    dmm2ssw.py の説明参照。
    キャッシュを終了時に削除する。

-v, --verbose
    デバッグ用情報を出力する。

-V, --version
    バージョン情報を表示して終了する。

-h, --help
    ヘルプメッセージを表示して終了する。


使用例:
 1)
    ・女優「鈴村あいり」の女優ページ用ウィキテキストを作成する。
    ・作成後にWikiの「鈴村あいり」のページをウェブブラウザで開く。(-b)

    dmmsar.py "http://www.dmm.co.jp/mono/dvd/-/list/=/article=actress/id=1019076/" -b

 2)
    ・シリーズ「バコバコ風俗」の女優ページ用とシリーズ一覧ページ用両方のウィキテキストを作成する。(-tt)
    ・作成したウィキテキストをファイル名「bakobako.wiki」に保存する(実際のファイル名は「bakobako_actress.1.wiki」と「bakobako_table.1.wiki」になる)。(-o)

    dmmsar.py "http://www.dmm.co.jp/mono/dvd/-/list/=/article=series/id=8225/" -tt -o bakobako.wiki

 3)
    ・女優「椎名ゆな」の女優ページ用ウィキテキストを作成する。
    ・2014年1月1日以降にリリースされた作品分だけ作成する。(--start-date)

    dmmsar.py "http://www.dmm.co.jp/mono/dvd/-/list/=/article=actress/id=30317/" --start-date 20140101

 4)
    ・シリーズ「PREMIUM STYLISH SOAP」のシリーズ一覧ページ用ウィキテキストを作成する。(-t)
    ・品番 PGD-702 以降の作品分だけ作成する。(--start-pid)
    ・PGD-702 はシリーズ第41作目であることを指定する(表形式の10件ごとのヘッダ挿入用)。(--row)

    dmmsar.py "http://www.dmm.co.jp/mono/dvd/-/list/=/article=series/id=6642/sort=date/" -t --start-pid "pgd-702" --row 41

 5)
    ・素人動画レーベル「恋する花嫁」のレーベル一覧ページ用ウィキテキストを作成する。(-Lt)
    ・cid(DMM上の品番)が khy070 から khy090 までの作品分を作成する。(--cid)
    ・URL指定がなく素人動画レーベルなのでサービス「ama」を指定する。(--service)

    dmmsar.py -Lt --cid "khy{}" "070" "090" --service "ama"

 6)
    ・レーベル「S級素人」のレーベル一覧ページ用ウィキテキストを作成する。(-t)
    ・品番のプレフィクスが SABA のものだけ作成する。(--filter-pid)
    ・品番が SABA-125 以降の作品分だけ作成する。(--start-pid)
    ・総集編を除外しない。(-mm)

    dmmsar.py "http://www.dmm.co.jp/mono/dvd/-/list/=/article=label/id=8893/" -tmm --filter-pid "^saba" --start-pid "saba-125" --row 125

"""
import sys
import re
import argparse
from operator import attrgetter
from itertools import zip_longest, compress
from collections import OrderedDict, namedtuple

import libssw
import dmm2ssw

__version__ = 20151010

OWNNAME = libssw.ownname(__file__)
VERBOSE = 0

emsg = libssw.Emsg(OWNNAME)

MSGLEVEL = {'E': 'ERROR',
            'W': 'WARN',
            'I': 'INFO'}

ACTINFOPAGE = 'https://actress.dmm.co.jp/-/detail/=/actress_id={}/'
ACTLISTPAGE = 'https://www.dmm.co.jp/mono/dvd/-/list/=/article=actress/id={}/sort=date/'

SPLIT_DEFAULT = 200

# sub_sort = (re.compile(r'(?<=/sort=)\w+'), 'date')

re_actdelim = re.compile(r'[（、]')


MakeType = namedtuple('MakeType', 'actress,table')
OutFile = namedtuple('OutFile', 'actr,tbl,suffix,writemode')


verbose = None


def get_args(argv):
    """コマンドライン引数の解釈"""
    global VERBOSE
    global verbose

    argparser = argparse.ArgumentParser(description='DMMから検索して作品一覧を作成する')

    # 処理タイプ
    retrieval = argparser.add_mutually_exclusive_group()
    retrieval.add_argument('-A', '--actress',
                           help='女優IDで一覧取得',
                           action='store_const',
                           dest='retrieval',
                           const='actress')
    retrieval.add_argument('-S', '--series',
                           help='シリーズIDで一覧取得',
                           action='store_const',
                           dest='retrieval',
                           const='series')
    retrieval.add_argument('-L', '--label',
                           help='レーベルIDで一覧取得',
                           action='store_const',
                           dest='retrieval',
                           const='label')
    retrieval.add_argument('-K', '--maker',
                           help='メーカーIDで一覧取得',
                           action='store_const',
                           dest='retrieval',
                           const='maker')
    retrieval.add_argument('-U', '--url',
                           help='していたURLページからそのまま取得',
                           action='store_const',
                           dest='retrieval',
                           const='url')

    # ファイル入力
    from_file = argparser.add_mutually_exclusive_group()
    from_file.add_argument('-i', '--from-tsv',
                           help='TSVファイルから入力',
                           action='store_true')
    from_file.add_argument('-w', '--from-wiki',
                           help='素人総合wikiのウィキテキスト(表形式)から入力',
                           action='store_true')
    from_file.add_argument('--cid',
                           help='DMM上の品番(cid)指定で取得(ページが見つからなくてもリンクは作成する)',
                           action='store_true')
    from_file.add_argument('--cid-l',
                           help='DMM上の品番(cid)指定で取得(ページが見つからなければリンクは作成しない)',
                           action='store_true')

    argparser.add_argument('keyword',
                           help='検索キーワード、ID、品番、URL、またはファイル名',
                           metavar='KEYWORD',
                           nargs='*')

    # ファイル出力
    argparser.add_argument('-o', '--out',
                           help='ファイルに出力 (未指定時は標準出力へ出力)',
                           metavar='FILE')
    argparser.add_argument('-r', '--replace',
                           help='出力ファイルと同名のファイルがあった場合上書きする',
                           action='store_true')

    # 出力形式
    table = argparser.add_mutually_exclusive_group()
    table.add_argument('-t', '--table',
                       help='一覧ページ用の表形式でウィキテキストを作成する, '
                       '2個以上指定すると両方作成する',
                       action='count',
                       default=0)
    table.add_argument('--tsv',
                       help='ウィキテキストを生成せず、タブ区切りの一覧を出力する',
                       action='store_false',
                       dest='wikitext',
                       default=True)

    # データ取得先
    argparser.add_argument('--service',
                           help='一覧を取得するサービスを指定する (デフォルト: '
                           'KEYWORD にURLが与えられればそれから自動判定、'
                           'それ以外なら dvd)',
                           choices=('dvd', 'rental', 'video', 'ama', 'all'))

    # 作品データの除外基準
    argparser.add_argument('-m', '--disable-omit',
                           help='IVを除外しない、2個指定すると総集編も、'
                           '3個指定するとアウトレット版も、'
                           '4個指定すると限定盤も除外しない',
                           dest='no_omit',
                           action='count',
                           default=0)

    # データ作成範囲基準
    id_type = argparser.add_mutually_exclusive_group()
    id_type.add_argument('--start-pid',
                         help='データ作成開始品番(例:JMD-112)',
                         metavar='PID',
                         default='')
    id_type.add_argument('--start-pid-s',
                         help='データ作成開始品番(厳密にチェック)',
                         metavar='PID',
                         default='')
    id_type.add_argument('--start-cid',
                         help='データ作成開始品番(DMM上の品番, 例:15jmd112so)',
                         metavar='CID',
                         default='')
    id_type.add_argument('-e', '--last-pid',
                         help='作成済み作品情報の最後の品番',
                         metavar='PID',
                         default='')
    id_type.add_argument('--last-cid',
                         help='作成済み作品情報の最後の品番(DMM上の品番)',
                         metavar='CID',
                         default='')

    argparser.add_argument('--start-date',
                           help='データ作成対象開始リリース日',
                           metavar='YYYYMMDD')
    argparser.add_argument('--existings-html',
                           help='Wikiの一覧ページに既にある作品の情報は作成しない',
                           nargs='+',
                           metavar='URL/HTML')

    filters = argparser.add_mutually_exclusive_group()
    filters.add_argument('--filter-pid',
                         help='品番(pid)がパターン(正規表現)とマッチしたものだけ作成',
                         metavar='PATTERN')
    filters.add_argument('--filter-pid-s',
                         help='品番(pid)がパターン(正規表現)とマッチしたものだけ作成(厳密にチェク)',
                         metavar='PATTERN')
    filters.add_argument('--filter-cid',
                         help='DMM上の品番(cid)がパターン(正規表現)とマッチしたものだけ作成',
                         metavar='PATTERN')
    filters.add_argument('--filter-title',
                         help='作品名がパターン(正規表現)とマッチしたものだけ作成',
                         metavar='PATTERN')

    argparser.add_argument('--not-in-series', '--n-i-s',
                           help='シリーズに所属していないもののみ作成(-K/-L/-U 指定時)',
                           action='store_true',
                           dest='n_i_s')

    argparser.add_argument('--row',
                           help='先頭行のみなし行開始位置 (-t/-tt 指定時のみ)',
                           type=int,
                           default=0)  # --row のデフォルトは後で決定

    argparser.add_argument('--pages-last',
                           help='データ収集ページ数(最新からPAGEページ分を収集)',
                           type=int,
                           default=0,
                           metavar='PAGE')

    # 外部からデータ補完
    argparser.add_argument('--join-tsv',
                           help='テキストファイル(TSV)でデータを補完する',
                           nargs='+',
                           metavar='FILE')
    argparser.add_argument('--join-wiki',
                           help='素人系総合Wikiのウィキテキスト(表形式)でデータを補完する',
                           nargs='+',
                           metavar='FILE')
    argparser.add_argument('--join-html',
                           help='素人系総合Wikiの一覧ページを読み込んで補完する',
                           nargs='+',
                           metavar='URL/HTML')

    argparser.add_argument('--hunter',
                           help='--join-*オプションを指定したときに作品タイトルは補完ファイルの'
                           'ものを採用する(Hunter系用)',
                           action='store_true')

    # ソート基準
    argparser.add_argument('--sort-key',
                           help='並び替えキー項目',
                           choices=('release', 'pid', 'title'))

    argparser.add_argument('--note',
                           help='エントリの最後かNOTEカラムにデータを追加する',
                           nargs='+',
                           metavar='DATA',
                           default=[])
    # 表形式出力装飾
    argparser.add_argument('-d', '--add-dir-col',
                           help='DIRECTORカラムを追加する (-t/-tt 指定時のみ)',
                           dest='dir_col',
                           action='store_true')
    argparser.add_argument('--add-column',
                           help='表に任意のカラムとデータを追加する (-t/-tt 指定時のみ)',
                           nargs='+',
                           metavar='COLUMN:DATA',
                           default=[])

    # 一覧ページへのリンク追加
    list_page = argparser.add_mutually_exclusive_group()
    list_page.add_argument('-s', '--series-link',
                           help='女優ページ形式でシリーズ一覧へのリンクを置き換え',
                           dest='series')
    list_page.add_argument('-l', '--label-link',
                           help='女優ページ形式でレーベル一覧へのリンクを置き換え',
                           dest='label')
    list_page.add_argument('--hide-list',
                           help='女優ページ形式で一覧ページへのリンクを追加しない',
                           action='store_true',
                           default=False)

    argparser.add_argument('--linklabel',
                           help='一覧ページへのリンクの表示名を置き換える')

    # 品番・副題など自動調整設定
    argparser.add_argument('--pid-regex',
                           help='品番自動生成のカスタム正規表現 (-t/-tt/-w 指定時のみ)',
                           nargs=2,
                           metavar=('PATTERN', 'REPL'))
    argparser.add_argument('--subtitle-regex',
                           help='副題自動生成のカスタム正規表現 (-t/-tt 指定時のみ)',
                           nargs=2,
                           metavar=('PATTERN', 'REPL'))
    argparser.add_argument('--disable-series-guide',
                           help='レーベル一覧ページからシリーズ一覧ページへのガイドを'
                           '追加しない (-t/-tt 指定時のみ)',
                           dest='series_guide',
                           action='store_false',
                           default=True)

    # 出力装飾
    argparser.add_argument('--without-header',
                           help='ヘッダ情報を出力しない',
                           dest='header',
                           action='store_false',
                           default=True)
    argparser.add_argument('--split',
                           help='1ページあたりのタイトル数 (デフォルト {})'.format(
                               SPLIT_DEFAULT),
                           type=int,
                           default=SPLIT_DEFAULT)

    # 補助チェック
    argparser.add_argument('-f', '--disable-follow-redirect',
                           help='ページのリダイレクト先をチェックしない',
                           dest='follow_rdr',
                           action='store_false',
                           default=True)
    argparser.add_argument('--enable-check-smm',
                           help='出演者情報がないときにSMMを検索する',
                           action='store_true',
                           dest='smm',
                           default=False)
    argparser.add_argument('--check-rental',
                           help='レンタル先行メーカーでレンタル版じゃなかったのとき'
                           'レンタル版のリリースをチェックする',
                           action='store_true',
                           default=False)
    argparser.add_argument('--disable-check-bd',
                           help='Blu-ray版のときDVD版があってもパスしない',
                           action='store_false',
                           dest='pass_bd',
                           default=True)
    argparser.add_argument('--disable-check-listpage',
                           help='Wiki上の実際の一覧ページを探さない',
                           dest='check_listpage',
                           action='store_false',
                           default=True)
    argparser.add_argument('--disable-check-related',
                           help='他メディアやサービスの情報収集を行わない',
                           dest='check_rltd',
                           action='store_false',
                           default=True)
    argparser.add_argument('--disable-longtitle',
                           help='アパッチ、SCOOPの長いタイトルを補完しない',
                           dest='longtitle',
                           action='store_false',
                           default=True)
    argparser.add_argument('--fastest',
                           help='ウェブにアクセスするあらゆる補助処理を行わない',
                           action='store_true')

    argparser.add_argument('--recheck',
                           help='キャッシュしているリダイレクト先を強制再チェック',
                           action='store_true')

    argparser.add_argument('-c', '--copy',
                           help='作成したウィキテキストをクリップボードへコピーする(pyperclipが必要)',
                           action='store_true')

    # ブラウザ制御
    argparser.add_argument('-b', '--browser',
                           help='生成後、wikiのページをウェブブラウザで開く',
                           action='store_true')

    # その他
    argparser.add_argument('-C', '--clear-cache',
                           help='プログラム終了時にキャッシュをクリアする',
                           action='store_true')
    argparser.add_argument('-v', '--verbose',
                           help='デバッグ用情報を出力する',
                           action='count',
                           default=0)
    argparser.add_argument('-V', '--version',
                           help='バージョン情報を表示して終了する',
                           action='version',
                           version='%(prog)s {}'.format(__version__))

    args = argparser.parse_args(argv)

    VERBOSE = args.verbose
    verbose = libssw.def_verbose(VERBOSE, libssw.ownname(__file__))
    verbose('Verbose mode on')

    libssw.RECHECK = args.recheck

    if args.retrieval == 'url' and (args.cid or args.cid_l):
        emsg('E', '-U 指定時に --cid/--cid-l は指定できません。')

    # サービス未指定の決定
    # 引数にURLが与えられていればそれから判定
    # TSVやウィキテキスト入力でなければそれ以外ならセル版
    # TSVやウィキテキスト入力ならあとで作品情報から判定
    if args.keyword:
        if not args.service:
            if re.match('https?://.+', args.keyword[0]):
                args.service = libssw.resolve_service(args.keyword[0])
            elif not (args.from_tsv or args.from_wiki):
                args.service = 'dvd'

        if (args.cid or args.cid_l) and '{}' in args.keyword[0]:
            verbose('args.cid check')
            # --row 未指定で --cid(-l) で連番指定の場合の自動決定
            # --start-{p,c}id だけでは連番と確定できないので何もしない
            if not args.row:
                args.row = int(args.keyword[1])
                verbose('row is set by cid: ', args.row)

    # ここで row 未指定時のデフォルト設定
    if not args.row:
        args.row = 1

    # start-pidは大文字、start-cidは小文字固定
    args.start_pid = args.start_pid.upper()
    args.start_pid_s = args.start_pid_s.upper()
    args.start_cid = args.start_cid.lower()

    args.last_pid = args.last_pid.upper()
    args.last_cid = args.last_cid.lower()

    # ヘッダを抑止するときはページ分割もしない
    if not args.header:
        args.split = 0

    if args.fastest:
        for a in ('follow_rdr', 'smm', 'check_rental', 'pass_bd',
                  'check_listpage', 'longtitle'):
            setattr(args, a, False)

    # キャッシュディレクトリの削除
    if args.clear_cache:
        libssw.clear_cache()

    verbose('args: ', args)
    return args


def parse_outfile(args, make):
    if not args.out:
        return None

    # ファイル名に拡張子があったら分割
    split, suffix = (args.out.rsplit('.', 1) + [''])[:2]

    outf_actr = split + '_actress'
    outf_tbl = split + '_table'

    if args.replace:
        writemode = 'w'
    else:
        chk = []
        if not args.wikitext:
            chk.append(args.out)
        else:
            if make.table:
                chk.append(outf_tbl + '.' + suffix)
            if make.actress:
                chk.append(outf_actr + '.' + suffix)

        libssw.files_exists('w', *chk)
        writemode = 'x'

    return OutFile(actr=outf_actr, tbl=outf_tbl, suffix=suffix,
                   writemode=writemode)


def det_filterpatn(args):
    """フィルター用パターンの決定"""
    if args.filter_pid:
        return re.compile(args.filter_pid, re.I), 'pid'
    elif args.filter_cid:
        return re.compile(args.filter_cid, re.I), 'cid'
    else:
        return None, ''


def det_keyinfo(args):
    """start/last-p/cidキー情報の決定"""
    if args.start_pid:
        return args.start_pid, 'start', 'pid'
    elif args.start_cid:
        return args.start_cid, 'start', 'cid'
    elif args.last_pid:
        return libssw.rm_hyphen(args.last_pid), 'last', 'pid'
    elif args.last_cid:
        return args.last_cid, 'last', 'cid'
    else:
        return None, None, 'pid'


def makeproditem(cid, service, sub_pid):
    pid = libssw.gen_pid(cid, sub_pid)[0]
    verbose('built cid: {}, pid: {}'.format(cid, pid))
    url = libssw.build_produrl(service, cid)
    return url, libssw.Summary(url=url, title='__' + pid, cid=cid, pid=pid)


def from_sequence(keywords: tuple, service, sub_pid):
    """連続した品番の生成ジェネレータ"""
    try:
        base, start, end = keywords[:3]
    except ValueError:
        emsg('E',
             '--cid オプションで範囲指定する場合は'
             '「基底」、「開始」、「終了」の3個の引数が必要です。')

    step = keywords[3] if len(keywords) >= 4 else 1

    digit = max(map(len, (start, end)))
    base = re.sub(r'{}', r'{:0>{}}', base)
    for num in range(int(start), int(end) + 1, int(step)):
        cid = base.format(num, digit)
        yield makeproditem(cid, service, sub_pid)


def make_pgen(args, ids, listparser, sub_pid, key_id, key_type, kidattr):
    """作品情報作成ジェネレータの作成"""
    if args.from_tsv:
        # TSVファイルから一覧をインポート
        verbose('Import from_tsv()')
        p_gen = libssw.from_tsv(args.keyword)
    elif args.from_wiki:
        # ウィキテキストから一覧をインポート
        verbose('Import from_wiki()')
        p_gen = libssw.from_wiki(args.keyword)
    elif args.cid or args.cid_l:
        # 品番指定
        if '{}' in ids[0]:
            # '品番基準' 開始番号 終了番号 ステップ
            p_gen = from_sequence(ids, args.service, sub_pid)
        else:
            # 各cidからURLを作成
            p_gen = (makeproditem(c, args.service, sub_pid) for c in ids)
    else:
        # DMMから一覧を検索/取得
        verbose('Call from_dmm()')
        if args.retrieval in {'url', 'keyword'}:
            priurls = args.keyword
        else:
            priurls = libssw.join_priurls(args.retrieval,
                                          *ids,
                                          service=args.service)
        p_gen = libssw.from_dmm(listparser, priurls,
                                pages_last=args.pages_last,
                                key_id=key_id,
                                key_type=key_type,
                                idattr=kidattr)

    return p_gen


def fmtheader(atclinfo):
    """ヘッダ整形"""
    return '\n*{}'.format(
        '／'.join('[[{}>{}]]'.format(a, u) for a, u in atclinfo))


def build_header_actress(actids: tuple):
    """女優名の再構成"""
    verbose('build_header_actress: {}'.format(actids))

    current = ''

    def _getnames(he):
        """女優名とよみの文字列の取得"""
        nonlocal current

        for name, yomi in zip_longest(*libssw.get_actname(he)):
            yield name if yomi is None else '{}（{}）'.format(name, yomi)

        current = libssw.get_actname.current

    def _build(aids):
        """女優名の整形とIDのペアを返す"""
        for aid in aids:
            resp, he = libssw.open_url(ACTINFOPAGE.format(aid), set_cookie='age_check_done=1')
            yield '／'.join(_getnames(he)), ACTLISTPAGE.format(aid)

    header = fmtheader(_build(actids))
    return current, header


def build_header(articles):
    """ページヘッダ文字列の作成"""
    header = fmtheader(articles)
    return articles[0][0], header


def build_header_listpage(retrieval, service, name, lstid):
    url = libssw.join_priurls(retrieval, lstid, service=service)[0]
    return build_header(((name, url),))


def det_articlename(args, ids, wikitexts, listparser):
    """アーティクル名の決定およびヘッダの作成"""
    if args.retrieval == 'actress':
        # 女優ID指定:
        article_name, article_header = build_header_actress(ids)
    else:
        # その他
        if libssw.from_wiki.article:
            article_name, article_header = build_header(
                libssw.from_wiki.article)
        elif args.retrieval == 'series':
            article_name, article_header = build_header_listpage(
                args.retrieval, args.service, *wikitexts[0].series)
        elif args.retrieval == 'label':
            article_name, article_header = build_header_listpage(
                args.retrieval, args.service, *wikitexts[0].label)
        elif args.retrieval == 'maker':
            article_name, article_header = build_header_listpage(
                args.retrieval, args.service, *wikitexts[0].maker)
        elif listparser.article:
            article_name, article_header = build_header(
                listparser.article)
        else:
            article_name = article_header = ''

    return article_name, article_header


def set_sortkeys(sort_key):
    """ソートキーの設定"""
    if sort_key == 'title':
        # 第1キー:タイトル、第2キー:リリース日
        keys = 'release', 'title'
    elif sort_key == 'release':
        # 第1キー:リリース日、第2キー:品番
        keys = 'pid', 'release'
    elif sort_key == 'pid':
        keys = 'release', 'pid'
    else:
        keys = ()

    return keys


def truncate_th(cols):
    for col in cols:
        try:
            yield col.split(':')[1]
        except IndexError:
            yield ''


def number_header(article, n_i_s, page):
    """ページヘッダの出力"""
    return '{}{} {}'.format(article,
                            'その他' if n_i_s else '',
                            page if page > 1 else '')


def build_outname(of, is_table, pagen):
    """指定した出力ファイル名を指定のモードでオープン"""
    stem = of.tbl if is_table else of.actr
    fname = '.'.join(map(str, filter(None, (stem, pagen, of.suffix))))
    return fname


class BuildPage:
    """ウィキテキスト生成(ページごと)"""
    def __init__(self, wikitexts, split, retrieval, a_name, a_hdr, t_hdr):
        self._wikitexts = wikitexts
        self._split = split
        self._retlabel = libssw.RETLABEL[retrieval]
        self._a_name = a_name
        self._a_hdr = a_hdr
        self._t_hdr = t_hdr

        self._length = len(wikitexts)
        self._page_names = set()

    def start(self, row, is_table):
        self._no = 0
        self._row = row - 1
        self._is_table = is_table
        self.done = False

        if is_table:
            self._attr = 'wktxt_t'
        else:
            self._attr = 'wktxt_a'
            # self._wikitexts.reverse()

        verbose('wktxt attr: ', self._attr)

    def _header(self, n_i_s):
        """ページヘッダの出力"""
        self.pagen = (self._row // self._split + 1) if self._row >= 0 else 0
        page_name = number_header(self._a_name, n_i_s, self.pagen)
        yield '\n' + page_name + '\n'

        if n_i_s:
            yield '\n{}「[[{}>]]」でシリーズ化されていない作品の一覧。\n'.format(
                self._retlabel,
                self._a_name)

        yield self._a_hdr + '\n'

        if self._is_table and self._t_hdr and not self._row % 10:
            yield self._t_hdr.format('NO')

        self._page_names.add(page_name)

    def _tail(self):
        # DMM上のタイトルを変更している作品のDMMタイトルをコメントで残す
        yield '\n■関連ページ\n-[[]]\n'

        # DMM上のタイトルを変更している作品のDMMタイトルをコメントで残す
        if self._titles_dmm:
            yield '//検索用'
            for tdmm in self._titles_dmm:
                yield '//' + tdmm

    def open_browser(self, browser):
        if browser and self._page_names:
            # ブラウザで開く
            libssw.open_ssw(*self._page_names)

    def __call__(self, n_i_s):

        self._titles_dmm = []

        yield from self._header(n_i_s)

        while self._no < self._length:

            verbose('Row #', self._row)

            item = self._wikitexts[self._no]

            remainder = self._row % self._split

            if self._t_hdr and remainder and not self._row % 10:
                # 10件ごとの表ヘッダの出力
#                yield self._t_hdr.format(remainder)
                yield self._t_hdr.format('NO')
                verbose('Header: ', self._no)

            # 作品情報の出力
            yield getattr(item, self._attr)

            if self._is_table and item.title_dmm:
                self._titles_dmm.append(item.title_dmm)

            self._no += 1
            self._row += 1

            if self._split and not self._row % self._split:
                # 1ページ分終了
                break
        else:
            self.done = True

        yield from self._tail()


def finalize(build_page, row, make, n_i_s, nis_series, outfile):
    """最終的なウィキテキスト出力"""
    for is_table in compress((True, False), (make.table, make.actress)):
        verbose('is_table: ', is_table)

        build_page.start(row, is_table)

        while not build_page.done:
            per_page = '\n'.join(build_page(n_i_s))
            yield per_page

            if outfile:
                outf = build_outname(outfile, is_table, build_page.pagen)
                fd = open(outf, outfile.writemode)
            else:
                fd = sys.stdout

            print(per_page, file=fd)

            if outfile:
                fd.close()

        if n_i_s and nis_series:
            fd = open(outf, 'a') if outfile else sys.stdout

            print('** 見つかったシリーズ一覧', file=fd)
            print(*map('-[[{}]]'.format, sorted(nis_series)),
                  sep='\n', file=fd)
            print(file=fd)

            if outfile:
                fd.close()


def main(argv=None):

    args = get_args(argv or sys.argv[1:])

    make = MakeType(actress=args.table != 1, table=args.table)
    outfile = parse_outfile(args, make)
    verbose('outfile: ', outfile)

    ids = tuple(libssw.extr_ids(args.keyword, args.cid))
    verbose('ids: ', ids)

    if not args.retrieval:
        args.retrieval = libssw.extr_ids.retrieval
    emsg('I', '対象: {}'.format(args.retrieval))

    # -L, -K , -U 以外では --not-in-series は意味がない
    if args.retrieval not in {'label', 'maker', 'url'}:
        args.n_i_s = False
        verbose('force disabled n_i_s')

    if args.retrieval == 'actress':
        for i in filter(lambda i: i in libssw.HIDE_NAMES, ids):
            emsg('W', '削除依頼が出されている女優です: {}'.format(
                libssw.HIDE_NAMES[i]))
            ids.remove(i)

    # 除外対象
    no_omits = libssw.gen_no_omits(args.no_omit)
    verbose('non omit target: ', no_omits)

    # 品番生成用パターンのコンパイル
    sub_pid = (re.compile(args.pid_regex[0], re.I),
               args.pid_regex[1]) if args.pid_regex else None
    # 副題生成用パターンのコンパイル
    re_subtitle = (re.compile(args.subtitle_regex[0], re.I),
                   args.subtitle_regex[1]) if args.subtitle_regex else None

    # フィルター用パターン
    filter_id, fidattr = det_filterpatn(args)

    re_filter_pid_s = args.filter_pid_s and re.compile(args.filter_pid_s, re.I)
    re_filter_ttl = args.filter_title and re.compile(args.filter_title, re.I)

    # 作成開始品番
    key_id, key_type, kidattr = det_keyinfo(args)
    not_key_id = libssw.NotKeyIdYet(key_id, key_type, kidattr)

    listparser = libssw.DMMTitleListParser(no_omits=no_omits, patn_pid=sub_pid)
    seriesparser = libssw.DMMTitleListParser(patn_pid=sub_pid, show_info=False)

    # 作品情報取得用イテラブルの作成
    p_gen = make_pgen(args, ids, listparser, sub_pid,
                      key_id, key_type, kidattr)

    # 作品情報の取り込み
    # 新着順
    products = OrderedDict((u, p) for u, p in p_gen)
    emsg('I', '一覧取得完了')

    total = len(products)
    if not total:
        emsg('E', '検索結果は0件でした。')

    if not args.service:
        # TSVやウィキテキスト入力の場合の作品情報からサービス判定
        args.service = libssw.resolve_service(next(iter(products)))

    join_d = dict()
    libssw.ret_joindata(join_d, args)

    if (args.join_tsv or args.join_wiki or args.join_html) and not len(join_d):
        emsg('E', '--join-* オプションで読み込んだデータが0件でした。')

    if args.existings_html:
        # 既存の一覧ページから既出の作品情報の取得
        verbose('existings html')
        existings = set(k[0] for k in libssw.from_html(args.existings_html,
                                                       service=args.service))
        if not existings:
            emsg('E', '--existings-* オプションで読み込んだデータが0件でした。')
    else:
        existings = set()

    # 作品情報の作成
    verbose('Start building product info')
    if not VERBOSE and args.wikitext:
        print('作成中...', file=sys.stderr, flush=True)

    wikitexts = []
    title_list = []
    nis_series_names = set()  # 発見したシリーズ名 (n_i_s用)
    nis_series_urls = set()  # 発見したシリーズ一覧のURL (n_i_s用)
    rest = total
    omitted = listparser.omitted
    before = True if key_id else False

    dmmparser = libssw.DMMParser(no_omits=no_omits,
                                 patn_pid=sub_pid,
                                 start_date=args.start_date,
                                 start_pid_s=args.start_pid_s,
                                 filter_pid_s=re_filter_pid_s,
                                 pass_bd=args.pass_bd,
                                 n_i_s=args.n_i_s,
                                 longtitle=args.longtitle,
                                 check_rental=args.check_rental,
                                 check_rltd=args.check_rltd,
                                 check_smm=args.smm)

    if args.retrieval in {'maker', 'label', 'series'}:
        keyiter = libssw.sort_by_id(products)
    else:
        keyiter = iter(products)

    for url in keyiter:
        props = products[url]

        # 品番の生成
        if not props.pid:
            props.pid, props.cid = libssw.gen_pid(props.url, sub_pid)

        # 開始ID指定処理(--{start,last}-{p,c}id)
        if before:
            # 指定された品番が見つかるまでスキップ
            if not_key_id(getattr(props, kidattr)):
                emsg('I', '作品を除外しました: {}={} (id not met yet)'.format(
                    kidattr, getattr(props, kidattr)))
                omitted += 1
                rest -= 1
                continue
            else:
                before = False
                if key_type == 'start':
                    emsg('I', '開始IDが見つかりました: {}'.format(
                        getattr(props, kidattr)))
                else:
                    emsg('I', '最終IDが見つかりました: {}'.format(
                        getattr(props, kidattr)))
                    continue

        # 品番(pid/cid)が指定されたパターンにマッチしないものはスキップ処理(--filter-{p,c}id)
        if filter_id and not filter_id.search(getattr(props, fidattr)):
            emsg('I', '作品を除外しました: {}={} (filtered)'.format(
                fidattr, getattr(props, fidattr)))
            omitted += 1
            rest -= 1
            continue

        # 作品名が指定されたパターンにマッチしないものはスキップ処理(--filter-title)
        if args.filter_title and not re_filter_ttl.search(props.title):
            emsg('I', '作品を除外しました: title={} (filtered)'.format(
                props.title))
            omitted += 1
            rest -= 1
            continue

        # 一覧ページ内に既存の作品はスキップ(--existings-)
        if props.url in existings:
            emsg('I', '作品を除外しました: pid={} (already existent)'.format(
                props.pid))
            omitted += 1
            rest -= 1
            continue

        # 既知のシリーズ物のURLならスキップ (--not-in-series)
        if props.url in nis_series_urls:
            emsg('I', '作品を除外しました: title="{}" (known series)'.format(
                props.title))
            omitted += 1
            rest -= 1
            continue

        if props.url in join_d:
            # joinデータがあるとデータをマージ
            props.merge(join_d[props.url])
            if args.hunter:
                props.title = join_d[props.url].title

        # 副題の生成
        if args.retrieval == 'series':
            # シリーズ一覧時のカスタムサブタイトル
            props.subtitle = libssw.sub(re_subtitle, props.title).strip() \
                if args.subtitle_regex else ''

        if args.wikitext:
            # ウィキテキストを作成
            libssw.inprogress('(残り {} 件/全 {} 件: 除外 {} 件)  '.format(
                rest, total, omitted))

            verbose('Call dmm2ssw')
            b, status, data = dmm2ssw.main(props, args, dmmparser)
            # 返り値:
            # b -> Bool
            # status -> url if b else http.status or 'Omitted'
            # data -> if b:
            #             ReturnVal(release,
            #                       pid,
            #                       title,
            #                       title_dmm,
            #                       url,
            #                       time,
            #                       ('maker', 'maker_id'),
            #                       ('label', 'label_id'),
            #                       ('series', 'series_id'),
            #                       wikitext_a,
            #                       wikitext_t)
            #         else:
            #             (key, hue) or empty ReturnVal (404)
            verbose('Return from dmm2ssw: {}, {}, {}'.format(
                b, status, data))

            if b:
                wikitexts.append(data)
            elif status == 404:
                wikitexts.append(data)
            else:
                emsg('I', '作品を除外しました: '
                     'cid={0}, reason=("{1[0]}", {1[1]})'.format(
                         props.cid, data))
                if args.n_i_s and data[0] == 'series':
                    # no-in-series用シリーズ作品先行取得
                    verbose('Retriving series products...')
                    nis_series_names.add(data[1].name)
                    priurls = libssw.join_priurls('series',
                                                  data[1].sid,
                                                  service=args.service)
                    nis_series_urls.update(
                        u[0] for u in libssw.from_dmm(seriesparser, priurls))
                omitted += 1

        else:
            # 一覧出力
            title_list.append(props.tsv('url', 'title', 'pid', 'actress',
                                        'number', 'director', 'note'))

        rest -= 1

    if wikitexts:
        # ウィキテキストの書き出し
        verbose('Writing wikitext')

        # アーティクル名の決定
        article_name, article_header = det_articlename(args, ids, wikitexts,
                                                       listparser)
        verbose('article name: ', article_name)
        verbose('article header: ', repr(article_header))

        if not libssw.le80bytes(article_name):
            emsg('W', 'ページ名が80バイトを超えています')

        # ソート
        sortkeys = set_sortkeys(args.sort_key)
        for k in sortkeys:
            wikitexts.sort(key=attrgetter(k))

        if args.add_column:
            add_header = '|'.join(
                c.split(':')[0] for c in args.add_column) + '|'
            args.add_column = tuple(truncate_th(args.add_column))
        else:
            add_header = ''
        verbose('add header: {}\nadd column: {}'.format(add_header,
                                                        args.add_column))

        if make.table and args.header:
            table_header = '|~{{}}|PHOTO|{}|ACTRESS|{}{}RELEASE|NOTE|'.format(
                'SUBTITLE' if args.retrieval == 'series' else 'TITLE',
                'DIRECTOR|' if args.dir_col else '',
                add_header)
        else:
            table_header = ''

        build_page = BuildPage(wikitexts, args.split, args.retrieval,
                               article_name, article_header, table_header)

        print(file=sys.stderr)

        result = '\n'.join(finalize(build_page, args.row, make,
                                    args.n_i_s, nis_series_names, outfile))

        build_page.open_browser(args.browser)

        if args.copy:
            libssw.copy2clipboard(result)

    else:
        # タブ区切り一覧の書き出し

        fd = open(args.out, outfile.writemode) if args.out else sys.stdout

        print(*title_list, sep='\n', file=fd)

        if args.out:
            fd.close()


if __name__ == '__main__':
    main()
