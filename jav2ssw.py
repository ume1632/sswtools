#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import re
import httplib2
import bs4
import urllib.request
import argparse
import libssw as _libssw
import dmm2ssw as _dmm2ssw
from collections import namedtuple as _namedtuple

re_inbracket = re.compile(r'[(（]')

_ReturnVal = _namedtuple('ReturnVal',
                         ('release', 'pid', 'title', 'title_dmm', 'url',
                          'time', 'maker', 'label', 'series',
                          'actress', 'link_label', 'link_series',
                          'wktxt_a', 'wktxt_t'))

# 対応サイトリスト
siteList = (('https://www.mgstage.com/', 'MGS'),
            ('https://www.heyzo.com/', 'HEYZO'),
            ('https://www.caribbeancom.com/', 'カリビアンコム'),
            ('https://www.caribbeancompr.com/', 'カリビアンコムプレミアム'),
            ('https://www.pacopacomama.com/', 'パコパコママ'),
            ('https://my.tokyo-hot.com/', 'Tokyo Hot'),
            ('https://www.tokyo-hot.com/', 'Tokyo Hot'),
            ('https://www.aventertainments.com/', 'AVE'),
            ('https://www.s-cute.com/', 'S-Cute'),
            ('https://mywife.cc/', '舞ワイフ'),
            ('https://real2.s-angels.com/', 'RSA'),
            ('https://www.g-area.org/', 'Perfect-G'),
            ('https://duga.jp/', 'DUGA'),
            ('https://dl.getchu.com/', 'Getchu'),
            ('https://www.h4610.com/', 'エッチな4610'),
            ('https://www.girls-blue.com/', 'Girls Blue'),
)


vThumbnail = {  'ラグジュTV',
                'ドキュメンTV',
                '投稿マーケット素人イッてQ',
                'プレステージプレミアム(PRESTIGE PREMIUM)',
                'ARA',
                '黒蜜',
                'MOON FORCE',
                'KANBi',
                '#きゅんです',
}



# コマンドライン引数の解釈
def _get_args(argv, p_args):
    argparser = argparse.ArgumentParser(
        description='URLから素人系総合wiki用ウィキテキストを作成する')

    argparser.add_argument('url',
                           help='作品ページのURL',
                           nargs='?',
                           metavar='URL')

    argparser.add_argument('-t', '--table',
                           help='一覧ページ用の表形式ウィキテキストを作成する, 2個以上指定すると両方作成する',
                           action='count',
                           default=getattr(p_args, 'table', 0))

    argparser.add_argument('-f', '--disable-follow-redirect',
                           help='ページのリダイレクト先をチェックしない',
                           dest='follow_rdr',
                           action='store_false',
                           default=getattr(p_args, 'follow_rdr', True))

    args = argparser.parse_args(argv)
    return args

# サイト判別
def getSite(reqURL):
    base = reqURL.replace('http:', 'https:')
    site = ''
    for i in siteList:
        if base.startswith(i[0]):
            site = i[1]

    return site

def _trim_name(name):
    """女優名の調整"""
    name = name.strip()
    name = re_inbracket.split(name)[0]
    return name

def _list_pfmrs(plist):
    return [(_trim_name(p.strip()), '', '') for p in plist]


#----------------------------
# MGS動画
#----------------------------
def mgsParser(soup, summ):
    if 'product' in summ['url']:
        mgsProductParser(soup, summ)
    else:
        mgsMonthlyParser(soup, summ)

