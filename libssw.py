#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""素人Wiki用スクリプト用ライブラリ"""

import os as _os
import sys as _sys
import re as _re
import time as _time
import sqlite3 as _sqlite3
import urllib.parse as _up
import fileinput as _fileinput
import pickle as _pickle
import webbrowser as _webbrowser
import unicodedata as _unicodedata
from operator import itemgetter as _itemgetter
from multiprocessing import Process as _Process
from collections import namedtuple as _namedtuple
from tempfile import gettempdir as _gettempdir, mkstemp as _mkstemp
from shutil import rmtree as _rmtree
from difflib import HtmlDiff as _HtmlDiff
from pathlib import Path as _Path
from itertools import chain as _chain
from copy import deepcopy as _deepcopy
from http.client import HTTPException as _HTTPException

try:
    import httplib2 as _httplib2
except ImportError:
    raise SystemExit('httplib2(python3用)をインストールしてください。')

try:
    from lxml.html import fromstring as _fromstring
except ImportError:
    raise SystemExit('lxml(python3用)をインストールしてください。')

try:
    from pyperclip import copy as _ppccopy
except ImportError:
    pass


__version__ = 20151010

_VERBOSE = 0

RECHECK = False

BASEURL_SSW = 'http://sougouwiki.com'
BASEURL_ACT = 'http://actress.dmm.co.jp'

ACTURL = BASEURL_ACT + '/-/detail/=/actress_id={}/'

RETLABEL = {'series': 'シリーズ',
            'label':  'レーベル',
            'maker':  'レーベル',
            'actress': '女優'}

_BASEURL_DMM = 'https://www.dmm.co.jp'

_SVC_URL = {'https://www.dmm.co.jp/mono/dvd/':       'dvd',
            'https://www.dmm.co.jp/rental/':         'rental',
            'https://www.dmm.co.jp/digital/videoa/': 'video',
            'https://www.dmm.co.jp/digital/videoc/': 'ama'}

_SERVICEDIC = {
    'dvd':    'mono/dvd',
    'rental': 'rental',
    'video':  'digital/videoa',
    'ama':    'digital/videoc'
}

# シリーズとして扱うとめんどくさいシリーズ
_IGNORE_SERIES = {'8369': 'E-BODY',
                  '205878': 'S級素人'}

# レンタル版のページの出演者が欠けていることがあるメーカー
_FORCE_CHK_SALE_MK = {'40121': ('LEO', 'dvd')}
# レンタル版のページの出演者が欠けていることがあるシリーズ
_FORCE_CHK_SALE_SR = {'79592': ('熟ズボッ！', 'videoa'),
                      '3820':  ('おはズボッ！', 'videoa')}

# 出演者情報を無視するメーカー
_IGNORE_PERFORMERS = {'45067': 'KIプランニング',
                      '45339': '豊彦',
                      '45352': 'リアルエレメント',
                      '46165': 'ジュエル',
                      '46654': 'メガハーツ',
                      '46655': 'MDMA',
                      '46656': '唾鬼'}

# 表記揺れ対応をするレーベル
_WIKITITLE_L = {'ティッシュ':            'TISSUE',
               'REAL（レアルワークス）': 'REAL',
               'SCOOP（スクープ）':      'スクープ',
               '頂 itadaki':             '頂_itadaki',
               'ヒプノシス':             '催眠研究所別館',
               'BALTAN Amazoness':       'amazoness',
               'hoppin’':               'Hoppin\'',
               'アクアモール':           'HERO（アクアモール）',
               'KSB企画/エマニエル':     'KSB企画／エマニエル',
               'e-kiss':                 'e-KiSSレーベル',
               'pistil':                 'PISTレーベル',
               'アテナ映像':             'ATHENA',
               'ヒプノシスRASH':         '催眠RASH',
}

# 表記揺れ対応をするシリーズ
_WIKITITLE_S = {'我慢できれば生中出しSEX！':    '我慢できれば生★中出しSEX！',
                'ママシ●タ実話':               'ママショタ実話',
}

# 送信防止措置依頼されている女優
HIDE_NAMES = {  '1004622': '大谷佳香',
                '1013226': '星ヰいちご',
                '1022948': '市川まひろ',
                '1023995': '立花恭子',
                '1024279': '藤崎かすみ',
                '1026305': '北野ひな',
                '1043328': '熊宮由乃',
}
HIDE_NAMES_V = HIDE_NAMES.values()

_GENRE_BD = '6104'  # Blu-rayのジャンルID

# 除外キーワード
_OMITWORDS = {'総集編':       '総集編作品',
              'BEST':         '総集編作品',
              'Best':         '総集編作品',
              'ベスト':       '総集編作品',
              'COMPLETE':     '総集編作品',
              'コンプリート': '総集編作品',
              '総編版':       '総集編作品',

              'アウトレット': 'アウトレット',
              '廉価版':       'アウトレット',

              '復刻版':       '復刻盤',
              '復刻盤':       '復刻盤',

              'FANZA初回限定': '限定盤',
              'FANZA限定':     '限定盤',
              '数量限定':      '限定盤',
              '枚限定':        '限定盤',
              '初回限定版':    '限定盤',

              '（DOD）':    '（DOD）',
              '（BOD）':    '（BOD）',

              'ブルーレイディスク':  '（BD）'
}
# 【混ぜるな危険】
#  'コレクション'
#  '保存版'
#  '大全集'
#  '全集'

_OMNI_PATTERN_WORDS = {
    _re.compile(r'(?:全|\d+)タイトル'): '総集編'}


_OMITTYPE = ('イメージビデオ', '総集編作品', 'アウトレット', '復刻盤', '限定盤', 'UMD')

# 除外対象ジャンル
_OMITGENRE = {'6014': 'イメージビデオ',
              '6003': '総集編作品',       # ベスト・総集編
              '6608': '総集編作品',       # 女優ベスト・総集編
              '7407': '総集編作品',       # ベスト・総集編
              '6147': 'アウトレット',
              '6175': 'アウトレット',  # '激安アウトレット'
              '6555': '復刻',
              '4104': 'UMD',
              }
#  '6561': '限定盤'} # 特典対象

# 総集編・再収録専門そうなやつ
# メーカー
_OMIT_MAKER = {
    '6500': 'BACK DROP',
    '6473': 'CHANGE',
    '40029': 'アヴァ (レンタル)',
}
#   '45810': 'エクストラ'}

# 収録時間が4時間以上は総集編だけそうなメーカー
_OMIT_SUSS_4H = {
    '1398': 'ドグマ',
    '3784': 'エムズビデオグループ',
    '4809': 'ミル',
    '4835': 'TRANS CLUB',
    '4836': 'SHEMALE a la carte',
    '5061': 'オーロラプロジェクト・アネックス',
    '5534': 'ABC/妄想族',
    '5665': 'ROOKIE',
    '5699': 'VENUS',
    '6368': '催眠研究所別館',
    '6413': 'フォーディメンション/エマニエル',
    '6426': '赤い弾丸/エマニエル',
    '6495': 'MANJIRO/エマニエル',
    '6381': 'CREAM PIE',
    '40006': 'ワンズファクトリー',
    '40014': 'グローリークエスト',
    '40018': 'ルビー',
    '40025': 'ドリームチケット',
    '40070': 'マルクス兄弟',
    '40074': 'ジャネス',
    '40077': 'AVS collector’s',
    '40082': 'ラハイナ東海',
    '40160': 'アテナ映像',
    '45003': 'スタイルアート/妄想族',
    '45016': 'センタービレッジ',
    '45017': 'ドリームステージ',
    '45059': 'デジタルアーク',
    '45099': '光夜蝶',
    '45195': '小林興業',
    '45216': 'なでしこ',
    '45340': 'BabyEntertainment',
    '45371': 'ROCKET',
    '45450': 'STAR PARADISE',
    '45457': 'NEXT GROUP',
    '45486': 'プリモ',
    '45532': 'スターゲート',
    '45700': 'バルタン',
    '45737': 'カマタ映像',
    '45883': 'Mellow Moon（メロウムーン）',
    '45941': 'MGM'}

# 総集編・再収録専門レーベル
_OMIT_LABEL = {
    '2745':  'アタッカーズ アンソロジー',
    '6010':  'ALL IN☆ ONE',
    '7111':  'CRYSTAL EX',
    '9164':  'オーロラプロジェクト・EX',
    '21231': 'DRAGON（ハヤブサ）',
    '22721': 'バイキング',
    '23581': 'K’S BEST',
    '24078': 'REBORN',
    '24230': '美少女（プレステージ）',
    '24558': '79Au',
    '24593': '熟肉',
    '24808': '変態仮面',
    '25025': 'コリーダ'}

# 総集編・再収録専門シリーズ
_OMIT_SERIES = {
    '2935':   'BEST（作品集）',
    '8750':   '微乳貧乳',
    '9939':   'プレミアムベスト',
    '9696':   'ism',
    '72538':  '○○大全集（TMA）',
    '77766':  '人妻の情事（なでしこ）',
    '78841':  '100人斬り（TMA）',
    '202979': '『無垢』特選 無垢ナ女子校生限定ソープランド 大好評記念感謝祭',
    '204625': 'いいなりな人妻たち',
    '205518': 'いやらしくてムッチリお尻で巨乳の人妻とHがしたい',
    '205779': 'フェラチオSP',
    '207233': '寸止め焦らしで大暴発スペシャル',
    '208033': '湯あがりぺちゃぱいバスタイム',
    '208077': '美熟女プレイ集',
    '208374': '催眠研究',
    '208519': '見下し丁寧淫語でございます。',
    '209310': 'ONEDAFULL1年の軌跡全60作品',
    '209360': '○○ism',
    '209413': 'アウトレットDVD5枚組 1980',
    '209887': '奥さんの体がエロいから犯されるんです！！！',
    '210101': '○時間SPECIAL',
    '210208': 'ママ友！増刊号 ヤリ友の輪',
    '210925': '淫乱すぎる若妻48人の連続ドスケベSEX',
    '210926': 'どすけべ妻のいやらしいフェラチオ',
    '211184': 'The○○ 美熟女スペシャル',
    '211414': '母乳厳選集',
    '212454': '実録出版 永久不滅傑作選',
    '212503': '極・奇譚クラブ',
    '212638': 'SM獄窓の女たち 囚われの肉魔',
    '213087': 'おませなJKの制服でオクチえっち！',
    '213109': '夫の前で犯される人妻',
    '213295': '麗しき若妻',
    '213420': 'キレイなお姉さんのパンモロ○○コレクション',
    '213604': 'ヌキサシバッチリ！！厳選センズリ専用ディルド＆指入れオナニー素材集',
    '213714': '1万人のAVユーザーが選んだ○○',
    '213840': '癒しのじゅるじゅぽフェラCOLLECTION',
    '214749': 'この神脚、生唾ごっくん…。',
}

