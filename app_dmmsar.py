#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import datetime
import tkinter as tk
import argparse

import libssw as _libssw
import dmm2ssw as _dmm2ssw
import dmmsar as _dmmsar

from tkinter import ttk

def button1_action(event):
    argv = []

    key = txtUrl.get()
    getService = Service.get()
    CidPrefix = txtCidPrefix.get()
    CidSTart = txtCidSTart.get()
    CidEnd = txtCidEnd.get()

    if Ind.get() != 'find':
        argv.append('--' + Ind.get())

    if key:
        argv.append(key)

    if getService != 'mono':
        argv.append('--service')
        argv.append(getService)

    if WikiPage.get() == 1:
        argv.append('-t')
    elif WikiPage.get() == 2:
        argv.append('-tt')

    if CidPrefix and CidSTart:
        CidPrefix = CidPrefix.strip()
        argv.append('--cid')
        if CidEnd:
            argv.append(CidPrefix + '{}')
            argv.append(CidSTart)
            argv.append(CidEnd)
        else:
            argv.append("{0}{1}".format(CidPrefix, CidSTart))

    startDate = txtDate.get()
    if startDate:
        argv.append('--start-date')
        argv.append(startDate)

    if Director.get():
        argv.append('-d')

    if cb1.current() > 0:
        argv.append('--pages-last')
        argv.append(str(cb1.current()))

    if cb2.current() == 1:
        argv.append('-f')
    elif cb2.current() == 2:
        argv.append('--fastest')

    if GetBest.get():
        argv.append('-mm')

    outFile = txtFile.get()
    argv.append('-o')
    if outFile:
        argv.append(outFile + '.txt')
    else:
        now = datetime.datetime.now()
        argv.append(now.strftime('%Y%m%d%H%M%S') + 'Dmmsar.txt')

    argv.append('--clear-cache')
    argv.append('-v')

    # dmmsar実行
    _dmmsar.main(argv)

def button2_action(event):
    txtUrl.delete      (0, tk.END)
    txtCidPrefix.delete(0, tk.END)
    txtCidSTart.delete (0, tk.END)
    txtCidEnd.delete   (0, tk.END)
    txtDate.delete     (0, tk.END)
    txtFile.delete     (0, tk.END)

root = tk.Tk()
root.title(u"素人系総合Wiki 編集ツール DmmSar")
root.geometry("640x480")

Ind = tk.StringVar()
Ind.set('find')

f1 = tk.LabelFrame(root, text = 'リスト指定')

radio1 = tk.Radiobutton(f1, text = '自動判別',     variable = Ind, value = 'find')
radio2 = tk.Radiobutton(f1, text = 'URL', variable = Ind, value = 'url')
radio3 = tk.Radiobutton(f1, text = '女優ID', variable = Ind, value = 'actress')
radio4 = tk.Radiobutton(f1, text = 'レーベルID', variable = Ind, value = 'label')
radio5 = tk.Radiobutton(f1, text = 'シリーズID', variable = Ind, value = 'series')
radio6 = tk.Radiobutton(f1, text = 'メーカーID', variable = Ind, value = 'maker')
radio1.pack(padx=10, side = tk.LEFT)
radio2.pack(padx=10, side = tk.LEFT)
radio3.pack(padx=10, side = tk.LEFT)
radio4.pack(padx=10, side = tk.LEFT)
radio5.pack(padx=10, side = tk.LEFT)
radio6.pack(padx=10, side = tk.LEFT)

f1.pack(padx = 10, pady = 5, side = tk.TOP, anchor = tk.NW)

# 作成ページ選択
f2 = tk.LabelFrame(root, text = 'サービス指定')

Service = tk.StringVar()
Service.set('mono')

radio7 = tk.Radiobutton(f2, text = 'DVD通販',     variable = Service, value = 'mono')
radio8 = tk.Radiobutton(f2, text = 'DVDレンタル', variable = Service, value = 'rental')
radio9 = tk.Radiobutton(f2, text = '動画/VR',     variable = Service, value = 'video')
radio10 = tk.Radiobutton(f2, text = '素人動画',    variable = Service, value = 'ama')

radio7.pack(padx=10, side = tk.LEFT)
radio8.pack(padx=20, side = tk.LEFT)
#radio9.pack(padx=20, side = tk.LEFT)
#radio10.pack(padx=20, side = tk.LEFT)

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

