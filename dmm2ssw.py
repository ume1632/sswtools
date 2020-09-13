#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DMMのURLからページを取得し素人系総合wiki用ウィキテキストを作成する


書式:
dmm2ssw.py [DMM作品ページのURL] [オプション...]


オプションで与えられない情報は可能な限りDMMのページから取得して
ウィキテキストを作成し標準出力へ出力する。

女優ページ、レーベル/シリーズ一覧ページのウィキテキスト(-t
 オプション)、およびその両方(-tt オプション)を作成できる。

DVD通販、DVDレンタル、動画-ビデオ/-素人のページに対応しているはず。

■タイトルの自動編集
タイトルに「（ハート）」と「◆」があった場合は「♥」に置き換える。
その他wiki構文上問題のある文字列があれば全角に置き換える([]や~)。
置き換えた場合、元のDMM上のタイトルはコメントとして残す(検索用)。
--disable-modify-title オプションが与えられるとこれらの置き換えは
行わない。

■無駄に長すぎるタイトルの一部対応
アパッチの作品に関してはタイトルをメーカー公式サイトから取得する。
HunterおよびATOMについては対応不可(hunterpp.pyにて対応)。

■女優名の自動編集
女優名に過去の芸名が付記されている場合(「現在の芸名 (旧芸名...)」)は
旧芸名を除去する。
--disable-strip-oldname オプションが与えられると除去しない。
削除依頼が出ている女優名は強制的に「(削除依頼対応)」に置き換えられる。

■SMM(supermm.jp)からの出演者情報の補完
DMM上から出演者情報が得られなかった場合、以下の条件においてSMMの
作品ページから出演者情報の取得を試みる。
・DVD/Blu-rayセル版であること
・Firefoxがインストールされていること
・Firefox上でSMMのCookieを受け入れる状態になっていること
・一度FirefoxからデフォルトプロファイルでSMMのアダルトページに
  アクセスして年齢認証を行っていること(Cookieの期限が24時間のよう
  なので、1日に1回行えばよいはず)
SMM上でも仮の名前のときがあるため、SMM上ですべてひらがなの名前の
ときはその名前の女優名が存在しなければ内部リンクにしない。
--disable-check-smm オプションが与えられると出演者情報がなくてもSMMを
見に行かない。

■ジュエル系の出演者名は無視
ジュエル系の出演者名は本人の女優名ではないので出演者情報があっても
無視する。(IGNORE_PERFORMERS 参照)

■リダイレクトページの検出とリダイレクト先の自動取得
Wikiの出演者名や一覧ページがリダイレクトページかどうかチェックし、
リダイレクトページならリダイレクト先を取得してリンク先にする。
-f オプションが与えられるとリダイレクトかどうかチェックしない。

■実際のレーベル/シリーズ一覧ページ名の自動取得
レーベル/シリーズ一覧ページ名を実際のWiki上の記事名から探して適切な
リンク先の取得を試みる(「DANDY」→「DANDY 2」など)。
作品のDMMのURLで検索するため、一覧ページにその作品のエントリがないか、
あっても他のサイトへのリンクになっていると失敗する。
そうでなくても失敗するかもしれない(一覧ページに追加して間もなく、
検索でまだヒットしないなど)。
検索してヒットしなかったらDMM上のものをそのまま設定する。

■レンタル先行レーベルでの自動切り替え
レンタル版が先行する作品もあるレーベルなのにレンタル以外のサービスの
URLが与えられた場合、レンタル版をチェックし、リリースが早ければ
レンタル版の情報でウィキテキストを作成、備考としてセル版へのリンクを
追加する。
--disable-check-rental オプションが与えられるとレンタル版をチェック
しない。(RENTAL_PRECEDES 参照)

■取得した情報のキャッシュ
採取したページ内容やリダイレクト情報などは、OSのテンポラリディレクトリ
(C:\TEMPや/tmpなど)にディレクトリ 'dmm2ssw_cache' を作成し、そこに
キャッシュする。
一度キャッシュしたページはWikiなら2時間、それ以外のサイトなら24時間
それを利用する(キャッシュされないページもある)。
キャッシュを消したい場合はディレクトリごと直接削除するか
 -C オプションを指定する。
--recheck オプションを指定すると「ページがない」およびリダイレクト
ページとキャッシュされているページを再チェックする。
キャッシュディレクトリがどこにあるかは --cache-info オプションで
確認できる。


動作条件:
    [必須] python3.4以降, httplib2(python3用), lxml(python3用)
    [必須] libssw.py  このスクリプトと同じ場所、またはPYTHONPATHが
    通っているところへおいておく。
    [任意] pyperclip(python3用)作成したウィキテキストをクリップボードへ
          コピーする機能(--copy)を使用する場合必要。


