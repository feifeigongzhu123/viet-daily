# 发布操作清单

## 0. 提交前确认

- [ ] `https://feifeigongzhu123.github.io/viet-daily/` 能打开，页面底部版本为 v1.2.2
- [ ] `https://feifeigongzhu123.github.io/viet-daily/privacy.html` 能打开
- [ ] 手机上测试：今日学习、词库分类、自动播放、语音页、清除记录
- [ ] 断网后重新打开，确认应用外壳和已缓存音频可用
- [ ] 用旧版本升级安装，确认学习记录仍在（localStorage 按 origin 保存，包名不变即可）
- [ ] 确认 `THIRD_PARTY_NOTICES.md` 和 `COPYRIGHT.md` 随仓库保留

## 1. 生成签名安装包

固定信息：

| 项目 | 值 |
| --- | --- |
| 包名 | `io.github.feifeigongzhu123.vietdaily` |
| 应用名 | 越词通 |
| 版本名 | 1.2.2 |
| 版本号 | 1 |
| 起始网址 | `https://feifeigongzhu123.github.io/viet-daily/` |

### 方案 A：PWABuilder 网页版（推荐，最省事）

1. 打开 <https://www.pwabuilder.com/>，输入上面的起始网址。
2. 选择 Android 包，填写应用名、包名、版本号和签名信息。
3. 下载 Android 包（通常包含 AAB、APK、签名密钥和 `assetlinks.json`）。
4. 妥善备份签名密钥与密码；以后更新必须使用同一密钥。

> 当前环境访问 PWABuilder 时出现代理连接失败，未能实际生成安装包；需要在网络正常的电脑上完成。

### 方案 B：Bubblewrap 命令行

需要 Node.js、JDK 17+ 和 Android SDK。

```bash
npm i -g @bubblewrap/cli
bubblewrap init --manifest https://feifeigongzhu123.github.io/viet-daily/manifest.webmanifest
bubblewrap build
```

初始化时填写上面的包名、应用名和版本号。`bubblewrap build` 会生成签名的 APK/AAB，并提示保存 keystore。

### 方案 C：本地静态壳 + WebView

如果无法使用 TWA，也可以做一个最小 WebView 壳加载线上地址；但离线体验、PWA 更新和审核通过率不如 TWA，不推荐作为首选。

## 2. 处理 Digital Asset Links（TWA 去地址栏）

TWA 首次启动时可能显示浏览器地址栏，直到完成域名验证。

`assetlinks.json` 必须放在**域名根目录**：

```text
https://feifeigongzhu123.github.io/.well-known/assetlinks.json
```

注意：本项目是项目站点，路径是 `/viet-daily/`，把文件放在本仓库的 `.well-known/` 下会变成 `/viet-daily/.well-known/assetlinks.json`，**不能通过验证**。两种做法：

1. 新建仓库 `feifeigongzhu123.github.io`，在其中放 `.well-known/assetlinks.json`；或
2. 绑定自定义域名，在域名根目录提供该文件。

文件内容使用本目录 `assetlinks.json` 模板，把 `REPLACE_WITH_SHA256_FINGERPRINT` 换成签名证书的 SHA-256 指纹（PWABuilder 会给出，或用 `keytool -list -v -keystore ...` 查看）。

验证：

```text
https://feifeigongzhu123.github.io/.well-known/assetlinks.json
```

能直接返回 JSON 且包名、指纹正确即可。即使验证未完成，应用仍可使用，只是顶部可能保留地址栏。

## 3. Google Play 提交

1. 注册 Google Play 开发者账号（一次性费用，按当前政策为准）。
2. 创建应用：名称“越词通”，默认语言简体中文，应用/游戏选“应用”，免费。
3. 上传 AAB 到内部测试轨道，先用自己的手机安装测试。
4. 填写商店资料：复制 `listing-zh.md` 中的名称、简短说明、完整说明和发布说明。
5. 上传图形：图标 512×512、功能图 1024×500、手机截图 2–8 张（本目录已提供 5 张 1080×1920）。
6. 完成“应用内容”问卷：无广告、无内购、无需登录、无用户生成内容、目标受众 13+。
7. 完成“数据安全”表单：参考 `data-safety.md`，按“不收集、不共享”填写；本地处理的数据如实说明。
8. 隐私政策填写：`https://feifeigongzhu123.github.io/viet-daily/privacy.html`。
9. 先走内部测试 / 封闭测试，确认审核要求（新开发者账号通常需要一定数量的测试人员），再申请正式发布。

## 4. 国内安卓商店（如华为、小米、OPPO、vivo、应用宝）

除安装包外，通常还需要：

- [ ] 软件著作权登记证书（建议尽早申请，周期较长）
- [ ] APP 备案（工信部）及域名 ICP 备案
- [ ] 隐私政策网址（不能只用 GitHub Pages，建议国内云主机）
- [ ] 隐私权限说明、第三方 SDK 清单
- [ ] 未成年人保护与内容安全说明
- [ ] 企业/个人开发者资质（各商店要求不同）

GitHub Pages 在国内访问不稳定，若主攻国内商店，建议把 PWA 部署到国内云主机（阿里云/腾讯云 OSS + CDN 或轻量服务器），绑定已备案域名，再生成指向国内域名的 TWA。

## 5. 发布后维护

- 每次改前端资源，必须同步提升 `sw.js` 的 `CACHE` 版本，否则老用户可能继续用旧缓存。
- 每次发版更新 `VERSION`、`manifest.webmanifest`、`index.html` meta、`app.js` 的 `APP_VERSION`、`CHANGELOG.md`。
- Android 包的 `versionCode` 每次提交必须递增；`versionName` 与应用版本保持一致。
- 备份签名密钥、密码、AAB 和商店文案。
