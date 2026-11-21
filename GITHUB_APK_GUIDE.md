# 上传 GitHub 与后续打包 APK

这份说明按 Windows 操作写。当前工程已经有：

- `index.html` 在仓库根目录，适合 GitHub Pages 直接部署
- `.nojekyll`，避免 GitHub Pages 用 Jekyll 处理静态资源
- `manifest.webmanifest`、Service Worker、1016 个词、2077 条音频

> 上架文案、截图、功能图和数据安全表单见 [store/README.md](store/README.md)。

> 本机目前没有安装 `git` 和 `gh`。下面第一步会安装 Git；上传时需要登录你的 GitHub 账号。

## 一、安装 Git

任选一种：

1. 官网下载：[Git for Windows](https://git-scm.com/download/win)
2. 或 PowerShell 安装：

```powershell
winget install --id Git.Git -e --source winget
```

安装后重新打开终端，确认：

```powershell
git --version
```

## 二、在 GitHub 新建仓库

1. 登录 GitHub。
2. 右上角 **+ → New repository**。
3. 仓库名填 `viet-daily`（也可以叫 `vocab-daily`）。
4. 选择 **Public**（免费 GitHub Pages 需要公开仓库）。
5. **不要**勾选 “Add a README file”，保持空仓库。
6. 点 **Create repository**。

## 三、把本地工程推上去

在 Windows 终端执行（把 `YOUR_NAME` 换成你的 GitHub 用户名）：

```bat
cd /d D:\AI\ZCode\vocab-daily

git init
git add .
git commit -m "VietDaily: 1016-word Vietnamese vocabulary PWA"

git branch -M main
git remote add origin https://github.com/YOUR_NAME/viet-daily.git
git push -u origin main
```

第一次 `push` 会弹出 GitHub 登录窗口。推荐用浏览器登录（Git Credential Manager）；也可以在 GitHub 生成 Personal Access Token，在密码位置填 token。

### 如果不想装 Git

GitHub 网页端也能 **Add file → Upload files**，把整个工程文件拖进去。但这里有 2000+ 个文件，网页上传很慢，仍建议用 Git。

## 四、开启 GitHub Pages

1. 打开仓库 **Settings → Pages**。
2. **Build and deployment → Source** 选 **Deploy from a branch**。
3. Branch 选 `main`，目录选 `/(root)`，点 **Save**。
4. 等 1–3 分钟，访问：

```text
https://YOUR_NAME.github.io/viet-daily/
```

如果 404：

- 确认 `index.html` 在仓库根目录，不是套了一层 `vocab-daily/` 目录
- 确认仓库 Settings → Pages 显示已发布
- 确认仓库是 Public（私有仓库的 Pages 通常需要付费计划）

## 五、安卓手机安装 PWA

1. 安卓 Chrome 打开 `https://YOUR_NAME.github.io/viet-daily/`
2. 等页面加载完，首次会后台缓存约 22 MB 音频
3. Chrome 右上角菜单 → **安装应用 / 添加到主屏幕**
4. 之后断网也能打开已缓存的词和音频

## 六、打包 APK：推荐用 PWABuilder

PWA 部署好、HTTPS 能打开后：

1. 打开 [PWABuilder](https://www.pwabuilder.com/)
2. 输入网址：

```text
https://YOUR_NAME.github.io/viet-daily/
```

3. 选择 **Package for stores → Android**
4. 建议选 **Trusted Web Activity (TWA)**，包名例如：

```text
com.yourname.vietdaily
```

5. 应用名填「越词通」，生成并下载 Android 包。
6. 下载内容里通常包含：
   - APK / AAB
   - 签名密钥（务必保存好）
   - `assetlinks.json`

### 关键：assetlinks.json 放在哪里

TWA 需要验证网站和 APK 的归属，文件必须能从**域名根目录**访问：

```text
https://YOUR_NAME.github.io/.well-known/assetlinks.json
```

注意：不是 `.../viet-daily/.well-known/...`。

如果应用放在 `https://YOUR_NAME.github.io/viet-daily/`，可以再建一个仓库：

```text
YOUR_NAME.github.io
```

把 `assetlinks.json` 放到这个仓库的：

```text
.well-known/assetlinks.json
```

这样它就会发布到 `https://YOUR_NAME.github.io/.well-known/assetlinks.json`。应用仓库仍然保持 `viet-daily` 不变。

也可以用自定义域名（例如 `viet.example.com`），把 `.well-known/assetlinks.json` 放到域名根目录。

> 没有正确放置 assetlinks 时，APK 仍可能打开，但顶部可能出现浏览器地址栏，不是完整全屏 App。

### 安装 APK

把 APK 传到安卓手机，允许“安装未知应用”后安装。首次打开需要联网；安装完成后 TWA 会加载线上页面，后续内容更新不需要重新装 APK。

## 七、用 Bubblewrap 打 APK（进阶）

需要 Node.js 18+、JDK 17、Android SDK：

```bash
npm install -g @bubblewrap/cli
bubblewrap init --manifest https://YOUR_NAME.github.io/viet-daily/manifest.webmanifest
bubblewrap build
```

Bubblewrap 会询问包名、签名密钥等信息。构建后得到：

- `app-release-signed.apk`
- `app-release-bundle.aab`
- 用于 TWA 的 `assetlinks.json` 内容

签名密钥（`.keystore`）一定保存好；以后更新上架 Play Store 需要同一个密钥。AAB 用于 Google Play，APK 可直接侧载测试。

## 八、更新流程

1. 修改本地工程
2. 如果改了网页/词表/音频，把 `sw.js` 里的 `CACHE` 版本号加一（例如 `vietdaily-v1.4.1`）
3. 运行检查：

```bash
python scripts/check.py
python scripts/check_tones.py
python scripts/audio_report.py
```

4. 提交并推送：

```bash
git add .
git commit -m "Update vocabulary"
git push
```

GitHub Pages 会自动更新。PWA 重新打开后会拿到新版本；TWA APK 加载的也是线上页面，因此内容同样会更新。

## 九、常见问题

**GitHub Pages 打开是 404**
- 仓库必须 Public（免费计划）
- Pages Source 必须是 `main` + `/(root)`
- `index.html` 必须在仓库根目录

**页面能开但安装按钮不出现**
- 必须 HTTPS（GitHub Pages 是 HTTPS）
- 用 Chrome，不要用微信内置浏览器
- 确认 `manifest.webmanifest` 和图标都能访问

**APK 顶部有地址栏**
- `assetlinks.json` 没放在域名根目录，或 SHA-256 指纹不匹配
- 重新从 PWABuilder/Bubblewrap 获取最新的 assetlinks 内容

**音频文件太大**
- 当前 2032 条 MP3 约 22 MB，总量对 GitHub 没问题
- 单个文件远小于 GitHub 100 MB 限制，不需要 Git LFS

**私有仓库**
- GitHub Pages 对私有仓库通常需要付费计划；想免费使用就选 Public，或改用 Netlify/Cloudflare Pages。