# 品番プレフィクス(URL上のもの)
_OMNI_PREFIX = (
    '118bst',         # プレステージの総集編
    '118dcm',         # プレステージの総集編
    '118dcx',         # プレステージの総集編
    '118ful',         # プレステージの総集編
    '118kmx',         # プレステージの総集編
    '118mzq',         # プレステージの総集編
    '118pet',         # プレステージの総集編
    '118ppb',         # プレステージの総集編
    '118ppt',         # プレステージの総集編
    '118pre',         # プレステージの総集編
    '118spa',         # プレステージの総集編
    '118spp',         # プレステージの総集編
    '118tgbe',        # プレステージの総集編
    '118tre',         # プレステージの総集編
    '118zesp',        # プレステージの総集編
    '13box',          # グローリークエストの総集編
    '13gqe',          # グローリークエストの総集編
    '13qq',           # グローリークエストの総集編
    '13rvg',          # グローリークエストの総集編
    '13sqv',          # グローリークエストの総集編
    '13ysr',          # グローリークエストの総集編
    '143umd',         # グローバルメディアエンタテインメントの総集編
    '15ald',          # 桃太郎映像出版の総集編
    '15mofd',         # 桃太郎映像出版の総集編
    '164sbdd',        # サイドビーの総集編レーベル クスコ
    '164sbhe',        # サイドビーの総集編レーベル HEROINE
    '17dbr',          # ルビーの総集編シリーズ
    '17hrd',          # ルビーの総集編
    '17kmk',          # ルビーの総集編シリーズ
    '187jame',        # スタイルアートjam/妄想族の総集編
    '187slba',        # スタイルアートLOVE BETES/妄想族の総集編
    '18alsp',         # タカラ映像の総集編
    '18mbox',         # タカラ映像の総集編
    '18mght',         # タカラ映像の総集編
    '1svomn',         # サディスティックビレッジの総集編
    '21issd',         # アウダースジャパンの総集編
    '21pssd',         # アウダースジャパンの総集編
    '23aukb',         # U＆Kの総集編
    '23uksp',         # U＆Kの総集編
    '24hfd',          # ドリームチケットの総集編
    '28drn',          # DRAGON（ハヤブサ） 総集編専門レーベル
    '28gen',          # GIGA TON 総集編専門レーベル
    '28wed',          # EIGHT MAN 総集編専門レーベル
    '29cxaz',         # ジャネス/ladiesの総集編
    '29cwaz',         # ジャネス/ladiesの総集編
    '29djsh',         # ジャネスの総集編
    '29djsj',         # ジャネスの総集編
    '29hwaz',         # ジャネスの総集編
    '2apao',          # オーロラプロジェクト・アネックスの総集編 (レンタル)
    '2bdclb',         # ワープエンタテインメントの総集編
    '2bom',           # BoinBB/ABCの総集編 (レンタル)
    '2box',           # ワープエンタテインメントの総集編
    '2clb',           # ワープエンタテインメントの総集編
    '2koze',          # ローグ・プラネット（フェチ）/妄想族の総集編 (レンタル)
    '2ptko',          # パツキン/ABCの総集編 (レンタル)
    '2slba',          # スタイルアート/妄想族の総集編 (レンタル)
    '2spbox',         # ワープエンタテインメントの総集編
    '2swac',          # 湘南/妄想族の総集編 (レンタル)
    '2tomn',          # TEPPANの総集編 (レンタル)
    '2wpw',           # ワープエンタテインメントの総集編
    '2wsp',           # ワープエンタテインメントの総集編
    '2ycc',           # ワープエンタテインメントの総集編
    '30dmbk',         # MAZO BOYS CLUB (未来フューチャー) の総集編
    '30dsmo',         # BS (未来フューチャー) の総集編
    '33awtb',         # AVS collector’sの総集編
    '33avsb',         # AVS collector’sの総集編
    '33avsw',         # AVS collector’sの総集編
    '33nopc',         # AVS collector’sの総集編
    '33acec',         # AVS collector’sの総集編
    '33dphb',         # AVS collector’sの総集編
    '33dphc',         # AVS collector’sの総集編
    '33dpnw',         # AVS collector’sの総集編
    '33dsfb',         # AVS collector’sの総集編
    '33exbs',         # AVS collector’sの総集編
    '33igub',         # AVS collector’sの総集編
    '33ncgb',         # AVS collector’sの総集編
    '33plzb',         # AVS collector’sの総集編
    '33zosb',         # AVS collector’sの総集編
    '3bmw',           # ワンズファクトリーの総集編
    '3mmb',           # 桃太郎ベスト (レンタル)
    '3naw',           # ワンズファクトリーの総集編
    '3swf',           # ワンズファクトリーの総集編
    '3veq',           # VENUSの総集編 (レンタル)
    '434dfda',        # デジタルアークの総集編
    '434dgtl',        # デジタルアークの総集編
    '434gkdfda',      # デジタルアークの総集編
    '434kcda',        # デジタルアークの総集編
    '49cadv',         # クリスタル映像の総集編
    '4atk',           # Attackers BEST 総集編専門レーベル (レンタル)
    '4idb',           # アイポケの総集編 (レンタル)
    '4jus',           # マドンナ/Madonnaの総集編 (レンタル)
    '4kib',           # kira☆kiraの総集編 (レンタル)
    '4kwb',           # kawaiiの総集編 (レンタル)
    '4hndb',          # 本中の総集編 (レンタル)
    '4mby',           # 溜池ゴローの総集編 (レンタル)
    '4mib',           # ムーディーズの総集編 (レンタル)
    '4mitb',          # 蜜月の総集編 (レンタル)
    '4mkck',          # E-BODYの総集編 (レンタル)
    '4mvb',           # エムズビデオグループの総集編 (レンタル)
    '4obe',           # マドンナ/Obasanの総集編 (レンタル)
    '4ons',           # S1の総集編 (レンタル)
    '4pbd',           # プレミアムの総集編 (レンタル)
    '4ppb',           # OPPAIの総集編 (レンタル)
    '4tmbt',          # teamZEROの総集編 (レンタル)
    '4tywd',          # 乱丸の総集編 (レンタル)
    '4vvv',           # ヴィの総集編 (レンタル)
    '51cma',          # シネマジックの総集編
    '55boya',         # BO-YA TMAの総集編レーベル
    '55hsrm',         # SCREAM 総集編専門レーベル
    '55id',           # TMAの総集編
    '5atk',           # Attackers BEST 総集編専門レーベル (レンタル)
    '5cra',           # クロスの総集編 (レンタル)
    '5krb',           # カルマ/BEST 総集編専門レーベル (レンタル)
    '5mkck',          # E-BODYの総集編 (レンタル)
    '83sbb',          # マルクス兄弟の総集編
    '83scf',          # マルクス兄弟の総集編
    '84bdhyaku',      # 100人 KMPの総集編レーベル
    '84hyaku',        # 100人 KMPの総集編レーベル
    '84hyas',         # 100人 KMPの総集編レーベル
    '9onsd',          # S1の総集編(BD)
    'abcb',           # ABC/妄想族の総集編
    'anhd',           # アンナと花子の総集編
    'atkd',           # Attackers BEST 総集編専門レーベル
    'apao',           # オーロラプロジェクト・アネックスの総集編
    'avsw',           # AVS collector’s の総集編
    'bcdp',           # 総集編メーカー BACK DROP
    'bijc',           # 美人魔女の総集編
    'bomn',           # BoinBB/ABCの総集編
    'bmw',            # ワンズファクトリーの総集編
    'cnz',            # キャンディの総集編
    'corb',           # たぶんCOREの総集編
    'crad',           # クロスの総集編
    'crmn',           # 痴ロモン/妄想族 総集編レーベル
    'daid',           # ダイナマイトエンタープライズの総集編
    'dazd',           # ダスッ！の総集編
    'dgtl',           # デジタルアークの総中編
    'emac',           # DX（エマニエル）の総集編
    'fabs',           # FAプロの総集編
    'h_066fabr',      # FAプロの総集編 (レンタル)
    'h_066fabs',      # FAプロの総集編
    'h_066rabs',      # FAプロ 竜二ベスト
    'h_068mxsps',     # マキシングの総集編
    'h_086abba',      # センタービレッジの総集編
    'h_086cbox',      # センタービレッジの総集編
    'h_086cvdx',      # センタービレッジの総集編
    'h_086euudx',     # センタービレッジの総集編
    'h_086ferax',     # センタービレッジの総集編
    'h_086gomu',      # センタービレッジの総集編
    'h_086hhedx',     # センタービレッジの総集編
    'h_086hthdx',     # センタービレッジの総集編
    'h_086honex',     # センタービレッジの総集編
    'h_086iannx',     # センタービレッジの総集編
    'h_086jrzdx',     # センタービレッジの総集編
    'h_086oita',      # センタービレッジの総集編
    'h_086qizzx',     # センタービレッジの総集編
    'h_108mobsp',     # モブスターズの総集編
    'h_127ytr',       # NONの総集編
    'h_175dbeb',      # BabyEntertainmentの総集編
    'h_175dxdb',      # BabyEntertainmentの総集編
    'h_179dmdv',      # ゲインコーポレーションの総集編
    'h_213agemix',    # SEX Agentの総集編 (レンタル)
    'h_213ageom',     # SEX Agentの総集編
    'h_237swat',      # シリーズ ○○三昧 プラネットプラスの総集編シリーズ
    'h_254kanz',      # 完全盤 STAR PARADISEの総集編レーベル
    'h_254mgdn',      # MEGADON STAR PARADISEの総集編レーベル
    'h_254wnxg',      # VOLUME STAR PARADISEの総集編レーベル
    'h_443hpr',       # 催眠研究所の総集編シリーズ
    'h_479gah',       # GO AHEAD 総集編レーベル (GALLOP)
    'h_479gfs',       # SPECIAL GIFT 総集編レーベル (GALLOP)
    'h_479gft',       # GIFT 総集編レーベル (GALLOP)
    'h_479gfx',       # GIFT DX 総集編レーベル (GALLOP)
    'h_479gne',       # NEO GIFT 総集編レーベル (GALLOP)
    'h_537odfg',      # ワンダフルの総集編
    'h_540exta',      # エクストラ 総集編専門レーベル
    'h_543rlod',      # 乱熟 総集編メーカー
    'h_543rloh',      # 乱熟 総集編メーカー
    'h_543rloj',      # 乱熟 総集編メーカー
    'h_543rlok',      # 乱熟 総集編メーカー
    'h_543rloi',      # 乱熟 総集編メーカー
    'h_544yuyg',      # ケンシロウプロジェクトの総集編
    'h_797impa',      # impact（サンワソフト）の総集編
    'h_838chao',      # CHAOS（Pandora）総集編レーベル (Pandra)
    'h_865jkn',       # 総集編シリーズ 完熟肉汁つゆだく交尾集
    'hjbb',           # はじめ企画の総集編
    'hndb',           # 本中の総集編
    'hoob',           # AVS collector’sの総集編
    'idbd',           # アイポケの総集編
    'jfb',            # Fitchの総集編
    'jomn',           # ABC/妄想族の総集編
    'jusd',           # マドンナ/Madonnaの総集編
    'kibd',           # kira☆kiraの総集編
    'koze',           # ローグ・プラネット（フェチ）/妄想族の総集編
    'krbv',           # カルマ/BEST 総集編専門レーベル
    'kwbd',           # kawaiiの総集編
    'mbyd',           # 溜池ゴローの総集編
    'mibd',           # ムーディーズの総集編
    'mitb',           # 蜜月の総集編
    'mkck',           # E-BODYの総集編
    'mmb',            # 桃太郎ベスト
    'mvbd',           # エムズビデオグループの総集編
    'n_1155dslb',     # グラッソの復刻版(?)
    'obe',            # マドンナ/Obasanの総集編
    'onsd',           # S1の総集編
    'oomn',           # お母さん.com/ABCの総集編
    'rbb',            # ROOKIEの総集編
    'pbd',            # プレミアムの総集編
    'ppbd',           # OPPAIの総集編
    'ptko',           # パツキン/ABCの総集編
    'rabs',           # FAプロ 竜二ベスト
    'slba',           # スタイルアート/妄想族の総集編
    'stol',           # 変態紳士倶楽部の総集編
    'swac',           # 湘南/妄想族の総集編
    'tmbt',           # teamZEROの総集編
    'tomn',           # TEPPANの総集編
    'tywd',           # 乱丸の総集編
    'veq',            # VENUSの総集編
    'vero',           # VENUSの総集編
    'veve',           # VENUSの総集編
    'vvvd',           # ヴィの総集編

    '15awad12',       # 桃太郎映像出版の総集編作品
    '15rawa012',      # 桃太郎映像出版の総集編作品 (レンタル)
    '15rsen167',      # 桃太郎映像出版の総集編作品 (レンタル)
    '15send167',      # 桃太郎映像出版の総集編作品
    '4bf249',         # BeFreeの総集編作品
    '84okax014',      # おかず。の総集編作品
    '84rokax014r',    # おかず。の総集編作品 (レンタル)
    '84umso013',      # UMANAMIの総集編作品
    'bf249',          # BeFreeの総集編作品
    'bf315',          # BeFreeの総集編作品
    'bf374',          # BeFreeの総集編作品
    'bf375',          # BeFreeの総集編作品
    'bf392',          # BeFreeの総集編作品
    'bnsps382',       # ながえSTYLEの総集編作品
    'h_093r18306',    # チェリーズの総集編作品
    'h_093r18308',    # チェリーズの総集編作品
    'emaf324',        # フォーディメンション（エマニエル）の総集編か再利用作品
    'h_254vnds3141',  # ネクストイレブンの総集編作品
    'h_606ylw4303',   # Yellow Moon (Mellow Moon) の総集編作品
    'h_606ylw4308',   # Yellow Moon (Mellow Moon) の総集編作品
    'h_746rssr051r',  # SOSORUの総集編作品 (レンタル)
    'h_746rssr081r',  # SOSORUの総集編作品 (レンタル)
    'h_746ssr051',    # SOSORUの総集編作品
    'h_746ssr081',    # SOSORUの総集編作品
    'h_970kagh023',   # かぐや姫（メロウムーン）の総集編作品
    'h_970kagh023r',  # かぐや姫（メロウムーン）の総集編作品 (レンタル)
    'h_970kagh015',   # かぐや姫（メロウムーン）の総集編作品
    'h_970kagh015r',  # かぐや姫（メロウムーン）の総集編作品 (レンタル)
)
# 品番正規表現
_OMNI_PATTERN_CID = (
    _re.compile(r'^(?:[hn]_)?\d*aaj'),  # AV30
    _re.compile(r'^(?:837?)?sbb'),      # コレクターズエディション (マルクス兄弟)
)

# イメージビデオ専門レーベル
_IV_PREFIX = (
    'h_803pnch',    # Panchu
    )

_ROOKIE = ('rki', '9rki')

# 既定のリンク先は同名別女優がいるためリダイレクトにできない女優をあらかじめ登録
_REDIRECTS = {'黒木麻衣':   '花野真衣',
              '若菜あゆみ': '若菜あゆみ(人妻)',
              '藤原ひとみ': '藤原ひとみ(kawaii*)',
              '佐々木玲奈': '佐々木玲奈(2013)',
              'すみれ':     '東尾真子',
              'EMIRI':      '丘咲エミリ',
              '松嶋葵':     '松嶋葵（2014）',
              '和久井ナナ': 'ふわりゆうき',
}