注意:
    このスクリプトを連続実行させて短時間に大量の情報を取得した場合、
    その間隔が短いと(D)DoS攻撃とみなされて通報されるかもしれないので
    注意。


引数:
DMM作品ページのURL
    省略時は標準入力から読み込む。


オプション:
-a, --actress 出演者 [出演者 ...]
    クレジットされてない出演者を追加する場合用。
    出演者(のwikiページ名)を指定する。
    リンクの表示文字列を変えたいならwiki同様 "表示名>ページ名" と
    指定する。
    DMMページ上にすでに出演者情報が存在しても無視され、ここの指定値に
    置き換えられる。
    ここに"("または"（"で始まる文字列(例: (1人目)、(M・Sさん) など)を
    指定すると内部リンクにしない。
    "女優A,女優B／(3人目)" というようにスラッシュやカンマなどで区切って
    渡すのも可(ただし出力では区切り文字はすべて"／"になる)。
    女優名ページ用ウィキテキストの場合、-n 指定も含め2名に満たない場合は
    出力されない。
    出演者文字列の先頭に @@ をつけるとウィキテキストの構文で直接指定した
    とみなし(@@を取り除いてそのままウィキテキストに出力する)、DMM上の
    出演者情報を置き換える以外の女優名に関する処理はすべて行われない。
    ウィキテキストで直接指定時のオプション引数は先頭の1個だけ取られ、
    2個目以降は無視される。

-n, --number 出演者数
    未知の出演者がいる場合用。
    出演者の総数を指定する。
    指定されると出演者の最後に「… ほか計n名」を追加する。
    正数を与えても既知の出演者数以下の場合は無視される。
    -1 を指定すると「… ほか」と人数を明記しない曖昧表示になる。
    -a をウィキテキストで直接指定したときは無視される。

-s, --series [シリーズ一覧ページ名]
    シリーズ一覧ページへのリンクを追加する場合用。
    DMM上でのシリーズとwikiでのシリーズの扱いが異なる時にwikiページ名を
    指定する
    一覧ページ名を指定しないとDMMページから取得する。
    指定されるとDMMページ上のものを置き換える。

-l, --label [レーベル一覧ページ名]
    -s 同様だが、シリーズ一覧ではなくレーベル一覧へのリンクとして
    追加する。

--linklabel 一覧ページへのリンクのラベル名
    作品一覧ページへのリンクに表示するラベル(「レーベル一覧」
    「シリーズ一覧」など)をここで指定した文字列に置き換える。

--hide-list
     一覧ページへのリンクを追加しない。

-t, --table
    シリーズ/レーベル一覧ページ用の表形式のウィキテキストを出力する。
    2個以上指定すると女優ページ用と両方出力する。

--pid 品番
    作品の品番を直接指定する。
    -t/-tt オプションが与えられた時用。

    ※指定しない場合
    DMM上の品番情報(cid=)から自動生成を試みる。
    正しい品番にならない場合があるので注意。

    自動生成パターン(python正規表現)と置換文字列:

    '^(?:[hn]_)?\d*([a-z]+)(\d+).*', '\1-\2'

    1hunt569     ⇒ HUNT-569
    41hrdv01212r ⇒ HRDV-01212
    h_093crc035  ⇒ CRC-035

    ※以下の場合は個別に対応して正しく生成する:
    ・チェリーズの一部レーベル
        h_093r18243 ⇒ R18-243
    ・LEOのレンタル版
        125ud537ra  ⇒ UD537R
    ・FAプロのレンタル版の一部
        h_066fad1976r ⇒ FAD1976
        h_066rhtr013r ⇒ RHTR013
    ・TMAの一部
        55t28349 ⇒ T28-349
        55id22036 ⇒ 22ID-036
    ・AROMAの一部作品(DMM上での過去の同一品番との衝突回避)
        11arm0374 ⇒ ARM-374
    ・ドグマの D1 CLIMAX レーベル
        d1001 ⇒ D1-001
    ・ドグマの AD1 CLIMAX レーベル
        ad1001 ⇒ AD1-001
    ・青空ソフト
        h_308aoz200z ⇒ AOZ-200Z
    ・ながえスタイルのセル版の一部
        h_102bnsps001 ⇒ NSPS-001
    ・アウダースの一部
        21psd001 ⇒ PSD+001
    ・D1グランプリ
        36d1clymax00004 ⇒ D1CLYMAX-004

--subtitle 副題
    -t/-tt オプションが与えられた時用。
    作品名の副題(SUBTITLEカラムに出力される)に指定された副題を出力する。