#----------------------------
# MGS動画(通常)
#----------------------------
def mgsProductParser(soup, summ):
    common_detail_cover = soup.find('div', class_='common_detail_cover')
    detail_data = common_detail_cover.find('div', class_='detail_left').find('div', class_='detail_data')

    # サブタイトル取得
    h1 = common_detail_cover.find('h1', class_='tag')
    if h1.string:
        summ['subtitle'] = h1.string.strip()

    # イメージ取得
    img = detail_data.find('div').find('h2').find('img')
    img_src = img['src']

    # タイトル・リリース日取得
    table = soup.find_all('tr')

    for tr in table:
        if tr.find('th'):
            th = tr.find('th').string
            if th == '品番：':
                summ['title'] = tr.find('td').string
                summ['pid'] = summ['title']
            elif th == '配信開始日：':
                summ['release'] = tr.find('td').string
            elif th == '出演：':
                summ['actress'].append(tr.find('td').text.strip())
            elif th == 'メーカー：':
                summ['label'] = tr.find('td').find('a').string.strip()
            elif th == 'シリーズ：':
                if tr.find('td').find('a'):
                    summ['series'] = tr.find('td').find('a').string.strip()
            elif th == '収録時間：':
                summ['time'] = tr.find('td').string.replace('min', '分')

    # 出演情報を改行付きでタイトルに含める
    if summ['actress']:
        summ['subtitle'] += "~~{0}".format(summ['actress'][0])

    # イメージ設定
    if summ['label'] == 'ナンパTV' or summ['label'] == 'シロウトTV':
        summ['image_sm'] = img_src.replace('pb_p_', 'pb_t1_')
        summ['image_lg'] = img_src.replace('pb_p_', 'pb_e_')
    elif summ['label'] in vThumbnail:
        summ['image_sm'] = "&ref({0},147)".format(img_src)
        summ['image_lg'] = img_src.replace('pf_o1_', 'pb_e_')
    else:
        summ['image_sm'] = img_src
        summ['image_lg'] = img_src.replace('pf_o1_', 'pb_e_')

    # Wikiに合わせてレーベル名変更
    if summ['label'] == 'ナンパTV':
        no = int(summ['pid'].replace('200GANA-', ''))
        if no < 201:
            summ['label'] = 'ナンパＴＶ'
        else:
            summ['label'] = 'ナンパＴＶ ' + str((no // 200 ) + 1)
    elif summ['label'] == 'プレステージプレミアム(PRESTIGE PREMIUM)':
        titles = summ['title'].split('-')
        if titles[0] == '300MAAN':
            summ['label'] = 'MAAN-san'
        else:
            summ['label'] = titles[0] + 'その他'
        no = int(titles[1])
        if no > 200:
            summ['label'] = summ['label'] + ' ' + str((no // 200 ) + 1)

#----------------------------
# MGS動画(月額)
#----------------------------
def mgsMonthlyParser(soup, summ):
    common_detail_cover = soup.find('div', class_='common_detail_cover')
    detail_data = common_detail_cover.find('div', class_='detail_left').find('div', class_='detail_data')

    # サブタイトル取得
    h1 = common_detail_cover.find('h1', class_='tag').text.strip().splitlines()
    summ['subtitle'] = h1[0]

    # イメージ取得
    img = detail_data.find('div').find('h2').find('img')
    img_src = img['src']

    # リリース日取得
    date = h1[1].split('▶')
    summ['release'] = date[1]

    # 詳細情報取得
    detail = common_detail_cover.find('ul', class_='detail_txt').find_all('li')
    pid = detail[0].string.split('：')
    summ['pid'] = pid[2]
    summ['series'] = detail[1].find('a').string
    summ['actress'] = detail[2].find('a').string

    # 出演情報を改行付きでタイトルに含める
    if summ['actress']:
        summ['subtitle'] += "~~{0}".format(summ['actress'])

    # イメージ設定
    summ['image_sm'] = img_src.replace('pb_p_', 'pb_t1_')
    summ['image_lg'] = img_src.replace('pb_p_', 'pb_e_')

#----------------------------
# HEYZO
#----------------------------
def heyzoParser(soup, summ):
    # タイトル取得
    title = soup.find('h1').string
    summ['title'] = title.replace('\n' , ' ').replace('\t' , '').lstrip()

    # リリース日取得
    table_release_day = soup.find('tr', class_='table-release-day')
    release_day = table_release_day.find_all('td')
    summ['release'] = release_day[1].string.strip()

#----------------------------
# カリビアンコム
#----------------------------
def caribParser(soup, summ):
    # タイトル取得
    summ['title'] = soup.find('h1', itemprop='name').string.replace('〜','～').replace(']','&#93;')

    # 女優一覧取得
    detail_spec = soup.find('li', class_='movie-spec')
    if detail_spec:
        actress = detail_spec.find_all('span', itemprop='name')
    for act in actress:
        summ['actress'].append(act.string)

    # リリース日取得
    summ['release'] = soup.find('span', itemprop='datePublished').string

#----------------------------
# カリビアンコムプレミアム
#----------------------------
def caribprParser(soup, summ):
    # タイトル取得
    summ['title'] = soup.find('h1').string

    # リリース日取得
    spec_content = soup.find_all('span', class_='spec-content')
    summ['release'] = spec_content[1].string

#----------------------------
# パコパコママ
#----------------------------
def pacpacoParser(soup, summ):
    # タイトル取得
    summ['title'] = soup.find('title').string.rstrip()

    # リリース日取得
    sp_url = summ['url'].split('/')
    date_url = sp_url[4]
    summ['release'] = '20' + date_url[4:6] + '.' + date_url[:2] + '.' + date_url[2:4]

    detail = soup.find('div', class_='detail-info-l')
    if detail:
        table = detail.find('table')
        tdSet = table.find_all('td')
        for i in range(len(tdSet)):
            item = tdSet[i].string
            if item == '名前:':
                summ['actress'].append(tdSet[i+1].string)

#----------------------------
# TOKYO-HOT
#----------------------------
def tokyoParser(soup, summ):
    # タイトル取得
    pagetitle = soup.find('div', class_='pagetitle')
    if pagetitle:
        summ['title'] = pagetitle.find('h2').string.rstrip()

    # リリース日・品番取得
    info = soup.find('dl', class_='info')
    info_dt = info.find_all('dt')
    info_dd = info.find_all('dd')

    for idx in range(len(info_dt)):
        dt = info_dt[idx].string
        if dt == '配信開始日':
            summ['release'] = info_dd[idx].string
        elif dt == '作品番号':
            summ['pid'] = info_dd[idx].string

    # 女優名
    actress = info_dd[0].find_all('a')
    for act in actress:
        summ['actress'].append(act.text.strip())

    if summ['pid'].startswith('k'):
        summ['series'] = 'チーム木村'
    else:
        summ['series'] = 'Tokyo Hot'

#----------------------------
# AV-Entertainment
#----------------------------
def aveParser(soup, summ):
    # 作品情報取得
    single_info = soup.find_all('div', class_='single-info')

    # タイトル取得
    section_title = soup.find('div', class_='section-title')
    if section_title:
        summ['title'] = section_title.find('h3').string

    for info in single_info:
        info_title = info.find('span', class_='title').string
        if info_title == '商品番号':
            summ['pid'] = info.find('span', class_='tag-title').string
        elif info_title == 'スタジオ':
            summ['maker'] = info.find('span', class_='value').string
        elif info_title == '主演女優':
            actress = info.find('span', class_='value').text.split(' ')
            for act in actress:
                summ['actress'].append(act)
        elif info_title == '発売日':
            tmpRelease = info.find('span', class_='value').text.split(' ')
            release = tmpRelease[0].split('/')
            summ['release'] = "{0}.{1:02d}.{2:02d}".format(release[2], int(release[0]), int(release[1]))
        elif info_title == 'シリーズ':
            summ['series'] = info.find('span', class_='value').string

#----------------------------
# S-Cute
#----------------------------
def scuteParser(soup, summ):
    # タイトル取得
    title = soup.find('h3', class_='h1').string
    summ['title'] = title
    summ['pid'] = title.replace('#', '')

    # サブタイトル取得
    horizontal = soup.find('dl', class_='dl-horizontal').find_all('dd')
    summ['subtitle'] = "{0}({1})".format(title, horizontal[0].string[0:2])

    # サイズ取得
    summ['size'] = "{0} {1}".format(horizontal[1].string, horizontal[2].string)

    # レーベル設定
    label_id = re.search(r'[0-9]+', title)
    if label_id:
        summ['label'] = 'S-Cute Girls ' + str(int(label_id.group()) // 100 + 1)

    # リリース日取得
    contents = soup.find_all('article', class_='contents')
    if contents:
        summ['release'] = contents[-1].find('div', class_='meta').span.string

    # 画像URL取得
    image_lg = soup.find('img', src=re.compile('^http://static.s-cute.com/images'))
    summ['image_sm'] = image_lg['src'].replace('_400', '_150')
    summ['image_lg'] = image_lg['src']

#----------------------------
# 舞ワイフ
#----------------------------
def mywifeParser(soup, summ):
    # タイトル取得
    title = soup.find('title').string
    id = re.sub("\\D", "", title)
    summ['pid'] = id

    # サブタイトル取得
    title = title.split('|')
    summ['subtitle'] = title[0].replace(' ', '', 1).replace('　', ' ')

    # レーベル設定
    summ['label'] = '舞ワイフ(' + str((int(id) // 200 ) * 200 + 1) + '～)'

    # リリース日取得
    summ['release'] = ''

    # プロフィール
    modelsamplephototop = soup.find('div', class_='modelsamplephototop')
    prof = modelsamplephototop.text.strip().splitlines()
    for prof_text in prof:
        if prof_text.strip().startswith('T'):
            summ['size'] = prof_text.strip()
        elif prof_text.startswith('【プロフィール】'):
            age = re.search(r'[0-9][0-9]歳', prof_text)
            summ['subtitle'] = summ['subtitle'] + ' ' + age.group()

    # 画像URL取得
    model_id = summ['url'].split('/')
    model_id = model_id[6]
    summ['image_sm'] = 'http://p02.mywife.cc/girl/0' + model_id + '/thumb.jpg'
    summ['image_lg'] = ''

#----------------------------
# REAL STREET ANGELS
#----------------------------
def rsaParser(soup, summ):
    # ID取得
    sp_url = summ['url'].split('=')
    model_id = sp_url[1]
    id = model_id.split('_')
    summ['pid'] = id[0]
    
    # サブタイトル取得
    model_profile = soup.find('div', id='model_profile')
    if model_profile is None:
        return

#    name = model_profile.find('li', class_='name')
    name = '(仮名)'
    profile = model_profile.find_all('li', class_='size')
    age = profile[0].contents[1]
    summ['subtitle'] = '{0} {1}歳'.format(name, age)

    # サイズ取得
    summ['size'] = profile[1].contents[1]

    # 画像URL取得
    summ['image_sm'] = 'http://real2.s-angels.com/images/sample/' + model_id + '/thumb/' + model_id + '.jpg'
    summ['image_lg'] = 'http://real2.s-angels.com/images/sample/' + model_id + '/thumb/model_top.jpg'

#----------------------------
# Perfect-G
#----------------------------
def gareaParser(soup, summ):
    prof_dat = soup.find('div', class_='prof_dat')
    model_id = prof_dat.find('div', class_='p_name').find(text=True).strip()
    summ['cid'] = model_id

    # ID取得
    id = re.sub("\\D", "", model_id)
    summ['pid'] = id

    # 出演者名
    model = prof_dat.find('div', class_='p_name').find('span').string
    model = model.replace('-', '')

    # 年齢を取得
    p_age = prof_dat.find('div', class_='p_age').findAll(text=True)
    age = p_age[1].strip()

    # 職業を取得
    p_job = prof_dat.find('div', class_='p_job').findAll(text=True)
    job = p_job[1].strip()

    # サイズ取得
    size = prof_dat.find('div', class_='p_prf').findAll(text=True)
    if size:
        summ['size'] = size[1].strip()

    # タイトル取得
    summ['title'] = 'No.{0} {1} {2}歳 {3}'.format(id, model, age, summ['size'])

    # サブタイトル取得
    summ['subtitle'] = '{0} {1}歳~~{2}~~{3}'.format(model, age, summ['size'], job)

    # レーベル設定
    summ['label'] = 'Perfect-G (' + str((int(id) // 200 ) * 200 + 1) + '～)'

    # 配信開始日取得
    pu_4_w = soup.findAll('div', class_='pu_4_w')
    if pu_4_w:
        summ['release'] = pu_4_w[0].find('div', class_='pu_2_day').string

    # 画像URL取得
    summ['image_sm'] = 'https://www.g-area.com/main_thumbnail/'+ model_id + '.jpg'
    summ['image_lg'] = 'https://www.g-area.com/img/main/' + model_id + '_320_180.jpg'

#----------------------------
# DUGA
#----------------------------
def dugaParser(soup, summ):
    # タイトル取得
    summ['title'] = soup.find('h1', class_='title').string

    # サマリ取得
    summary = soup.find('div', class_='summaryinner')
    table = summary.find('table').findAll('tr')

    for tr in table:
        if tr.find('th'):
            th = tr.find('th').string
            if th == '配信開始日' and summ['release'] == '':
                summ['release'] = tr.find('td').string.replace('年', '-').replace('月', '-').replace('日', '')
            if th == '発売日':
                summ['release'] = tr.find('td').string.replace('年', '-').replace('月', '-').replace('日', '')
            elif th == '監督':
                summ['director'] = tr.find('td').string
            elif th == 'メーカー':
                summ['maker'] = tr.find('td').string
            elif th == '出演者':
                actList = tr.find('td').findAll('a')
                for act in actList:
                    summ['number'] += 1
                    summ['actress'].append(act.string)

    # 品番取得
    pid = soup.find('span', itemprop='mpn')
    if pid:
        summ['pid'] = pid.string
    else:
        pid = soup.find('span', itemprop='sku')
        if pid:
            summ['pid'] = pid.string.upper()

    # メーカー調整
    if summ['pid'].startswith('GRAV'):
        summ['maker'] = 'グリップAV'
    elif summ['pid'].startswith('RFW'):
        summ['maker'] = 'RUBBER LOVER'

    # 画像URL取得
    img = soup.find('img', id='productjpg')
    summ['image_sm'] = img['src']
    summ['image_lg'] = img['src'].replace('_240', '')

#----------------------------
# DL.Getchu
#----------------------------
def getchuParser(soup, summ):
    # タイトル取得
    title = soup.find('meta', property="og:title")
    summ['subtitle'] = title['content']

    # サムネイル取得
    img = soup.find('meta', property="og:image")
    summ['image_sm'] = '&ref(' + img['content'] + ',,200)'
    summ['image_lg'] = img['content']

    # 商品詳細取得
    table1 = soup.find_all('table', bgcolor='#999999')
    table2 = table1[1].table
    
    if table2:
        trSet = soup.find_all('tr')
        for tr in trSet:
            table3 = tr.find('table', width='560')
            if table3:
                tdSet = table3.find_all('td')
                for i in range(len(tdSet)):
                    item = tdSet[i].string
                    if item == '作品詳細':
                        detail = tdSet[i+1].b.string.split('／')
                        if detail:
                            summ['pid'] = detail[0].replace('作品ID：', '')
                    if item == 'サークル':
                        summ['label'] = tdSet[i+1].string
                    if item == '配信開始日':
                        summ['release'] = tdSet[i+1].string

#----------------------------
# Hな4610
#----------------------------
def h4610Parser(soup, summ):
    # タイトル
    moviePlay_title = soup.find('div', class_="moviePlay_title")
    summ['title'] = moviePlay_title.find('h1').string

    # No
    sp_url = summ['url'].split('/')
    summ['pid'] = sp_url[4]

    # 公開日
    movieInfo = soup.find('div', id="movieInfo")
    section = movieInfo.find_all('section')
    if section:
        dtSet = section[1].find_all('dt')
        ddSet = section[1].find_all('dd')
        for i in range(len(dtSet)):
            item = dtSet[i].string
            if item == '公開日':
                summ['release'] = ddSet[i].string.strip()

#----------------------------
# Girl's Blue
#----------------------------
def girlsblueParser(soup, summ):
    # No
    sp_url = summ['url'].split('=')
    summ['pid'] = sp_url[-1]

    # サムネイル取得
    summ['image_lg'] = 'https://www.girls-blue.com/free_photo/' + summ['pid'] + '/img1.jpg'

    # 仮名取得
    profile = soup.find('div', id="gallery_girl_profile").p.get_text(',').split(',')
    print(profile)
    summ['subtitle'] = profile[0].replace(' 名　前：', '').replace('　', '')

    # サイズ取得
    tall = profile[1].split('：')
    size3 = profile[2].split('：')
    summ['size'] = 'T' + tall[1] + ' B' + size3[1].replace('-', ' W', 1).replace('-', ' H', 1)

    # レーベル設定
    no = re.sub("\\D", "", summ['pid'])
    summ['label'] = 'Girl\'s Blue(' + str((int(no) // 200 ) * 200 + 1) + '～)'

##############################
# Parser
##############################
javParser = {
    'MGS':                      mgsParser,
    'HEYZO':                    heyzoParser,
    'カリビアンコム':           caribParser,
    'カリビアンコムプレミアム': caribprParser,
    'パコパコママ':             pacpacoParser,
    'Tokyo Hot':                tokyoParser,
    'AVE':                      aveParser,
    'S-Cute':                   scuteParser,
    '舞ワイフ':                 mywifeParser,
    'RSA':                      rsaParser,
    'Perfect-G':                gareaParser,
    'DUGA':                     dugaParser,
    'Getchu':                   getchuParser,
    'エッチな4610':             h4610Parser,
    'Girls Blue':               girlsblueParser,
}

#----------------------------
# MGS動画
#----------------------------
def mgsFormat_t(summ):
    wtext = ''
    wtext += '|[[{0}>{1}]]|[[{2}>{3}]]|'.format(summ['title'], summ['url'], summ['image_sm'], summ['image_lg'])

    # 各シリーズ一覧ページの仕様に合わせこむ
    if summ['label'] == 'シロウトTV' or summ['label'] == 'ラグジュTV':
        wtext += '|{0}|[[ ]]|{1}|{2}||\n'.format(summ['subtitle'], summ['time'], summ['release'].replace('/', '-'))
    elif summ['series'] == 'マジ軟派、初撮。':
        subtext = re.sub(r'マジ軟派、初撮。 ([0-9]*) ', r'vol.\1~~', summ['subtitle'])
        wtext += '{0}|[[ ]]|{1}||\n'.format(subtext, summ['release'].replace('/', '-').replace('.', '-'))
    else:
        wtext += '{0}|[[ ]]|{1}||\n'.format(summ['subtitle'], summ['release'].replace('/', '-').replace('.', '-'))

    return wtext

#----------------------------
# HEYZO
#----------------------------
def heyzoFormat_t(summ):
    return '非対応'

#----------------------------
# カリビアンコム
#----------------------------
def caribFormat_t(summ):
    return '非対応'

#----------------------------
# カリビアンコムプレミアム
#----------------------------
def caribprFormat_t(summ):
    return '非対応'

#----------------------------
# パコパコママ
#----------------------------
def pacpacoFormat_t(summ):
    return '未対応'

#----------------------------
# TOKYO-HOT
#----------------------------
def tokyoFormat_t(summ):
    date = summ['release'].replace('/', '-')

    wtext = ''
    wtext += '|[[{0}>{1}]]|{2}|'.format(summ['pid'], summ['url'], summ['title'])
    
    for act in summ['actress']:
        if act == summ['actress'][-1]:
            wtext += '[[{0}]]'.format(act)
        else:
            wtext += '[[{0}]]／'.format(act)

    wtext += '|{0}||'.format(date)

    return wtext

#----------------------------
# AV-Entertainment
#----------------------------
def aveFormat_t(summ):
    wtext = ''
    wtext += '|[[{0}>{1}]]|{2}|'.format(summ['pid'], summ['url'], summ['title'])

    # 出演者一覧
    for act in summ['actress']:
        if act == summ['actress'][-1]:
            wtext += '[[{0}]]'.format(act)
        else:
            wtext += '[[{0}]]／'.format(act)

	# リリース日
    wtext += '|{0}||'.format(summ['release'].replace('.', '-'))

    return wtext

#----------------------------
# S-Cute
#----------------------------
def scuteFormat_t(summ):
    wtext = ''
    wtext += '|[[{0}>{1}]]|[[{2}>{3}]]|'.format(summ['pid'], summ['url'], summ['image_sm'], summ['image_lg'])
    wtext += '{0}~~{1}|[[ ]]|{2}||\n'.format(summ['subtitle'], summ['size'].replace(' ', '~~'), summ['release'].replace('/', '-'))

    return wtext

#----------------------------
# 舞ワイフ
#----------------------------
def mywifeFormat_t(summ):
    wtext = ''
    tmp = summ['subtitle'].split(' ', 1)
    alias = tmp[-1]

    if '蒼い再会' in alias:
        summ['note'].append('※蒼い再会~~No.以来')
        alias = alias.replace(' 蒼い再会', '')

    wtext += '|[[{0}>{1}]]|{2}~~{3}|'.format(summ['pid'], summ['url'], alias, summ['size'])
    wtext += '[[ ]]|&ref({0},305,180)|{1}'.format(summ['image_sm'], summ['release'].replace('/', '-'))
    wtext += '|{}|\n'.format('、'.join(summ['note']))
    
    return wtext

#----------------------------
# REAL STREET ANGELS
#----------------------------
def rsaFormat_t(summ):
    if summ['subtitle'] == '':
        return '取得失敗'

    wtext = '|[[{0}>{1}]]|{2}~~{3}|[[ ]]|[[{3}>{4}]]||'.format(summ['pid'], summ['url'], summ['subtitle'], summ['size'], summ['image_sm'], summ['image_lg'])

    return wtext

#----------------------------
# Perfect-G
#----------------------------
def gareaFormat_t(summ):
    wtext = ''
    image_sm_t = 'http://www.g-area.com/pg_info_thumb/pg_info_' + summ['cid'] + '150_100.jpg'
    
    wtext += '|[[{0}>{1}]]|[[{2}>{3}]]|{4}|[[ ]]|{5}||'.format(summ['pid'], summ['url'], image_sm_t, summ['image_lg'], summ['subtitle'], summ['release'].replace('.', '-'))

    return wtext

#----------------------------
# DL.Getchu
#----------------------------
def getchuFormat_t(summ):
    wtext = ''
    image_sm_t = summ['image_lg'].replace('top', 'small')
    wtext += '|[[{0}>{1}]]|[[{2}>{3}]]|{4}|[[ ]]|{5}||'.format(summ['pid'], summ['url'], image_sm_t, summ['image_lg'], summ['subtitle'], summ['release'].replace('/', '-'))

    return wtext

#----------------------------
# DUGA
#----------------------------
def dugaFormat_t(summ):
    wtext = ''
    wtext += '|[[{0}>{1}]]|[[&ref({2},147)>{3}]]|{4}|'.format(summ['pid'], summ['url'], summ['image_sm'], summ['image_lg'], summ['title'])
    for act in summ['actress']:
        if act == summ['actress'][-1]:
            wtext += '[[{0}]]'.format(act)
        else:
            wtext += '[[{0}]]／'.format(act)

    wtext += '|{0}||'.format(summ['release'])

    return wtext

#----------------------------
# Hな4610
#----------------------------
def h4610Format_t(summ):
    no = re.search(r'[0-9]+', summ['pid'])
    wtext = '|[[{0}>{1}]]|{2}|[[]]|{3}||'.format(no.group(), summ['url'], summ['title'], summ['release'])
    return wtext

#----------------------------
# Girls Blue
#----------------------------
def girlsblueFormat_t(summ):
    no = re.sub("\\D", "", summ['pid'])

    wtext = '|[[{0}>{1}]]|#ref({2},80)|{3}~~{4}|[[ ]]|||'.format(no, summ['url'], summ['image_lg'], summ['subtitle'], summ['size'])

    return wtext

##############################
# Format Table
##############################
Format_t = {
    'MGS':                      mgsFormat_t,
    'HEYZO':                    heyzoFormat_t,
    'カリビアンコム':           caribFormat_t,
    'カリビアンコムプレミアム': caribprFormat_t,
    'パコパコママ':             pacpacoFormat_t,
    'Tokyo Hot':                tokyoFormat_t,
    'AVE':                      aveFormat_t,
    'S-Cute':                   scuteFormat_t,
    '舞ワイフ':                 mywifeFormat_t,
    'RSA':                      rsaFormat_t,
    'Perfect-G':                gareaFormat_t,
    'DUGA':                     dugaFormat_t,
    'Getchu':                   getchuFormat_t,
    'エッチな4610':             h4610Format_t,
    'Girls Blue':               girlsblueFormat_t,
}

#----------------------------
# MGS動画
#----------------------------
def mgsFormat_a(summ):
    wtext = ''

    # 配信日
    if summ['release']:
        date = '//' + summ['release'].replace('/', '.')
    else:
        date = '//'

    wtext += date

    # 品番
    if summ['pid']:
        wtext += ' '
        wtext += summ['pid']

    # サイト名
    wtext += '\n[[MGS '

    # 作品番号
    if summ['cid']:
        wtext += summ['cid']

    # タイトル
    wtext += summ['subtitle'].replace('~~', '　')

    # レーベル（※慣例的に一部レーベルのみつけている）
    if summ['label'] == '投稿マーケット素人イッてQ' or summ['label'] == 'MOON FORCE':
        wtext += "（{0}）".format(summ['label'])

    # URL
    wtext += '>'
    wtext += summ['url']
    wtext += "]]"

    # レーベルリンク
    if summ['label'] != '':
        if summ['pid'] != '':
            actuall = _libssw.check_actuallpage(summ['url'], summ['label'], 'レーベル', summ['pid'])
            if actuall:
                wtext += "　[[(レーベル一覧)>{0}]]".format(actuall)
        else:
            wtext += "　[[(レーベル一覧)>{0}]]".format(summ['label'])

    # シリーズリンク
    if summ['series'] != '' and summ['label'] != summ['series']:
        actuall = _libssw.check_actuallpage(summ['url'], summ['series'], 'シリーズ', summ['pid'])
        if actuall:
            wtext += "　[[(シリーズ一覧)>{0}]]".format(actuall)

    # 改行
    wtext += "\n"

    # 画像URL
    if summ['image_lg'] == '':
        wtext += "&ref({0},,147)".format(summ['image_sm'])
    else:
        wtext += "[[{0}>{1}]]".format(summ['image_sm'], summ['image_lg'])

    return wtext

#----------------------------
# HEYZO
#----------------------------
def heyzoFormat_a(summ):
    wtext = "//{0}\n-[[HEYZO {1}>{2}]]".format(summ['release'].replace('-', '.'), summ['title'], summ['url'])
    return wtext

#----------------------------
# カリビアンコム
#----------------------------
def caribFormat_a(summ):
    wtext = ''

    isSingle = (len(summ['actress']) == 1)

    # 配信日・品番
    wtext += "//{}\n".format(summ['release'].replace('/', '.'))

    # タイトル
    if isSingle and (not summ['actress'][0] in summ['title']):
        # 女優名を足す
        summ['title'] += ' ' +  summ['actress'][0]

    wtext += "-[[カリビアンコム {0}>{1}]]".format(summ['title'], summ['url'])

    if not isSingle:
        wtext += '~~出演者：'
        for act in summ['actress']:
            if act == summ['actress'][-1]:
                wtext += "[[{0}]]".format(act)
            else:
                wtext += "[[{0}]]／".format(act)

    return wtext

def caribprFormat_a(summ):
    # 未作成
    return ''

#----------------------------
# パコパコママ
#----------------------------
def pacpacoFormat_a(summ):
    wtext = "//{0}\n-[[パコパコママ {1} {2}>{3}]]".format(summ['release'].replace('-', '.'), summ['title'], summ['actress'][0], summ['url'])
    return wtext

#----------------------------
# Tokyo Hot
#----------------------------
def tokyoFormat_a(summ):
    wtext = ''

    # 配信日・品番
    wtext += "//{0} {1}".format(summ['release'].replace('/', '.'), summ['pid'])

    # タイトル
    wtext += "\n-[[Tokyo Hot 『{0}』>{1}]]".format(summ['title'], summ['url'])

    # シリーズリンク
    if summ['series'] != '':
        actuall = _libssw.check_actuallpage(summ['url'], summ['series'], 'シリーズ', summ['pid'])
        if actuall:
            wtext += "　[[(シリーズ一覧)>{0}]]".format(actuall)

    return wtext

#----------------------------
# AV-Entertainment
#----------------------------
def aveFormat_a(summ):
    wtext = ''

    # 配信日
    if summ['release']:
        date = '//' + summ['release'].replace('-', '.').replace('/', '.') + ' '
    else:
        date = '//'
    wtext += date

    # 品番
    if summ['pid']:
        wtext += summ['pid']

    # タイトル
    wtext += '\n-[['
    wtext += summ['title']

    # スタジオ
    wtext += '（'
    wtext += summ['maker']
    wtext += '）'

    # URL
    wtext += '>'
    wtext += summ['url']
    wtext += ']]'

    # シリーズ一覧
    if summ['series'] == 'キャットウォーク ポイズン':
        wtext += '　[[(シリーズ一覧)>CATWALK POISON]]'
    elif summ['series'] == 'スカイエンジェル':
        wtext += '　[[(シリーズ一覧)>SKY ANGEL]]'
    elif summ['series'] == 'ゴールド エンジェル':
        wtext += '　[[(シリーズ一覧)>Gold Angel]]'

    # 出演者一覧
    if len(summ['actress']) > 1:
        wtext += '~~出演者：'
        for act in summ['actress']:
            if act == summ['actress'][-1]:
                wtext += "[[{0}]]".format(act)
            else:
                wtext += "[[{0}]]／".format(act)

    wtext += '\n'

    return wtext

#----------------------------
# S-Cute
#----------------------------
def scuteFormat_a(summ):
    wtext = ''

    # 配信日
    date = '//' + summ['release'].replace('-', '.').replace('/', '.')
    wtext += date

    # サイト名
    wtext += '\n[[S-Cute '

    # タイトルとURL
    wtext += "{0} {1}>{2}]]".format(summ['subtitle'], summ['size'], summ['url'])

    # レーベルリンク
    if summ['label'] != '':
        wtext += "　[[(レーベル一覧)>{0}]]".format(summ['label'])

    # 改行
    wtext += "\n"

    # 画像URL
    wtext += "[[{0}>{1}]]".format(summ['image_sm'], summ['image_lg'])

    return wtext

#----------------------------
# 舞ワイフ
#----------------------------
def mywifeFormat_a(summ):
    wtext = ''

    # 配信日
    wtext += '//\n'

    # サイト名
    wtext += '[[舞ワイフ '

    # タイトルとURL
    wtext += "{0} {1}>{2}]]".format(summ['subtitle'], summ['size'], summ['url'])

    # レーベルリンク
    if summ['label'] != '':
        wtext += "　[[(レーベル一覧)>{0}]]".format(summ['label'])

    # 改行
    wtext += "\n"

    # 画像URL
    wtext += "&ref({0},,147)".format(summ['image_sm'])

    return wtext

#----------------------------
# REAL STREET ANGELS
#----------------------------
def rsaFormat_a(summ):
    if summ['subtitle'] == '':
        return '取得失敗'

    wtext = '//\n[[Real Street Angels {0} {1} {2}>{3}]]\n[[{4}>{5}]]'.format(summ['pid'], summ['subtitle'], summ['size'], summ['url'], summ['image_sm'], summ['image_lg'])

    return wtext

#----------------------------
# Perfect-G
#----------------------------
def gareaFormat_a(summ):
    wtext = ''

    # 配信日
    date = '//' + summ['release']
    wtext += date

    # タイトルとURL
    wtext += "\n[[Perfect-G {0}>{1}]]".format(summ['title'], summ['url'])

    # レーベルリンク
    if summ['label'] != '':
        wtext += "　[[(レーベル一覧)>{0}]]".format(summ['label'])

    # 画像URL
    wtext += "\n[[{0}>{1}]]".format(summ['image_sm'], summ['image_lg'])

    return wtext

#----------------------------
# DL.Getchu
#----------------------------
def getchuFormat_a(summ):
    wtext = ''

    # 配信日
    wtext += "//{0}".format(summ['release'].replace('/', '.'))

    # タイトル
    wtext += "\n[[{0}（{1}）>{2}]]".format(summ['subtitle'], summ['label'], summ['url'])

    # レーベル（サークル）リンク
    if summ['label'] != '':
        wtext += "　[[(レーベル一覧)>{0}]]".format(summ['label'])

    return wtext

#----------------------------
# DUGA
#----------------------------
def dugaFormat_a(summ):
    wtext = ''

    # 配信日
    if summ['release']:
        date = '//' + summ['release'].replace('-', '.').replace('/', '.') + ' '
    else:
        date = '//'
    wtext += date

    # 品番
    if summ['pid']:
        wtext += summ['pid']

    # タイトル
    wtext += '\n[['
    wtext += summ['title']

    # スタジオ
    wtext += '（'
    wtext += summ['maker']
    wtext += '）'

    # URL
    wtext += '>'
    wtext += summ['url']
    wtext += ']]\n'

    # DVDジャケット
    wtext += "[[&ref({0},147)>{1}]]".format(summ['image_sm'], summ['image_lg'])

    # 出演者一覧
    if len(summ['actress']) > 1:
        wtext += '\n出演者：'
        for shown in summ['actress']:
            dest = _libssw.follow_redirect(shown)
            ilink = '{}>{}'.format(shown, dest) if dest and shown != dest \
                    else shown
            if shown == summ['actress'][-1]:
                wtext += "[[{0}]]".format(ilink)
            else:
                wtext += "[[{0}]]／".format(ilink)

    wtext += '\n'

    return wtext

#----------------------------
# Hな4610
#----------------------------
def h4610Format_a(summ):
    if 'ori' in summ['pid']:
        no = re.search(r'[0-9]+', summ['pid'])
        if int(no.group()) > 1001:
            summ['label'] = 'エッチな4610（1001～）'
        else:
            summ['label'] = 'エッチな4610'

    elif 'gol' in summ['pid']:
        summ['label'] = 'エッチな4610（ゴールド）'
    elif 'pla' in summ['pid']:
        summ['label'] = 'エッチな4610（プラチナ）'

    wtext = '//{0}\n-[[エッチな4610 {1} {2}>{3}]]'.format(summ['release'].replace('-', '.'), summ['pid'], summ['title'], summ['url'])

    if summ['label'] != '':
        wtext += "　[[(レーベル一覧)>{0}]]".format(summ['label'])

    return wtext

#----------------------------
# Girls Blue
#----------------------------
def girlsblueFormat_a(summ):
    wtext = ''

    # 配信日
    date = '//' + summ['release']
    wtext += date

    # タイトルとURL
    wtext += "\n[[Girl's Blue {0} {1} {2}>{3}]]".format(summ['pid'], summ['subtitle'], summ['size'], summ['url'])

    # レーベルリンク
    if summ['label'] != '':
        wtext += "　[[(レーベル一覧)>{0}]]".format(summ['label'])

    # 画像URL
    wtext += "\n&ref({0},147)".format(summ['image_lg'])

    return wtext

##############################
# Format Actress
##############################
Format_a = {
    'MGS':                      mgsFormat_a,
    'HEYZO':                    heyzoFormat_a,
    'カリビアンコム':           caribFormat_a,
    'カリビアンコムプレミアム': caribprFormat_a,
    'パコパコママ':             pacpacoFormat_a,
    'Tokyo Hot':                tokyoFormat_a,
    'AVE':                      aveFormat_a,
    'S-Cute':                   scuteFormat_a,
    '舞ワイフ':                 mywifeFormat_a,
    'RSA':                      rsaFormat_a,
    'Perfect-G':                gareaFormat_a,
    'DUGA':                     dugaFormat_a,
    'Getchu':                   getchuFormat_a,
    'エッチな4610':             h4610Format_a,
    'Girls Blue':               girlsblueFormat_a,
}

def main(props=_libssw.Summary(), p_args = argparse.Namespace):
    argv = [props.url] if __name__ != '__main__' else sys.argv[1:]
    args = _get_args(argv, p_args)
    reqUrl = args.url

    # 作品情報
    summ = _libssw.Summary()
    summ['url'] = reqUrl
    output = ['']
    site = getSite(reqUrl)

    if not site:
        return False, _ReturnVal(summ['release'],
                                 summ['pid'],
                                 summ['title'],
                                 summ['title_dmm'],
                                 summ['url'],
                                 summ['time'],
                                 summ('maker', 'maker_id'),
                                 summ('label', 'label_id'),
                                 summ('series', 'series_id'),
                                 summ['actress'],
                                 summ['link_label'],
                                 summ['link_series'],
                                 wktxt_a='',
                                 wktxt_t='')

    if site == 'MGS':
        data = {
            "Cookie": 'adc=1',
        }
        req = urllib.request.Request(reqUrl, None, data)
        with urllib.request.urlopen(req) as res:
            s = res.read()
        s = bs4.BeautifulSoup(s, "html.parser")
    else:
        h = httplib2.Http('.cashe')
        if site == 'Tokyo Hot':
            response, content = h.request(reqUrl + '?lang=jp')
        else:
            response, content = h.request(reqUrl)

        if site == 'カリビアンコム' or site == 'カリビアンコムプレミアム' or site == 'パコパコママ' or site == 'Getchu' or site == 'エッチな4610':
            html = content.decode('euc-jp', 'ignore')
        elif site == 'Perfect-G':
            html = content.decode('Shift_JIS')
        else:
            html = content.decode('utf-8', 'ignore')

        s = bs4.BeautifulSoup(html, 'html.parser')

    # HTML解析実行
    javParser[site](s, summ)

    # Wikiテキスト作成
    wktxt_t = Format_t[site](summ) if args.table else ''
    wktxt_a = Format_a[site](summ) if args.table != 1 else ()

    if __name__ != '__main__':
        # モジュール呼び出しならタプルで返す。
        return True, _ReturnVal(summ['release'],
                                summ['pid'],
                                summ['title'],
                                summ['title_dmm'],
                                summ['url'],
                                summ['time'],
                                summ('maker', 'maker_id'),
                                summ('label', 'label_id'),
                                summ('series', 'series_id'),
                                _list_pfmrs(summ['actress']),
                                summ['link_label'],
                                summ['link_series'],
                                wktxt_a,
                                wktxt_t)
    else:
        # 書き出す
        output = ['']
        if wktxt_a:
            output.append(wktxt_a)

        if wktxt_t:
            output.append(wktxt_t)

        print(*output, sep='\n')

if __name__ == "__main__":
    main()
