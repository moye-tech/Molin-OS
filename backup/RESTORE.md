# 墨麟OS 还原指南

## 从本地硬盘还原（推荐 — 含密钥）
```bash
bash /Volumes/MolinOS/Molin-OS/scripts/restore.sh
```

## 从 GitHub 还原（需手动输入密钥）
```bash
git clone https://github.com/moye-tech/Molin-OS.git ~/Molin-OS
cd ~/Molin-OS && bash scripts/restore.sh
```

## 验证
```bash
python -m molib health
hermes cron list
```