--as-series
    -t/-tt オプションが与えられた時用。
    シリーズ一覧用にタイトルではなく副題を出力する。

--note 備考 [備考 ...]
    女優ページ形式ではウィキテキストの最後、一覧ページ形式では右端の
    「NOTE」カラムに指定された文字列を出力する。
    データは固定の文字列と以下の変数を指定できる。
    これら変数はウィキテキスト作成時に対応する文字列に展開される。
    @{media}  メディアの種類
    @{time}   収録時間
    @{series} シリーズ名
    @{maker}  メーカー名
    @{label}  レーベル名
    @{cid}    品番

-d, --add-dir-col
    DIRECTORカラムを出力する。
    -t/-tt オプションが与えられた時用。

--add-column [カラム名[:データ] [カラム名[:データ] ...]]
    表形式に任意のカラムを追加する。
    -t/-tt を指定しない場合は無視される。
    書式はカラム名のあとに :とともに各カラム内に出力するデータを
    指定できる。
    データの書式は --note オプションと同じ。

--join-tsv ファイル [ファイル ...] (TSV)
    DMMから得た作品と(URLが)同じ作品がファイル内にあった場合、
    DMMからは取得できなかった情報がファイル側にあればそれで補完する
    (NOTEも含む)。
    ファイル形式については dmmsar.py の「インポートファイル形式」参照。

--join-wiki ウィキテキスト [ウィキテキスト ...] (一覧ページの表形式)
    DMMから得た作品と(URLが)同じ作品がウィキテキスト内にあった場合、
    DMMからは取得できなかった情報がウィキテキスト側にあればそれで
    補完する(NOTEも含む)。
    セルが結合されている表には未対応。

--join-html Wiki一覧ページのURL/HTML [Wiki一覧ページのURL/HTML ...] (一覧ページのHTML)
    DMMから得た作品と(URLが)同じ作品が、Wikiの一覧ページにあった場合、
    DMMからは取得できなかった情報がWiki側にあればそれで補完する
    (NOTEも含む)。
    一覧ページを保存したHTMLのファイルでも可。
    セルが結合されている表には未対応。

-f, --disable-follow-redirect
    指定・取得した出演者名のwikiページがリダイレクトページかどうか
    チェックしない。

--enable-check-smm
    このオプションが与えられるとDMM上に出演者情報がないときにSMMを検索する。
    (https://supermediamall.com/ のドメイン移行及び仕様変更のため現在動作未確認)

--disable-check-rental
    レンタル先行レーベルなのにレンタル以外のサービスの作品URLだった
    場合にレンタル版の方をチェックしない。

--disable-check-related'
    他メディアやサービスの情報収集を行わない

--disable-check-bluray
    入力されたURLがBlu-ray版だったときにDVD版の有無をチェックしない。

--disable-check-listpage
    Wiki上の実際の一覧ページをチェックせず、オプションで与えられた
    ものかDMMのものをそのまま採用する。

--recheck
    「ページが見つからない」とキャッシュされているページを再チェックする。

--disable-modify-title
    タイトルの自動修正を無効にする(「説明」参照)。

--disable-strip-oldname
    出演者の旧名の自動除去を無効にする(「説明」参照)。

--fastest
    処理時間に影響する(ウェブページにアクセスする)あらゆる補助処理を
    行わない。

-c, --copy
    作成したウィキテキストをクリップボードへコピーする。
    Python モジュール pyperclip が必要。

-b, --browser
    ウィキテキスト作成後、Wikiの女優またはシリーズ一/レーベル一覧の
    ページをウェブブラウザで開く。

-C, --clear-cache
    キャッシュを終了時に削除する(「説明」参照)。

--cache-info
    キャッシュのパスとファイルサイズの合計を出力して終了する。

-v, --verbose
    デバッグ用情報を出力する。

-V, --version
    バージョン情報を表示して終了する。

-h, --help
    ヘルプメッセージを表示して終了する。


使用例:
 作品 http://www.dmm.co.jp/mono/dvd/-/detail/=/cid=h_635sw251/ のウィキテキストを作成する場合:

 1) 女優ページ用ウィキテキストを作成する場合。

    dmm2ssw.py "http://www.dmm.co.jp/mono/dvd/-/detail/=/cid=84scop225/"

 2) レーベル一覧ページ用(表形式)ウィキテキストを作成する場合。

    dmm2ssw.py "http://www.dmm.co.jp/mono/dvd/-/detail/=/cid=84scop225/" -t

 3) 出演者が「波多野結衣」だけ確認でき、出演者数は計3名だとわかった場合。

    dmm2ssw.py "http://www.dmm.co.jp/mono/dvd/-/detail/=/cid=84scop225/" -a "波多野結衣" -n 3

 4) 出演者全員が確認でき、女優ページ用とレーベル一覧ページ用両方のウィキテキストを作成し、作成したら各Wikiページをウェブブラウザで開く場合。

    dmm2ssw.py "http://www.dmm.co.jp/mono/dvd/-/detail/=/cid=84scop225/" -ttb -a "波多野結衣" "羽川るな" "椿かなり"