# FANZA独自の伏字 解除リスト
_NGWORD = {
    '●す':   '犯す',
    '犯●れ': '犯され',
    '輪●':   '輪姦',
    '凌●':   '凌辱',
    '陵●':   '陵辱',
    '奴●':   '奴隷',
    '痴●':   '痴漢',
    '泥●':   '泥酔',
    '催●':   '催眠',
    '夜●い': '夜這い',
    '昏●':   '昏睡',
    '●ませ': '飲ませ',
    '虐●':   '虐待',
    '折●':   '折檻',
    '●っ':   '酔っ',
    '●気':   '幼気',
    '●物':   '薬物'
}

_CACHEDIR = _Path(_gettempdir()) / 'dmm2ssw_cache'
_RDRDFILE = 'redirects'


re_delim = _re.compile(r'[/／,、]')
re_inbracket = _re.compile(r'[(（]')
re_linkpare = _re.compile(r'\[\[(.+?)(?:>(.+?))?\]\]')
re_hiragana = _re.compile(r'[ぁ-ゞー]')
re_neghirag = _re.compile(r'[^ぁ-ゞー]')
re_more = _re.compile(r"url: '(.*?)'")

_re_number = _re.compile(r'\d+')
_re_interlink = _re.compile(r'(\[\[.+?\]\])')


_DummyResp = _namedtuple('DummyResp', 'status,fromcache')
_NiS = _namedtuple('n_i_s', 'sid,name')


def ownname(path):
    return _Path(path).stem

_OWNNAME = ownname(__file__)


class _Verbose:
    """デバッグ用情報の出力"""
    def __init__(self, ownname, verbose):
        self._ownname = ownname
        self.verbose = verbose

    def __call__(self, *msg):
        msg = ''.join(map(str, msg))
        print('({0}): >>> {1}'.format(self._ownname, msg),
              file=_sys.stderr, flush=True)


def _verbose(*args):
    pass


def def_verbose(vmode, ownname):
    global _VERBOSE
    global _verbose

    if vmode:
        if vmode > 1:
            vv = vmode - 1
            _VERBOSE = vv
            _verbose = _Verbose(_OWNNAME, vv)
        return _Verbose(ownname, vmode)
    else:
        return _verbose


class Emsg:
    """標準エラー出力へメッセージ出力"""
    _msglevel = {'E': 'ERROR',
                 'W': 'WARN',
                 'I': 'INFO'}

    def __init__(self, ownname):
        self._ownname = ownname

    def __call__(self, level, *msg):
        msg = ''.join(map(str, msg))
        m = '({}:{}) {}'.format(self._ownname, self._msglevel[level], msg)
        if level == 'W':
            m = '\033[1;33m{}\033[0m'.format(m)
        elif level == 'E':
            m = '\033[1;31m{}\033[0m'.format(m)
        print(m, file=_sys.stderr, flush=True)

        if level == 'E':
            # エラーなら終了
            raise SystemExit()

_emsg = Emsg(_OWNNAME)


class Summary:
    """作品情報格納用"""
    __slots__ = ('url',
                 'media',
                 'release',
                 'time',
                 'title',
                 'title_dmm',
                 'subtitle',
                 'actress',
                 'size',
                 'director',
                 'series',
                 'series_id',
                 'label',
                 'label_id',
                 'maker',
                 'maker_id',
                 'link_label',
                 'link_series',
                 'pid',
                 'cid',
                 'image_sm',
                 'image_lg',
                 'number',
                 'genre',
                 'note',
                 'others')

    def __init__(self,
                 url='',
                 media='',
                 release='',
                 time='',
                 title='',
                 title_dmm='',
                 subtitle='',
                 actress=[],
                 size='',
                 director=[],
                 series='',
                 series_id='',
                 label='',
                 label_id='',
                 maker='',
                 maker_id='',
                 link_label='',
                 link_series='',
                 pid='',
                 cid='',
                 image_sm='',
                 image_lg='',
                 number=0,
                 genre=[],
                 note=[],
                 others=[]):
        for key in self.__slots__:
            value = eval(key)
            if isinstance(value, list):
                setattr(self, key, value[:])
            else:
                setattr(self, key, value)

    def __contains__(self, key):
        return hasattr(self, key)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __call__(self, *keys):
        return self.values(*keys)

    def __iter__(self):
        return iter(self.__slots__)

    def keys(self):
        return self.__slots__

    def values(self, *keys):
        attrs = keys or self.__slots__
        return list(getattr(self, k) for k in attrs)

    def items(self, *args):
        attrs = args or self.__slots__
        return list((a, getattr(self, a)) for a in attrs)

    def stringize(self, *args):
        attrs = args or self.__slots__
        for a in attrs:
            v = getattr(self, a)
            if a == 'note' and not v:
                break
            elif isinstance(v, (list, tuple)):
                v = ','.join(v)
            else:
                v = str(v) if v else ''
            yield v

    def tsv(self, *args):
        attrs = args or self.__slots__
        return '\t'.join(self.stringize(*attrs))

    def __set(self, attr, other, overwrite):
        this = getattr(self, attr)
        if isinstance(other, list):
            other = other.copy()
        if not this or overwrite:
            setattr(self, attr, other)

    def merge(self, otherobj, overwrite=False):
        if hasattr(otherobj, 'keys'):
            for key in otherobj:
                val = otherobj[key]
                if val:
                    self.__set(key, val, overwrite)
        else:
            for key, val in otherobj:
                if val:
                    self.__set(key, val, overwrite)

    def update(self, otherobj):
        self.merge(otherobj, overwrite=True)


def sub(re_list, string, n=False):
    """re.sub()、re.subn()ラッパー"""
    return re_list[0].subn(re_list[1], string) if n else \
        re_list[0].sub(re_list[1], string)


def copy2clipboard(string):
    """クリップボードへコピー"""
    try:
        _ppccopy(string)
    except NameError:
        _emsg('W', 'Python pyperclip モジュールがインストールされていないためクリップボードにはコピーされません。')


def quote(string: str, safe='/', encoding='euc_jisx0213', errors=None):
    """URL埋め込みように文字列をクオート"""
    return _up.quote(string, safe=safe, encoding=encoding,
                     errors=errors).replace('-', '%2d')


def unquote(string: str, encoding='euc_jisx0213', errors='replace'):
    """文字列をアンクオート"""
    return _up.unquote(string, encoding=encoding, errors=errors)


def _clip_pname(url: str):
    """WikiページのURLからページ名を取得"""
    return unquote(url.rsplit('/', 1)[-1])


_tt_nl = str.maketrans('', '', '\r\n')


def rm_nlcode(string: str):
    """改行文字を除去"""
    return string.translate(_tt_nl)


_tt_pidsep = str.maketrans('', '', '+-')


def rm_hyphen(string: str):
    """ハイフンを除去"""
    return string.translate(_tt_pidsep)


def extr_num(string: str):
    """文字列から数値だけ抽出"""
    return _re_number.findall(string)


def cvt2int(item: str):
    """数値だけ取り出してintに変換(数値がなければ0を返す)"""
    num = extr_num(item) or (0,)
    return int(num[0])


def inprogress(msg):
    """「{}中...」メッセージ"""
    if not _VERBOSE:
        print('{}  '.format(msg), end='\r', file=_sys.stderr, flush=True)


re_list_article = _re.compile(r'(?<=/article=)\w+')


def get_article(url: str):
    """DMM URLからarticle=部を抽出"""
    return re_list_article.findall(url)[0]


def le80bytes(string: str, encoding='euc_jisx0213'):
    """Wikiページ名最大長(80バイト)チェック"""
    return len(bytes(string, encoding)) <= 80


_tt_filename = str.maketrans(r'/:<>?"\*|;', '_' * 10)


def trans_filename(filename: str):
    """ファイル名に使用できない文字列の置き換え"""
    return filename.translate(_tt_filename)


_tt_wikisyntax = str.maketrans('[]~', '［］～')


def trans_wikisyntax(wikitext: str):
    """Wiki構文と衝突する記号の変換"""
    return wikitext.translate(_tt_wikisyntax)


def files_exists(mode, *files):
    """同名のファイルが存在するかどうかチェック"""
    for f in filter(lambda x: x not in {_sys.stdin, _sys.stdout}, files):
        _verbose('file: ', f)
        isexist = _os.path.exists(f)
        if mode == 'r' and not isexist:
            _emsg('E', 'ファイルが見つかりません: ', f)
        elif mode == 'w' and isexist:
            _emsg('E', '同名のファイルが存在します (-r で上書きします): ', f)


def save_cache(target, stem):
    """キャッシュ情報の保存"""
    _verbose('Saving cache...')

    lockfile = _CACHEDIR / (stem + '.lock')
    pkfile = _CACHEDIR / (stem + '.pickle')
    _verbose('cache file: ', pkfile)

    if lockfile.exists():
        # ロックファイルの有無と期限のチェック
        now = _time.time()
        mtime = lockfile.stat().st_mtime
        if now - mtime > 180:
            lockfile.unlink()

    for i in range(10):
        # ロックファイルの作成
        try:
            lockfile.touch(exist_ok=False)
        except FileExistsError:
            _time.sleep(1)
        else:
            break
    else:
        _emsg('E', 'キャッシュファイルが10秒以上ロック状態にあります: ', lockfile)

    ctrlc = False

    while True:
        try:
            with pkfile.open('wb') as f:
                _pickle.dump(target, f)
            _verbose('cache saved: ({})'.format(stem))
        except KeyboardInterrupt:
            ctrlc = True
        else:
            break

    lockfile.unlink()

    if ctrlc:
        raise SystemExit


def load_cache(stem, default=None, expire=7200):
    """保存されたキャッシュ情報の読み込み"""
    _verbose('Loading cache...')

    pkfile = _CACHEDIR / (stem + '.pickle')
    _verbose('cache file path: ', pkfile)

    now = _time.time()

    try:
        mtime = pkfile.stat().st_mtime
    except FileNotFoundError:
        _verbose('cache file not found')
        return default

    if (now - mtime) > expire:
        # 最終更新から expire 秒以上経ってたら使わない。
        _verbose('saved cache too old')
        return default
    else:
        with pkfile.open('rb') as f:
            try:
                cache = _pickle.load(f)
            except:
                return default

        return cache

_REDIRECTS = load_cache(_RDRDFILE, default=_REDIRECTS)


def gen_no_omits(no_omit=None):
    """除外しない対象セットの作成"""
    if isinstance(no_omit, int):
        return set(_OMITTYPE[:no_omit])
    elif no_omit is None:
        return set(_OMITTYPE)
    else:
        return set(_OMITTYPE[i] for i in no_omit)


def gen_ntfcols(tname, fsource: 'sequence'):
    """表形式ヘッダから名前付きタプルを作成"""
    if isinstance(fsource, str):
        fsource = ('TITLE' if c == 'SUBTITLE' else c
                   for c in fsource.replace('~', '').split('|'))
    return _namedtuple(tname, fsource, rename=True)


class __OpenUrl:
    """URLを開いて読み込む"""
    _re_charset = _re.compile(r'(?<=charset=)[\w-]+')

    def __init__(self):
        if _VERBOSE > 1:
            _httplib2.debuglevel = 1
        self.__http = _httplib2.Http(str(_CACHEDIR))
        self.__wait = dict()

    def __sleep(self):
        _time.sleep(5)

    def _url_openerror(self, name, info, url):
        """URLオープン時のエラーメッセージ"""
        _emsg('E',
              'URLを開く時にエラーが発生しました ({})。詳細: {}, url={}'.format(
                  name, info, url))

    def _resolve_charset(self, resp, html):
        """文字エンコーディングの解決"""
        # HTTPレスポンスから取得
        c_type = self._re_charset.findall(resp['content-type'])
        if c_type:
            _verbose('charset from resp.')
            return c_type[0]

        # HTMLヘッダから取得
        c_type = self._re_charset.findall(_fromstring(html).xpath(
            '//meta[@http-equiv="Content-Type"]')[0].get('content', False))
        if c_type:
            _verbose('charset from meta.')
            return c_type[0]

    def __call__(self, url, charset=None, set_cookie=None, cache=True,
                 method='GET', to_elems=True):
        _verbose('open url: ', url)

        if method == 'HEAD':
            to_elems = False

        site = _up.urlparse(url).netloc
        if not site:
            _emsg('E', '不正なURL?: ', url)

        if cache:
            maxage = '7200' if site == 'sougouwiki.com' else '86400'
            headers = {'cache-control': 'private, max-age={}'.format(maxage)}
        else:
            headers = dict()

        if set_cookie:
            headers['cookie'] = set_cookie
        _verbose('http headers: ', headers)

        for i in range(5):

            try:
                self.__wait[site].is_alive()
            except KeyError:
                pass
            else:
                _verbose('joinning wait_', site)
                self.__wait[site].join()

            try:
                resp, html = self.__http.request(
                    url, headers=headers, method=method)
            except _httplib2.HttpLib2Error as e:
                self._url_openerror(
                    e.__class__.__name__, ", ".join(e.args), url)
            except _HTTPException as e:
                if e == 'got more than 100 headers':
                    if '/limit=60/' in url:
                        _emsg('E', '(おそらくサーバー側に問題のある)HTTP例外です。')
                    else:
                        url = url.replace('/limit=120/', '/limit=60/')
                resp = _DummyResp(status=0, fromcache=False)
            _verbose('http status: ', resp.status)
            _verbose('fromcache: ', resp.fromcache)

            # HTTPステータスがサーバ/ゲートウェイの一時的な問題でなければ終了
            if resp.status and not 500 <= resp.status <= 504:
                if resp.status not in {200, 404}:
                    _emsg('W', 'HTTP status: ', resp.status)
                break

            # Windowsでweakref objectエラーが出るので移動
            # 上記のifで抜けるとsleepしたインスタンス消滅？
            if not resp.fromcache:
                _verbose('start wait_', site)
                self.__wait[site] = _Process(target=self.__sleep, daemon=True)
                self.__wait[site].start()

        else:
            _verbose('over 5 cnt with status 50x')
            return resp, ''

        if charset or not to_elems:
            encoding = charset or self._resolve_charset(resp, html)
            _verbose('encoding: ', encoding)

            try:
                html = html.decode(encoding, 'ignore')
            except UnboundLocalError:
                _emsg('E', 'HTMLの読み込みに失敗しました: resp=', resp)

        return resp, _fromstring(html) if to_elems else html

