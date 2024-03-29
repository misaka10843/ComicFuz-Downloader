#!/usr/bin/env python3
import os
import re
import time

from rich.progress import track

import fuz_pb2
import json
import argparse
import py7zr
import getpass
import shutil
import logging
from urllib.request import Request, ProxyHandler, build_opener
from google.protobuf import json_format
from threading import Thread
from queue import Queue
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from rich import print
from rich.console import Console
from PIL import Image

console = Console()

COOKIE = "is_logged_in=true; fuz_session_key="
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" \
             " AppleWebKit/537.36 (KHTML, like Gecko)" \
             " Chrome/96.0.4664.55" \
             " Safari/537.36" \
             " Edg/96.0.1054.34"

API_HOST = "https://api.comic-fuz.com"
IMG_HOST = "https://img.comic-fuz.com"
TABLE = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-_"
T_MAP = {s: i for i, s in enumerate(TABLE)}

urlopen = build_opener()


def main():
    global urlopen
    parser = get_parser()
    args = parser.parse_args()
    # 添加代理
    if args.proxy:
        proxy_handler = ProxyHandler(
            {'http': f'http://{args.proxy}', 'https': f'http://{args.proxy}'})
        urlopen = build_opener(proxy_handler)
    else:
        urlopen = build_opener()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")
    print(
        "[white]= [#f9487d]ComicFuz-Extractor [#00BFFF]made with [red]:red_heart-emoji: [#00BFFF]by EnkanRec Repaired "
        "[white]and [#00BFFF]Modified and repair by misaka10843[white]=")
    os.makedirs(args.output_dir, exist_ok=True)

    token = get_session(args.token_file, args.user_email, args.password)
    que = Queue(args.n_jobs)
    Thread(target=worker, args=(que,), daemon=True).start()
    downloaded_path = ""
    if args.book:
        if ',' in args.book:
            string_list = args.book.split(',')
            for item in string_list:
                downloaded_path = down_book(args.output_dir, int(item), token, que)
                print(f"[bold green]正在等待10s后继续下载")
                time.sleep(10)
        else:
            downloaded_path = down_book(args.output_dir, int(args.book), token, que)
    if args.magazine:
        if ',' in args.magazine:
            string_list = args.magazine.split(',')
            for item in string_list:
                downloaded_path = down_magazine(args.output_dir, int(item), token, que)
                print(f"[bold green]正在等待10s后继续下载")
                time.sleep(10)
        else:
            downloaded_path = down_magazine(args.output_dir, int(args.magazine), token, que)
    if args.manga:
        if ',' in args.manga:
            string_list = args.manga.split(',')
            for item in string_list:
                downloaded_path = down_manga(args.output_dir, int(item), token, que)
                print(f"[bold green]正在等待10s后继续下载")
                time.sleep(10)
        else:
            downloaded_path = down_manga(args.output_dir, int(args.manga), token, que)
    if args.compression:
        compression(args.compression, downloaded_path, args.output_dir, args.quality, args.keepog)
    logging.debug("Done.")


def sign(email: str, password: str) -> str:
    body = fuz_pb2.SignInRequest()
    body.deviceInfo.deviceType = fuz_pb2.DeviceInfo.DeviceType.BROWSER
    body.email = email
    body.password = password
    url = API_HOST + "/v1/sign_in"
    req = Request(url, body.SerializeToString(), method="POST")
    try:
        with urlopen.open(req) as r:
            res = fuz_pb2.SignInResponse()
            res.ParseFromString(r.read())
            if not res.success:
                logging.error("Login failed")
                exit(1)
            for header in r.headers:
                m = re.match(r'fuz_session_key=(\w+)(;.*)?', r.headers[header])
                if m:
                    return m.group(1)
    except Exception as e:
        console.print_exception(show_locals=True)
        exit()


def check_sign(token: str) -> bool:
    url = API_HOST + "/v1/web_mypage"
    headers = {
        "user-agent": USER_AGENT,
        "cookie": COOKIE + token
    }
    req = Request(url, headers=headers, method="POST")
    try:
        with urlopen.open(req) as r:
            res = fuz_pb2.WebMypageResponse()
            res.ParseFromString(r.read())
            if res.mailAddress:
                print(f"[#FFB6C1]Login as: {res.mailAddress}")
                return True
            return False
    except Exception as e:
        console.print_exception(show_locals=True)
        exit()


