# 越词通 · 上架资料

本目录存放 Android 安装包与 Google Play / 应用商店上架所需的文字和图片素材。当前应用版本 **1.2.1**。

## 已准备好的材料

| 文件 | 用途 | 状态 |
| --- | --- | --- |
| `listing-zh.md` | 商店名称、简介、完整描述、分类、标签、发布说明 | 可用 |
| `data-safety.md` | Google Play“数据安全”表单参考答案 | 可用 |
| `release-checklist.md` | 生成签名包、上传、测试、国内商店补充材料 | 操作清单 |
| `assetlinks.json` | TWA 去除浏览器地址栏用的 Digital Asset Links 模板 | 待填签名指纹 |
| `screenshots/01-today.png` | 手机截图：今日学习 | 1080×1920 |
| `screenshots/02-library.png` | 手机截图：分类词库 | 1080×1920 |
| `screenshots/03-phonetics.png` | 手机截图：元音/辅音/声调 | 1080×1920 |
| `screenshots/04-progress.png` | 手机截图：学习统计与设置 | 1080×1920 |
| `screenshots/05-autoplay.png` | 手机截图：不熟词自动播放 | 1080×1920 |
| `feature-graphic.png` | Google Play 功能图 | 1024×500 |
| `../icons/icon-512.png` | 商店图标 | 512×512 |
| `../privacy.html` | 在线隐私政策页面 | 需部署后访问 |

## 隐私政策网址

部署到 GitHub Pages 后使用：

```text
https://feifeigongzhu123.github.io/viet-daily/privacy.html
```

提交商店前先在浏览器打开确认能访问。国内访问 GitHub Pages 可能不稳定；如果主要面向国内商店，建议把同一页面部署到国内云主机并绑定已备案域名。

## 安装包状态

签名 APK / AAB **尚未生成**。本机没有 Android SDK、JDK 和可用网络环境，PWABuilder 网页版也未能完成打包。生成步骤见 `release-checklist.md`，任选 PWABuilder 网页版或 Bubblewrap 命令行。

生成时请固定以下信息，后续更新必须保持一致：

- 包名：`io.github.feifeigongzhu123.vietdaily`
- 应用名：`越词通`
- 版本名：`1.2.1`
- 版本号：`1`
- 签名密钥：自行生成并备份，丢失后无法更新已上架应用

## 重要说明

- 词库包含 65 个《越南语123》主题入门词和 951 个通用高频词；通用词不是教材原词表。商店描述中已如实说明。
- 例句、词表、音频的第三方来源与许可见仓库根目录 `THIRD_PARTY_NOTICES.md`，上架时不要删除。
- 版权归安得半日闲所有；第三方内容按各自许可使用。
- 应用无账号、无广告、无统计分析，学习记录只存本机。数据安全表单按此填写。