open_url = __OpenUrl()


_tt_knum = str.maketrans('一二三四五六七八九〇壱弐参伍', '12345678901235')
_re_ksuji = _re.compile('[十拾百千万億兆〇\d]+')
_re_kunit = _re.compile(r'[十拾百千]|\d+')
_re_manshin = _re.compile(r'[万億兆]|[^万億兆]+')

_TRANSUNIT = {'十': 10,
              '拾': 10,
              '百': 100,
              '千': 1000}
_TRANSMANS = {'万': 10000,
              '億': 100000000,
              '兆': 1000000000000}


def _kansuji2arabic(string):
    """漢数字をアラビア数字に正規化"""
    def _transpowers(sj, re_obj=_re_kunit, transdic=_TRANSUNIT):
        """漢数字(位)の解析"""
        unit = 1
        result = 0
        for piece in reversed(re_obj.findall(sj)):
            if piece in transdic:
                if unit > 1:
                    result += unit
                unit = transdic[piece]
            else:
                val = int(piece) if piece.isdecimal() else _transpowers(piece)
                result += val * unit
                unit = 1

        if unit > 1:
            result += unit

        return result

    normstr = string.translate(_tt_knum)
    # 数字と漢数字(位)を抽出して位が含まれてたら展開
    for suji in sorted(set(_re_ksuji.findall(normstr)),
                       key=lambda s: len(s),
                       reverse=True):
        if not suji.isdecimal():
            arabic = _transpowers(suji, _re_manshin, _TRANSMANS)
            normstr = normstr.replace(suji, str(arabic))

    return normstr


_ROMANNUMS = {'M':1000, 'D':500, 'C':100, 'L':50, 'X':10, 'V':5, 'I':1, '0':0}
_re_roman = _re.compile(
    r'M{0,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})$')


def _roman2arabic(string):
    """ローマ数字をアラビア数字に正規化"""
    for r in filter(None, reversed(_re_roman.findall(string))):
        roman = r
        break
    else:
        return string

    result = 0
    prev = '0'
    for num in reversed(roman):
        factor = +1 if _ROMANNUMS[num] >= _ROMANNUMS[prev] else -1
        result += factor * _ROMANNUMS[num]
        prev = num

    return _re_roman.sub(str(result), string)


def _corenormalizer(strings):
    """漢数字・ローマ数字をアラビア数字にしてunicode正規化"""
    for string in strings:
        # 漢数字(数字)の変換
        normstr = _kansuji2arabic(string)
        # ローマ数字の変換
        normstr = _roman2arabic(normstr)
        # unicode正規化
        normstr = _unicodedata.normalize('NFKC', normstr)

        yield normstr


_re_tailnum = _re.compile(r'(?:no|vol|パート|part|第|その|其[ノ之])(\d+)巻?$', flags=_re.I)


def _ret_serial(strings):
    """通番らしきものの採取"""
    for tailnum in filter(lambda s: s.isdecimal(), reversed(strings)):
        return tailnum

    for part in reversed(strings):
        for tailnum in filter(None, reversed(_re_tailnum.findall(part))):
            return tailnum

    return None


# _sub_blbracket = (_re.compile(r'^【.+?】+?|【.+?】+?$'), '')
_sub_blbtag = (_re.compile(
    r'【[^】]*?(限定|アウトレット|予約|[早旧]得|Blu-ray|DM便|メール便|パンツ|ポイント|特価|セール|在庫|セット|今週|GQE).*?】', flags=_re.I),
               '')
_sub_nowrdchr = (_re.compile(r'\W'), ' ')
_tt_dot = str.maketrans('', '', '.')


def _normalize(string: str, sep=''):
    """タイトル文字列を正規化"""

    # 【.+?】くくりタグ文字列を除去
    string = sub(_sub_blbtag, string).upper()
    # 「.」だけは詰める(No., Vol.)
    string = string.translate(_tt_dot)
    # 非unicode単語文字を空白に置き換えて空白文字で分割
    strings = sub(_sub_nowrdchr, string).split()
    # 漢数字・ローマ数字をアラビア数字に置き換えてunicode正規化
    strings = tuple(_corenormalizer(strings))

    # 連番らしきものがあれば採取
    serial = _ret_serial(strings)

    return sep.join(strings), serial


def _fix_ngword(string):
    """FANZAの伏字解除"""
    if '●' in string:
        for key in filter(lambda k: k in string, _NGWORD):
            string = string.replace(key, _NGWORD[key])

    return string

def _check_omitword(title: str):
    """タイトル内の除外キーワードチェック"""

    # タイトル内に除外文字列があればそれとタイプをyield
    for key in filter(lambda k: k in title, _OMITWORDS):
        _verbose('omit key, word: {}, {}'.format(key, _OMITWORDS[key]))
        yield _OMITWORDS[key], key

    # タイトルとマッチする除外文字列パターンがあればそれとタイプをyield
    for re in _OMNI_PATTERN_WORDS:
        match = re.findall(title)
        if match:
            _verbose('omit match, word: {}, {}'.format(
                match[0], _OMNI_PATTERN_WORDS[re]))
            yield _OMNI_PATTERN_WORDS[re], match[0]


_re_oroshi = _re.compile(r'撮り(おろ|下ろ|卸)し')


def _isnot_torioroshi(genre, title):
    """総集編でタイトルに「撮りおろし」となければ真を返す"""
    return genre == '総集編作品' and not _re_oroshi.search(title)


_re_omnivals = (
    # 10人/名 以上
    _re.compile(r'(?:1[0-9]|[2-9]\d|\d{3,})(?:人[^目\d]?|名)'),
    # 20(連)発(射) 以上
    _re.compile(r'(?:[2-9]\d|\d{3,})連?[発射]'),
    # 10本番/SEX 以上
    _re.compile(r'(?:1[0-9]|[2-9]\d|\d{3,})(?:本番|SEX)', _re.I),
    # 4時間 以上
    _re.compile(r'(?:[4-9](?:\.\d+)?|\d{2,}(?:\.\d+)?)時間'),
    # 240分 以上
    _re.compile(r'(?:2[4-9]\d|[3-9]\d{2}|\d{4,})分'),
    # nn選
    _re.compile(r'\d+選'),
    # 10組 以上
    _re.compile(r'(?:1[0-9]|[2-9]\d|\d{3,})組'),
)


_re_ge4h = _re.compile(r'(?:[4-9]|\d{2,})時間')
_re_ge200m = _re.compile(r'(?:[2-9]\d{2}|\d{4,})分')


def check_omit(title, cid, omit_suss_4h=None, no_omits=set()):
    """
    除外対象かどうかチェック

    除外対象なら対象の情報を返す。
    """
    def _check_omitprfx(cid, prefix=_OMNI_PREFIX, patn=_OMNI_PATTERN_CID):
        """隠れ総集編チェック(プレフィクス版)"""
        return any(map(cid.startswith, prefix)) or any(p.search(cid) for p in patn)

    def _check_omnivals(title):
        """隠れ総集編チェック(関連数値編)"""
        title = _normalize(title, sep=' ')[0]
        hit = tuple(_chain.from_iterable(
            p.findall(title) for p in _re_omnivals))
        if len(hit) > 1:
            return hit

    def _is_omnirookie(cid, title):
        """ROOKIE隠れ総集編チェック"""
        if _check_omitprfx(cid, _ROOKIE):
            # ROOKIEチェック
            hh = _re_ge4h.findall(title)
            mmm = _re_ge200m.findall(title)
            return hh, mmm
        else:
            return None, None

    # 除外作品チェック (タイトル内の文字列から)
    for key, word in filter(lambda k: k[0] not in no_omits,
                            _check_omitword(title)):
        return key, word

    # 隠れ総集編チェック
    if '総集編作品' not in no_omits and _isnot_torioroshi('総集編作品', title):
        # 隠れ総集編チェック(タイトル内の数値から)
        omnivals = _check_omnivals(title)
        if omnivals:
            return '総集編作品', omnivals

        # 隠れ総集編チェック(cidから)
        if _check_omitprfx(cid):
            return '総集編作品', cid

        # 総集編容疑メーカー
        if omit_suss_4h:
            hh, mmm = _is_omnirookie(cid, title)
            if hh or mmm:
                return '総集編作品', omit_suss_4h + '(4時間以上)'

    # 隠れIVチェック
    if 'イメージビデオ' not in no_omits:
        if _check_omitprfx(cid, _IV_PREFIX):
            return 'イメージビデオ', cid


class NotKeyIdYet:
    """品番が key_id になるまで True を返す"""
    def _is_start_pid(self, pid):
        prefix, serial = split_pid(pid)
        return prefix == self._key_id[0] and serial < self._key_id[1]

    def __init__(self, key_id, key_type, attr, if_inactive=False):
        if not key_id:
            self._match = lambda x: if_inactive

        else:
            if key_type == 'start':

                if attr == 'pid':
                    self._key_id = split_pid(key_id)
                    self._match = self._is_start_pid

                elif attr == 'cid':
                    self._key_id = key_id
                    self._match = lambda cid: cid < self._key_id

                else:
                    raise ValueError('Invalid value: attr({})'.format(attr))

            elif key_type == 'last':

                if attr == 'pid':
                    self._key_id = rm_hyphen(key_id)
                    self._match = lambda pid: rm_hyphen(pid) != self._key_id

                elif attr == 'cid':
                    self._key_id = key_id
                    self._match = lambda cid: cid != self._key_id

                else:
                    raise ValueError('Invalid value: attr({})'.format(attr))

            else:
                raise ValueError('Invalid value: key_id({})'.format(key_id))

    def __call__(self, cand):
        return self._match(cand)


def _compare_title(cand, title, ttl_s=None):
    """
    同じタイトルかどうか比較

    title はあらかじめ _normalize() に通しておくこと
    """
    cand, cand_s = _normalize(cand.strip())
    _verbose('cand norm:  {}, {}'.format(cand, cand_s))

    is_startsw = title.startswith(cand) or cand.startswith(title)

    return (is_startsw and ttl_s == cand_s) if ttl_s or cand_s else is_startsw


class _LongTitleError(Exception):
    pass


def _ret_apache(cid, pid):
    """Apacheのタイトルの長いやつ"""
    _verbose('Checking Apache title...')

    serial = cid.replace('h_701ap', '')
    url = 'http://www.apa-av.jp/list_detail/detail_{}.html'.format(serial)

    resp, he = open_url(url)

    if resp.status != 200:
        raise _LongTitleError(url, resp.status)

    opid, actress, director = ret_apacheinfo(he)

    if pid != opid:
        _verbose('check_apache: PID on Apache official is different from DMM')
        raise _LongTitleError(pid, opid)

    return he.head.find('title').text.strip().replace('\n', ' ')


class _RetrieveTitleSCOOP:
    """SCOOPのタイトルの長いやつ"""
    def __init__(self):
        self._cookie = load_cache('kmp_cookie', expire=86400)

    def __call__(self, cid, pid):
        _verbose('Checking SCOOP title...')

        prefix = cid[2:6]
        serial = cid[6:]
        url = 'http://www.km-produce.com/works/{}-{}'.format(prefix, serial)

        while True:
            _verbose('cookie: ', self._cookie)
            resp, he = open_url(url, set_cookie=self._cookie)
            if 'set-cookie' in resp:
                self._cookie = resp['set-cookie']
                _verbose('set cookie')
                save_cache(self._cookie, 'kmp_cookie')
            else:
                break

        if resp.status != 200:
            raise _LongTitleError(url, resp.status)

        return he.find_class('title')[0].text.strip()

_ret_scoop = _RetrieveTitleSCOOP()