def get_session(file: str, user: str, pwd: str) -> str:
    if not file and not user:
        logging.info("Disable login, get only free part.")
        return ""
    if file and os.path.exists(file):
        with open(file) as f:
            token = f.read().strip()
        if check_sign(token):
            return token
        logging.debug("Get failed, try signing")
    user = user if user else input("您的邮箱: ")
    pwd = pwd if pwd else getpass.getpass("您的密码: ")
    token = sign(user, pwd)
    try:
        with open(file, "w") as f:
            f.write(token)
        print(f"[bold green]您的token已经存放到{file}中，请妥善保管")
        return token
    except Exception as e:
        console.print_exception(show_locals=True)
        console.print(
            "\n[bold yellow]自动获取token出错！\n请如果输出fuz_session_key类似的内容，请从fuz_session_key=开始复制("
            "不包含fuz_session_key=)到第一个分号(;)\n然后存入-t指定的文件中")
        exit()


def b64_to_10(s: str) -> int:
    i = 0
    for c in s:
        i = i * 64 + T_MAP[c]
    return i


def get_index(path: str, body: str, token: str) -> str:
    url = API_HOST + path
    headers = {"user-agent": USER_AGENT}
    if token:
        headers["cookie"] = COOKIE + token
    req = Request(url, body, headers, method="POST")
    try:
        with urlopen.open(req) as r:
            return r.read()
    except Exception as e:
        console.print_exception(show_locals=True)
        console.print("\n[bold red]获取相关信息出错！\n请检查ID参数是否正确！\n或者稍后重试")
        exit()


def get_book_index(book_id: int, token: str) -> fuz_pb2.BookViewer2Response:
    body = fuz_pb2.BookViewer2Request()
    body.deviceInfo.deviceType = fuz_pb2.DeviceInfo.DeviceType.BROWSER
    body.bookIssueId = book_id
    body.viewerMode.imageQuality = fuz_pb2.ViewerMode.ImageQuality.HIGH

    res = get_index("/v1/book_viewer_2", body.SerializeToString(), token)
    index = fuz_pb2.BookViewer2Response()
    index.ParseFromString(res)
    return index


def get_magazine_index(magazine_id: int, token: str) -> fuz_pb2.MagazineViewer2Response:
    body = fuz_pb2.MagazineViewer2Request()
    body.deviceInfo.deviceType = fuz_pb2.DeviceInfo.DeviceType.BROWSER
    body.magazineIssueId = magazine_id
    body.viewerMode.imageQuality = fuz_pb2.ViewerMode.ImageQuality.HIGH

    res = get_index("/v1/magazine_viewer_2", body.SerializeToString(), token)
    index = fuz_pb2.MagazineViewer2Response()
    index.ParseFromString(res)
    return index


def get_manga_index(manga_id: int, token: str) -> fuz_pb2.MangaViewerResponse:
    body = fuz_pb2.MangaViewerRequest()
    body.deviceInfo.deviceType = fuz_pb2.DeviceInfo.DeviceType.BROWSER
    body.chapterId = manga_id
    body.viewerMode.imageQuality = fuz_pb2.ViewerMode.ImageQuality.HIGH

    res = get_index("/v1/manga_viewer", body.SerializeToString(), token)
    index = fuz_pb2.MangaViewerResponse()
    index.ParseFromString(res)
    return index


def download_thumb(save_dir: str, url: str, overwrite=False):
    name = re.match(r'.*/([0-9a-zA-Z_-]+)\.(\w+)\?.*', url)
    if not name or not name.group(1):
        print("Can't gass filename: ", url)
        return
    name = f"{save_dir}{b64_to_10(name.group(1))}.{name.group(2)}"
    if not overwrite and os.path.exists(name):
        return
    with open(name, "wb") as f:
        with urlopen.open(IMG_HOST + url) as r:
            f.write(r.read())
    # os.system(f"curl -s \"{IMG_HOST}{url}\" -o {name}")


