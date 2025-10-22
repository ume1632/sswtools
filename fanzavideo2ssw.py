#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import re
import httplib2
import bs4
import argparse
import libssw as _libssw
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from collections import namedtuple as _namedtuple

_ReturnVal = _namedtuple('ReturnVal',
                         ('release', 'pid', 'title', 'title_dmm', 'url',
                          'time', 'maker', 'label', 'series',
                          'actress', 'link_label', 'link_series',
                          'wktxt_a', 'wktxt_t'))

# コマンドライン引数の解釈
def _get_args(argv, p_args):
    argparser = argparse.ArgumentParser(
        description='URLから素人系総合wiki用ウィキテキストを作成する')

    argparser.add_argument('url',
                           help='作品ページのURL',
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

    list_page.add_argument('-l', '--label',
                           help='レーベル一覧へのリンクを追加(FANZA上のものを置き換え)',
                           default=getattr(p_args, 'label', None))

    argparser.add_argument('-t', '--table',
                           help='一覧ページ用の表形式ウィキテキストを作成する, 2個以上指定すると両方作成する',
                           action='count',
                           default=getattr(p_args, 'table', 0))

    argparser.add_argument('-f', '--disable-follow-redirect',
                           help='ページのリダイレクト先をチェックしない',
                           dest='follow_rdr',
                           action='store_false',
                           default=getattr(p_args, 'follow_rdr', True))

    argparser.add_argument('--disable-check-listpage',
                           help='Wiki上の実際の一覧ページを探さない',
                           dest='check_listpage',
                           action='store_false',
                           default=getattr(p_args, 'check_listpage', True))

    argparser.add_argument('--fastest',
                           help='ウェブにアクセスするあらゆる補助処理を行わない',
                           action='store_true',
                           default=getattr(p_args, 'fastest', False))

    args = argparser.parse_args(argv)

    if args.fastest:
        for a in ('follow_rdr', 'check_rental', 'check_listpage',
                  'check_rltd', 'longtitle'):
            setattr(args, a, False)

    return args

# htmlの取得
def decode_chrome(url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://www.dmm.co.jp/age_check/=/declared=yes/?rurl="+url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
        )

        # JavaScript 実行後のHTMLを取得
        html = driver.page_source

    finally:
        driver.quit()

    return html


def fanzaVideoParser(soup, summ, service):
    title = soup.find('meta', property='og:title')
    if title:
        summ['title'] = _libssw._fix_ngword(title['content'])

    flex = soup.find('div', class_='flex relative')
    flex4 = flex.find('div', class_='flex flex-col gap-4')

    table = flex4.find('table', class_='text-xs shrink table-fixed')
    trs = table.find_all('tr')

    plist = []

    for tr in trs:
        span = tr.find_all('span')
        inlineFlex = span[0].text
        if (inlineFlex == '配信開始日：') and (service == 'ama'):
            summ['release'] = span[1].text
        if inlineFlex == '商品発売日：':
            summ['release'] = span[1].text
        elif inlineFlex == '名前：':
            _re_age = re.compile(r'(\(\d+?\))$')
            name = span[1].text
            # 素人動画のタイトルは後でページタイトルと年齢をくっつける
            try:
                age = _re_age.findall(name)[0]
            except IndexError:
                age = ''
            summ['subtitle'] = age
        elif inlineFlex == 'サイズ：':
            size = span[1].text
            re_size = re.compile(r'[TBWH]-+ *')
            summ['size'] = re_size.sub('', size).rstrip()
        elif inlineFlex == '出演者：':
            actress = span[1].find_all('a')
            for act in actress:
               plist.append(act.string)
            summ['actress'] = [(p.strip(), '', '') for p in plist]
        elif inlineFlex == 'シリーズ：':
            series = span[1].text
            if (series != '----'):
                summ['series'] = series
        elif inlineFlex == 'メーカー：':
            summ['maker'] = span[1].text
        elif inlineFlex == 'レーベル：':
            label = span[1].text
            if (label != '----'):
                summ['label'] = label
        elif inlineFlex == '配信品番：':
            summ['cid'] = span[1].text
        elif inlineFlex == 'メーカー品番：':
            summ['pid'] = span[1].text

    # イメージ設定
    baseUrl = 'https://pics.dmm.co.jp/digital'
    if service == 'ama':
        summ['image_sm'] = "{0}/amateur/{1}/{1}js.jpg".format(baseUrl, summ['cid'])
        summ['image_lg'] = "{0}/amateur/{1}/{1}jp.jpg".format(baseUrl, summ['cid'])
    else:
        summ['image_sm'] = "{0}/video/{1}/{1}ps.jpg".format(baseUrl, summ['cid'])
        summ['image_lg'] = "{0}/video/{1}/{1}pl.jpg".format(baseUrl, summ['cid'])

    # 素人動画の時のタイトル/副題の再作成
    if service == 'ama':
        summ['title'] = summ['subtitle'] = \
                        summ['title'] + summ['subtitle']


def FanzaFormat_a(summ, anum, astr, service):
    """ウィキテキストの作成 女優ページ用"""
    wtext = ''

    # 発売日
    date = summ['release']
    wtext += '{0[release]} {0[pid]}\n'.format(summ)
    # 自動修正があった場合のDMM上のタイトル (コメント)
    if summ['title_dmm']:
        wtext += '//{0[title_dmm]} #検索用\n'.format(summ)
    # タイトルおよびメーカー
    if service == 'ama':
        titleline = '[[{0[label]} {0[subtitle]} {0[size]}>{0[url]}]]'.format(summ) if summ['size'] \
        else '[[{0[label]} {0[title]}>{0[url]}]]'.format(summ)
    else:
        # レーベルの並記
        maker = summ['maker'].split('（')[0]
        add_label = summ['label']
        if add_label and (not '/' in summ['maker']) and (maker != add_label):
            maker += '／{0}'.format(add_label)
        titleline = '[[{0[title]}（{1}）>{0[url]}]]'.format(summ, maker)
    # レーベル一覧へのリンク
    if summ['link_label']:
        titleline += '　[[(レーベル一覧)>{0}]]'.format(summ['link_label'])
    # シリーズ一覧へのリンク
    if summ['link_series']:
        titleline += '　[[(シリーズ一覧)>{0}]]'.format(summ['link_series'])
    wtext += titleline + '\n'
    # 画像
    if service == 'ama':
        wtext += '[[&ref({0[image_lg]},147)>{0[image_lg]}]]\n'.format(summ)
    else:
        wtext += '[[{0[image_sm]}>{0[image_lg]}]]\n'.format(summ)
    # 出演者
    if anum not in {0, 1}:
        wtext += '出演者：{0}\n'.format(astr)
    # 備考
    notes = summ['note'] + summ['others'] if summ['others'] else summ['note']
    if notes:
        wtext += '、'.join(notes) + '\n'

    return wtext


def FanzaFormat_t(summ, astr, add_column, retrieval):
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
    if astr:
        wtext += '|{0}'.format(astr)
    else:
        wtext += '|----' if ('総集編作品' in summ['note']) else '|[[ ]]'

    # 追加カラム
    if add_column:
        wtext += '|' + '|'.join(add_column)

    # 発売日
    wtext += '|{0[release]}'.format(summ)

    # 備考
    if retrieval == 'label' and summ['link_series']:
        wtext += '|[[シリーズ一覧>{0}]]|'.format(summ['link_series'])
    else:
        wtext += '|{}|'.format('、'.join(summ['note']))

    return wtext


def main(props=_libssw.Summary(), p_args = argparse.Namespace):
    argv = [props.url] if __name__ != '__main__' else sys.argv[1:]
    args = _get_args(argv, p_args)
    reqUrl = args.url

    # 作品情報
    summ = _libssw.Summary()
    
    if __name__ != '__main__':
        summ.update(props)

    summ['url'] = reqUrl

    html = decode_chrome(reqUrl)

    s = bs4.BeautifulSoup(html, 'html.parser')

    service = getattr(p_args, 'service', None)

    # サービス未指定時の自動決定
    if not service:
        if '/amateur/' in reqUrl:
            service = 'ama'
        else:
            service = 'video'

    fanzaVideoParser(s, summ, service)

    summ['link_label'] = getattr(args, 'label')

    retrieval = ''
    add_column = ''

    if args.check_listpage:
        # レーベル一覧へのリンク情報の設定
        if summ['pid'] and summ['label'] and (not summ['link_label']):
            actuall = _libssw.check_actuallpage(summ['url'], summ['label'], 'レーベル', summ['pid'])
            if actuall:
                summ['link_label'] = actuall

        if summ['pid'] and summ['series'] and (summ['series'] != summ['label']):
            actuall = _libssw.check_actuallpage(summ['url'], summ['series'], 'シリーズ', summ['pid'])
            if actuall:
                summ['link_series'] = actuall

    # 出演者文字列の作成
    pfmrslk = ()
    if len(summ['actress']) < 2 and not summ['number'] and args.table == 0:
        # 女優ページ用のみ作成で出演者数が1人ならやらない
        pfmrsstr, pnum = '', 0
    else:
        pfmrsstr, pnum = _libssw.stringize_performers(summ['actress'],
                                                      summ['number'],
                                                      args.follow_rdr)

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

    # Wikiテキスト作成
    wktxt_a = FanzaFormat_a(summ, pnum, pfmrsstr, service) if args.table != 1 else ()
    wktxt_t = FanzaFormat_t(summ, pfmrsstr, add_column, retrieval) if args.table else ''

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