class _RetrieveTitlePlum:
    """プラムのタイトル"""
    def __init__(self, prefix):
        self._prefix = prefix
        self._ssid = None
        self._cart = None

    def _parse_cookie(self, cookie):
        _verbose('parse cookie: ', cookie)
        for c in filter(lambda c: '=' in c,
                        (i.split(';')[0].strip() for i in cookie.split(','))):
            lhs, rhs = c.split('=')
            if rhs == 'deleted':
                self._ssid = lhs
            elif lhs == 'cart_pDq7k':
                self._cart = rhs

        if self._ssid and self._cart:
            return 'AJCSSESSID={}; cart_pDq7k={}; enter=enter'.format(
                self._ssid, self._cart)
        else:
            return None

    def __call__(self, cid, pid):
        _verbose('Checking Plum title...')

        serial = cid.replace(self._prefix, '')
        if len(serial) < 3:
            serial = '{:0>3}'.format(serial)
        url = 'http://www.plum-web.com/?view=detail&ItemCD=SE{}&label=SE'.format(
            serial)

        cookie = ''
        for i in range(5):
            cookie = self._parse_cookie(cookie)
            _verbose('plum cookie: ', cookie)

            resp, he = open_url(url, set_cookie=cookie, cache=False)

            cookie = self._parse_cookie(resp.get('set-cookie', cookie))

            if resp.status != 200:
                raise _LongTitleError(url, resp.status)

            if not len(he.get_element_by_id('nav', '')):
                break

        else:
            _emsg('E', 'プラム公式サイトをうまく開けませんでした。')

        title = he.find('.//h2[@id="itemtitle"]').text.strip()
        title = sub(_sub_ltbracket, title)

        return title

# _ret_plum_se = _RetrieveTitlePlum('h_113se')


class OmitTitleException(Exception):
    """総集編など除外タイトル例外"""
    def __init__(self, key, word):
        self.key = key
        self.word = word


class DMMParser:
    """DMM作品ページの解析"""
    _TITLE_FROM_OFFICIAL = {'h_701ap': _ret_apache,    # アパッチ
                            # '84scop': _ret_scoop,    # SCOOP
                            # '84scpx': _ret_scoop,    # SCOOP
                            # 'h_113se': _ret_plum_se, # 素人援交生中出し(プラム)
    }

    _re_genre = _re.compile(r'/article=keyword/id=(\d+)/')
    _re_age = _re.compile(r'(\(\d+?\))$')

    def __init__(self, no_omits=gen_no_omits(), patn_pid=None,
                 start_date=None, start_pid_s=None, filter_pid_s=None,
                 autostrip=True, pass_bd=False, n_i_s=False,
                 longtitle=False, check_rental=False, check_rltd=False,
                 deeper=True, quiet=False):
        self._no_omits = no_omits
        self._patn_pid = patn_pid
        self._start_date = start_date
        self._not_sid = NotKeyIdYet(start_pid_s, 'start', 'pid')
        self._filter_pid_s = filter_pid_s
        self._autostrip = autostrip
        self._pass_bd = pass_bd
        self._n_i_s = n_i_s
        self._longtitle = longtitle
        self._check_rental = check_rental
        self._check_rltd = check_rltd
        self._deeper = deeper
        self._quiet = quiet

        self._sm = Summary()

    def _mark_omitted(self, key, hue):
        """除外タイトルの扱い"""
        if key in self._no_omits:
            # 除外対称外なら備考に記録
            if not any(key in s for s in self._sm['note']):
                self._sm['note'].append(key)
        else:
            # 除外対象なら処理中止
            _verbose('Omit exception ({}, {})'.format(key, hue))
            raise OmitTitleException(key, hue)

    def _chk_longtitle(self):
        """DMMでは端折られている可能性があるタイトルが長いメーカーチェック"""
        def _det_longtitle_maker():
            for key in filter(lambda k: self._sm['cid'].startswith(k),
                              self._TITLE_FROM_OFFICIAL):
                _verbose('title from maker: ', key)
                return self._TITLE_FROM_OFFICIAL[key]
            return False

        tmkr = ''
        titleparser = _det_longtitle_maker()
        if titleparser:
            # Apacheの作品タイトルはメーカー公式から
            try:
                tmkr = titleparser(self._sm['cid'], self._sm['pid'])
            except _LongTitleError as e:
                _emsg(
                    'W',
                    'メーカー公式サイトから正しい作品ページを取得できませんでした: ',
                    e.args)
            _verbose('title maker: ', tmkr)

            return tmkr
        else:
            return None

    def _ret_title(self):
        """タイトルの採取 (DMMParser)"""
        try:
            tdmm = self._he.find('.//div[@class="hreview"]/h1').text
        except AttributeError:
            _emsg('E', 'DMM作品ページではないようです。')

        _verbose('title dmm: ', tdmm)

        title = self._chk_longtitle() or tdmm

        title_dmm = tdmm if not _compare_title(title,
                                               *_normalize(tdmm)) else ''

        return title, title_dmm

    def _ret_props(self, prop):
        """各種情報"""

        tag = prop.text.strip()

        if tag == '種類：':

            self._sm['media'] = rm_nlcode(getnext_text(prop))
            _verbose('media: ', self._sm['media'])

        elif tag in ('発売日：', '貸出開始日：', '配信開始日：', '商品発売日：'):

            data = getnext_text(prop)

            if self._start_date and data.replace('/', '') < self._start_date:
                raise OmitTitleException('release', 'date')

            rl = rm_nlcode(data).replace(' 10:00～', '')

            if rl != '':
                self._sm['release'] = rl

            _verbose('release: ', self._sm['release'])

        elif tag == '収録時間：':

            self._sm['time'] = rm_nlcode(getnext_text(prop))
            _verbose('time: ', self._sm['time'])

        elif tag == 'メーカー：':

            mk = prop.getnext().find('a')

            try:
                self._sm['maker_id'] = mkid = get_id(mk.get('href'), param='maker')[0]
            except AttributeError:
                return

            if not self._sm['maker']:
                self._sm['maker'] = getnext_text(prop, 'a')[0]

            # ジュエル系なら出演者情報は無視
            if mkid in _IGNORE_PERFORMERS:
                self._ignore_pfmrs = True
                _verbose('Jewel family found')

            # 総集編メーカーチェック
            if mkid in _OMIT_MAKER:
                self._mark_omitted('総集編作品', _OMIT_MAKER[mkid])

            # 総集編容疑メーカー
            if mkid in _OMIT_SUSS_4H:
                self._omit_suss_4h = _OMIT_SUSS_4H[mkid]

            # 他のサービスを強制チェック
            self._force_chk_sale = _FORCE_CHK_SALE_MK.get(mkid, False)
            _verbose('series forece chk other: ', self._force_chk_sale)

            _verbose('maker: ', self._sm['maker'])

        elif tag == 'レーベル：':

            lb = prop.getnext().find('a')

            try:
                lbid = get_id(lb.get('href'), param='label')[0]
            except AttributeError:
                return

            self._sm['label'] = lb.text

            # 隠れ総集編レーベルチェック
            if lbid in _OMIT_LABEL:
                self._mark_omitted('総集編作品', _OMIT_LABEL[lbid])

            self._sm['label_id'] = lbid
            _verbose('label: ', self._sm['label'])

        elif tag == 'シリーズ：':

            sr = prop.getnext().find('a')

            if sr is None:
                return

            srid = get_id(sr.get('href'), param='series')[0]

            if self._n_i_s:
                _verbose('not in series')
                raise OmitTitleException('series',
                                         _NiS(sid=srid, name=sr.text))

            # 隠れ総集編シリーズチェック
            if srid in _OMIT_SERIES:
                self._mark_omitted('総集編作品', _OMIT_SERIES[srid])

            if srid in _IGNORE_SERIES:
                # シリーズとして扱わない処理
                _verbose('series hid: ', _IGNORE_SERIES[srid])
                self._sm['series'] = '__HIDE__'
            else:
                self._sm['series'] = _fix_ngword(getnext_text(prop, 'a')[0])

            # 独自ページ個別対応
            # ・SOD女子社員
            if self._sm['series'] == 'SOD女子社員':
                self._sm['series'] += ('シリーズ' +
                                       self._sm['release'].split('/', 1)[0])

            self._sm['series_id'] = srid

            # 他のサービスを強制チェック
            self._force_chk_sale = _FORCE_CHK_SALE_SR.get(srid, False)
            _verbose('series forece chk other: ', self._force_chk_sale)

            _verbose('series: ', self._sm['series'])

        elif tag == '監督：':
            data = getnext_text(prop, 'a')
            if data and not self._sm['director']:
                self._sm['director'] = data

            _verbose('director: ', self._sm['director'])

        elif tag == 'ジャンル：':
            for g in prop.getnext():
                _verbose('genre: ', g.text)
                try:
                    gid = self._re_genre.findall(g.get('href'))[0]
                except IndexError:
                    continue

                omitgenre = _OMITGENRE.get(gid, False)
                # 除外対象ジャンルであれば記録または中止
                if omitgenre and _isnot_torioroshi(omitgenre,
                                                   self._sm['title']):
                    self._mark_omitted(omitgenre, 'genre')

                if gid == _GENRE_BD:
                    self._bluray = True
                    _verbose('media: Blu-ray')

                self._sm['genre'].append(g.text)

        elif tag == '品番：':
            data = getnext_text(prop)

            # URL上とページ内の品番の相違チェック
            if not self._quiet and \
               self._sm['cid'] and \
               self._sm['cid'] != data.rsplit('so', 1)[0]:
                _emsg('I', '品番がURLと異なっています: url={}, page={}'.format(
                    self._sm['cid'], data))

            self._sm['pid'], self._sm['cid'] = gen_pid(data, self._patn_pid)
            _verbose('cid: ', self._sm['cid'], ', pid: ', self._sm['pid'])

            # 作成開始品番チェック(厳密)
            if self._not_sid(self._sm['pid']):
                raise OmitTitleException('pid', self._sm['pid'])

            # filter-pid-sチェック
            if self._filter_pid_s and not self._filter_pid_s.search(
                    self._sm['pid']):
                raise OmitTitleException('pid filtered', self._sm['pid'])

        # 動画用
        elif tag == '名前：':
            # 素人動画のタイトルは後でページタイトルと年齢をくっつける
            try:
                age = self._re_age.findall(getnext_text(prop))[0]
            except IndexError:
                age = ''
            self._sm['subtitle'] = age
            _verbose('ama subtitle(age): ', self._sm['subtitle'])

        elif tag == 'サイズ：':
            self._sm['size'] = getnext_text(prop)
            self._sm['size'] = self._sm['size'].replace('W-- H', '').replace('T--- ', '').replace('B-- ', '').rstrip()
            _verbose('ama size: ', self._sm['size'])

        return

    def _ret_images(self, service):
        """パッケージ画像のURLの取得"""
        meta_img = self._he.find('.//meta[@property="og:image"]')
        try:
            meta_img = meta_img.get('content')
            if meta_img.endswith('ps.jpg'):
                # 配信動画, VR
                img_sm = meta_img
                img_lg = meta_img.replace('ps.jpg', 'pl.jpg')
            elif meta_img.endswith('jp.jpg'):
                # 素人
                img_sm = meta_img.replace('jp.jpg', 'js.jpg')
                img_lg = meta_img
            else:
                # DVD
                img_lg = meta_img
                img_sm = meta_img.replace('pl.jpg', 'ps.jpg')
        except AttributeError:
            img_lg = None
            img_sm = None

        return img_lg, img_sm

    def _ret_performers(self, gvnpfmrs):
        """
        出演者の取得
        (女優名, リダイレクト先, おまけ文字列) のタプルを返すジェネレータ
        """
        def _trim_name(name):
            """女優名の調整"""
            name = name.strip()
            if self._autostrip:
                name = re_inbracket.split(name)[0]
            return name

        def _list_pfmrs(plist):
            return [(_trim_name(p.strip()), '', '') for p in plist]

        _verbose('Retrieving performers... ')

        el = self._he.get_element_by_id('performer', ())
        len_el = len(el)
        if len_el:
            # if self._omit_suss and len_el > 3:
            #     # ROOKIE出演者数チェック
            #     self._mark_omitted('総集編作品', self._omit_suss)

            if el[-1].get('href') == '#':
                # 「▼すべて表示する」があったときのその先の解析
                _verbose('more performers found')
                more_js = el.getparent().find('script')

                if more_js is not None:
                    more_path = re_more.findall(more_js.text)[0]
                else:
                    # 処理スクリプトがHEAD内にある場合(動画ページ)用
                    for scr in self._he.xpath('head/script/text()'):
                        more_path = re_more.findall(scr)
                        if more_path:
                            more_path = more_path[0]
                            break
                    else:
                        _emsg('E', '出演者の「▼すべて表示する」先が取得できませんでした。')

                more_url = _up.urljoin(_BASEURL_DMM, more_path)
                resp, he_more = open_url(more_url, 'utf-8', set_cookie='age_check_done=1')
                _verbose('more_url opened')

                p_list = _list_pfmrs(he_more.xpath('.//a/text()'))
            else:
                p_list = _list_pfmrs(el.xpath('a/text()'))
        else:
            p_list = []

        # pfilter = ''.join(_chain.from_iterable(p_list))

        # DMMから取得した出演者をyield
        return p_list.copy()
        # for name in p_list:
        #     yield name

        # 与えられた出演者情報でDMMに欠けているものをyield
        # for gvn in gvnpfmrs:
        #     _verbose('gvn: ', gvn)
        #     if all(g not in pfilter for g in gvn[:2] if g):
        #         yield gvn

    _choosepare = {'rental': ('/rental/', lambda x: x.replace('/ppr', '')),
                   'videoa': ('/digital/videoa/', lambda x: x),
                   'dvd':    ('/mono/dvd/', lambda x: x)}

    def _get_otherslink(self, service, firmly=True):
        """他のサービスの作品リンクの取得"""

        def _chooselink(others, service):
            part, how = self._choosepare[service]
            for o in others:
                link = o.get('href')
                if part in link:
                    return how(link)
            return ''

        _verbose('Getting otherslink...')
        opath = _chooselink(self._he.iterfind('.//ul[@class="others"]/li/a'),
                            service)

        if not opath and firmly:
            # 「他のサービスでこの作品を見る」欄がないときに「他の関連商品を見る」で探してみる
            _verbose('link to others not found. checking related item...')
            searstr = self._sm['title'] + '|' + (
                self._sm['series'] if self._sm['series'] else '')

            searlurl = '{}/search/=/searchstr={}/cid={}/{}'.format(
                _BASEURL_DMM,
                quote(searstr),
                self._sm['cid'],
                'limit=120/related=1/sort=rankprofile/view=text/')

            resp, he_rel = open_url(searlurl)

            ttl_nr, ttl_s = _normalize(self._sm['title'])
            _verbose('title norm: ', ttl_nr, ttl_s)

            others = filter(lambda t: _compare_title(t.text, ttl_nr, ttl_s),
                            he_rel.iterfind('.//p[@class="ttl"]/a'))
            opath = _chooselink(others, service).split('?')[0]

        return _up.urljoin(_BASEURL_DMM, opath) if opath else False

    def _link2other(self, url, tag, release):
        return '※[[{}版>{}]]のリリースは{}。'.format(tag, url, release)

    def _get_otherscontent(self, service):
        """他サービス版の情報取得"""
        others_url = self._get_otherslink(service)
        if not others_url:
            _verbose('Others link not found')
            return False

        resp, he_others = open_url(others_url)

        others_data = Summary(self._sm.values())
        others_data['url'] = others_url
        others_data['pid'], others_data['cid'] = gen_pid(others_url,
                                                         self._patn_pid)

        others_data.update(_othersparser(he_others, service, sm=others_data))
        _verbose('others data: ', others_data.items())

        if service == ('rental',):
            # レンタル版のリリースが早ければそれを返す
            if others_data['release'] >= self._sm['release']:
                _verbose("rental isn't released earlier")
                return False
            else:
                others_data['others'].append(
                    self._link2other(self._sm['url'],
                                     'セル',
                                     self._sm['release']))
                _verbose('rental precedes: ', others_data['note'])

        return _deepcopy(others_data)

    def _check_rltditem(self, media):
        """
        DVD⇔Blu-ray (「ご注文前にこちらの商品もチェック！」の欄)関連商品リンクを返す
        """
        _verbose('checking {}...'.format(media))
        iterrltd = self._he.iterfind(
            './/div[@id="rltditem"]/ul/li/a/img[@alt="{}"]'.format(media))

        for rlitem in iterrltd:
            rlttl = rlitem.getparent().text_content().strip()
            _verbose('rltd ttl: ', rlttl)
            # 限定品の除外チェック
            if any(k not in self._no_omits
                   for k, w in _check_omitword(rlttl)):
                break
            else:
                _verbose('rltditem: ', rlitem.getparent().get('href'))
                return _up.urljoin(_BASEURL_DMM,
                                   rlitem.getparent().get('href'))

        _verbose('rltditem not found.')
        return False

    def __call__(self, he, service, sm=Summary(), ignore_pfmrs=False):
        """作品ページの解析"""
        self._he = he
        self._sm = sm
        self._ignore_pfmrs = ignore_pfmrs
        self._bluray = False
        self._omit_suss_4h = False
        self._rental_pcdr = False
        self._force_chk_sale = False

        self.data_replaced = False

        _verbose('Parsing DMM product page: deper=', self._deeper)
        _verbose('self._sm preset: ', self._sm.items())

        # タイトルの取得
        if not self._sm['title'] or self._sm['title'].startswith('__'):
            self._sm['title'], self._sm['title_dmm'] = self._ret_title()

        # 伏字の解除
        self._sm['title'] = _fix_ngword(self._sm['title'])

        # 作品情報の取得
        for prop in self._he.iterfind('.//td[@class="nw"]'):
            self._ret_props(prop)

        # 除外作品チェック
        omitinfo = check_omit(self._sm['title'],
                              self._sm['cid'],
                              self._omit_suss_4h,
                              no_omits=gen_no_omits())

        if omitinfo:
            self._mark_omitted(*omitinfo)

        if self._omit_suss_4h and cvt2int(self._sm['time']) > 200:
            # 総集編容疑メーカーで4時間以上
            self._mark_omitted('総集編作品', self._omit_suss_4h + '(4時間以上)')

        if service == 'ama':
            # 素人動画の時のタイトル/副題の再作成
            self._sm['title'] = self._sm['subtitle'] = \
                                self._sm['title'] + self._sm['subtitle']
            # メディア情報はないのでここで
            self._sm['media'] = '素人動画'
        elif service == 'video':
            self._sm['media'] = 'ビデオ動画'

        sale_data = None
        # if self.deeper and service != 'ama' and __name__ != '__main__':
        if self._deeper and service != 'ama':
            # Blu-ray版のときのDVD版の、またはその逆のチェック
            related = 'DVD' if self._bluray else 'Blu-ray'
            rltd_url = self._check_rltditem(related)
            if rltd_url:
                if self._bluray and self._pass_bd:
                    # Blu-ray版だったときDVD版があればパス
                    _verbose('raise Blu-ray exception')
                    raise OmitTitleException('Blu-ray', 'DVD exists')
                else:
                    self._sm['note'].append('[[{}版あり>{}]]'.format(
                        related, rltd_url))

        # パッケージ画像の取得
        self._sm['image_lg'], self._sm['image_sm'] = self._ret_images(service)

        if not (self._ignore_pfmrs or self._sm['actress']):
            # 出演者の取得
            # self._sm['actress'] = list(
            self._sm['actress'] = self._ret_performers(
                self._sm['actress'])

            # レンタル版で出演者情報がない/不足しているかもなとき他のサービスで調べてみる
            if self._deeper and self._check_rltd and self._force_chk_sale:
                _verbose('possibility missing performers, checking others...')
                other_data = self._get_otherscontent(self._force_chk_sale[1])

                if other_data and other_data['actress']:
                    self._sm['actress'].extend(
                        filter(lambda a: a not in self._sm['actress'],
                               other_data['actress']))

        return ((key, self._sm[key]) for key in self._sm if self._sm[key])