def download(save_dir: str, image: fuz_pb2.ViewerPage.Image, overwrite=False):
    if not image.imageUrl:
        logging.debug("Not an image: %s", image)
        return
    name = re.match(r'.*/([0-9a-zA-Z_-]+)\.(\w+)\.enc\?.*', image.imageUrl)
    if not name or not name.group(1):
        logging.debug("Can't gass filename: %s", image)
        return
    name_num = "%03d" % b64_to_10(name.group(1))
    name = f"{save_dir}{name_num}.{name.group(2)}"
    if not overwrite and os.path.exists(name):
        logging.debug("Exists, continue: %s", name)
        return
    try:
        with urlopen.open(IMG_HOST + image.imageUrl) as r:
            data = r.read()
    except Exception as e:
        time.sleep(5)
        with urlopen.open(IMG_HOST + image.imageUrl) as r:
            data = r.read()
    key = bytes.fromhex(image.encryptionKey)
    iv = bytes.fromhex(image.iv)
    decryptor = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    out = decryptor.update(data) + decryptor.finalize()
    with open(name, "wb") as f:
        f.write(out)
    # os.system(f"curl -s \"{IMG_HOST}{image.imageUrl}\" | openssl aes-256-cbc -d -K {image.encryptionKey} -iv {
    # image.iv} -in - -out {name}")
    logging.debug("Downloaded: %s", name)


def down_pages(
        save_dir: str,
        data,  # : fuz_pb2.BookViewer2Response | fuz_pb2.MagazineViewer2Response | fuz_pb2.MangaViewerResponse,
        que: Queue,
        book_name: str
):
    os.makedirs(save_dir, exist_ok=True)
    with open(save_dir + "index.protobuf", "wb") as f:
        f.write(data.SerializeToString())
    with open(save_dir + "index.json", "w", encoding='utf-8') as f:
        json.dump(json_format.MessageToDict(data),
                  f, ensure_ascii=False, indent=4)

    # downloadThumb(save_dir, data.bookIssue.thumbnailUrl)

    for page in track(data.pages, description=f"[bold yellow]正在下载:{book_name}[/]"):
        t = Thread(target=download, name=page.image.imageUrl,
                   args=(save_dir, page.image))
        t.start()
        # download(save_dir, page)
        que.put(t)
    que.join()


def down_book(out_dir: str, book_id: int, token: str, que: Queue):
    book = get_book_index(book_id, token)
    book_issue_id = str(book.bookIssue.bookIssueId)
    down_pages(
        f"{out_dir}/{has_numbers(str(book.bookIssue.bookIssueName))}/", book, que,
        f"[{book_issue_id}]{book.bookIssue.bookIssueName}")
    print(
        f"[bold green]{has_numbers(str(book.bookIssue.bookIssueName))}下载完成！如果下载时遇见报错，请重新运行一下命令即可")
    return f"{has_numbers(str(book.bookIssue.bookIssueName))}"


def down_magazine(out_dir: str, magazine_id: int, token: str, que: Queue):
    magazine = get_magazine_index(magazine_id, token)
    magazine_name = str(magazine.magazineIssue.magazineName)
    if magazine_name == 'まんがタイムきらら':
        magazine_name = "Kirara"
    elif magazine_name == 'まんがタイムきららMAX':
        magazine_name = "Max"
    elif magazine_name == 'まんがタイムきららキャラット':
        magazine_name = "Carat"
    elif magazine_name == 'まんがタイムきららフォワード':
        magazine_name = "Forward"
    down_pages(
        f"{out_dir}/{magazine_name}{has_numbers(str(magazine.magazineIssue.magazineIssueName))}/", magazine, que,
        f"[{magazine_name}]{magazine.magazineIssue.magazineIssueName}[/]")
    print(
        f"[bold green]{has_numbers(str(magazine.magazineIssue.magazineIssueName))}下载完成！如果下载时遇见报错，请重新运行一下命令即可")
    return f"{magazine_name}{has_numbers(str(magazine.magazineIssue.magazineIssueName))}"


def down_manga(out_dir: str, manga_id: int, token: str, que: Queue):
    manga = get_manga_index(manga_id, token)
    down_pages(f"{out_dir}/m{manga_id}/", manga, que, f"[{manga_id}]{manga.viewerTitle}[/]")
    print(f"[bold green]{manga.viewerTitle}下载完成！如果下载时遇见报错，请重新运行一下命令即可")
    return f"m{manga_id}"


def has_numbers(chat):
    res_list = [str(int(i)) if i.isdigit() else i for i in chat]
    return "".join(res_list)


