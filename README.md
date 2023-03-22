![qwq](./repository-open-graph-template.png)

## 简介

使用python来下载Comic-fuz中的漫画/单行本/杂志！

### 一些运行截图

![image.png](https://s2.loli.net/2023/02/19/deW4goM2pNfJlqS.png)
![image.png](https://s2.loli.net/2023/02/19/PdabVKxiqu3j2Az.png)
![image.png](https://s2.loli.net/2023/03/19/3salmTkZ4GEvgBV.png)

## 支持功能

* 漫画/单行本/杂志多线程下载
* 使用代理
* 自定义线程数量
* 自定义下载文件夹
* 支持登录
* 支持自动压缩图片(可自定义压缩率)/生成压缩包

如需其他功能可以在Issue中提出！

## Dependence

```bash
cryptography
protobuf
retrying
rich
pillow
py7zr
```

## 如何使用

```bash
$ python main.py --help                                                       
usage: main.py [-h] [-t <Token文件路径>] [-u <用户email>] [-p [<密码>]] [-o <输出路径>] [-j <并行线程数>] [-b <BookId>] [-m <MangaId>] [-z <MagazineId>] [-v] [-y <ip:port>] [-c <1/2/3>] [-k <0/1/2>] [-q <quality number>]

options:
  -h, --help            show this help message and exit
  -t <Token文件路径>, --token-file <Token文件路径>
                        Token文件路径（不指定此参数则不读入或保存Token）
  -u <用户email>, --user-email <用户email>
                        用户email，不填且无Token的话会以游客身份登录
  -p [<密码>], --password [<密码>]
                        密码可直接由命令行参数传入；不传入的话，如果指定了用户名（`-u`），将会询问
  -o <输出路径>, --output-dir <输出路径>
                        输出目录（默认当前目录）
  -j <并行线程数>, --n-jobs <并行线程数>
                        并行线程数（默认16）
  -b <BookId>, --book <BookId>
                        目标单行本Id
  -m <MangaId>, --manga <MangaId>
                        目标漫画Id
  -z <MagazineId>, --magazine <MagazineId>
                        目标杂志Id
  -v, --verbose         打印调试输出
  -y <ip:port>, --proxy <ip:port>
                        设置程序代理(http代理)
  -c <1/2/3>, --compression <1/2/3>
                        使用7z与ffmpeg压缩图片(1为仅生成压缩包,2为仅使用PIL压缩图片,3为两者都使用)
  -k <0/1/2>, --keepog <0/1/2>
                        是否保留原图片(默认不保留，1为保留，2为保留并压缩，0为不保留)
  -q <quality number>, --quality <quality number>
                        设置压缩图片的质量(越高文件越大,默认80)


```

### 命令示例

`fuz_down -t token.txt -m 2443 -y 127.0.0.1`

`python .\main.py -t token.txt -y 127.0.0.1:7890 -j 64 -z 26235`

`python main.py -t token.txt -y 127.0.0.1:7890 -j 64 -b 26001 -c 3 -q 60 -k 2`

### 注意

一般情况下，只需要传入 `-t token.txt`即可，无需传入用户邮箱与密码，如果指定的token文件为空，程序会自动向您索取邮箱与密码！

线程数请不要超过64，防止fuz服务器拒绝连接（如果一次性下载多个请减少至16）

如果您需要源码运行，请自行下载[Releases · protocolbuffers/protobuf (github.com)](https://github.com/protocolbuffers/protobuf/releases) 然后运行 `protoc fuz.proto --python_out .`构建API解析py后再进行正常运行（虽然已经附带了`fuz_pb2.py`）

如果您不想配置环境，可以从[releases](https://github.com/misaka10843/ComicFuz-Down/releases/)中下载供Windows的程序，或者可以下载[自动构建版本](https://github.com/misaka10843/ComicFuz-Down/actions/)，请选择最新一次打上绿勾的版本

### 如何获取ID

从url获取漫画/书籍/杂志id。

* `https://comic-fuz.com/manga/1902` -- `1902`
* `https://comic-fuz.com/book/25120` -- `25120`
* `https://comic-fuz.com/magazine/25812` -- `25812`

![image.png](https://s2.loli.net/2023/03/19/Z1OPVb5Ey7tTuka.png)

## 常见问题

### Q1：下载时报错

如果您在下载的时候已经输出了类似以下的文字后

```bash
= ComicFuz-Extractor made with ♡ by EnkanRec Repaired and Modified by misaka10843=
Login as: xxxxxx@126.com
[Max]２０２３年３月号
```

出现了以下类似的报错

```python
  File ".\fuz_down.py", line 194, in download
    result = func(*args)
    with urlopen.open(IMG_HOST + image.imageUrl) as r:
  File "D:\PL\Python\Python38\lib\urllib\request.py", line 1397, in https_open
  File "D:\PL\Python\Python38\lib\urllib\request.py", line 525, in open
    response = self._open(req, data)
  File "D:\PL\Python\Python38\lib\urllib\request.py", line 542, in _open
    return self.do_open(http.client.HTTPSConnection, req,
  File "D:\PL\Python\Python38\lib\urllib\request.py", line 1357, in do_open
    result = self._call_chain(self.handle_open, protocol, protocol +
  File "D:\PL\Python\Python38\lib\urllib\request.py", line 502, in _call_chain
    raise URLError(err)
urllib.error.URLError: <urlopen error [Errno 2] No such file or directory>
    result = func(*args)
  File "D:\PL\Python\Python38\lib\urllib\request.py", line 1397, in https_open
    return self.do_open(http.client.HTTPSConnection, req,
  File "D:\PL\Python\Python38\lib\urllib\request.py", line 1357, in do_open
    raise URLError(err)
urllib.error.URLError: <urlopen error [Errno 2] No such file or directory>
```

请重新运行一次你刚刚运行的命令，这似乎是因为**线程太多或者短时间内防蚊次数过多**导致一些图片并未下载，重新运行后，程序会自动识别是否下载，然后进行补充下载(如果使用了图片压缩，可能需要重新下载，如果启动图片压缩并备份了原图，请删除压缩后的文件夹并将原图文件夹后面的_og删除再重新运行)

## More

原分支仓库：[EnkanRec/ComicFuz-Down](https://github.com/EnkanRec/ComicFuz-Down)

`.proto` is rebuild with reading form [Official protobuf in js](https://comic-fuz.com/_next/static/chunks/pages/_app-b24da103ab4a3f25b6bc.js)

自动构建程序icon：[xuzhengyi1995](https://github.com/xuzhengyi1995)/**[Comic-fuz-Downloader](https://github.com/xuzhengyi1995/Comic-fuz-Downloader)**

[tampermonkey script by CircleLiu](https://github.com/CircleLiu/Comic-Fuz-Downloader)
