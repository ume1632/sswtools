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
            ('https://www.prestige-av.com', 'Prestige'),
            ('https://adult.contents.fc2.com/', 'FC2'),
            ('https://www.heyzo.com/', 'HEYZO'),
            ('https://www.dmm.com/', 'DMM'),
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
            ('https://pcolle.jp/', 'Pcolle'),
            ('https://www.pcolle.com/', 'Pcolle'),
            ('https://gold2.h-paradise.net/', '人妻パラダイス'),
            ('https://faleno.jp/', 'FALENO'),
            ('https://www.akibacom.jp/', 'AKIBACOM'),
            ('https://www.h-fish.com/', 'HAPPY FISH'),
)

# EUC-JPでデコードするサイト
charsetEucJp = ( 'カリビアンコム',
                 'カリビアンコムプレミアム',
                 'パコパコママ',
                 'Getchu',
                 'エッチな4610',
                 'RSA',
                 '人妻パラダイス'
)

# MGS独占メーカー
OnlyMGS = ( 'ナンパTV',
            'シロウトTV',
            'プレステージプレミアム(PRESTIGE PREMIUM)',
            'ラグジュTV',
            'NTR.net',
            'なまなま.net',
            'Jackson',
            'SUKEKIYO',
            'ARA',
            'DIEGO',
            'GOOD-BYE-CHERRYBOY',
            'HHH',
            '変態サムライ',
            'ドキカクch',
            'セイキョウイク',
)

# プレステージレーベル
PrestigeLabel = ( 'DOC',
                  'KANBi',
                  'SUKESUKE',
                  'ゲッツ!!',
                  '最強属性',
                  'ONE MORE',
                  'マジック',
                  'フルセイル',
                  '藪スタイル',
                  'TOY GIRL',
)

