# YeeLux - 智能灯具局域网中枢 (Smart Light Controller)

中文 | [English](README.md)

这是一个基于 `python-miio` 开发，专为 **Yeelight（及米家）系列智能灯具** 打造的开源局域网控制面板。
无需依赖公网连接或官方 App，完全在局域网内与设备直连通信，响应延迟在毫秒级别。

## 1. 特性 (Features)
- ⏱️ **睡眠定时**: 一键设置倒计时，到时自动关灯。
- 🍅 **番茄钟/专注模式**: 自定义工作与休息时间。工作结束时，台灯会自动闪烁提醒，并自动切入护眼昏黄模式；休息结束再次闪烁并恢复工作明亮灯光。
## 2. 兼容性说明 (Compatibility)
得益于底层的 `python-miio` 通用协议库，本项目理论上兼容市面上绝大多数支持“局域网控制”的 Yeelight 灯具产品。

## 3. 安装说明 (Installation)

### 3.1 获取基础依赖
确保你的电脑或服务器上安装了 Python 3.8+ 环境。
克隆本仓库后，安装相关依赖包：
```bash
pip install -r requirements.txt
```

### 3.2 配置设备 (devices.json)
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

### 3.3 启动服务 (Run)

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

服务启动后，你可以在浏览器中访问本机的 `http://localhost:<PORT>` 或服务器的局域网 IP (例如 `http://192.168.1.x:<PORT>`) 开始使用。
*(注：`<PORT>` 为 `.env` 中配置的端口号，默认 5000。)*

---

### 3.4 🌐 局域网极客访问：零配置 mDNS 域名广播

为了带来最极致的智能家居体验，本项目内置了基于 `zeroconf` 的 **mDNS (多播 DNS) 局域网广播** 功能。

**1. 核心优势与解决的痛点**
在家庭局域网中，路由器的 DHCP 机制可能会导致服务器的 IP 地址发生变化。一旦 IP 变化，你之前保存在手机或电脑上的书签就会失效，每次都要重新去查 IP，极其枯燥且繁琐。
mDNS 功能完美解决了这个问题：它会自动向整个局域网广播一个固定的域名。你**再也不需要去死记硬背枯燥的 IP 地址了**，只需在连着同一个 Wi-Fi 的任何浏览器里输入专属域名 👉 **`http://yeelux.local:5000`** 即可永远稳定地打开控制面板！

**2. 支持的环境与相关配置**
- **适用环境**：原生的 Linux 物理机（如树莓派、Ubuntu 服务器）、NAS、以及安卓手机 (Termux) 环境。
- **用户需要做什么**：
  - **如果你是用 Python 直接运行**：无需任何配置，代码会自动广播 `yeelux.local`，开箱即用。
  - **如果你是用 Docker 部署**：你**必须**修改 `docker-compose.yml` 文件：**注释掉 `ports` 相关行，并取消注释 `network_mode: "host"`**。这会让容器直接绑定宿主机的物理网卡，从而把 mDNS 广播发送到整个局域网。
  - *(进阶)* **如果你家里部署了多套本服务**：为了防止多台设备抢占同一个名字导致冲突，你需要在对应机器的 `.env` 文件里加上一行配置强制重命名（例如：`MDNS_NAME=yeelux-bedroom`），此时该机器的访问域名就会变成 `http://yeelux-bedroom.local:5000`。
  - *(进阶)* **自定义 mDNS 轮询自愈间隔**：如果在无法使用**操作系统底层网卡事件被动监听**的环境（如 Android Termux 沙盒权限受限），服务会自动降级为主动轮询来检测 IP 变化。默认每 180 秒检测一次。你可以在 `.env` 中设置 `MDNS_POLLING_INTERVAL=180` 来更改这个时间（单位：秒）。
  
**3. 不支持的环境与应对方式**
- **不适用环境**：Windows 本地环境、Mac 本地环境、Windows 的 WSL 虚拟机环境、以及 Windows/Mac 上的 Docker Desktop。这些环境由于底层存在虚拟 NAT 网络隔离，mDNS 多播包无法穿透到真实的物理局域网中。
- **用户需要做什么**：
  - 代码在启动时会自动嗅探到这类虚拟隔离环境，并**自动静默关闭** mDNS 功能以防止程序因网络冲突而报错。
  - 你不需要修改任何代码。如果你是用 Docker 部署的，请务必**保持 `docker-compose.yml` 中默认的 `ports: ["5000:5000"]` 映射配置不变**。
  - 你只能通过老方法，在浏览器中输入 `http://localhost:5000` 或服务器当前的真实局域网 IP 来访问控制面板。

**4. 常见避坑：浏览器报 `ERR_EMPTY_RESPONSE` 或无法访问**
如果你能够使用真实 IP 正常打开面板，但在电脑或手机上使用 `yeelux.local` 域名时却提示 `ERR_EMPTY_RESPONSE` 或无法访问，这通常是因为你当前设备上的**网络代理或 VPN 软件开启了全局 TUN 虚拟网卡或 Fake-IP 模式**。
- **发生原理**：代理软件全局劫持了 `.local` 后缀的局域网域名请求，将其当成了外网域名去公网 DNS 求解，导致连接被强行切断。
- **解决办法**：最快的方法是**临时退出代理软件**。如果想一劳永逸，请在代理软件的高级配置（如 `fake-ip-filter` 或 Bypass 绕过列表）中将 `*.local` 加入直连白名单。

---

### 3.5 📱 部署在安卓手机 (Termux) 上

如果你想把安卓手机当成 24 小时运行的微型服务器，使用 **Termux** 部署是一个极佳的选择。由于本项目使用了 `cryptography`（底层依赖 Rust），在手机上直接编译极大概率会报错。请严格按照以下**避坑步骤**进行部署：

**1. 安装基础环境与预编译包**
在 Termux 中执行以下命令，直接使用系统提供的高性能预编译包，绕过 Rust 编译报错：
```bash
pkg update && pkg upgrade -y
pkg install python git clang make python-cryptography rust openssl -y
```

**2. 克隆项目并使用系统包创建虚拟环境**
这里**必须**加上 `--system-site-packages` 参数，让虚拟环境能够“借用”上一步安装好的 `python-cryptography` 预编译包。
```bash
git clone https://github.com/您的用户名/yeelux.git
cd yeelux
python -m venv venv --system-site-packages
source venv/bin/activate
pip install -r requirements.txt
```

**3. 配置与解决 Android 底层 Bug 启动**
由于最新的 Termux Python 3.13 存在 `PyBaseObject_Type` 动态链接 Bug，我们必须使用 `LD_PRELOAD` 进行底层库注入启动：
```bash
cp devices.example.json devices.json
nano devices.json  # 填入你真实的台灯 IP 和 Token

# 注入动态库并启动魔法服务！
LD_PRELOAD=$PREFIX/lib/libpython3.13.so python web_app/app.py
```

> **⚠️ 保持后台运行的极其重要提醒：**
> 1. 下拉手机通知栏，在 Termux 通知上点击 **Acquire wakelock** (获取唤醒锁)，防止息屏后 CPU 休眠导致断网。
> 2. 去手机系统设置中，将 Termux 的电池优化策略改为 **“无限制”**。
> 3. 在多任务界面给 Termux **加锁**，防止被系统清理。

---

> **⚖️ 免责声明 (Disclaimer)**
> 本项目为第三方本地控制面板，非 Yeelight 或小米官方出品。本项目仅基于官方公开的局域网协议实现兼容控制，不提供任何官方应用的相关服务。