"""
import sys as _sys
import re as _re
import argparse as _argparse
import urllib.parse as _up
from itertools import chain as _chain
from collections import namedtuple as _namedtuple

import libssw as _libssw

__version__ = 20151010

_VERBOSE = 0
_AUTOMODIFY = True

_emsg = _libssw.Emsg(_libssw.ownname(__file__))

_ReturnVal = _namedtuple('ReturnVal',
                         ('release', 'pid', 'title', 'title_dmm', 'url',
                          'time', 'maker', 'label', 'series',
                          'wktxt_a', 'wktxt_t'))

_sub_heart = (_re.compile(r'（ハート）|◆'), r'♥')


_IMG_URL = {'dvd':    'http://pics.dmm.co.jp/mono/movie/adult/',
            'rental': 'http://pics.dmm.co.jp/mono/movie/',
            'video':  'http://pics.dmm.co.jp/digital/video/',
            'ama':    'http://pics.dmm.co.jp/digital/amateur/'}


# _verbose() に置き換えられる
_verbose = None


def _get_args(argv, p_args):
    """
    コマンドライン引数の解釈
    """
    global _VERBOSE
    global _AUTOMODIFY
    global _verbose

    argparser = _argparse.ArgumentParser(
        description='DMMのURLから素人系総合wiki用ウィキテキストを作成する')
    argparser.add_argument('url',
                           help='DMMの作品ページのURL',
                           nargs='?',
                           metavar='URL')

    argparser.add_argument('-a', '--actress',
                           help='出演者 (DMMページ内のものに追加する)',
                           nargs='+',
                           default=())
    argparser.add_argument('-n', '--number',
                           help='未知の出演者がいる場合の総出演者数 (… ほか計NUMBER名)',
                           type=int,
                           default=0)

    list_page = argparser.add_mutually_exclusive_group()
    list_page.add_argument('-s', '--series',
                           help='シリーズ一覧へのリンクを追加(DMM上のものを置き換え)',
                           default=getattr(p_args, 'series', None))
    list_page.add_argument('-l', '--label',
                           help='レーベル一覧へのリンクを追加(DMM上のものを置き換え)',
                           default=getattr(p_args, 'label', None))
    list_page.add_argument('--hide-list',
                           help='一覧ページへのリンクを追加しない',
                           action='store_true',
                           default=getattr(p_args, 'hide_list', False))

    argparser.add_argument('--linklabel',
                           help='一覧ページへのリンクの表示名を置き換える',
                           default=getattr(p_args, 'linklabel', None))

    argparser.add_argument('-t', '--table',
                           help='一覧ページ用の表形式ウィキテキストを作成する, 2個以上指定すると両方作成する',
                           action='count',
                           default=getattr(p_args, 'table', 0))

    argparser.add_argument('--pid',
                           help='作品の品番を直接指定(-t/-tt 指定時用)')

    argparser.add_argument('--subtitle',
                           help='タイトルの副題を直接指定(-t/-tt 指定時用)')
    argparser.add_argument('--as-series',
                           help='タイトルではなく副題で作成(-t/-tt 指定時用)',
                           action='store_true')

    argparser.add_argument('--note',
                           help='備考(表形式ではNOTEカラム)として出力する文字列',
                           nargs='+',
                           metavar='DATA',
                           default=getattr(p_args, 'note', []))
    argparser.add_argument('-d', '--add-dir-col',
                           help='DIRECTORカラムを出力する (-t/-tt 指定時用)',
                           dest='dir_col',
                           action='store_true',
                           default=getattr(p_args, 'dir_col', False))
    argparser.add_argument('--add-column',
                           help='表形式ヘッダに任意のカラムを追加する (-t/-tt 指定時のみ)',
                           nargs='+',
                           metavar='COLUMN:DATA',
                           default=getattr(p_args, 'add_column', []))

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

    argparser.add_argument('-f', '--disable-follow-redirect',
                           help='ページのリダイレクト先をチェックしない',
                           dest='follow_rdr',
                           action='store_false',
                           default=getattr(p_args, 'follow_rdr', True))
    argparser.add_argument('--enable-check-smm',
                           help='出演者情報がないときにSMMを検索する',
                           action='store_true',
                           dest='smm',
                           default=False)
    argparser.add_argument('--disable-check-rental',
                           help='レンタル先行レーベルでもレンタル版のリリースをチェックしない',
                           dest='check_rental',
                           action='store_false',
                           default=getattr(p_args, 'check_rental', True))
    argparser.add_argument('--disable-check-related',
                           help='他メディアやサービスの情報収集を行わない',
                           dest='check_rltd',
                           action='store_false',
                           default=getattr(p_args, 'check_rltd', True))
    argparser.add_argument('--disable-check-listpage',
                           help='Wiki上の実際の一覧ページを探さない',
                           dest='check_listpage',
                           action='store_false',
                           default=getattr(p_args, 'check_listpage', True))
    argparser.add_argument('--disable-longtitle',
                           help='アパッチ、SCOOPの長いタイトルを補足しない',
                           dest='longtitle',
                           action='store_false',
                           default=getattr(p_args, 'longtitle', True))
    argparser.add_argument('--fastest',
                           help='ウェブにアクセスするあらゆる補助処理を行わない',
                           action='store_true',
                           default=getattr(p_args, 'fastest', False))

    argparser.add_argument('--recheck',
                           help='キャッシュしているリダイレクト先を強制再チェック',
                           action='store_true',
                           default=getattr(p_args, 'recheck', False))

    argparser.add_argument('--disable-modify-title',
                           help='タイトルの自動調整を無効にする',
                           action='store_false',
                           default=True)
    argparser.add_argument('--disable-strip-oldname',
                           help='出演者の旧芸名の自動除去を無効にする',
                           action='store_false',
                           dest='autostrip',
                           default=True)

    argparser.add_argument('-c', '--copy',
                           help='作成したウィキテキストをクリップボードへコピーする(pyperclipが必要)',
                           action='store_true')

    argparser.add_argument('-b', '--browser',
                           help='生成後、wikiのページをウェブブラウザで開く',
                           action='store_true')

    argparser.add_argument('-C', '--clear-cache',
                           help='プログラム終了時にキャッシュをクリアする',
                           action='store_true',
                           default=False)
    argparser.add_argument('--cache-info',
                           help='キャッシュのパスとファイルサイズの合計を出力して終了する',
                           action='store_true')

    argparser.add_argument('-v', '--verbose',
                           help='デバッグ用情報を出力する',
                           action='count',
                           default=getattr(p_args, 'verbose', 0))
    argparser.add_argument('-V', '--version',
                           help='バージョン情報を表示して終了する',
                           action='version',
                           version='%(prog)s {}'.format(__version__))

    args = argparser.parse_args(argv)

    if args.verbose and __name__ != '__main__':
        args.verbose -= 1
    _VERBOSE = args.verbose

    _verbose = _libssw.def_verbose(_VERBOSE, _libssw.ownname(__file__))
    _verbose('verbose mode on')  # verbose モードでなければ無視される

    if args.cache_info:
        _libssw.cache_info()

    # キャッシュディレクトリの削除
    if args.clear_cache:
        _libssw.clear_cache()

    if args.fastest:
        for a in ('follow_rdr', 'smm', 'check_rental', 'check_listpage',
                  'check_rltd', 'longtitle'):
            setattr(args, a, False)

    _AUTOMODIFY = args.disable_modify_title
    _libssw.RECHECK = args.recheck

    _verbose('args: ', args)
    return args


def _build_image_url(service, cid):
    """画像URL作成"""
    _verbose('force building image url')
    suffix = ('js', 'jp') if service == 'ama' else ('ps', 'pl')
    return tuple(_up.urljoin(_IMG_URL[service],
                             '{0}/{0}{1}.jpg'.format(cid, s)) for s in suffix)


_rep_expansion = (('@{media}', 'media'),
                  ('@{time}', 'time'),
                  ('@{series}', 'series'),
                  ('@{maker}', 'maker'),
                  ('@{label}', 'label'),
                  ('@{cid}', 'cid'))


def _expansion(phrases, summ):
    """予約変数の展開"""
    for ph in phrases:
        for p, r in _rep_expansion:
            ph = ph.replace(p, getattr(summ, r))
        yield ph


class _ResolveListpage:
    """一覧ページへのリンク情報の決定"""
    def __init__(self):
        self._unknowns = set()

    def __call__(self, summ, retrieval, args):
        _verbose('Processing list link')

        list_type = ''

        for attr in ('series', 'label', 'maker'):

            list_page = summ[attr]

            if list_page:
                if list_page == '__HIDE__':
                    continue
                elif _libssw.le80bytes(list_page):
                    list_attr = attr
                    list_type = _libssw.RETLABEL[attr]
                    # break
                else:
                    _emsg('W',
                          _libssw.RETLABEL[attr],
                          '名が80バイトを超えているのでそのページは無いものとします: ',
                          list_page)

                _verbose('List type: {}, List page: {}'.format(list_type, list_page))

                # SCOOP個別対応
                if list_page == 'SCOOP（スクープ）':
                    list_page = 'スクープ'

                # wiki構文と衝突する文字列の置き換え
                list_page = _libssw.trans_wikisyntax(list_page)

                if not args.check_listpage or \
                (list_attr == retrieval and args.table == 1):
                    _verbose('pass checking listpage')
                    return list_type, list_page

                if (list_type, list_page) not in self._unknowns:

                    # Wiki上の実際の一覧ページを探し、見つかったらそれにする。
                    actuall = _libssw.check_actuallpage(summ['url'],
                                                        list_page,
                                                        list_type,
                                                        summ['pid'])
                    if actuall:
                        list_page = actuall
                        return list_type, list_page
                    else:
                        _emsg('W', list_type,
                            '一覧ページが見つからなくてもDMMのものを採用しません')
                        _emsg('W', list_type, ': ', list_page)
                        if __name__ != '__main__':
                            _emsg('I', 'タイトル: ', summ['title'],
                                ' ({})'.format(summ['pid']))
                        self._unknowns.add((list_type, list_page))
        else:
            return '', ''


_resolve_listpage = _ResolveListpage()


def _build_addcols(add_column, summ):
    return tuple(_expansion(add_column, summ)) if add_column else ()


def _check_missings(summ):
    """未取得情報のチェック"""
    missings = list(filter(lambda m: not summ[m],
                           ('release', 'title', 'maker', 'label', 'image_sm')))
    if missings:
        _emsg('W', '取得できない情報がありました: ', ",".join(missings))


def _format_wikitext_a(summ, anum, astr, service):
    """ウィキテキストの作成 女優ページ用"""
    wtext = ''

    # 発売日
    date = summ['release'].replace('/', '.')
    wtext += '//{0} {1[pid]}\n'.format(date, summ)
    # 自動修正があった場合のDMM上のタイトル (コメント)
    if summ['title_dmm']:
        wtext += '//{0[title_dmm]} #検索用\n'.format(summ)
    # タイトルおよびメーカー
    titleline = '[[{0[label]} {0[title]} {0[size]}>{0[url]}]]'.format(
        summ
    ) if summ['size'] else '[[{0[title]}（{1}）>{0[url]}]]'.format(
        summ, summ['maker'] or summ['label'])
    # シリーズ
    if summ['list_type']:
        titleline += '　[[({0[list_type]}一覧)>{0[list_page]}]]'.format(summ)
    wtext += titleline + '\n'
    # 画像
    if service == 'ama':
        wtext += '[[&ref({0[image_lg]},147)>{0[image_lg]}]]'.format(summ)
    else:
        wtext += '[[{0[image_sm]}>{0[image_lg]}]]'.format(summ)
    # 出演者
    if anum not in {0, 1}:
        wtext += '出演者：{0}\n'.format(astr)
    # 備考
    notes = summ['note'] + summ['others'] if summ['others'] else summ['note']
    if notes:
        wtext += '、'.join(notes) + '\n'

    return wtext


def _format_wikitext_t(summ, astr, dstr, dir_col, add_column):
    """ウィキテキストの作成 table形式"""
    wtext = ''

    # 品番
    wtext += '|[[{0[pid]}>{0[url]}]]'.format(summ) if summ['url'] \
             else '|{0[pid]}'.format(summ)

    # 画像
    wtext += '|[[{0[image_sm]}>{0[image_lg]}]]'.format(summ) if summ['url'] \
             else '|'

    # サブタイトル
    wtext += '|{0[subtitle]}~~{0[size]}'.format(summ) if summ['size'] \
             else '|{0[subtitle]}'.format(summ)

    # 出演者
    wtext += '|{0}'.format(astr)

    # 監督
    if dir_col:
        wtext += '|{0}'.format(dstr)

    # 追加カラム
    if add_column:
        wtext += '|' + '|'.join(add_column)

    # 発売日
    wtext += '|{0[release]}'.format(summ).replace('/', '-')

    # 備考
    wtext += '|{}|'.format('、'.join(summ['note']))

    return wtext


def main(props=_libssw.Summary(), p_args=_argparse.Namespace, dmmparser=None):

    # モジュール呼び出しの場合継承したコマンドライン引数は無視
    argv = [props.url] if __name__ != '__main__' else _sys.argv[1:]
    args = _get_args(argv, p_args)

    # 作品情報
    summ = _libssw.Summary()

    if __name__ == '__main__':
        _verbose('args: ', args)
        if not args.url:
            # URLが渡されなかったときは標準入力から
            _verbose('Input from stdin...')

            data = _sys.stdin.readline().rstrip('\n')

            if not data:
                _emsg('E', 'URLを指定してください。')

            for key, data in zip(('url', 'title', 'pid', 'actress', 'number',
                                  'director', 'director', 'note'),
                                 data.split('\t')):
                if key == 'url':
                    summ[key] = data.split('?')[0]
                elif key == 'actess':
                    summ[key] = list(_libssw.parse_names(data))
                elif key == 'number':
                    summ[key] = int(data) if data else 0
                elif key == 'director':
                    summ[key] = _libssw.re_delim.split(data)
                elif key == 'note':
                    summ[key].append(data)
                else:
                    summ[key] = data

            _verbose('summ from stdin: ', summ.items())

        for attr in ('url', 'number', 'pid', 'subtitle'):
            if not summ[attr]:
                summ[attr] = getattr(args, attr)

        if not summ['actress'] and args.actress:
            actiter = _chain.from_iterable(map(_libssw.re_delim.split,
                                               args.actress))
            summ['actress'] = list(_libssw.parse_names(actiter))

    else:
        _verbose('props: ', props.items())
        _verbose('p_args: ', vars(p_args))

        summ.update(props)

    for attr, typ in (('series', 'シリーズ'), ('label', 'レーベル')):
        if getattr(args, attr):
            summ['list_type'] = typ
            summ['list_page'] = getattr(args, attr)

    retrieval = getattr(p_args, 'retrieval',
                        'series' if args.as_series else 'find')
    service = getattr(p_args, 'service', None)
    series_guide = getattr(p_args, 'series_guide', True)

    if args.actress and args.actress[0].startswith('@@'):
        # ウィキテキストで直接指定
        rawpfmrs = args.actress[0][2:]
    else:
        rawpfmrs = ''

    # サービス未指定時の自動決定
    if not service:
        service = _libssw.resolve_service(summ['url'])
    _verbose('service resolved: ', service)

    if service == 'ama':
        # 動画(素人)の場合監督欄は出力しない。
        args.dir_col = False

    join_d = dict()
    _libssw.ret_joindata(join_d, args)

    if (args.join_tsv or args.join_wiki or args.join_html) and not len(join_d):
        _emsg('E', '--join-* オプションで読み込んだデータが0件でした。')

    # URLを開いて読み込む
    resp, he = _libssw.open_url(summ['url'], set_cookie='age_check_done=1')

    if resp.status == 404:
        # 404の時、空のエントリを作成(表形式のみ)して返す
        _emsg('I', 'ページが見つかりませんでした: ', summ['url'])
        if not summ['pid']:
            summ['pid'], summ['cid'] = _libssw.gen_pid(summ['url'])
        if p_args.cid_l:
            summ['url'] = ''
        else:
            if not summ['subtitle']:
                summ['subtitle'] = summ['title']
            summ['image_sm'], summ['image_lg'] = _build_image_url(service,
                                                                  summ['cid'])
        wktxt_t = _format_wikitext_t(summ,
                                     '',
                                     '／'.join(summ['director']),
                                     args.dir_col,
                                     False,
                                     _build_addcols(args.add_column, summ))
        _verbose('wktxt_t: ', wktxt_t)
        return False, resp.status, _ReturnVal(summ['release'],
                                              summ['pid'],
                                              summ['title'],
                                              summ['title_dmm'],
                                              summ['url'],
                                              summ['time'],
                                              summ('maker', 'maker_id'),
                                              summ('label', 'label_id'),
                                              summ('series', 'series_id'),
                                              wktxt_a=(),
                                              wktxt_t=wktxt_t)
    elif resp.status != 200:
        return False, resp.status, ('HTTP status', resp.status)

    # 構文ミスの修正
    # html = _libssw.sub(sub_href, html)

    # HTMLの解析
    if not dmmparser:
        dmmparser = _libssw.DMMParser(autostrip=args.autostrip,
                                      longtitle=args.longtitle,
                                      check_rental=args.check_rental,
                                      check_rltd=args.check_rltd,
                                      check_smm=args.smm)

    try:
        summ.update(dmmparser(he, service, summ, ignore_pfmrs=rawpfmrs))
    except _libssw.OmitTitleException as e:
        # 除外対象なので中止
        return False, 'Omitted', (e.key, e.word)

    _verbose('summ: ', summ.items())

    if dmmparser.data_replaced:
        service = dmmparser.data_replaced

    # joinデータがあったら補完
    if summ['url'] in join_d:
        summ.merge(join_d[summ['url']])

    if args.pid:
        summ['pid'] = args.pid

    # 画像がまだないときのリンク自動生成
    if not summ['image_lg']:
        summ['image_sm'], summ['image_lg'] = _build_image_url(service,
                                                              summ['cid'])
        _verbose('image_sm: ', summ['image_sm'])
        _verbose('image_lg: ', summ['image_lg'])

    #
    # タイトルの調整
    #
    # 削除依頼対応
    for dl in _libssw.HIDE_NAMES_V:
        summ['title'] = summ['title'].replace(dl, '').strip()

    on_dmm = summ['title']
    # wiki構文と衝突する文字列の置き換え
    modified = _libssw.trans_wikisyntax(on_dmm)
    if _AUTOMODIFY:
        # ♥の代替文字列の置き換え
        modified = _libssw.sub(_sub_heart, modified)

    summ['title'] = modified
    if not summ['title_dmm'] and modified != on_dmm:
        summ['title_dmm'] = on_dmm
    _verbose('summ[title]: ', summ['title'])
    _verbose('summ[title_dmm]: ', summ['title_dmm'])

    # シリーズ/レーベル一覧へのリンク情報の設定
    # 一覧ページの直接指定があればそれを、なければ シリーズ > レーベル で決定
    if not (args.hide_list or summ['list_type']):
        summ['list_type'], summ['list_page'] = _resolve_listpage(summ,
                                                                 retrieval,
                                                                 args)
    if args.linklabel:
        summ['list_type'] = args.linklabel
    _verbose('summ[list_page]: ', summ['list_page'])

    if args.note:
        summ['note'] = list(_expansion(args.note, summ)) + summ['note']
    _verbose('note: ', summ['note'])

    add_column = _build_addcols(args.add_column, summ)
    _verbose('add column: ', add_column)

    # 出演者文字列の作成
    pfmrslk = ()
    if rawpfmrs:
        # ウィキテキスト
        pfmrslk = _libssw.re_linkpare.findall(rawpfmrs)
        pfmrsstr, pnum = rawpfmrs, len(pfmrslk)
    elif len(summ['actress']) < 2 and not summ['number'] and args.table == 0:
        # 女優ページ用のみ作成で出演者数が1人ならやらない
        pfmrsstr, pnum = '', 0
    else:
        pfmrsstr, pnum = _libssw.stringize_performers(summ['actress'],
                                                      summ['number'],
                                                      args.follow_rdr)

    # 監督文字列の作成
    dirstr = '／'.join(summ['director'])

    # table形式用副題の生成
    if retrieval == 'series':
        # シリーズ名が list_page にあってタイトルの先頭からシリーズ名と
        # 同じ文字列があれば落とす。
        # list_page に値がなければタイトルをそのまま入れる。
        if not summ['subtitle']:
            summ['subtitle'] = _re.sub(
                r'^{}[、。！？・…♥]*'.format(summ['series']),
                '',
                summ['title'],
                flags=_re.I).strip()

    elif not summ['subtitle']:
        # タイトルをそのまま副題に(表形式用)
        summ['subtitle'] = summ['title']
    _verbose('subtitle: ', summ['subtitle'])

    # 未取得情報のチェック
    if _VERBOSE:
        _check_missings(summ)

    # ウィキテキストの作成
    wikitext_a = _format_wikitext_a(
        summ, pnum, pfmrsstr, service) if args.table != 1 else ()
    wikitext_t = _format_wikitext_t(summ,
                                    pfmrsstr,
                                    dirstr,
                                    args.dir_col,
                                    add_column) if args.table else ''

    if __name__ != '__main__':
        # モジュール呼び出しならタプルで返す。
        return True, summ['url'], _ReturnVal(summ['release'],
                                             summ['pid'],
                                             summ['title'],
                                             summ['title_dmm'],
                                             summ['url'],
                                             summ['time'],
                                             summ('maker', 'maker_id'),
                                             summ('label', 'label_id'),
                                             summ('series', 'series_id'),
                                             wikitext_a,
                                             wikitext_t)
    else:
        # 書き出す
        output = ['']
        if wikitext_a:
            output.append(wikitext_a)

        if wikitext_t:
            output.append(wikitext_t)

        print(*output, sep='\n')

        if args.copy:
            _verbose('copy 2 clipboard')
            _libssw.copy2clipboard(''.join(output))

        if args.browser:
            # wikiのページを開く
            if args.table != 1:
                pages = pfmrslk or summ['actress']
                for a in pages:
                    _libssw.open_ssw(a[1] or a[0])
            if args.table:
                _libssw.open_ssw(summ['list_page'])


if __name__ == '__main__':
    main()