_othersparser = DMMParser(deeper=False)


class DMMTitleListParser:
    """一覧ページの解析"""
    _sub_tsuffix = (_re.compile(r' - \S*( - DMM.R18)?$'), '')

    def __init__(self, no_omits=set(_OMITTYPE), patn_pid=None, show_info=True):
        self._no_omits = no_omits
        self._patn_pid = patn_pid
        self._show_info = show_info
        self.omitted = 0
        self.priurl = ''
        self.article = []

    def _get_article(self, he):
        """アーティクル名の取得"""
        try:
            article = he.find('head/title').text.strip()
        except AttributeError:
            article = ''

        # wiki構文と衝突する文字列の置き換え
        article = trans_wikisyntax(article)
        article = sub(self._sub_tsuffix, article)

        return article

    def _ret_titles(self, titles):
        """作品タイトルとURLの取得 (DMMTitleListParser)"""
        def omit(key, word):
            if self._show_info or _VERBOSE:
                _emsg('I', 'ページを除外しました: cid={}, {:<20}'.format(
                    cid, 'reason=("{}", "{}")'.format(key, word)))
            self.omitted += 1

        for ttl in titles:
            t_el = ttl.find('a')
            if t_el is None:
                continue
            s_el = t_el.find('span')
            if s_el is not None:
                # セール情報を除去
                s_el.drop_tree()
            title = t_el.text
            path = t_el.get('href')
            rx = _re.match("(.+/=/cid=.+/).+", path)
            # url末尾の余計な /?dmmref=aMonoDvd_List/ を消去
            if rx:
                url = _up.urljoin(_BASEURL_DMM, rx[1])
            else:
                url = _up.urljoin(_BASEURL_DMM, path)
            pid, cid = gen_pid(url, self._patn_pid)
            # cid = cid.lstrip('79')

            # 除外作品チェック
            omitinfo = check_omit(title, cid, no_omits=self._no_omits)
            if omitinfo:
                omit(*omitinfo)
            else:
                yield url, Summary(url=url, title=title, pid=pid, cid=cid)

    def _ret_nextpage(self, he):
        """ページネーション処理"""
        try:
            pagin = he.find_class(
                'list-boxpagenation')[0].xpath('.//a[text()="次へ"]')
        except IndexError:
            return False

        return _up.urljoin(_BASEURL_DMM,
                           pagin[0].get('href')) if pagin else False

    def __call__(self, he):
        """解析実行"""
        self.article.append((self._get_article(he), self.priurl))

        self.nexturl = self._ret_nextpage(he)

        return self._ret_titles(he.find_class('ttl'))


_re_splitpid1 = _re.compile(r'[+-]')
_re_splitpid2 = _re.compile(r'([a-z]+)(\d+)', _re.I)


def split_pid(pid):
    """品番をプレフィクスと連番に分離"""
    try:
        prefix, serial = _re_splitpid1.split(pid)
    except ValueError:
        prefix, serial = _re_splitpid2.findall(pid)[0]

    return prefix, serial


def sort_by_id(products, reverse=False):
    """
    品番をソート

    桁数が揃ってない品番もソート
    """
    def _make_items(products, maxdigit):
        """URL(キー)と桁を揃えた品番"""
        for url in products:
            prefix, serial = split_pid(products[url].pid)
            yield url, '{0}{1:0>{2}}'.format(prefix, serial, maxdigit)

    maxdigit = max(cvt2int(products[p].pid) for p in products)

    return (url for url, pid in sorted(_make_items(products, maxdigit),
                                       key=_itemgetter(1),
                                       reverse=reverse))


def from_dmm(listparser, priurls, pages_last=0,
             key_id=None, key_type=None, idattr='pid',
             ignore=False, show_info=True):
    """DMMから作品一覧を取得"""
    _verbose('Start parsing DMM list pages')

    match_key_id = NotKeyIdYet(key_id, key_type, idattr, if_inactive=True)

    for purl in priurls:

        listparser.priurl = purl

        searchurl = _up.urljoin(purl, 'limit=120/view=text/')
        pages = 1

        while searchurl:

            if show_info:
                inprogress('(一覧: {} ページ)  '.format(pages))

            resp, he = open_url(searchurl, set_cookie='age_check_done=1')
            if resp.status != 200 and ignore:
                return ((False, False),)

            if resp.status == 404:
                _emsg('E',
                      '指定した条件でページは見つかりませんでした: url=',
                      searchurl)
            elif resp.status != 200:
                _emsg('E',
                      'URLを開く際にエラーが発生しました: staus=',
                      resp.status)

            # HTMLの解析
            for url, prop in listparser(he):

                yield url, prop

                if not match_key_id(getattr(prop, idattr)):
                    p = pages + 1
                    pages_last = min((pages_last, p)) if pages_last else p
                    _verbose('set pages last: ', pages_last)

            pages += 1
            _verbose('Pages : {} > {}'.format(pages, pages_last))

            searchurl = listparser.nexturl
            _verbose('nexturl: ', searchurl)

            if pages_last and pages > pages_last:
                _verbose('reached pages_last')
                break

    _verbose('Parsing list pages finished')


_re_name = _re.compile(
    r'(?P<fore>[\w>]*)?(?P<paren>[(（][\w>]*[）)])?(?P<back>[\w>]*)?')


def parse_names(names):
    """
    出演者情報の解析(rawテキスト)

    dmm2ssw.py -a オプション渡しとTSVからインポート用
    """
    _verbose('Parsing name (raw text)...')

    for name in names:
        # カッコ括りの付記の分割
        m = _re_name.search(name)

        if any(m.groups()):
            shown = m.group('fore') or m.group('back')
            parened = m.group('paren') or ''
        else:
            shown = name
            parened = ''

        if shown.endswith('人目') and not parened:
            # n人目だったときのカッコ内送り
            parened = '({})'.format(shown)
            shown = ''

        # リダイレクト先の取得
        if '>' in shown:
            shown, dest = shown.split('>')
        else:
            dest = ''

        _verbose('name prepared: {}, {}, {}'.format(shown, dest, parened))
        yield shown, dest, parened


_re_etc = _re.compile(r'ほか\w*?計(\d+)名')


def ret_numofpfmrs(etc):
    """ほか計n名を取得"""
    number = None

    m = _re_etc.findall(etc)

    if m:
        number = int(m[0])
    elif etc == 'ほか':
        number = -1
    elif etc == 'ほか数名':
        number = -2

    return number


