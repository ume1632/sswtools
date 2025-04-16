#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import re
import tkinter as tk
import argparse
import webbrowser as _webbrowser
import urllib.parse as _up

import libssw as _libssw
import dmm2ssw as _dmm2ssw
import jav2ssw as _jav2ssw

from tkinter import ttk

re_inbracket = re.compile(r'[(（]')

g_link_label = ''
g_link_series = ''
g_pid = ''
g_actress = []

def _trim_name(name):
    """女優名の調整"""
    name = name.strip()
    name = re_inbracket.split(name)[0]
    return name

def _list_pfmrs(plist):
    return [(_trim_name(p.strip()), '', '') for p in plist]

def open_wiki(*pages):
    """wikiページをウェブブラウザで開く"""
    for p in filter(None, pages):
        url = _up.urljoin('http://seesaawiki.jp/w/sougouwiki/d/', _libssw.quote(p))
        resp, he = _libssw.open_url(url)
        if resp.status == 200:
            dest = _libssw._rdrparser(p, he)
            if dest != p and dest != '':
                # リダイレクト先を再度読み込み
                url = _up.urljoin('http://seesaawiki.jp/w/sougouwiki/d/', _libssw.quote(dest))
                resp, he = _libssw.open_url(url)
            inner = he.find_class('inner')[0]
            editurl = inner.xpath('.//a')[0].get('href')
            if editurl:
                _webbrowser.open_new_tab(editurl)
        else:
            message = p + ' : ページが見つかりませんでした'
            label7.config(text=message)

def button1_action():
    props=_libssw.Summary()
    props['url'] = txtUrl.get()

    if props['url']:
        # テキストクリア
        txtList.delete('1.0', 'end')
        txtAct.delete('1.0', 'end')
        # ボタン無効化
        button3['state'] = tk.DISABLED
        button5['state'] = tk.DISABLED

        # オプション引数設定
        args = argparse.Namespace()
        args.table = WikiPage.get()
        args.dir_col = Director.get()
        args.label = inpLabel.get()
        args.cid_l = ''

        if cb1.current() == 1:
            args.follow_rdr = False
        elif cb1.current() == 2:
            args.fastest = True

        # Fanza判定
        isFanza = ('dmm.co.jp' in props['url'])

        if isFanza:
            if ('?' in props['url']):
                urll = props['url'].split('?')
                props['url'] = urll[0]
            _libssw.clear_cache()
            b, status, data = _dmm2ssw.main(props, args)
        else:
            b, data = _jav2ssw.main(props, args)

        global g_link_label
        global g_link_series
        global g_actress
        global g_pid

        if b:

            g_link_label = data.link_label
            g_link_series = data.link_series
            g_actress = data.actress
            g_pid = data.pid

            # 結果を反映
            if data.wktxt_t:
                # Wikiテキスト出力
                txtList.insert(tk.END, data.wktxt_t)
                if g_link_label or g_link_series:
                    # 編集ボタン有効化
                    button3['state'] = tk.NORMAL
            if data.wktxt_a:
                # Wikiテキスト出力
                txtAct.insert(tk.END, data.wktxt_a)
                if g_actress:
                    # 編集ボタン有効化
                    button5['state'] = tk.NORMAL

            label7.config(text='取得完了')

        else:
            g_link_label = ''
            g_link_series = ''
            g_actress = []
            g_pid = ''
            label7.config(text='取得失敗')

# クリア
def button2_action():
    # 入力クリア
    txtUrl.delete(0, tk.END)
    inpLabel.delete(0, tk.END)
    inpAct.delete(0, tk.END)
    # テキストクリア
    txtList.delete('1.0', 'end')
    txtAct.delete('1.0', 'end')
    label7.config(text='')
    # ボタン無効化
    button3['state'] = tk.DISABLED
    button5['state'] = tk.DISABLED

# 一覧ページ編集画面を開く
def button3_action():
    _libssw.open_ssw(g_link_label)
    _libssw.open_ssw(g_link_series)

# 一覧ページ用テキストをクリップボードにコピー
def button4_action():
    root.clipboard_clear()
    root.clipboard_append(txtList.get('1.0', 'end -1c'))

# 女優ページ編集画面を開く
def button5_action():
    for a in g_actress:
        open_wiki(a[1] or a[0])

# 女優ページ用テキストをクリップボードにコピー
def button6_action():
    root.clipboard_clear()
    root.clipboard_append(txtAct.get('1.0', 'end -1c'))

# URL入力
def enter_url(event):
    button1_action()

# 右クリックメニュー表示
def show_popup(event):
    menuPop.post(event.x_root, event.y_root)

# クリップボード貼り付け
def paste_url():
    txtUrl.insert(tk.END, root.clipboard_get())

#-----------------------------------------------
# Main
#-----------------------------------------------
root = tk.Tk()
root.title(u'素人系総合Wiki 編集ツール Dmm2Ssw')
root.geometry('640x560')

menuPop = tk.Menu(root, tearoff=False)
menuPop.add_cascade(label='貼り付け', command=paste_url)

# Label 1
f1 = tk.Frame(root)
label1 = tk.Label(f1, text='URL')
label1.pack(padx = 10, side = tk.LEFT)

