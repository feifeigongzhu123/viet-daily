# 越词通 · VietDaily

> 作者：**安得半日闲** · 当前版本：**1.2.0**

每天学几个越南语单词的安卓可用 PWA。当前词库 **1016 个词**：

- **65 个《越南语123》入门词**：第 1、2、3、4、5、10、12、13、14 课主题
- **951 个通用高频词**：1000mostcommonwords.com 常用词去重 + 日常补充词

每个词都有：

- 越南语拼写、中文释义
- 河内音 IPA 音标
- 近似读音（教材词为中文谐音，通用词为自动拼音近似）
- 越南语例句 + 中文翻译
- 预生成的越南语标准发音（每个词一条，例句也有一条）
- 出处：教材词标《越南语123》课次，通用词标“通用高频词表”

打开即学，不需要登录，学习进度只存在本机。安装到安卓桌面后可离线使用。

## 主要功能

- **每日推荐**：默认每天 5 个词，可切换 3 / 5 / 8 个
- **间隔复习**：按 3、7、15、30、60、120、240 天安排复习；选“还不熟”则明天再练
- **今日计划**：先安排到期的复习词，再补新词；完成后可继续加词
- **词库**：1016 个词；教材词按课次归组、通用词按首字母归组，“不熟”单独归类
- **自动播放**：在词库中顺序播放单词；可按“不熟”分类顺序播放加强
- **语音**：独立“语音”页，包含 12 个元音、27 个辅音、6 个声调，字母音可朗读
- **显示大小**：紧凑 / 标准 / 宽屏三档；滚动后“还不熟 / 记住了”出现在导航栏上方
- **发音**：2077 条音频：1016 个单词 + 1016 条例句 + 45 条语音基础示例，支持 0.7× 慢速
- **离线**：Service Worker 缓存应用和全部 2077 条音频
- **进度**：连续学习天数、已学/已掌握/待复习、最近 7 天柱状图
- **安装**：Chrome 安卓端可添加到主屏幕，独立窗口运行

## 最快的安卓使用方法

### 方式 A：部署到静态网站（推荐，能安装、能离线）