def from_tsv(files):
    """タイトル一覧をファイルからインポートするジェネレータ(TSV)"""
    files_exists('r', *files)
    _verbose('from tsv file: {}'.format(files))

    with _fileinput.input(files=files) as f:
        for row in f:
            # タブ区切りなので改行を明示して除去してタブを明示して分割
            row = tuple(c.strip() for c in row.rstrip('\n').split('\t'))

            # 女優名がある場合分割
            try:
                actress = re_delim.split(row[3]) if row[3] else []
            except IndexError:
                _emsg('E', '正しいインポートファイル形式ではないようです。')

            # 処理用に女優名を要素解析
            actress = list(parse_names(actress))
            numcols = len(row)
            number = cvt2int(row[4]) if numcols > 4 else 0
            director = re_delim.split(row[5]) if numcols > 5 else []
            note = row[6] if numcols > 6 else []

            yield row[0], Summary(url=row[0],
                                  title=row[1],
                                  pid=row[2],
                                  actress=actress.copy(),
                                  number=number,
                                  director=director.copy(),
                                  note=note)


class _FromWiki:
    """タイトル一覧をウィキテキスト(表形式)からインポート"""
    def __init__(self):
        self.article = ''

    def _parse_names(self, name):
        """出演者情報の解析(ウィキテキスト)"""
        shown = dest = parened = ''

        for e in filter(None, _re_interlink.split(name)):

            # いったん丸カッコ括りを解く
            elem = e.strip().strip('()')

            if elem.startswith('[['):
                shown = elem.strip('[]')
                if '>' in shown:
                    shown, dest = shown.split('>')
                else:
                    dest = ''
            else:
                parened = '({})'.format(elem)

        _verbose('name prepared: {}, {}, {}'.format(shown, dest, parened))
        return shown, dest, parened

    def __call__(self, files, rawpfmrs=False):
        _verbose('from wiki: ', files)

        self.article = ''
        Cols = None

        with _fileinput.input(files) as fd:
            for row in fd:

                row = row.strip()

                if row.startswith('*[[') and not self.article:
                    self.article = re_linkpare.findall(row)
                    _verbose('article from wiki: ', self.article)

                if row.startswith('|~NO'):
                    Cols = gen_ntfcols('Cols', row)
                elif not row.startswith('|[['):
                    continue

                md = Cols(*(c.strip() for c in row.split('|')))

                try:
                    pid, url = re_linkpare.findall(md.NO)[0]
                except IndexError:
                    continue

                if not url.endswith('/'):
                    url += '/'

                if not md.TITLE:
                    # タイトルがない時は品番を利用
                    md = md._replace(TITLE='__' + pid)

                # 出演者の解析
                actress = []

                if md.ACTRESS and '別ページ' not in md.ACTRESS:
                    if rawpfmrs:
                        actress = [(a[0], a[1], '')
                                   for a in re_linkpare.finditer(md.ACTRESS)]
                    else:
                        # 「 ほか～」の切り離し
                        # TODO: もっと賢く
                        s = md.ACTRESS.rsplit(maxsplit=1)

                        number = ret_numofpfmrs(s[1]) if len(s) > 1 else 0

                        alist = re_delim.split(s[0])
                        actress = [self._parse_names(a) for a in alist if a]

                note = re_delim.split(md.NOTE)
                note = list(filter(lambda n: 'シリーズ' not in n, note))

                yield url, Summary(url=url,
                                   title=md.TITLE,
                                   pid=pid,
                                   actress=actress.copy(),
                                   number=number,
                                   note=note)

            if Cols is None:
                _emsg('E', '素人系総合Wikiの一覧ページのウィキテキストではないようです: ',
                      _fileinput.filename())


from_wiki = _FromWiki()


class _FromHtml:
    """素人総合WikiページをURLから(HTMLで)読み込んでインポート"""
    def _unquotename(self, el):
        """URLからページ名を取得"""
        url = el.get('href')
        if not url.startswith(BASEURL_SSW):
            return url
        return _clip_pname(el.get('href'))

    def _enclose(self, ph):
        """括弧でくくってなかったらくくる"""
        return ph if ph.startswith('(') else '({})'.format(ph)

    def _parse_performers(self, td):
        """出演者カラムの解析(FromHtml)"""

        # 内部リンクの前にある文字列チェック
        foretxt = (td.text or '').strip()

        if foretxt:
            # 先頭にリテラルあり
            if not len(td.xpath('a')):
                # リテラルのみでアンカー無し
                yield '', '', foretxt
                return
            else:
                # アンカーあり
                fores = re_delim.split(foretxt)
                for ph in filter(None, fores):
                    yield '', '', self._enclose(ph)

        if not len(td):
            # リテラルだけだったら終了
            return

        # 内部リンク処理
        for a in td.iterchildren('a'):

            shown = a.text.strip()
            if shown == '別ページ':
                return

            dest = self._unquotename(a)
            if dest == shown:
                dest = ''

            # 内部リンクの後にある文字列チェック
            tailtxt = (a.tail or '').strip()

            if not tailtxt:
                yield shown, dest, ''
            else:
                # 「~ ほか」チェック
                splitetc = tailtxt.rsplit(maxsplit=1)
                self._number = ret_numofpfmrs(splitetc[-1])
                if len(splitetc) > 1:
                    tailtxt = splitetc[0]
                elif self._number is not None:
                    tailtxt = ''

                tails = re_delim.split(tailtxt)

                # 内部リンクに付随する文字列がないかチェック
                yield shown, dest, tails.pop(0) if tails[0] else ''

                for ph in tails:
                    if ph:
                        yield '', '', self._enclose(ph)

    def _parse_notes(self, note):
        """NOTEの解析"""
        result = ''

        if note.text:
            result += note.text.strip()

        for el in note.iterchildren():
            if el.tag == 'br':
                result += '~~'

            elif el.tag == 'a':
                shown = el.text
                if 'シリーズ' in shown:
                    continue

                dest = self._unquotename(el)

                if shown == dest:
                    dest == ''

                result += '[[{}{}]]'.format(
                    shown, '>{}'.format(dest) if dest else '')

            if el.tail is not None:
                result += el.tail

        return [result.replace('~~', '', 1)] if result else []

    def __call__(self, wikiurls, service='dvd', cache=True):

        def _makeheader(iterth):
            """ヘッダの TITLE → SUBTITLE の置き換え"""
            for th in iterth:
                yield 'TITLE' if th.text == 'SUBTITLE' else th.text

        for wurl in wikiurls:

            if wurl.startswith('http://'):
                resp, he = open_url(wurl, cache=cache)
                if resp.status == 404:
                    _emsg('E', 'ページが見つかりません: ', wurl)
            else:
                with open(wurl, 'rb') as f:
                    he = _fromstring(f.read())

            try:
                self.article = he.find(
                    './/div[@id="page-header-inner"]//h2').text.strip()
            except AttributeError:
                _emsg('E', '素人系総合Wiki一覧ページのHTMLではないようです: ', wurl)

            userarea = he.find_class('user-area')[0]

            for tbl in userarea.iterfind('.//table'):
                try:
                    Cols = gen_ntfcols(
                        'Cols', _makeheader(tbl.find('.//tr[th]').iterfind('th')))
                except:
                    continue

                for tr in tbl.iterfind('.//tr[td]'):
                    self._number = 0

                    tds = tr.xpath('td')

                    try:
                        md = Cols(*tds)
                    except TypeError:
                        continue

                    anchor = md.NO.find('a')
                    if anchor is not None:
                        if anchor.text is None:
                            continue
                        pid = anchor.text.strip()
                        url = anchor.get('href')
                        if not url.endswith('/'):
                            url += '/'
                    else:
                        pid = md.NO.text
                        if not pid:
                            continue
                        altera = md.PHOTO.find('a')
                        if altera is not None:
                            url = altera.get('href')
                            if url.endswith('jpg'):
                                continue
                        else:
                            cid = rm_hyphen(pid).lower()
                            url = build_produrl(service, cid)

                    url = url.replace('http:', 'https:')

                    # タイトルに改行があればスペースへ置き換え
                    if 'TITLE' in md._fields:
                        title = ' '.join(md.TITLE.xpath('text()')) or \
                                '__' + pid
                    else:
                        title = '__' + pid
                    # actress = [a for a in self._parse_performers(md.ACTRESS)
                    #            if a is not None]
                    actress = list(filter(lambda a: a is not None,
                                          self._parse_performers(md.ACTRESS)))
                    note = self._parse_notes(md.NOTE)
                    if 'ORIGINAL' in md._fields:
                        note.extend(self._parse_notes(md.ORIGINAL))

                    yield url, Summary(url=url,
                                       title=title,
                                       pid=pid,
                                       actress=actress.copy(),
                                       number=self._number,
                                       note=note)

from_html = _FromHtml()


def ret_joindata(join_d, args):
    """--join-*データ回収"""
    if args.join_tsv:
        # join データ作成(tsv)
        _verbose('join tsv')
        join_d.update((k, p) for k, p in from_tsv(args.join_tsv))

    if args.join_wiki:
        # join データ作成(wiki)
        _verbose('join wiki')
        for k, p in from_wiki(args.join_wiki):
            if k in join_d:
                join_d[k].merge(p)
            else:
                join_d[k] = p

    if args.join_html:
        # jon データ作成(url)
        _verbose('join html')
        for k, p in from_html(args.join_html, service=args.service):
            if k in join_d:
                join_d[k].merge(p)
            else:
                join_d[k] = p


def join_priurls(retrieval, *keywords, service='dvd'):
    """DMM基底URLの作成"""
    return tuple('{}/{}/-/list/=/article={}/id={}/sort=date/'.format(
        _BASEURL_DMM, _SERVICEDIC[service], retrieval, k) for k in keywords)


def build_produrl(service, cid):
    """DMM作品ページのURL作成"""
    return '{}/{}/-/detail/=/cid={}/'.format(
        _BASEURL_DMM, _SERVICEDIC[service], cid)


def getnext_text(elem, xpath=False):
    """.getnext()してtextしてstrip()"""
    if xpath:
        return [t.strip().strip('-')
                for t in elem.getnext().xpath('{}/text()'.format(xpath))]
    else:
        nexttext = elem.getnext().text
        return nexttext.strip().strip('-') if nexttext else None


def _rdrparser(page, he):
    """wikiリダイレクトページかどうかの検出"""
    _verbose('is sswrdr/page: ', page)
    rdr_flg = False
    userarea = he.find_class('user-area')[0]

    if any(a.get('href').startswith(_BASEURL_DMM)
           for a in userarea.iterfind('.//a[@class="outlink"]')):
        # DMMへのリンクが見つかったらリダイレクトページではないとみなし終了
        _verbose('Not redirect page (dmm link found)')
        return page

    if userarea.text and userarea.text.strip() == '誘導ページ':
        rdr_flg = True
        _verbose('guide page')

    for el in userarea:
        if el.tail and el.tail.strip() == 'リダイレクト：':
            rdr_flg = True
            dest = _clip_pname(el.getnext().get('href'))
            _verbose('rdr dest: ', dest)

            if dest:
                return dest
                # if len(dest) > 1:
                #     _emsg('W',
                #          '"{}"のリダイレクト先を特定できません。もしかして…'.format(
                #              page))
                #     for cand in dest:
                #         _emsg('W', '⇒  ', cand)
                # else:
                #     return dest[0]

    if rdr_flg:
        _emsg('W', '"{}"のリダイレクト先が見つからないか特定できません。'.format(page))
        cands = userarea.xpath('.//a//text()')

        if len(cands) == 1:
            _emsg('W', 'とりあえず"{}"にしておきました。'.format(cands[0]))
            return cands[0]
        elif len(cands):
            _emsg('W', 'もしかして…')
            for cand in cands:
                _emsg('W', '⇒  ', cand)
        else:
            _emsg('W', 'リダイレクトページのようですがリダイレクト先が見つかりません。')

    return ''


def follow_redirect(page):
    """
    リダイレクト先の取得と記録

    辞書REDIRECTS内の値:
    __NON__ ⇒ 実際のページ (リダイレクト不要)
    __NOT_FOUND__ ⇒ page が存在しない
    (リダイレクト先)

    返り値:
    ・実際のページならそのままページ名、
    ・リダイレクト先があればリダイレクト先ページ名、
    ・ページが存在しなければ空文字
    """
    global _REDIRECTS

    _verbose('check redirection: ', page)

    dest = _REDIRECTS.get(page, '')

    if dest:
        _verbose('"{}" found on REDIRECTS: {}'.format(page, dest))
        if dest == '__NON__':
            # 実際のページなら空文字を返す
            return page
        elif dest != '__NOT_FOUND__':
            # リダイレクト先がわかっていればそれを返す
            return dest
        elif not RECHECK:
            # __NOT_FOUND__ でもRECHECKでなければ空文字を返す
            return ''

    # 未知のページのリダイレクト先チェックまたは再チェック
    url = _up.urljoin('http://sougouwiki.com/d/', quote(page))

    resp, he = open_url(url)

    if resp.status == 200:
        dest = _rdrparser(page, he)
        _REDIRECTS[page] = dest or '__NON__'
    elif resp.status == 404:
        _REDIRECTS[page] = '__NOT_FOUND__'

    _verbose('rdr dest: ', dest)
    return dest


