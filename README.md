# 集成电路学院学生工作网站

> Fork of [ASUKAwph/icstudentunion](https://github.com/ASUKAwph/icstudentunion)，图片全部迁移至腾讯云 COS 图床，提升国内访问速度。

**线上地址：** https://icstudentunion.pages.savrc3.icu

## ✨ 特性

- 🚀 **国内加速**：所有图片走腾讯云 COS 图床，国内访问更快
- 🔄 **自动同步**：提供一键同步脚本，轻松跟进上游更新
- 📱 **响应式设计**：适配手机、平板、桌面等多种设备
- 🎨 **现代化 UI**：开屏动画、品牌导航、图片轮播等交互效果
- 🔍 **SEO 优化**：完整的 meta 标签、Open Graph 协议支持
- ⚡ **性能优化**：图片懒加载、CSS/JS CDN 加速

## 📁 项目结构

```
icstudentunion/
├── index.html              # 首页（身份选择入口）
├── undergraduate-home.html # 本科生入口
├── undergraduate.html      # 学生会介绍
├── graduate.html           # 研究生会介绍
├── organizations.html      # 学生组织
├── teams.html              # 学院院队
├── join.html               # 纳新入口
├── 404.html                # 404 页面
├── cos_map.json            # 本地路径 → COS URL 映射表
├── sync.py                 # 一键同步脚本
└── assets/                 # 本地图片备份（已上传 COS）
```

## 🚀 快速开始

### 查看网站

直接访问 https://icstudentunion.pages.savrc3.icu

### 同步上游更新

```bash
# 检查是否有新更新
python sync.py --check

# 同步更新
python sync.py

# 强制重新同步
python sync.py --force
```

### 手动同步

1. 下载上游文件
2. 压缩新图片（PNG→WebP，JPEG→压缩）
3. 上传到 COS
4. 更新 `cos_map.json`
5. 替换 HTML 中的图片路径
6. Git commit & push

## 🛠️ 技术栈

- **前端**：HTML5 + CSS3 + Vanilla JavaScript
- **图床**：腾讯云 COS（ap-beijing 区域）
- **托管**：Cloudflare Pages
- **构建**：无构建步骤，纯静态文件

## 📝 与原版的差异

| 项目 | 原版 (WPH) | 本 Fork |
|------|-----------|---------|
| 图片存储 | 本地 assets/ | 腾讯云 COS |
| CSS/JS | 本地引用 | CDN 引用 |
| favicon | 无 | 有 |
| 404 页面 | Cloudflare 默认 | 自定义 |
| SEO | 基础 | 完整 meta + OG |

## 🤝 贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源。

## 🙏 致谢

- [ASUKAwph/icstudentunion](https://github.com/ASUKAwph/icstudentunion) - 原版项目
- 山东大学集成电路学院学生会
