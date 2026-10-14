# 京东云哪吒 AX3000（RE-OS-03U）刷机变砖与救砖完整实录

> 一台被刷成"红灯常亮、全网段找不到 IP、按键无效"砖头的京东云哪吒 AX3000，从拆机 TTL 到重新跑上 OpenWrt 的全过程记录。
> 所有踩过的坑、用过的命令、验证过的固件，都在这。**给后人一条活路。**

**最终成果**：板子跑上 **Nwrt (QSDK 12.5) 23.05**（OpenWrt 23.05 系、QSDK/NSS 加速版），eMMC 正常读写、WiFi 正常、SSH/Web 管理正常，救砖总耗时约 1 天（大部分时间花在固件选型上）。

---

## 相关仓库（同一系列教程）

- [cbywyz/ha-midea-hualing-ac](https://github.com/cbywyz/ha-midea-hualing-ac) —— 美的/华凌空调云端接入教程（midea_auto_cloud）
- [cbywyz/gree-yapqf-broadlink-smartir](https://github.com/cbywyz/gree-yapqf-broadlink-smartir) —— 格力空调 Broadlink + SmartIR 红外接入教程
- [cbywyz/ha-hualing-fan-broadlink](https://github.com/cbywyz/ha-hualing-fan-broadlink) —— 华凌风扇红外接入教程（含全套遥控器编码库）
- [cbywyz/phicomm-aircat-m1](https://github.com/cbywyz/phicomm-aircat-m1) —— 斐讯悟空 M1 空气检测仪复活教程（HA 集成）
- [cbywyz/ha-tv-kids-lock](https://github.com/cbywyz/ha-tv-kids-lock) —— 电视**家长管控**教程（HA 自动化，任意智能电视通用）：音量上限锁 + 信号源锁定 + 儿童观看定时锁
- [cbywyz/jdcloud-re-sp-01b-flash](https://github.com/cbywyz/jdcloud-re-sp-01b-flash) —— 京东云一代 RE-SP-01B 刷 OpenWrt AP 教程

---

## 一、先认清你的机器：RE-OS-03U ≠ RE-CS-03

京东云 AX3000 有两个高度相似的型号，**教程通用但固件不通用**：

| 型号 | 平台 | 关键差异 |
|---|---|---|
| RE-CS-03（恩山教程主角） | 高通 IPQ5018 | eMMC 颗粒/设备树与 RE-OS-03U 有差异 |
| **RE-OS-03U（本实录主角）** | 高通 IPQ5018 | 部分固件（Kwrt NSS 版）eMMC 起不来，详见第四章 |

**识别方法**：串口启动日志里 `Model RE-OS-03U`；或主板丝印。本实录所有结论仅对 RE-OS-03U 负责，RE-CS-03 可参考但请自行验证。

硬件关键信息：
- SoC：高通 IPQ5018（四核 Cortex-A53 1.0GHz）
- eMMC：8GB（识别为 `SDS6D2 rev1.1 total=59648MiB`）
- 内存：512MB DDR3
- 网口：1×WAN + 2×LAN（千兆 PHY）
- WiFi：QCA 方案，ath0(2.4G) + ath1(5G)，驱动 `ath11k`
- U-Boot：2016.01（救砖后为第三方不死版 `2016.01-gf84ce15`）

## 二、变砖现象与病根

**现象**（刷第三方固件失败后）：
- 电源灯**常亮红灯**，不闪不灭，没有任何网络活动迹象
- 所有网口（WAN/LAN）都拿不到 IP，DHCP 无响应
- 复位键、恢复键均无效
- Web 恢复页（192.168.1.1 / 192.168.10.10 等常见段）全部打不开

**病根**（拆机接 TTL 后从串口日志确诊）：
1. 板子的 eMMC 分区表/U-Boot 已被改动，但启动链断裂
2. U-Boot 环境变量 `bootcmd=jdboot` 指向一条**不存在的命令**（`jdboot`）——原厂 U-Boot 被替换/环境被清后，自动引导必然失败
3. 关键证据串口日志：`Hit any key to stop autoboot` 后停住，无任何后续引导动作

**结论：不是真砖。** eMMC 和 U-Boot 都活着，只是启动链断了。这是本案例能救回来的前提。

## 三、救砖实录（完整流程）

### 3.1 硬件准备

| 物品 | 说明 |
|---|---|
| USB-TTL 模块 | CP2102 / CH340 均可，**3.3V** |
| 测试钩夹子 | 夹焊盘用，比焊接省事（焊盘间距小，钩夹刚好） |
| 网线 | 一根，后面 Web 上传固件用 |
| 螺丝刀 | 拆底盖用 |

**接线（重点，接错不开机）**：

| 板子焊盘 | 接 TTL 模块 | 线色建议 |
|---|---|---|
| RX | TX | 白 |
| TX | RX | 绿 |
| GND | GND | 黑 |
| **VCC（3V3）** | **不接！** | 红线悬空 |

- 波特率 **115200 8N1**
- ⚠️ 红线（VCC）**绝对不接**，只接三根（RX/TX/GND）。接了有烧板风险
- ⚠️ 串口首字符有丢失老毛病，发命令前加个前导空格可避开

### 3.2 进入 U-Boot

1. 先开串口监控（本仓库 `tools/nezha_catch_uboot.py` 可自动抓 autoboot 并打空格中断）
2. 给板子上电
3. 倒计时内**疯狂按空格**（或等自动抓到），看到 `Hit any key to stop autoboot` → 回车
4. 进入提示符 `IPQ5018#`

**确诊当前状态**（依次执行）：

```bash
printenv              # 看 bootcmd 等环境变量
mtdparts              # 看分区表是否健在
mmc part              # 看 eMMC 实际分区（GPT）
help                  # 看可用命令（有无 httpd/tftpboot/flash）
version               # 看 U-Boot 版本与编译工具链
```

### 3.3 救砖三板斧（顺序不能乱）

**第一斧：刷/确认 GPT 分区表**

```bash
# 若分区表已损坏才需要；本案例分区表健在故跳过
# tftpboot 0x44000000 gpt.bin
# flash 0:GPT 0x44000000 0x4400      # 17KB = 34 扇区
```

**第二斧：确认不死 U-Boot 在位**

- U-Boot 版本显示 `arm-openwrt-linux-gcc` 工具链 = 已刷第三方版（好事）
- 若还是原厂版：`tftpboot 0x44000000 uboot.bin` → `flash 0:APPSBL` → `flash 0:APPSBL_1`（**A/B 双分区都刷，防变砖**）

**第三斧：清 BOOTCONFIG（关键！）**

```bash
flasherase 0:BOOTCONFIG
flasherase 0:BOOTCONFIG1
```

原厂的 `bootcmd=jdboot` 就存在这两个分区里，清掉后 U-Boot 才会走默认引导流程。**这一步是本案例起死回生的直接转折点。**

### 3.4 Web 恢复页上传固件

清完 BOOTCONFIG 后：

```bash
httpd                  # 启动 Web 恢复页，默认 192.168.1.1，DHCP 池 .2-.101
```

电脑网卡设静态 IP（如 192.168.1.2），浏览器打开 `http://192.168.1.1`，用「更新固件」页上传。

**本案例最终成功姿势**：命令行 curl 上传（比浏览器稳）：

```bash
curl --noproxy "*" -F "firmware=@nwrt-qsdk.bin" http://192.168.1.1/
```

上传后 U-Boot 自动校验、写入 HLOS（内核）+ rootfs 分区、自动重启。

### 3.5 验证救砖成功

- 串口出现完整内核启动日志，直到 `root@Nwrt:/#`
- 关键看 eMMC：`F2FS-fs (loop0): Mounted` + `mount_root: switching to f2fs overlay`（eMMC 活了的铁证）
- 网线插 **LAN 口**（eth1，在 br-lan 桥里；eth0 是 WAN 不在桥里），电脑可 ping 通 192.168.1.1、SSH/Web 全开

## 四、固件选型血泪史（本实录最大价值）

这一章是用**两天时间 + 一台板子反复试错**换来的，请仔细读。

### 4.1 Kwrt NSS 版（jdcloud_re-cs-03）——**RE-OS-03U 上别用**

恩山/QQ 群流传最广的 Kwrt 后羿 AX3000 固件（`openwrt-ipq50xx-jdcloud_re-cs-03`）：

- ✅ 能刷进去，U-Boot Web 页也认（如果是 FIT 格式）
- ❌ **内核起来后 eMMC 初始化失败**：

```
sdhci_msm 7804000.mmc: TCXO clk not present (-517)
gcc_q6_axim2_clk status stuck at 'off'
mmc0: Reset 0x1 never completed
mmc0: Failed to initialize a non-removable card
```

- 后果：内核卡在 `Waiting for root device` 直到超时，`/dev/mmc*` 完全不存在，系统起不来
- **根因：设备树（DTB）不匹配。** 该固件 DTB 为 RE-CS-03 设计，eMMC 用 HS400 模式；RE-OS-03U 的 eMMC 需要降为 HS200（社区补丁正是删 `mmc-hs400-1_8v` 改 `mmc-hs200-1_8v`）
- 社区有人专为 RE-OS-03U 修了这个补丁（`wdrma2010/JDC-Re_os_03u`），但无现成 Release 产物，需自行 CI 构建

**教训：initramfs 内存启动法救不了它。** 我们试过从内存启动（不碰 eMMC），照样 eMMC 不识别——因为根因在 DTB，不在分区表/刷写位置。

### 4.2 「类型不匹配」type_mismatch——格式问题，不是固件问题

第三方 U-Boot 的「更新固件」页**只认 FIT / QSDK / UBI 格式**的固件（源码 `1980490718/u-boot-2016` 确认）：

| 固件格式 | 头部特征 | Web 页结果 |
|---|---|---|
| 纯 squashfs（很多 factory.bin 实际是这种） | `hsqs` | ❌ type_mismatch |
| sysupgrade tar 包 | tar | ❌ type_mismatch |
| **FIT 镜像** | `d00dfeed` | ✅ 通过，正常刷写 |

**判断方法**：`xxd firmware.bin | head -1`，看前 4 字节。`d00dfeed` 才是 FIT。

### 4.3 最终可用固件：Nwrt（godsun.pro 生态）

 godsun.pro（数码罗记）专为京东云哪吒/后羿 AX3000 生态编译的 **Nwrt** 固件：

- `Nwrt-2025-06-01-openwrt-ipq50xx-ipq50xx_32-jdcloud_ax3000-squashfs-factory.bin`（51MB，**QSDK/NSS 版，本实录最终采用**）
- `Nwrt-2025-05-27-openwrt-ipq50xx-generic-jdcloud_ax3000-squashfs-factory.bin`（44MB，主线版，备用）
- 两个都是 **FIT 格式**，U-Boot Web 页直接认，一次刷入成功
- 配套的 `gpt.bin`（17KB）与我们板上分区表完全一致（MD5 `0896dba8`），**分区表不用动**

**下载渠道**：`p.godsun.pro`（AList 网盘，需 GitHub OAuth 登录），JD 文件夹。文件均已收录到本仓库 [Releases](https://github.com/cbywyz/jdcloud-nezha-ax3000-rescue/releases)。

## 五、工具链（tools/ 目录）

| 文件 | 用途 |
|---|---|
| `nezha_cli.py` | 串口交互核心：`send "命令"` / `raw 0x03` / `mon 秒数`，自动挑 CP2102，115200 8N1 |
| `nezha_catch_uboot.py` | 自动抓 autoboot 倒计时并按空格中断进 U-Boot，解决手工卡时机难题 |
| `nezha_failsafe.py` | 自动抓 OpenWrt failsafe 提示并按 `f`，拿免密救援 shell |
| `tftp_nezha.py` | TFTP 服务器（绑指定网卡 IP，已修 65535 块回绕 bug，41MB 文件不会断） |
| `tftp_start.bat` | Windows 一键开 TFTP（纯英文，避免 GBK 编码乱码） |

依赖：`pip install pyserial paramiko psutil`。

**注意**：Windows 沙箱/远程环境可能连不到板子网段（虚拟网络栈），上传操作需在**物理直连板子的电脑**上用 PowerShell `curl.exe` 执行。

## 六、一页命令清单（抄作业用）

```bash
# ===== 1. 接线：RX→TX, TX→RX, GND→GND, VCC 不接，115200 8N1 =====
# ===== 2. 上电，autoboot 倒计时按空格中断，进入 IPQ5018# =====

# 3. 确诊
printenv
mtdparts
mmc part

# 4. 确认/刷 U-Boot（若已是不死版可跳过）
#    setenv serverip 192.168.1.2; setenv ipaddr 192.168.1.1
#    tftpboot 0x44000000 uboot.bin
#    flash 0:APPSBL 0x44000000 0x68000
#    flash 0:APPSBL_1 0x44000000 0x68000

# 5. 清 BOOTCONFIG（关键）
flasherase 0:BOOTCONFIG
flasherase 0:BOOTCONFIG1

# 6. 起 Web 恢复页
httpd

# 7. 电脑设静态 192.168.1.2，上传固件（网线插 WAN 口）
curl --noproxy "*" -F "firmware=@nwrt-qsdk.bin" http://192.168.1.1/

# 8. 等自动重启，串口看到 F2FS overlay 挂载 = 成功
# 9. 网线换到 LAN 口，192.168.1.1 管理
```

## 七、避坑清单

1. **VCC 红线别接**，只接 RX/TX/GND 三根
2. **网线插 LAN 口**才能管理系统（eth1 在 br-lan；eth0 是 WAN）
3. 家里光猫可能也占 192.168.1.1——访问恢复页时**关掉电脑 WiFi**，否则流量飘到光猫
4. 恢复页只认 FIT 格式固件（`d00dfeed` 头），tar/squashfs 免谈
5. **Kwrt re-cs-03 固件在 RE-OS-03U 上 eMMC 起不来**，选固件先看有没有 RE-OS-03U 适配
6. 救砖中途**绝不能断电**，eMMC 写入中掉电=真砖
7. 串口发命令首字符会丢，命令前加个空格
8. `httpd` 启动时网线要先插好（eth0 要 up，否则 DHCP 起不来）
9. 浏览器上传大文件可能丢包，优先 curl `-F` 上传
10. 备份！`tftpput` 或 `mmc read` 把原分区读出来存电脑，本仓库 backup/ 思路可参考

## 八、原厂固件兜底

若 OpenWrt 玩腻了想回原厂 JDCOS：p.godsun.pro 网盘有 `ax3000-nazhe-yuanban.rar`（706MB，原厂 eMMC 全盘备份）。注意新版 JDCOS 4.3.x 无 telnet 漏洞，刷回去就失去免拆刷机能力，**且只有原厂 U-Boot 才认它的网页上传**，回生前想清楚。

---

## 声明

- 本实录为个人救砖过程记录，刷机有风险，操作前备份，后果自负
- 固件版权归原作者（Kwrt: kiddin9；Nwrt/godsun 生态: 数码罗记；U-Boot: 1980490718），本仓库仅收录文件供救砖备用，不主张任何权利
- 固件 MD5 与文件清单见 [Releases](https://github.com/cbywyz/jdcloud-nezha-ax3000-rescue/releases) 页面
