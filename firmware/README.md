# 固件文件目录说明

本目录放**小文件**（分区表、U-Boot），大固件（>10MB）放在仓库 [Releases](https://github.com/cbywyz/jdcloud-nezha-ax3000-rescue/releases) 页面下载。

## 本目录文件

| 文件 | 大小 | MD5 | 用途 |
|---|---|---|---|
| `gpt.bin` | 17KB | `0896dba8958684376a3c16868e490902` | ⭐ GPT 分区表（HLOS 6M + rootfs 256M + rootfs_data + swap，17 分区），与板上已刷版本完全一致 |
| `uboot.bin` | 419KB | `ce26eed3983e6e96173fceef75ac4045` | 不死 U-Boot（已刷在板上，备用） |
| `uboot-nwrt.mbn` | 531KB | 见 Release | Nwrt 生态配套 U-Boot（25-05-21 版） |
| `uboot-recs03.mbn` | 533KB | 见 Release | RE-CS-03 标注版 U-Boot（25-05-21 版） |
| `uboot-ipq50xx-jdcloud_ax3000-260907_172823_3e89586.bin` | 640KB | `6048a4232828993bdcd272d1e424cd8e` | 另一版不死 U-Boot（Web 默认 IP 192.168.3.3，DHCP+Web） |

## Releases 页面文件（大固件）

| 文件 | 大小 | 格式 | 结论 |
|---|---|---|---|
| `nwrt-qsdk.bin` | 51MB | FIT | ⭐ **本实录最终采用**（Nwrt QSDK/NSS 版，RE-OS-03U 实测 eMMC 正常） |
| `nwrt-generic.bin` | 44MB | FIT | 主线 OpenWrt 版，备用 |
| `kwrt-factory.bin` | 41MB | squashfs | ❌ RE-OS-03U 上 eMMC 起不来（见 README 第四章），仅存档 |
| `kwrt-sysupgrade.bin` | 47MB | tar | 同上，且 Web 页不认 tar 格式 |
| `initramfs.itb` | 23MB | FIT | 内存启动镜像（诊断用，Kwrt 25.12 版） |

## 原始出处

- Nwrt / U-Boot / GPT / 原厂备份：`p.godsun.pro`（AList 网盘，GitHub OAuth 登录，JD 文件夹）
- Kwrt：恩山无线论坛 / 京东云无线宝哪吒刷机群
- 不死 U-Boot 源码：`1980490718/u-boot-2016`