MGS_SERIES = {'働くドMさん.':       '働くドMさん',
              'レンタル彼女':       'レンタル彼女',
              '朝まではしご酒':     '朝まではしご酒',
              '私立パコパコ女子大学 女子大生とトラックテントで即ハメ旅':    '私立パコパコ女子大学 女子大生とトラックテントで即ハメ旅',
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

    # タイトル取得
    h1 = common_detail_cover.find('h1', class_='tag')
    if h1.string:
        summ['title'] = h1.string.strip()

    # イメージ取得
    img = detail_data.find('div').find('h2').find('img')
    img_src = img['src']

    # タイトル・リリース日取得
    table = soup.find_all('tr')

    isDvd = False
    tmpActress = ''

    for tr in table:
        if tr.find('th'):
            th = tr.find('th').string
            if th == '品番：':
                summ['pid'] = tr.find('td').string
            elif th == '配信開始日：':
                summ['release'] = tr.find('td').string
            elif th == '商品発売日：':
                tmpRelease = tr.find('td').string
                if (tmpRelease != 'DVD未発売'):
                    isDvd = True
            elif th == '出演：':
                tmpActress = tr.find('td').find_all('a')
                summ['subtitle'] = tr.find('td').text.strip()
            elif th == 'メーカー：':
                if tr.find('td').find('a'):
                    summ['maker'] = tr.find('td').find('a').string.strip()
            elif th == 'レーベル：':
                if tr.find('td').find('a'):
                    summ['label'] = tr.find('td').find('a').string.strip()
            elif th == 'シリーズ：':
                if tr.find('td').find('a'):
                    summ['series'] = tr.find('td').find('a').string.strip()
            elif th == '収録時間：':
                summ['time'] = tr.find('td').string.replace('min', '分')

    if isDvd:
        summ['media'] = 'DVD動画'
        summ['release'] = tmpRelease
        # 特典情報は削除する
        summ['title'] = re.sub('【MGSだけの.*分】', '', summ['title'])
        summ['title'] = re.sub('【フルバージョン】', '', summ['title'])
    else:
        summ['media'] = '配信専用動画'

    # イメージ設定
    if summ['maker'] == 'ナンパTV' or summ['maker'] == 'シロウトTV':
        summ['image_sm'] = img_src.replace('pb_p_', 'pb_t1_')
        summ['image_lg'] = img_src.replace('pb_p_', 'pb_e_')
    else :
        summ['image_sm'] = "&ref({0},147)".format(img_src)
        summ['image_lg'] = img_src.replace('pf_o1_', 'pb_e_')

    # Wikiに合わせてレーベル名変更
    if isDvd:
        if tmpActress:
            summ['actress'] = [(p.text.strip(), '', '') for p in tmpActress]

        if summ['maker'] in PrestigeLabel:
            summ['label'] = summ['maker']
            summ['maker'] = 'プレステージ'
    else:
        if summ['maker'] == 'ナンパTV':
            summ['label'] = 'ナンパＴＶ'
        elif summ['maker'] == 'プレステージプレミアム(PRESTIGE PREMIUM)' or summ['maker'] == 'ARA':
            titles = summ['pid'].split('-')
            if titles[0] == '300MAAN':
                summ['label'] = 'MAAN-san'
            elif titles[0] == '261ARA':
                summ['label'] = 'ARA'
            else:
                summ['label'] = titles[0] + 'その他'

    # レーベルリンク
    if summ['maker'] != '' and summ['media'] != 'DVD動画' and summ['pid'] != '' and summ['maker'] != 'ナンパTV' and summ['maker'] != 'プレステージプレミアム(PRESTIGE PREMIUM)':
        actuall = _libssw.check_actuallpage(summ['url'], summ['maker'], 'レーベル', summ['pid'])
        if actuall:
            summ['link_label'] = actuall

    if summ['label'] != '' and summ['label'] != summ['maker']:
        if summ['pid'] != '':
            actuall = _libssw.check_actuallpage(summ['url'], summ['label'], 'レーベル', summ['pid'])
            if actuall:
                summ['link_label'] = actuall
        else:
            summ['link_label'] = actuall

    # シリーズリンク
    if summ['series'] in MGS_SERIES:
        summ['link_series'] = MGS_SERIES.get(summ['series'])
    elif summ['series'] != '' and summ['label'] != summ['series'] and summ['maker'] != summ['series']:
        actuall = _libssw.check_actuallpage(summ['url'], summ['series'], 'シリーズ', summ['pid'])
        if actuall:
            summ['link_series'] = actuall


#----------------------------
# MGS動画(月額)
#----------------------------
def mgsMonthlyParser(soup, summ):
    common_detail_cover = soup.find('div', class_='common_detail_cover')
    detail_data = common_detail_cover.find('div', class_='detail_left').find('div', class_='detail_data')

    # タイトル取得
    h1 = common_detail_cover.find('h1', class_='tag').text.strip().splitlines()
    summ['title'] = h1[0]

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
    summ['subtitle'] = detail[2].find('a').string

    # イメージ設定
    summ['image_sm'] = img_src.replace('pb_p_', 'pb_t1_')
    summ['image_lg'] = img_src.replace('pb_p_', 'pb_e_')

    summ['media'] = '月額見放題'

    # メーカー設定
    if 'shiroutotv' in summ['url']:
        summ['maker'] = 'シロウトTV'
    elif 'nanpatv' in summ['url']:
        summ['maker'] = 'ナンパＴＶ'

    # レーベルリンク
    if summ['pid'] != '' and summ['maker'] != '':
        actuall = _libssw.check_actuallpage(summ['url'], summ['maker'], 'レーベル', summ['pid'])
        if actuall:
            summ['link_label'] = actuall

    # シリーズリンク
    if summ['series'] != '' and summ['maker'] != summ['series']:
        actuall = _libssw.check_actuallpage(summ['url'], summ['series'], 'シリーズ', summ['pid'])
        if actuall:
            summ['link_series'] = actuall

#----------------------------
# Prestige
#----------------------------
def prestigeParser(soup, summ):
    Wrapper = soup.find('div', id="Wrapper")

    # プレステージ公式の商品情報を取得
    spec_layout = Wrapper.find('dl', class_="spec_layout")
    dtl = spec_layout.find_all('dt')
    ddl = spec_layout.find_all('dd')

    for idx in range(len(dtl)):
        dt = dtl[idx].string
        if dt == '出演：':
            tmpActress = ddl[idx].text.replace(' ','')
        elif dt == '収録時間：':
            summ['time'] = ddl[idx].string
        elif dt == '発売日：':
            summ['release'] = ddl[idx].text.strip()
        elif dt == 'メーカー名：':
            summ['maker'] = ddl[idx].text.strip()
        elif dt == '品番：':
            summ['pid'] = re.sub('^(TKT|SHA)', '', ddl[idx].string)
        elif dt == 'レーベル：':
            summ['label'] = ddl[idx].text.strip()
        elif dt == 'シリーズ：':
            summ['series'] = ddl[idx].text.strip()

    product_title_layout = Wrapper.find('div', class_="product_layout_01")
    summ['title'] = product_title_layout.h1.text.strip()
    package_layout = Wrapper.find('p', class_="package_layout")
    summ['image_sm'] = '&ref(https://www.prestige-av.com' + package_layout.img['src'] + ',147)'
    summ['image_lg'] = 'https://www.prestige-av.com' + package_layout.a['href']

    if not re.search(r'[0-9]+名', tmpActress):
        summ['actress'] = [(p.strip(), '', '') for p in tmpActress.split()]

    # レーベルリンク
    if summ['label'] != '' and summ['label'] != summ['maker']:
        if summ['pid'] != '':
            actuall = _libssw.check_actuallpage(summ['url'], summ['label'], 'レーベル', summ['pid'])
            if actuall:
                summ['link_label'] = actuall
        else:
            summ['link_label'] = actuall

    # シリーズリンク
    if summ['series'] != '' and summ['maker'] != summ['series']:
        actuall = _libssw.check_actuallpage(summ['url'], summ['series'], 'シリーズ', summ['pid'])
        if actuall:
            summ['link_series'] = actuall

#----------------------------
# FC2
#----------------------------
def fc2Parser(soup, summ):
    # ID取得
    sp_url = summ['url'].split('/')
    summ['pid'] = sp_url[4]

    # タイトル取得
    headerInfo = soup.find('div', class_='items_article_headerInfo')
    summ['title'] = headerInfo.h3.text

    # リリース日取得
    Releasedate = headerInfo.find('div', class_='items_article_Releasedate').text.split(' ')
    summ['release'] = Releasedate[-1]

    # 販売者設定
    for li in headerInfo.ul.find_all('li'):
        tmp = li.text.strip()
        if tmp.startswith('by'):
           summ['label'] = li.a.text

    # サムネイル取得
    summ['image_sm'] = soup.find('meta', property='og:image')['content']

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
# DMM
#----------------------------
def dmmParser(soup, summ):
    # タイトル取得
    detail = soup.find('div', class_='page-detail')
    summ['title'] = detail.find('h1', id='title').text

    # 作品情報を取得
    table = soup.find('table', class_='mg-b20').find_all('tr')
    for tr in table:
        td = tr.find_all('td')
        dt = td[0].text
        if dt == '出演者：':
            actress = td[1].text.split()
            for act in actress:
                summ['actress'].append(act)
        elif dt == '収録時間：':
            summ['time'] = td[1].text
        elif dt == '発売日：':
            summ['release'] = td[1].text
        elif dt == 'メーカー：':
            summ['maker'] = td[1].text
        elif dt == '品番：':
            tmpid = td[1].text
            summ['pid'], summ['cid'] = _libssw.gen_pid(tmpid)

    # サムネイル取得
    sample = soup.find('div', id='sample-video')
    tx10 = sample.find('div', class_='tx10').a
    if tx10:
        summ['image_sm'] = tx10.img['src']
        summ['image_lg'] = tx10['href']

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

    name = model_profile.find('li', class_='name').string.replace('Real Street Angels ', '')
    profile = model_profile.find_all('li', class_='size')
    age = profile[0].contents[1]
    summ['subtitle'] = '{0} {1}'.format(name, age)

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
    summ['subtitle'] = profile[0].split('：')[-1].replace('　','')

    # サイズ取得
    tall = profile[1].split('：')[-1]
    size3 = profile[2].split('：')[-1]
    if tall != '---':
        summ['size'] = 'T' + tall + ' B' + size3.replace('-', ' W', 1).replace('-', ' H', 1)

    # レーベル設定
    no = int(re.sub("\\D", "", summ['pid']))
    if no < 201:
        summ['label'] = 'Girl\'s Blue'
    elif no < 401:
        summ['label'] = 'Girl\'s Blue(201～）'
    else:
        summ['label'] = 'Girl\'s Blue(' + str((no // 200 ) * 200 + 1) + '～)'

#----------------------------
# Pcolle
#----------------------------
def pcolleParser(soup, summ):
    # タイトル
    top = soup.find('div', class_='item-top')
    summ['title'] = top.find('div', class_='red').string

    # サムネイル取得
    img = soup.find('div', class_='item-content').img
    summ['image_sm'] = img['src']

    # 販売会員
    table = soup.find('div', class_='item-content').table
    thl = table.find_all('th')
    tdl = table.find_all('td')

    for idx in range(len(thl)):
        th = thl[idx].string
        if th == '販売会員:':
            summ['maker'] = tdl[idx].string

    item_detail = soup.find('section', class_='item_detail').div.dl
    dtl = item_detail.find_all('dt')
    ddl = item_detail.find_all('dd')

    for idx in range(len(dtl)):
        dt = dtl[idx].string
        if dt == 'ファイル名:':
            summ['pid'] = ddl[idx].string.replace('.mp4', '')
        elif dt == '販売開始日:':
            summ['release'] = ddl[idx].string

#----------------------------
# 人妻パラダイス
#----------------------------
def hparaParser(soup, summ):
    # ID取得
    sp_url = summ['url'].split('=')
    model_id = sp_url[1]
    summ['pid'] = re.sub("\\D", "", model_id)

    # サムネイル設定
    summ['image_sm'] = 'http://gold2.h-paradise.net/images/gold/sample/{0}/thumb/top02.jpg'.format(model_id)
    summ['image_lg'] = 'http://gold2.h-paradise.net/images/gold/sample/{0}/thumb/{0}.jpg'.format(model_id)

    # 作品情報
    model_prof = soup.find('div', class_='model-prof')
    if not model_prof:
        model_prof = soup.find('div', class_='model-prof-noflv')

    prof = model_prof.ul.find_all('li')

    if prof:
        # タイトル取得
        name = prof[0].text.replace('名前：', '')
        age = prof[1].text.replace('年齢：', '')
        summ['title'] = '{0} {1}'.format(name, age)

        # サイズ取得
        summ['size'] = prof[2].text.replace('サイズ：', '')

#----------------------------
# FALENO
#----------------------------
def falenoParser(soup, summ):
    # タイトル
    summ['title'] = soup.find('h1').string

    # 作品情報
    box_works = soup.find('div', class_='box_works01')
    if not box_works:
        box_works = soup.find('div', class_='box_actress02_list clearfix')

    if box_works:
        clearfix = box_works.find_all('li', class_='clearfix')
        for i in clearfix:
            item = i.span.text
            if item == '出演女優':
                summ['actress'] = i.p.text
            elif item == '配信開始日':
                summ['release'] = i.p.text
            elif item == '監督':
                summ['director'] = i.p.text

    # 品番作成
    tmpid = summ['url'].split('/')[-2]
    if '-' in tmpid:
        summ['pid'] = tmpid.upper()
    else:
        prefix = re.sub(r'[^a-zA-Z]', '', tmpid)
        no = re.sub('\\D', '', tmpid)
        summ['pid'] = prefix.upper() + '-' + no

    # メーカー・レーベル設定
    summ['maker'] = 'FALENO'
    if 'variety' in summ['url']:
        summ['label'] = 'FALENO TUBE'

    # 商品サムネイル
    box_works_img = soup.find('div', class_='box_works01_img')
    if not box_works_img:
        box_works_img = soup.find('div', class_='box_actress02_left')

    if box_works_img:
        img_src = box_works_img.img['src'].split('?')[0].replace('cdn.faleno.net', 'faleno.jp')
        if summ['label'] == 'FALENO TUBE':
            summ['image_sm'] = img_src.replace('.jpg', '-1.jpg')
        else:
            summ['image_sm'] = img_src.replace('1200.jpg', '2125.jpg')
        summ['image_lg'] = img_src

#----------------------------
# AKIBACOM
#----------------------------
def akibaParser(soup, summ):
    maincol = soup.find('div', id='undercolumn_02')
    cdpr = maincol.find('td', class_='cdpr')

    # 品番
    pid = cdpr.div.string
    if pid:
        summ['pid'] = pid.split('：')[-1]

    # タイトル
    summ['title'] = cdpr.find('h2').text

    datatable = maincol.find('table', class_='datatable')

    for tr in datatable.find_all('tr'):
        img = tr.img
        if img:
            summ['image_sm'] = 'https://www.akibacom.jp' + img['src']

        dtt = tr.find('td', class_='dtt').text
        if dtt == '発売日':
            summ['release'] = tr.find('td', class_='dtc').text
        elif dtt == 'メーカー':
            summ['maker'] = tr.find('td', class_='dtc').text

    # 出演者
    other = maincol.find('td', class_='other')
    if other:
        actress = other.p.text.split('、')
        for act in actress:
            summ['actress'].append(act)

#----------------------------
# HAPPY FISH
#----------------------------
def hfishParser(soup, summ):
    # No
    sp_url = summ['url'].split('=')
    summ['pid'] = sp_url[-1]

    # サムネイル取得
    summ['image_lg'] = 'https://www.h-fish.com/free_photo/' + summ['pid'] + '/1.jpg'

    # 仮名取得
    profile = soup.find('div', id="gallery_girl_profile").p.get_text(',').split(',')
    summ['subtitle'] = profile[0].split('：')[-1].replace('　','')

    # サイズ取得
    if '身　長' in profile[1]:
        tall = profile[1].split('：')[-1]
        size3 = profile[2].split('：')[-1]
        summ['size'] = 'T' + tall + ' B' + size3.replace(' - ', ' W', 1).replace(' - ', ' H', 1)
    else:
        size = profile[1].split()
        summ['size'] = size[0].replace('サイズ：', 'T') + ' B' + size[1] + ' W' + size[3] + ' H' + size[5]

    # レーベル設定
    summ['label'] = 'HAPPY FISH'


##############################
# Parser
##############################
javParser = {
    'MGS':                      mgsParser,
    'Prestige':                 prestigeParser,
    'FC2':                      fc2Parser,
    'HEYZO':                    heyzoParser,
    'DMM':                      dmmParser,
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
    'Pcolle':                   pcolleParser,
    '人妻パラダイス':           hparaParser,
    'FALENO':                   falenoParser,
    'AKIBACOM':                 akibaParser,
    'HAPPY FISH':               hfishParser,
}

#----------------------------
# MGS動画
#----------------------------
def mgsFormat_t(summ):

    date = summ['release'].replace('/', '-').replace('.', '-')

    wtext = ''
    wtext += '|[[{0}>{1}]]|[[{2}>{3}]]|'.format(summ['pid'], summ['url'], summ['image_sm'], summ['image_lg'])

    if summ['media'] == 'DVD動画':
        wtext += '{0}|'.format(summ['title'])
        for act in summ['actress']:
            if act == summ['actress'][0]:
                wtext += '[[{0}]]'.format(act[0])
            else:
                wtext += '／[[{0}]]'.format(act[0])
        wtext += '|{0}||\n'.format(date.replace('.', '-'))
    else:
        wtext += '{0}~~{1}|[[ ]]|{2}|'.format(summ['title'], summ['subtitle'], date) if summ['subtitle'] \
            else '{0}|[[ ]]|{1}|'.format(summ['title'], date)

        wtext += '[[シリーズ一覧>{0}]]|\n'.format(summ['link_series']) if summ['link_series'] and summ['maker'] != 'シロウトTV' \
            else '|\n'

    return wtext

#----------------------------
# Prestige
#----------------------------
def prestigeFormat_t(summ):

    # 出演者文字列の作成
    pfmrslk = ()
    pfmrsstr, pnum = _libssw.stringize_performers(summ['actress'],
                                                  summ['number'],
                                                  False)

    print(pfmrsstr)

    wtext = ''
    wtext += '|[[{0}>{1}]]|[[{2}>{3}]]|{4}|{5}|{6}||'.format(summ['pid'], summ['url'], summ['image_sm'], summ['image_lg'], summ['title'], pfmrsstr, summ['release'].replace('/', '-'))

    return wtext

#----------------------------
# FC2
#----------------------------
def fc2Format_t(summ):
    wtext = '|[[{0}>{1}]]|&ref({2},147)|{3}|[[ ]]|{4}||'.format(summ['pid'], summ['url'], summ['image_sm'], summ['title'], summ['release'].replace('/', '-'))

    return wtext

#----------------------------
# HEYZO
#----------------------------
def heyzoFormat_t(summ):
    return '非対応'

#----------------------------
# DMM
#----------------------------
def dmmFormat_t(summ):
    # 出演者一覧
    alist = ''
    for act in summ['actress']:
        if act == summ['actress'][-1]:
            alist += '[[{0}]]'.format(act)
        else:
            alist += '[[{0}]]／'.format(act)

    wtext = ''
    wtext += '|[[{0}>{1}]]|[[{2}>{3}]]|{4}|{5}|{6}||'.format(summ['pid'], summ['url'], summ['image_sm'], summ['image_lg'], summ['title'], alist, summ['release'].replace('/', '-'))

    return wtext

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

#----------------------------
# Pcolle
#----------------------------
def pcolleFormat_t(summ):
    release = summ['release'].replace('年', '-').replace('月', '-').replace('日', '')

    wtext = '|[[{0}>{1}]]|&ref({2},147)|{3}|[[ ]]|{4}||'.format(summ['pid'], summ['url'], summ['image_sm'], summ['title'], release)

    return wtext

#----------------------------
# 人妻パラダイス
#----------------------------
def hparaFormat_t(summ):
    wtext = '|[[{0}>{1}]]|{2}~~{3}|[[ ]]|#ref({4})||'.format(summ['pid'], summ['url'], summ['title'], summ['size'], summ['image_sm'])

    return wtext

#----------------------------
# FALENO
#----------------------------
def falenoFormat_t(summ):
    release = summ['release'].replace('/', '-')
    wtext = '|[[{0}>{1}]]|[[&ref({2},147)>{3}]]|{4}|[[ ]]|{5}||'.format(summ['pid'], summ['url'], summ['image_sm'], summ['image_lg'], summ['title'], release)

    return wtext

#----------------------------
# AKIBACOM
#----------------------------
def akibaFormat_t(summ):
    return '未対応'

#----------------------------
# HAPPY FISH
#----------------------------
def hfishFormat_t(summ):
    no = re.sub("\\D", "", summ['pid'])

    wtext = '|[[{0}>{1}]]|{2}~~{3}|[[ ]]|20--||'.format(no, summ['url'], summ['subtitle'], summ['size'])

    return wtext

##############################
# Format Table
##############################
Format_t = {
    'MGS':                      mgsFormat_t,
    'Prestige':                 prestigeFormat_t,
    'FC2':                      fc2Format_t,
    'HEYZO':                    heyzoFormat_t,
    'DMM':                      dmmFormat_t,
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
    'Pcolle':                   pcolleFormat_t,
    '人妻パラダイス':           hparaFormat_t,
    'FALENO':                   falenoFormat_t,
    'AKIBACOM':                 akibaFormat_t,
    'HAPPY FISH':               hfishFormat_t,
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

    wtext += '\n[['

    if summ['media'] != 'DVD動画':
        wtext += 'MGS '

    # 作品番号
    if summ['cid']:
        wtext += summ['cid']

    # タイトル
    wtext += summ['title']

    # MGS独占動画か判定
    isOnlyMGS = (summ['media'] == '月額見放題' or (summ['maker'] in OnlyMGS))

    # サブタイトル（出演名義）をつける
    if isOnlyMGS:
        wtext += '　{0}'.format(summ['subtitle'])

    # メーカー、レーベル（※MGS独占動画は慣例的にメーカー・メーベルをつけない）
    if not isOnlyMGS:
        wtext += '（{0[maker]}／{0[label]}）'.format(summ) if summ['label'] and (summ['maker'] != summ['label']) \
            else '（{0[maker]}）'.format(summ)

    # URL
    wtext += '>'
    wtext += summ['url']
    wtext += "]]"

    # レーベルリンク
    if summ['maker'] != '' and summ['media'] != 'DVD動画' and summ['pid'] != '' and summ['maker'] != 'ナンパTV' and summ['maker'] != 'プレステージプレミアム(PRESTIGE PREMIUM)':
        actuall = _libssw.check_actuallpage(summ['url'], summ['maker'], 'レーベル', summ['pid'])
        if actuall:
            wtext += "　[[(レーベル一覧)>{0}]]".format(actuall)

    if summ['label'] != '' and summ['label'] != summ['maker']:
        if summ['pid'] != '':
            actuall = _libssw.check_actuallpage(summ['url'], summ['label'], 'レーベル', summ['pid'])
            if actuall:
                wtext += "　[[(レーベル一覧)>{0}]]".format(actuall)
        else:
            wtext += "　[[(レーベル一覧)>{0}]]".format(summ['label'])

    # シリーズリンク
    if summ['series'] != '' and summ['label'] != summ['series'] and summ['maker'] != summ['series']:
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
# Prestige
#----------------------------
def prestigeFormat_a(summ):
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

    wtext += '\n[['

    # タイトル
    wtext += summ['title']

    wtext += '（{0[maker]}／{0[label]}）'.format(summ) if summ['label'] and (summ['maker'] != summ['label']) \
        else '（{0[maker]}）'.format(summ)

    # URL
    wtext += '>'
    wtext += summ['url']
    wtext += "]]"

    # レーベルリンク
    if summ['link_label']:
        wtext += "　[[(レーベル一覧)>{0}]]".format(summ['link_label'])

    # シリーズリンク
    if summ['link_series']:
        wtext += "　[[(シリーズ一覧)>{0}]]".format(summ['link_series'])

    # 改行
    wtext += "\n"

    # 画像URL
    if summ['image_lg'] == '':
        wtext += "&ref({0},,147)".format(summ['image_sm'])
    else:
        wtext += "[[{0}>{1}]]".format(summ['image_sm'], summ['image_lg'])

    return wtext

#----------------------------
# FC2
#----------------------------
def fc2Format_a(summ):

    wtext = ''

    # 配信日
    if summ['release']:
        date = '//' + summ['release'].replace('/', '.')
    else:
        date = '//'
    wtext += date

    # 品番
    if summ['pid']:
        wtext += ' FC2 PPV ' + summ['pid']

    # タイトルとURL
    wtext += '\n[[FC2 {0}（{1}）>{2}]]'.format(summ['title'], summ['label'], summ['url'])

    # 画像URL
    wtext += '\n&ref({0},147)'.format(summ['image_sm'])

    return wtext

#----------------------------
# HEYZO
#----------------------------
def heyzoFormat_a(summ):
    wtext = "//{0}\n-[[HEYZO {1}>{2}]]".format(summ['release'].replace('-', '.'), summ['title'], summ['url'])
    return wtext

#----------------------------
# DMM
#----------------------------
def dmmFormat_a(summ):
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

    wtext += '\n[['

    # タイトル
    wtext += summ['title']

    wtext += '（{0[maker]}／{0[label]}）'.format(summ) if summ['label'] and (summ['maker'] != summ['label']) \
        else '（{0[maker]}）'.format(summ)

    # URL
    wtext += '>'
    wtext += summ['url']
    wtext += "]]"

    # レーベルリンク
    if summ['maker'] != '' and summ['media'] != 'DVD動画' and summ['pid'] != '' and summ['maker'] != 'ナンパTV' and summ['maker'] != 'プレステージプレミアム(PRESTIGE PREMIUM)':
        actuall = _libssw.check_actuallpage(summ['url'], summ['maker'], 'レーベル', summ['pid'])
        if actuall:
            wtext += "　[[(レーベル一覧)>{0}]]".format(actuall)

    if summ['label'] != '' and summ['label'] != summ['maker']:
        if summ['pid'] != '':
            actuall = _libssw.check_actuallpage(summ['url'], summ['label'], 'レーベル', summ['pid'])
            if actuall:
                wtext += "　[[(レーベル一覧)>{0}]]".format(actuall)
        else:
            wtext += "　[[(レーベル一覧)>{0}]]".format(summ['label'])

    # 改行
    wtext += "\n"

    # 画像URL
    if summ['image_lg'] == '':
        wtext += "&ref({0},,147)".format(summ['image_sm'])
    else:
        wtext += "[[{0}>{1}]]".format(summ['image_sm'], summ['image_lg'])

    # 出演者一覧
    if len(summ['actress']) > 1:
        wtext += '\n出演者：'
        for act in summ['actress']:
            if act == summ['actress'][-1]:
                wtext += "[[{0}]]".format(act)
            else:
                wtext += "[[{0}]]／".format(act)

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
    wtext = "//{0}\n-[[パコパコママ {1} {2}>{3}]]".format(summ['release'].replace('-', '.'), summ['title'], summ['actress'], summ['url'])
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

    # タイトルとURL
    wtext += "[[Girl's Blue {0} {1} {2}>{3}]]".format(summ['pid'], summ['subtitle'], summ['size'], summ['url']) if summ['size'] \
        else "[[Girl's Blue {0} {1}>{2}]]".format(summ['pid'], summ['subtitle'], summ['url'])

    # レーベルリンク
    if summ['label'] != '':
        wtext += "　[[(レーベル一覧)>{0}]]".format(summ['label'])

    # 画像URL
    wtext += "\n&ref({0},147)".format(summ['image_lg'])

    return wtext

#----------------------------
# Pcolle
#----------------------------
def pcolleFormat_a(summ):
    wtext = ''

    # 配信日・ファイル名
    release = summ['release'].replace('年', '.').replace('月', '.').replace('日', '')
    header = '//{0} {1}'.format(release, summ['pid'])
    wtext += header

    # タイトルとURL
    wtext += "\n[[Pcolle {0}（{1}）>{2}]]".format(summ['title'], summ['maker'], summ['url'])

    # レーベルリンク
    actuall = _libssw.check_actuallpage(summ['url'], summ['maker'], 'レーベル', summ['pid'])
    if actuall:
        wtext += "　[[(レーベル一覧)>{0}]]".format(actuall)

    # 画像URL
    wtext += "\n&ref({0},,147)".format(summ['image_sm'])

    return wtext

#----------------------------
# 人妻パラダイス
#----------------------------
def hparaFormat_a(summ):
    wtext = ''

    # 配信日
    date = '//'
    wtext += date

    # タイトルとURL
    wtext += "\n[[人妻パラダイス {0} {1}>{2}]]".format(summ['title'], summ['size'], summ['url'])

    # 画像URL
    wtext += "\n&ref({0})".format(summ['image_lg'])

    return wtext

#----------------------------
# FALENO
#----------------------------
def falenoFormat_a(summ):
    wtext = ''

    # 配信日
    date = '//' + summ['release'].replace('/', '.')
    wtext += date

    # 品番
    if summ['pid']:
        wtext += ' ' + summ['pid']

    # タイトルとURL
    if summ['label']:
        wtext += "\n[[U-NEXT {0}（FALENO／{1}）>{2}]]　[[(レーベル一覧)>{1}]]".format(summ['title'], summ['label'], summ['url'])
    else:
        wtext += "\n[[U-NEXT {0}（FALENO）>{1}]]".format(summ['title'], summ['url'])

    # 画像URL
    wtext += "\n[[{0}>{1}]]".format(summ['image_sm'], summ['image_lg'])

    return wtext

#----------------------------
# AKIBACOM
#----------------------------
def akibaFormat_a(summ):
    wtext = ''

    # 配信日
    date = '//' + summ['release'].replace('年 ', '.').replace('月 ', '.').replace('日', '')
    wtext += date

    # 品番
    if summ['pid']:
        wtext += ' ' + summ['pid']

    # タイトルとURL
    wtext += '\n[[{0}（{1}）>{2}]]'.format(summ['title'], summ['maker'], summ['url'])

    # 画像URL
    wtext += '\n&ref({0},,200)'.format(summ['image_sm'])

    # 出演者一覧
    isSingle = (len(summ['actress']) == 1)
    if not isSingle:
        wtext += '\n出演者：'
        for act in summ['actress']:
            if act == summ['actress'][-1]:
                wtext += '[[{0}]]'.format(act)
            else:
                wtext += '[[{0}]]／'.format(act)

    return wtext

#----------------------------
# HAPPY FISH
#----------------------------
def hfishFormat_a(summ):
    wtext = ''

    # タイトルとURL
    wtext += "[[HAPPY FISH {0} {1} {2}>{3}]]".format(summ['pid'], summ['subtitle'], summ['size'], summ['url']) if summ['size'] \
        else "[[HAPPY FISH {0} {1}>{2}]]".format(summ['pid'], summ['subtitle'], summ['url'])

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
    'Prestige':                 prestigeFormat_a,
    'FC2':                      fc2Format_a,
    'HEYZO':                    heyzoFormat_a,
    'DMM':                      dmmFormat_a,
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
    'Pcolle':                   pcolleFormat_a,
    '人妻パラダイス':           hparaFormat_a,
    'FALENO':                   falenoFormat_a,
    'AKIBACOM':                 akibaFormat_a,
    'HAPPY FISH':               hfishFormat_a,
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
    elif site == 'Prestige':
        data = {
            "Cookie": 'age_auth=1',
        }
        req = urllib.request.Request(reqUrl, None, data)
        with urllib.request.urlopen(req) as res:
            s = res.read()
        s = bs4.BeautifulSoup(s, "html.parser")
    elif site == 'FALENO':
        data = {
            "Cookie": 'modal=off',
        }
        req = urllib.request.Request(reqUrl, None, data)
        with urllib.request.urlopen(req) as res:
            s = res.read()
        s = bs4.BeautifulSoup(s, "html.parser")
    elif site == 'AKIBACOM':
        data = {
            "Cookie": 'agree=true',
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

        if site in charsetEucJp:
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
                                summ['actress'],
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
