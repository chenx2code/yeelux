# YeeLux - 智能灯具局域网中枢 (Smart Light Controller)

中文 | [English](README.md)

这是一个基于 `python-miio` 开发，专为 **Yeelight（及米家）系列智能灯具** 打造的开源局域网控制面板。
无需依赖公网连接或官方 App，完全在局域网内与设备直连通信，响应延迟在毫秒级别。

## ✨ 特性 (Features)
- ⏱️ **睡眠定时**: 一键设置倒计时，到时自动关灯。
- 🍅 **番茄钟/专注模式**: 自定义工作与休息时间。工作结束时，台灯会自动闪烁提醒，并自动切入护眼昏黄模式；休息结束再次闪烁并恢复工作明亮灯光。
## 💡 兼容性说明 (Compatibility)
得益于底层的 `python-miio` 通用协议库，本项目理论上兼容市面上绝大多数支持“局域网控制”的 Yeelight 灯具产品。

## 🛠️ 安装说明 (Installation)

### 1. 获取基础依赖
确保你的电脑或服务器上安装了 Python 3.8+ 环境。
克隆本仓库后，安装相关依赖包：
```bash
pip install -r requirements.txt
```

### 2. 配置设备 (devices.json)
本项目支持控制全屋的多个智能灯具。在项目根目录复制 `devices.example.json` 并重命名为 `devices.json`，然后填入你所有设备的 IP 和 Token：
```json
[
  {
    "id": "lamp_1",
    "name": "工作台灯",
    "ip": "192.168.1.X",
    "token": "你的32位Token"
  },
  {
    "id": "lamp_2",
    "name": "卧室吸顶灯",
    "ip": "192.168.1.Y",
    "token": "你的32位Token_2"
  }
]
```
*(你还可以复制根目录下的 `.env.example` 并重命名为 `.env`，在里面修改和指定运行端口等配置，非必填。)*

> **🔑 关于如何获取 Yeelight Token：**
> 本项目基于纯局域网 UDP 协议通信，需要你设备的 32 位 Token 才能进行身份验证。
> 推荐使用 Piotr Machowski 编写的第三方提取工具：
> 👉 [Xiaomi Cloud Tokens Extractor (GitHub)](https://github.com/PiotrMachowski/Xiaomi-cloud-tokens-extractor)
>
> 按照该项目的官方指引运行提取器，即可自动列出账号下所有智能设备的 IP 和 Token。获取后填入上方的 `devices.json` 文件即可。（注：本项目无内置任何涉及小米云端登录的第三方脚本。）

### 3. 启动服务 (Run)

**方式一：使用 Python 本地运行**
```bash
python web_app/app.py
```

**方式二：使用 Docker 部署 (推荐)**
本项目支持使用 Docker 一键部署。请确保你的环境中已安装 `docker` 和 `docker compose`，并且已经在根目录下创建好了 `devices.json` 文件。
```bash
docker compose up -d
```
*(注：如果你的 Docker 运行在真实的 Linux 系统如 NAS/树莓派 上，强烈建议修改 `docker-compose.yml` 启用 `network_mode: "host"`，以支持局域网设备 UDP 自动发现功能。Windows/Mac 用户保持默认配置即可。)*

服务启动后，在你的浏览器中访问 `http://localhost:<PORT>` (或你服务器的局域网 IP:`<PORT>`) 即可开始使用！
*(注：`<PORT>` 为你在上文 `.env` 中配置的端口号；若未配置，则默认使用 5000 端口。)*


> **⚖️ 免责声明 (Disclaimer)**
> 本项目为第三方本地控制面板，非 Yeelight 或小米官方出品。本项目仅基于官方公开的局域网协议实现兼容控制，不提供任何官方应用的相关服务。