1. 把整个 `vocab-daily` 文件夹上传到任意静态托管：
   - [Netlify Drop](https://app.netlify.com/drop)：把文件夹拖进去即可得到网址
   - GitHub Pages、Cloudflare Pages、Vercel 也可以
2. 用安卓 Chrome 打开这个网址。
3. 点右上角菜单 → **添加到主屏幕 / 安装应用**。
4. 首次打开会在后台缓存应用和音频，之后断网也能学。

> 安装和 Service Worker 需要 HTTPS（`localhost` 除外）。通过局域网 IP 的普通 HTTP 只能浏览，不能完整安装。

### 方式 B：电脑上本地预览

Windows 双击 `start-server.bat`，或：

```bash
python scripts/serve.py
```

然后打开：

- 电脑：`http://127.0.0.1:8765/`
- 手机：脚本会打印同一 Wi-Fi 下的局域网地址

局域网 HTTP 适合快速看效果；要装到手机桌面，请用方式 A 的 HTTPS 部署。

### 方式 C：打包成 APK（可选）

PWA 本身已经能安装到安卓桌面。如果一定要 APK：

1. 先按方式 A 部署，拿到 HTTPS 网址。
2. 用 [PWABuilder](https://www.pwabuilder.com/) 输入网址，生成 Android 包；或使用 Bubblewrap：
   ```bash
   npm i -g @bubblewrap/cli
   bubblewrap init --manifest https://你的网址/manifest.webmanifest
   bubblewrap build
   ```
3. 签名后安装 APK。

> 我没有在你的电脑上签名或编译 APK；当前交付的是可直接部署的 PWA 源码。

## GitHub Pages 与 APK

从零上传 GitHub、开启 Pages、用 PWABuilder/Bubblewrap 打 APK 的完整步骤见：[GITHUB_APK_GUIDE.md](GITHUB_APK_GUIDE.md)。

## 项目结构

```text
vocab-daily/
├── .gitignore
├── .nojekyll
├── GITHUB_APK_GUIDE.md
├── COPYRIGHT.md
├── THIRD_PARTY_NOTICES.md
├── CHANGELOG.md
├── VERSION
├── index.html
├── app.css
├── app.js
├── manifest.webmanifest
├── sw.js
├── data/
│   ├── words.json              # 最终词表（教材词 + 通用词）
│   ├── words.js                # 由 build.py 生成，供页面直接加载
│   ├── words.textbook.json     # 原始 65 个教材词备份
│   ├── phonetics.json          # 元音、辅音、声调内容
│   ├── phonetics.js            # 由 build.py 生成
│   ├── general/                # 通用词源、补充词与构建缓存
│   └── tatoeba/                # Tatoeba 越南语句库（例句来源）
├── audio/
│   ├── words/                  # 1016 条单词 MP3
│   ├── examples/               # 1016 条例句 MP3
│   ├── phonetics/              # 45 条语音基础示例 MP3
│   └── index.json              # 离线缓存清单
├── icons/                      # PWA 图标
├── scripts/
│   ├── build.py                # 校验词表、生成 words.js 和图标
│   ├── build_general_pack.py   # 生成通用高频词包
│   ├── generate_audio.py       # 用 Edge TTS 生成越南语音频
│   ├── check.py                # 检查 JS 语法和音频完整性
│   ├── check_tones.py          # 检查教材词声调与 IPA 是否一致
│   ├── audio_report.py         # 检查全部 MP3 的时长和可读性
│   └── serve.py                # 本地预览服务器
├── start-server.bat
└── start-server.sh
```

## 修改词表

`data/words.json` 是最终词表。每个词至少包含：

```json
{
  "id": "b1-chao",
  "word": "chào",
  "pos": "动词",
  "ipa": "tɕaːw˨˩",
  "homophone": "照 zhào（低降）",
  "meaning": "问候；你好",
  "example": "Chào bạn!",
  "exampleZh": "你好！",
  "lesson": 1,
  "topic": "问候",
  "source": "《越南语123》第1课",
  "tip": "可选的发音提示"
}
```

修改后运行：

```bash
python scripts/build.py          # 更新 data/words.js 和图标
python scripts/check.py          # 检查 JS 语法、音频文件是否齐全
python scripts/check_tones.py    # 检查教材词的声调与 IPA
python scripts/audio_report.py   # 检查全部 MP3
```

新增或修改了越南语文本后，重新生成音频：

```bash
python -m pip install edge-tts
python scripts/generate_audio.py
```

最后把 `sw.js` 里的 `CACHE` 版本号改一下（例如 `vietdaily-v2.0.0`），否则已经安装过的用户会继续用旧缓存。

### 重新生成通用词包

```bash
python scripts/build_general_pack.py --target 1050
```

它会读取 `data/general/common1000.html` 和 `data/general/extra_words.txt`，查询开放词典/翻译缓存，合并 `data/words.textbook.json`，重新写出 `data/words.json`。缓存文件在 `data/general/`。

## 显示大小与屏幕适配

在“我的 → 学习设置 → 显示大小”里可以选择：

- **紧凑**：小屏手机优先，字号、间距和卡片高度更小
- **标准**：默认布局
- **宽屏**：平板/桌面使用，最大宽度 720px；卡片限宽 600px，词库在宽屏下两列显示

“还不熟 / 记住了”不再常显：页面顶部只展示单词内容；向下滚动后，这组按钮才出现在底部导航栏上方。界面本身会根据 320 / 360 / 390 / 430px 等宽度自动换行。

## 音标与发音说明

- **教材词**使用人工标注的河内音宽式 IPA；**通用词**的 IPA 主要来自 `dict.minhqnd.com` 开放词典，部分为自动生成。
- 中文谐音只能近似，不能准确表达越南语的声调、长短音和内爆音，请以音频和 IPA 为准。
- 通用词的“谐音”是自动拼音近似，准确度低于教材词，只作辅助。
- `đ` 是内爆音 `/ɗ/`，`b` 是 `/ɓ/`；`d`、`gi`、`r` 在河内音中接近 `/z/`；`ch` 接近 `/tɕ/`。
- 音频由 Microsoft Edge 神经网络语音 `vi-VN-HoaiMyNeural` 生成，是标准北方越南语发音。

调符对照（教材词）：

| 调符 | 声调 | 例子 |
|---|---|---|
| ˧ | 平声 ngang | ma |
| ˨˩ | 玄声 huyền | mà |
| ˧˥ | 锐声 sắc | má |
| ˧˩˧ | 问声 hỏi | mả |
| ˧ˀ˥ | 跌声 ngã | mã |
| ˧ˀ˩ | 重声 nặng | mạ |

## 词表与数据出处

### 教材词（65 个）

按以下公开课次页面中的主题词汇整理，**不是教材完整词表**，也未复制教材全文：

- [第 1 课 · Tên tôi là Peter](https://chinese.edu.vn/bai-1-sach-tieng-viet-123-danh-cho-nguoi-trung-quoc-ten-toi-la-peter.html)
- [第 2 课 · Tôi là giáo viên](https://chinese.edu.vn/bai-2-sach-tieng-viet-123-danh-cho-nguoi-trung-quoc-toi-la-giao-vien.html)
- [第 3 课 · Anh bao nhiêu tuổi](https://chinese.edu.vn/bai-3-sach-tieng-viet-123-danh-cho-nguoi-trung-quoc-anh-bao-nhieu-tuoi.html)
- [第 4 课 · Nhà của anh rất đẹp](https://chinese.edu.vn/bai-4-sach-tieng-viet-123-danh-cho-nguoi-trung-quoc-nha-cua-anh-rat-dep.html)
- [第 5 课 · Cái này bao nhiêu tiền](https://chinese.edu.vn/bai-5-sach-tieng-viet-123-danh-cho-nguoi-trung-quoc-cai-nay-bao-nhieu-tien.html)
- [第 10 课 · Anh đi thẳng đường này](https://chinese.edu.vn/bai-10-sach-tieng-viet-123-danh-cho-nguoi-trung-quoc-anh-di-thang-duong-nay.html)
- [第 12 课 · Quyển sách ở trên bàn](https://chinese.edu.vn/bai-12-sach-tieng-viet-123-danh-cho-nguoi-trung-quoc-quyen-sach-o-tren-ban.html)
- [第 13 课 · Cho chúng tôi xem thực đơn](https://chinese.edu.vn/bai-13-sach-tieng-viet-123-danh-cho-nguoi-trung-quoc-cho-chung-toi-xem-thuc-don.html)
- [第 14 课 · Hôm nay trời nắng và nóng](https://chinese.edu.vn/bai-14-sach-tieng-viet-123-danh-cho-nguoi-trung-quoc-hom-nay-troi-nang-va-nong.html)

教材信息：《越南语123》（*Tiếng Việt 123*），123VIETNAMESE 编写，世界出版社出版，面向中文母语学习者。

### 通用高频词（951 个）

- 频率列表：[1000 Most Common Vietnamese Words](https://1000mostcommonwords.com/1000-most-common-vietnamese-words/)（去重后 843 个）
- 日常补充词：`data/general/extra_words.txt`
- IPA、词性、部分例句参考：[dict.minhqnd.com](https://dict.minhqnd.com) 开放词典，数据许可 **CC BY-SA 4.0**
- 中文释义：开放词典条目 + MyMemory/Edge 机器翻译，再用人工规则修正
- 例句：[Tatoeba](https://tatoeba.org) 越南语句库（CC BY 2.0 FR），每条保留 Tatoeba 句子 ID；中文由 Edge 翻译。常用词另有手写例句，少数没有语料时使用简单的按词性句型
- 通用词中文谐音为自动拼音近似，仅供辅助

如果再次分发通用词数据，请保留对 `dict.minhqnd.com` 的署名，并遵守 CC BY-SA 4.0；1000mostcommonwords.com 列表的使用条件请自行确认。

## 版权与许可

- 作者：**安得半日闲**
- 当前版本：**1.2.0**（见 `VERSION`、`CHANGELOG.md`）
- 原创代码、界面、原创文字和编排：© 2026 安得半日闲，保留所有权利。详见 [COPYRIGHT.md](COPYRIGHT.md)。
- 第三方词表、Tatoeba 例句、开放词典数据和 Edge 语音服务的许可与署名：详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。

### 著作权如何固定证据

著作权通常在作品完成时自动产生。为了在发生争议时更容易证明归属，建议：

1. 保留 Git 提交历史、源文件、设计稿和早期版本的原始时间记录。
2. 对发布版本计算 SHA-256 哈希并保存，或使用可信时间戳服务。
3. 需要更强证明时，可向中国版权保护中心申请计算机软件著作权登记。
4. 公开仓库保留 `COPYRIGHT.md`、作者署名和第三方许可说明；没有许可证不等于放弃权利。

> 以上为一般性说明，不构成法律意见；正式商用前请咨询专业律师或版权登记机构。

## 已知限制

- 通用词的中文释义是机器翻译整理，可能有个别义项不够准确，重要用法请再查词典。
- 通用词例句大部分来自 Tatoeba 真实语料，中文为机器翻译；少数为生成句，可能不如教材例句自然。
- 教材 65 个词保留真实例句和音频。
- 没有账号和云同步，清除浏览器数据会丢失进度。
- 没有推送通知；每天的计划在打开应用时按日期更新。
- 没有语音识别/跟读评分。
- 当前是 PWA，不是已签名的 APK；APK 需要自行用 PWABuilder/Bubblewrap 打包。
- 音频是机器生成的神经语音，适合学习但不替代真人纠音；商业使用前请自行确认语音服务条款。

## 隐私

所有学习进度保存在浏览器 `localStorage`，不上传到任何服务器；应用没有后端、没有统计脚本、没有账号系统。