def compression(com_type: int, download_dir: str, out_dir: str, im_quality: int, save_og: int):
    print("[bold yellow]正在进行压缩中...")
    all_run = False
    if com_type == 3:
        all_run = True
    if com_type == 2 or all_run is True:
        if save_og == 1 or save_og == 2:
            source_path = os.path.abspath(fr'{out_dir}/{download_dir}')
            target_path = os.path.abspath(fr'{out_dir}/{download_dir}_og')
            if not os.path.exists(target_path):
                # 如果目标路径不存在原文件夹的话就创建
                os.makedirs(target_path)
            if os.path.exists(source_path):
                # 如果目标路径存在原文件夹的话就先删除
                shutil.rmtree(target_path)
            shutil.copytree(source_path, target_path)
            print(f'[bold green]已经将所有原文件复制到{out_dir}/{download_dir}_og中，准备开始图片压缩')
        with console.status(f"[bold yellow]正在将{download_dir}中的图片压缩"):
            file_list = os.listdir(f'{out_dir}/{download_dir}')
            for i in file_list:
                # 判断是否为comic fuz中的特殊(也并不特殊)的后缀
                if os.path.splitext(i)[1] == '.jpeg':
                    imName = i.split('.')[0]
                    im = Image.open(f"{out_dir}/{download_dir}/{i}")
                    im.save(f"{out_dir}/{download_dir}/{imName}.jpg", quality=im_quality)
                    os.remove(f"{out_dir}/{download_dir}/{i}")
        print("[bold green]已经将所有图片压缩完毕")

    if com_type == 1 or all_run is True:
        with console.status(f"[bold yellow]正在将{download_dir}压缩成7z中"):
            with py7zr.SevenZipFile(f'{out_dir}/{download_dir}.7z', 'w') as archive:
                archive.writeall(f"{out_dir}/{download_dir}")
        print(f"[bold green]已经将图片打包压缩到{out_dir}/{download_dir}.7z")
    # 进行压缩
    if save_og == 2:
        with console.status(f"[bold yellow]正在将{download_dir}的原图压缩成7z中"):
            with py7zr.SevenZipFile(f'{out_dir}/{download_dir}_og.7z', 'w') as archive:
                archive.writeall(f"{out_dir}/{download_dir}_og")
        print(f"[bold green]已经将原图打包压缩到{out_dir}/{download_dir}_og.7z")


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-t',
        '--token-file',
        metavar='<Token文件路径>',
        help="Token文件路径（不指定此参数则不读入或保存Token）")
    parser.add_argument(
        '-u',
        '--user-email',
        metavar='<用户email>',
        help="用户email，不填且无Token的话会以游客身份登录")
    parser.add_argument(
        '-p',
        '--password',
        metavar='<密码>',
        nargs='?',
        help="密码可直接由命令行参数传入；不传入的话，如果指定了用户名（`-u`），将会询问")
    parser.add_argument(
        '-o',
        '--output-dir',
        metavar='<输出路径>',
        default=".",
        help="输出目录（默认当前目录）")
    parser.add_argument(
        '-j',
        '--n-jobs',
        metavar='<并行线程数>',
        type=int,
        default=16,
        help="并行线程数（默认16）")
    parser.add_argument(
        '-b',
        '--book',
        metavar='<BookId>',
        type=str,
        help="目标单行本Id")
    parser.add_argument(
        '-m',
        '--manga',
        metavar='<MangaId>',
        type=str,
        help="目标漫画Id")
    parser.add_argument(
        '-z',
        '--magazine',
        metavar='<MagazineId>',
        type=str,
        help="目标杂志Id")
    parser.add_argument(
        '-v',
        '--verbose',
        action="store_true",
        help="打印调试输出")
    parser.add_argument(
        '-y',
        '--proxy',
        metavar='<ip:port>',
        type=str,
        help="设置程序代理(http代理)")
    parser.add_argument(
        '-c',
        '--compression',
        metavar='<1/2/3>',
        type=int,
        help="使用7z与ffmpeg压缩图片(1为仅生成压缩包,2为仅使用PIL压缩图片,3为两者都使用)")
    parser.add_argument(
        '-k',
        '--keepog',
        metavar='<0/1/2>',
        default=0,
        type=int,
        help="是否保留原图片(默认不保留，1为保留，2为保留并压缩，0为不保留)")
    parser.add_argument(
        '-q',
        '--quality',
        metavar='<quality number>',
        type=int,
        default=80,
        help="设置压缩图片的质量(越高文件越大,默认80)")
    return parser


def worker(que: Queue):
    count = 0
    while True:
        item = que.get()
        count += 1
        item.join()
        # logging.debug("[%d] ok.", count)
        que.task_done()


main()