# キーワードボックス
f4 = tk.Frame(root)
label1 = tk.Label(f4, text='URLまたはID :')
txtUrl = tk.Entry(f4, width=80)
label1.pack(side = tk.LEFT)
txtUrl.pack(padx = 10, side = tk.LEFT)
f4.pack(padx = 10, pady = 10, side = tk.TOP, anchor = tk.NW)

# 品番指定
f5 = tk.Frame(root)
label2 = tk.Label(f5, text='品番指定 :')
label3 = tk.Label(f5, text='プレフィックス')
label4 = tk.Label(f5, text='開始No')
label5 = tk.Label(f5, text='終了No')
txtCidPrefix = tk.Entry(f5, width=15)
txtCidSTart = tk.Entry(f5, width=15)
txtCidEnd = tk.Entry(f5, width=15)

label2.pack(side = tk.LEFT)
label3.pack(padx = 10, side = tk.LEFT)
txtCidPrefix.pack(padx = 10, side = tk.LEFT)
label4.pack(side = tk.LEFT)
txtCidSTart.pack(padx = 10, side = tk.LEFT)
label5.pack(side = tk.LEFT)
txtCidEnd.pack(padx = 10, side = tk.LEFT)
f5.pack(padx = 10, pady = 10, side = tk.TOP, anchor = tk.NW)

# 開始日指定
f6 = tk.Frame(root)
label6 = tk.Label(f6, text='データ作成開始日(YYYYMMDD) :')
txtDate = tk.Entry(f6, width=20)
label6.pack(side = tk.LEFT)
txtDate.pack(padx = 10, side = tk.LEFT)
f6.pack(padx = 10, pady = 10, side = tk.TOP, anchor = tk.NW)

# 出力ファイル名
f7 = tk.Frame(root)
label7 = tk.Label(f7, text='出力ファイル名 :')
txtFile = tk.Entry(f7, width=20)
label7.pack(side = tk.LEFT)
txtFile.pack(padx = 10, side = tk.LEFT)
f7.pack(padx = 10, pady = 10, side = tk.TOP, anchor = tk.NW)

# 監督欄の出力
f8 = tk.Frame(root)
Director = tk.BooleanVar()
Director.set(False)

chk1 = tk.Checkbutton(f8, text = '監督欄を出力する', variable = Director)
chk1.pack(side = tk.LEFT)

# 総集編を除外しない
GetBest = tk.BooleanVar()
GetBest.set(False)

chk4 = tk.Checkbutton(f8, text = '総集編を取得対象にする', variable = GetBest)
chk4.pack(padx = 10, side = tk.LEFT)
f8.pack(padx = 10, side = tk.TOP, anchor = tk.NW)

# 検索範囲
f9 = tk.Frame(root)
label8 = tk.Label(f9, text='検索範囲 :')
label8.pack(side = tk.LEFT)

SearchPage = tk.StringVar()
cbValues1 = ['全件取得', '最新120件', '最新240件', '最新360件']

cb1 = ttk.Combobox(f9, textvariable = SearchPage, values = cbValues1)
cb1.current(0)
cb1.pack(side = tk.LEFT)

# Wiki内検索をしない
label9 = tk.Label(f9, text='Wiki内検索 :')
label9.pack(padx = 10, side = tk.LEFT)

SearchWiki = tk.StringVar()
cbValues2 = ['Wiki内検索をする', 'リダイレクト確認をしない', 'Wiki内検索を行わない']

cb2 = ttk.Combobox(f9, textvariable = SearchWiki, values = cbValues2)
cb2.current(0)
cb2.pack(side = tk.LEFT)

f9.pack(padx = 10, pady = 10, side = tk.TOP, anchor = tk.NW)

# 検索・消去ボタン
f10 = tk.Frame(root)

button1 = tk.Button(f10, text='Search', width=40)
button1.bind("<Button-1>", button1_action)
button1.pack(side = tk.LEFT)

button2 = tk.Button(f10, text='Clear', width=20)
button2.bind("<Button-1>", button2_action)
button2.pack(padx = 10, side = tk.LEFT)
f10.pack(padx = 10, pady = 10, side = tk.TOP, anchor = tk.NW)



root.mainloop()