# URL入力ボックス
txtUrl = tk.Entry(f1, width=80)
txtUrl.pack(padx = 10, side = tk.LEFT)
txtUrl.bind('<Return>', enter_url)
txtUrl.bind('<Button-3>',show_popup)
f1.pack(padx = 10, pady = 5, side = tk.TOP, anchor = tk.NW)

# Label 2
f2 = tk.Frame(root)
label2 = tk.Label(f2, text='レーベル設定(任意)')
label2.pack(padx = 10, side = tk.LEFT)

# レーベル入力ボックス
inpLabel = tk.Entry(f2, width=25)
inpLabel.pack(padx = 10, side = tk.LEFT)

# Label 3
label3 = tk.Label(f2, text='女優設定(任意)')
#label3.pack(padx = 10, side = tk.LEFT)

# 女優入力ボックス
inpAct = tk.Entry(f2, width=25)
#inpAct.pack(padx = 10, side = tk.LEFT)
f2.pack(padx = 10, pady = 5, side = tk.TOP, anchor = tk.NW)

# 作成ページ選択
f3 = tk.LabelFrame(root, text = '作成ページ')

WikiPage = tk.IntVar()
WikiPage.set(2)

radio11 = tk.Radiobutton(f3, text = '一覧＋女優',     variable = WikiPage, value = 2)
radio12 = tk.Radiobutton(f3, text = '一覧ページのみ', variable = WikiPage, value = 1)
radio13 = tk.Radiobutton(f3, text = '女優ページのみ', variable = WikiPage, value = 0)
radio11.pack(padx=10, side = tk.LEFT)
radio12.pack(padx=20, side = tk.LEFT)
radio13.pack(padx=20, side = tk.LEFT)
f3.pack(padx = 10, pady = 5, side = tk.TOP, anchor = tk.NW)

# 監督欄の出力
Director = tk.BooleanVar()
Director.set(False)

chk1 = tk.Checkbutton(text = '監督欄を出力する', variable = Director)
chk1.pack(padx = 10, side = tk.TOP, anchor = tk.NW)

# Wiki内検索をしない
f4 = tk.Frame(root)
label4 = tk.Label(f4, text='Wiki内検索 :')
label4.pack(padx = 10, side = tk.LEFT)

SearchWiki = tk.StringVar()
cbValues1 = ['Wiki内検索をする', 'リダイレクト確認をしない', 'Wiki内検索を行わない']

cb1 = ttk.Combobox(f4, textvariable = SearchWiki, values = cbValues1)
cb1.current(0)
cb1.pack(side = tk.LEFT)

f4.pack(padx = 10, pady = 10, side = tk.TOP, anchor = tk.NW)

# 実行ボタン
f5 = tk.Frame(root)
button1 = tk.Button(f5, text='Export', width=30, command=button1_action)
button1.pack(padx = 10, side = tk.LEFT)

# 消去ボタン
button2 = tk.Button(f5, text='Clear', width=15, command=button2_action)
button2.pack(padx = 10, side = tk.LEFT)
f5.pack(padx = 10, pady = 10, side = tk.TOP, anchor = tk.NW)

# Label 5
label5 = tk.Label(text='一覧ページ用Wikiテキスト')
label5.pack(padx = 20, pady = 5, side = tk.TOP, anchor = tk.NW)

# 一覧ページ出力
txtList = tk.Text(height=6, width=80)
txtList.pack(padx = 10, side = tk.TOP, anchor = tk.NW)

# Wiki編集ボタン 1
f6 = tk.Frame(root)
button3 = tk.Button(f6, text='一覧ページを編集', width=15, command=button3_action, state=tk.DISABLED)
button3.pack(padx = 10, side = tk.LEFT)

# クリップボードへのコピーボタン 1
button4 = tk.Button(f6, text='クリップボードにコピー', width=15, command=button4_action)
button4.pack(padx = 5, side = tk.LEFT)
f6.pack(padx = 10, pady = 5, side = tk.TOP, anchor = tk.NW)

# Label 6
label6 = tk.Label(text='女優ページ用Wikiテキスト')
label6.pack(padx = 20, pady = 5, side = tk.TOP, anchor = tk.NW)

# 女優ページ出力
txtAct = tk.Text(height=6, width=80)
txtAct.pack(padx = 10, side = tk.TOP, anchor = tk.NW)

# Wiki編集ボタン 2
f7 = tk.Frame(root)
button5 = tk.Button(f7, text='女優ページを編集', width=15, command=button5_action, state=tk.DISABLED)
button5.pack(padx = 10, side = tk.LEFT)

# クリップボードへのコピーボタン 2
button6 = tk.Button(f7, text='クリップボードにコピー', width=15, command=button6_action)
button6.pack(padx = 5, side = tk.LEFT)

# クリップボードへのコピーボタン 2
f7.pack(padx = 10, pady = 5, side = tk.TOP, anchor = tk.NW)

# Label 7
label7 = tk.Label(text='')
label7.pack(padx = 20, pady = 5, side = tk.TOP, anchor = tk.NW)

root.mainloop()