def _search_listpage(url, listname, listtype, pid):
    """実際の一覧ページをWiki内で探してみる"""
    # listname = set((listname,)) | set(
    #     re_inbracket.split(listname.rstrip(')）')))
    _verbose('Searching listpage: listname=', listname, ', pid=', pid)

    # http:とhttps:どちらでもヒットさせる
    search_url = _re.sub('https?://', '', url)

    # urlで検索
    resp, he = open_url(
        'http://sougouwiki.com/search?keywords={}'.format(
            quote(search_url, safe='')),
        cache=False)

    searesult = he.find_class('result-box')[0].find('p[1]/strong').tail

    if searesult.strip() == 'に該当するページは見つかりませんでした。':
        _verbose('url not found on ssw')
        return ()

    found = False
    while not found:
        keywords = he.xpath('//h3[@class="keyword"]/a/text()')
        _verbose('list page keywords: ', keywords)

        for word in keywords:
            cand = word.strip().rstrip(' 0123456789')
            _verbose('list cand key: ', cand)

            if cand.startswith(listname) or listname.startswith(cand):
                # Wikiページ名にレーベル/シリーズ名が含まれるか、その逆のとき採用
                yield word
                found = True

            if not found and listtype == 'レーベル':
                # レーベル一覧であれば、品番のプレフィクスが含まれるとき採用
                prefix = split_pid(pid)[0]
                _verbose('prefix: ', prefix)
                if prefix in word and not word.startswith('作品一覧'):
                    _verbose('prefix in pid: ', prefix)
                    yield word
                    found = True

        if not found:
            # 次のページがあったらそちらで再度探す
            he = ssw_searchnext(he)
            if he is None:
                break


def check_actuallpage(url, lpage, ltype, pid):
    """
    実際の一覧ページのチェック

    # 見つかったら_REDIRECTSにキャッシュしておく
    """
    # global _REDIRECTS

    _verbose('check actual list page on ssw...')

    # if not RECHECK \
    #    and url in _REDIRECTS \
    #    and _REDIRECTS[url] != '__NOT_FOUND__':
    #     # キャッシュされてたらそれを返す
    #     _verbose('list page found on REDIRECTS: ', _REDIRECTS[url])
    #     return lpage if _REDIRECTS[url] == '__NON__' else _REDIRECTS[url]

    # 表記揺れ解消
    if ltype == 'レーベル':
        if lpage in _WIKITITLE_L:
            lpage = _WIKITITLE_L[lpage]
    elif ltype == 'シリーズ':
        if lpage in _WIKITITLE_S:
            lpage = _WIKITITLE_S[lpage]

    pages = tuple(_search_listpage(url, lpage, ltype, pid))
    _verbose('list page found: ', pages)

    result = None
    numcand = len(pages)
    if not numcand:
        _verbose('list page search result is zero')
        # 見つからなかったらシリーズ/レーベル名で開いてあればそれを返す
        dest = follow_redirect(lpage)
        _verbose('dest: ', dest)
        if dest:
            result = dest
    elif numcand == 1:
        # 候補が1個ならそれを返す
        result = pages[0]
    else:
        _emsg('I', '一覧ベージ候補が複数見つかりました:')
        for cand in pages:
            _emsg('I', '⇒ ', cand)

    # if result:
    #     _REDIRECTS[url] = result
    #     save_cache(_REDIRECTS, _RDRDFILE)

    return result


def stringize_performers(pfmrs, number, follow):
    """出演者文字列の作成"""
    def _build_performerslink(pfmrs, follow):
        """女優リンクの作成"""
        for shown, dest, parened in pfmrs:
            if shown in HIDE_NAMES_V:
                shown, dest, parened = '', '', '(削除依頼対応)'
            elif follow and shown and not dest:
                # 名前が無かったり既にリダイレクト先があったらスルー
                dest = follow_redirect(shown)

            ilink = '{}>{}'.format(shown, dest) if dest and shown != dest \
                    else shown
            yield '[[{}]]{}'.format(ilink, parened) if shown else parened

    pfmrsstr = '／'.join(_build_performerslink(pfmrs, follow))

    if follow:
        save_cache(_REDIRECTS, _RDRDFILE)

    # 「～ほかn名」
    if number == -1:
        pfmrsstr += '　ほか'
        pnum = -1
    elif number == -2:
        pfmrsstr += '　ほか数名'
        pnum = -1
    else:
        pnum = len(pfmrs)
        if number > pnum:
            pfmrsstr += '　ほか計{0}名'.format(number)
            pnum = number

    return pfmrsstr, pnum


_re_base_url = _re.compile(r'https?://(.*/)-/')


def resolve_service(url):
    """サービスの決定"""
    _verbose('Resolving service...')
    base = "https://" + _re_base_url.findall(url)[0]

    if not base or base not in _SVC_URL:
        _emsg('E', '未サポートのURLです。')
    else:
        return _SVC_URL[base]


_re_cid = _re.compile(r'/cid=([a-z0-9_]+)/?')
_re_id = _re.compile(r'/id=([\d,]+?)/')


def get_id(url, cid=False, ignore=False, param=''):
    """URLからIDを取得"""
    try:
        return _re_cid.findall(url) if cid \
            else _re_id.findall(url)[0].split(',')
    except IndexError:
        if ignore:
            return ()
        if param != '':
            return _get_id_from_query_string(url, param)
        else:
            _emsg('E', 'IDを取得できません: ', url)

def _get_id_from_query_string(url, param):
    """Query StringからIDを取得する"""
    try:
        query = _up.parse_qs(_up.urlparse(url).query)
        return query[param]
    except (ValueError, KeyError, IndexError):
        _emsg('E', 'IDを取得できません: ', url)

_sub_pid = (_re.compile(r'^(?:[hn]_)?\d*([a-z]+)(\d+).*', _re.I), r'\1-\2')

# 品番変換個別対応
_sub_pid_indv = (
    (_re.compile(r'^125ud(\d+).*'), r'ud\1r'),              # LEOのレンタル
    (_re.compile(r'^h_093r18(\d+)'), r'r18-\1'),            # チェリーズの一部レーベル
    (_re.compile(r'^h_066fad(\d+).*'), r'fad\1'),           # FAプロのレンタルの一部
    (_re.compile(r'^h_066rhtr(\d+).*'), r'rhtr\1'),         # FAプロのレンタルの一部
    (_re.compile(r'^55t28(\d+)'), r't28-\1'),               # TMAの一部
    (_re.compile(r'^5528id(\d+)'), r'28id-\1'),             # TMAの一部
    (_re.compile(r'^\d{2}id(\d{2})(\d+)'), r'\1id-\2'),     # TMAの一部
    (_re.compile(r'^117?((?:tk)?arm[a-z]?)0?(\d{3}).*'), r'\1-\2'),  # アロマ企画の一部
    (_re.compile(r'^d1(\d+)'), r'd1-\1'),                   # ドグマのD1 CLIMAXレーベル
    (_re.compile(r'^ad1(\d+)'), r'ad1-\1'),                 # ドグマのAD1 CLIMAXレーベル
    (_re.compile(r'^h_308aoz(\d+z?)'), r'aoz-\1'),          # 青空ソフト
    (_re.compile(r'^(?:h_102)?bnsps(\d+).*'), r'nsps-\1'),  # ながえスタイルのセル版の一部
    (_re.compile(r'^21psd(\d+)'), r'psd+\1'),               # アウダースの一部
    (_re.compile(r'^\d*d1clymax00(\d+)'), r'd1clymax-\1'),  # D1グランプリ
    (_re.compile(r'^13dsvr0(\d+)'), r'3dsvr-\1'),           # SOD VRレーベル
    (_re.compile(r'^h_094ktra(\d+)e'), r'ktra-\1e'),        # ケー・トライブの一部
    (_re.compile(r'^n_709m([a-z])r([a-z]{2})(\d{3})'), r'm\1r-\2\3'),   # スパイスビジュアルの一部
    (_re.compile(r'^(?:[hn]_)?\d*([a-z]+)vr00(\d{3})'), r'\1vr-\2'),    # VR作品
)


def gen_pid(cid, pattern=None):
    """DMMの品番(cid)から正規の品番を生成"""
    if cid.startswith('https://'):
        cid = get_id(cid, True)[0]

    if pattern:
        pid, m = sub(pattern, cid, True)
    else:
        # 個別対応パターン
        for sp in _sub_pid_indv:
            pid, m = sub(sp, cid, True)
            if m:
                break
        else:
            pid, m = sub(_sub_pid, cid, True)

    if m:
        pid = pid.upper()

    return pid, cid


class _ExtractIDs:
    """位置引数からIDと検索対象の抽出"""
    def __call__(self, keywords: tuple, is_cid=False):
        self.retrieval = None

        for k in keywords:

            if _re.match('https?://', k):

                if not self.retrieval:
                    try:
                        self.retrieval = get_article(k)
                    except IndexError:
                        self.retrieval = 'keyword'
                    _verbose('retrieval(extracted): ', self.retrieval)

                yield from get_id(k, is_cid, ignore=True)
            else:
                yield k

extr_ids = _ExtractIDs()


class _InvalidPage(Exception):
    pass


class _GetActName:
    """名前の取得"""
    _re_actname1 = _re.compile(r'[)）][(（]')
    _re_actname2 = _re.compile(r'[（(、]')

    def __call__(self, elems):
        try:
            data = elems.find('.//h1').text.strip()
        except AttributeError:
            raise _InvalidPage

        # 複数の女優名チェク ('）（' で分割を試みる)
        named = self._re_actname1.split(data)

        if len(named) == 1:
            # 分割されなかったら名前は1つのみ
            named = re_inbracket.split(data)

        yomis = elems.find_class('c-tx-actressName__ruby')[0].text.strip()

        # 名前を分割
        name = self._re_actname2.split(named[0])
        # よみを分割
        yomi = self._re_actname2.split(yomis.rstrip('）)'))

        # 現在の名前の格納
        self.current = name[0]

        # # 名前と読みの数が一致しないのときの数合わせ
        # namelen = len(name)
        # yomilen = len(yomi)
        # if namelen > 1 and yomilen == 1:
        #     yomi = yomi * namelen
        # elif namelen == 1 and yomilen > 1:
        #     name = name * yomilen

        _verbose('name: {}, yomi: {}'.format(name, yomi))
        return name, yomi

get_actname = _GetActName()


def fmt_name(director: str):
    return ','.join(director.split('：')[-1].split('＋'))


def ret_apacheinfo(elems):
    """Apache公式から作品情報を取得"""

    pid = actress = director = ''

    for t in elems.find_class("detail-main-meta")[0].xpath('li/text()'):

        t = t.strip()

        if t.startswith('品番：'):
            pid = t.split('：')[-1].strip()
            _verbose('pid: ', pid)
        elif t.startswith('出演女優：'):
            actress = fmt_name(t)
            _verbose('actress: ', actress)
        elif t.startswith('監督：'):
            director = fmt_name(t)
            _verbose('director: ', director)

        if pid and director:
            break
    else:
        missings = []

        if not pid:
            missings.append('品番')

        if not director:
            missings.append('監督')

        _emsg('E', 'Apacheサイトから「{}」を取得できませんでした。'.format(
            'と'.join(missings)))

    return pid, actress, director


def ssw_searchnext(el):
    """Wiki検索ページの次ページがあれば取得"""
    pagin = el.xpath('.//div[@class="paging-top"]/a[text()="次の20件"]')
    if pagin:
        nextp = pagin[0].get('href')
        resp, he = open_url(_up.urljoin(BASEURL_SSW, nextp), cache=False)
        return he


def open_ssw(*pages):
    """wikiページをウェブブラウザで開く"""
    for p in filter(None, pages):
        url = _up.urljoin('http://sougouwiki.com/d/', quote(p))
        resp, he = open_url(url)
        if resp.status == 200:
            inner = he.find_class('inner')[0]
            editurl = inner.xpath('.//a')[0].get('href')
            if editurl:
                _webbrowser.open_new_tab(editurl)


_rep_diff = (('Courier', 'Sans'),
             ('nowrap="nowrap"', ''))


def show_diff(flines, tlines, fdesc, tdesc, context=True):
    """
    差分をとってブラウザで開く

    open_new_tab() のパラメータは実在するuriでなければならないので
    ファイルライクオブジェクトはNG
    """
    diff = _HtmlDiff().make_file(flines,
                                 tlines,
                                 fdesc,
                                 tdesc,
                                 context=context)
    for p, r in _rep_diff:
        diff = diff.replace(p, r)
    dummy, tmpf = _mkstemp(suffix='.html', dir=str(_CACHEDIR))
    with open(tmpf, 'w') as f:
        f.writelines(diff)
    _webbrowser.open_new_tab(tmpf)


def clear_cache():
    """キャッシュのクリア"""
    _rmtree(str(_CACHEDIR), ignore_errors=True)
    _emsg('I', 'キャッシュをクリアしました。')
    open_url.__init__()


def cache_info():
    """キャッシュ情報の出力"""
    size = sum(f.stat().st_size for f in _CACHEDIR.glob('*')) / 1048576
    _emsg('I', 'キャッシュパス: ', _CACHEDIR)
    _emsg('I', 'サイズ: {:.2f}MB'.format(size))
    raise SystemExit
