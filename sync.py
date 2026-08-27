#!/usr/bin/env python3
"""
icstudentunion-fork 同步自动化脚本
从 WPH 上游 (ASUKAwph/icstudentunion) 同步更新到本 fork
图片自动压缩+上传 COS，HTML 自动替换引用

用法：
  python sync.py              # 检查上游并同步
  python sync.py --check      # 只检查是否有更新
  python sync.py --force      # 强制重新同步（即使没有新提交）
"""

import json
import os
import re
import subprocess
import sys
import base64
from pathlib import Path

# ========== 配置 ==========
UPSTREAM_REPO = "ASUKAwph/icstudentunion"
FORK_DIR = Path(__file__).parent
COS_BASE = "https://tuchuang-1441466534.cos.ap-beijing.myqcloud.com"
COS_MAP_FILE = FORK_DIR / "cos_map.json"
HTML_FILES = [
    "index.html", "undergraduate-home.html", "undergraduate.html",
    "graduate.html", "organizations.html", "teams.html", "join.html",
]
ASSET_FILES = ["assets/site.css", "assets/site.js"]

# 图片扩展名（需要替换为 COS URL）
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".ico"}

# ========== 工具函数 ==========

def run(cmd, check=True, capture=True):
    """运行命令并返回输出"""
    result = subprocess.run(
        cmd, shell=True, capture_output=capture, text=True, encoding="utf-8"
    )
    if check and result.returncode != 0:
        print(f"ERROR: {cmd}")
        print(f"  stderr: {result.stderr}")
        sys.exit(1)
    return result.stdout.strip() if capture else ""


def gh_api(path):
    """调用 GitHub API"""
    return run(f"gh api {path}")


def download_file(repo_path):
    """从 GitHub 下载文件内容"""
    content = gh_api(f"repos/{repo_path}/contents --jq '.content'")
    if not content:
        return None
    return base64.b64decode(content).decode("utf-8")


def load_cos_map():
    """加载 COS 映射表"""
    if COS_MAP_FILE.exists():
        return json.loads(COS_MAP_FILE.read_text(encoding="utf-8"))
    return {}


def save_cos_map(cos_map):
    """保存 COS 映射表"""
    COS_MAP_FILE.write_text(
        json.dumps(cos_map, indent=1, ensure_ascii=False),
        encoding="utf-8"
    )


def is_image(path):
    """判断是否是图片文件"""
    return Path(path).suffix.lower() in IMAGE_EXTS


def upload_to_cos(local_path, cos_key):
    """上传文件到 COS"""
    sid = os.environ.get("COS_SECRET_ID")
    skey = os.environ.get("COS_SECRET_KEY")
    if not sid or not skey:
        print("    警告: COS_SECRET_ID/COS_SECRET_KEY 未设置，跳过上传")
        return False
    
    try:
        from qcloud_cos import CosConfig, CosS3Client
        cfg = CosConfig(Region="ap-beijing", SecretId=sid, SecretKey=skey, Scheme="https")
        client = CosS3Client(cfg)
        
        # 根据扩展名设置 ContentType
        ext = Path(local_path).suffix.lower()
        content_type = {
            ".css": "text/css",
            ".js": "application/javascript",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }.get(ext, "application/octet-stream")
        
        with open(local_path, "rb") as f:
            client.put_object(
                Bucket="tuchuang-1441466534",
                Key=cos_key,
                Body=f,
                ContentType=content_type
            )
        return True
    except Exception as e:
        print(f"    上传失败: {e}")
        return False


# ========== 主要逻辑 ==========

def check_upstream():
    """检查上游是否有新提交"""
    print("检查上游仓库...")
    commits_json = gh_api(f"repos/{UPSTREAM_REPO}/commits?per_page=5")
    commits = json.loads(commits_json)
    
    latest = commits[0]
    sha = latest["sha"][:7]
    date = latest["commit"]["author"]["date"][:10]
    msg = latest["commit"]["message"].split("\n")[0]
    
    print(f"  最新提交: {sha} {date}")
    print(f"  提交信息: {msg}")
    
    return commits


def get_local_last_commit():
    """获取本地最后同步的提交 SHA"""
    log = run("git log --oneline -20", check=False)
    for line in log.split("\n"):
        if "sync" in line.lower() or "同步" in line:
            return line.split()[0]
    return None


def sync_html(cos_map):
    """同步 HTML 文件"""
    print("\n同步 HTML 文件...")
    cos_base = COS_BASE
    
    for file in HTML_FILES:
        # 下载 WPH 版本
        content = download_file(f"{UPSTREAM_REPO}/contents/{file}")
        if not content:
            print(f"  跳过 {file}（下载失败）")
            continue
        
        # 替换图片路径为 COS URL
        def replace_src(m):
            path = m.group(1)
            # CSS/JS 不替换
            if path.endswith(".css") or path.endswith(".js"):
                return m.group(0)
            # 图片替换
            if path in cos_map:
                return f'src="{cos_base}/{cos_map[path]}"'
            print(f"  WARNING: {file} 中的 {path} 不在 cos_map 中")
            return m.group(0)
        
        content = re.sub(r'src="(assets/[^"]+)"', replace_src, content)
        
        # 写入本地
        (FORK_DIR / file).write_text(content, encoding="utf-8")
        print(f"  OK: {file}")


def sync_assets(cos_map):
    """同步 CSS/JS 文件"""
    print("\n同步 CSS/JS...")
    cos_base = COS_BASE
    
    for asset in ASSET_FILES:
        content = download_file(f"{UPSTREAM_REPO}/contents/{asset}")
        if not content:
            print(f"  跳过 {asset}（下载失败）")
            continue
        
        # 写入本地
        local_path = FORK_DIR / asset
        local_path.write_text(content, encoding="utf-8")
        print(f"  OK: {asset}")
        
        # 上传到 COS（如果设置了密钥）
        if os.environ.get("COS_SECRET_ID"):
            cos_key = asset
            if upload_to_cos(local_path, cos_key):
                print(f"    已上传到 COS: {cos_key}")


def sync_images():
    """同步新图片（下载→压缩→上传→更新 cos_map）"""
    print("\n检查新图片...")
    
    # 获取 WPH 的文件列表
    tree_json = gh_api(f"repos/{UPSTREAM_REPO}/git/trees/main?recursive=1")
    tree = json.loads(tree_json)
    
    cos_map = load_cos_map()
    new_images = []
    
    for item in tree.get("tree", []):
        path = item["path"]
        if path.startswith("assets/") and is_image(path):
            if path not in cos_map:
                new_images.append(path)
    
    if not new_images:
        print("  没有新图片")
        return cos_map
    
    print(f"  发现 {len(new_images)} 张新图片")
    
    # 下载并压缩
    from PIL import Image
    import io
    
    for img_path in new_images:
        print(f"  处理: {img_path}")
        
        # 下载
        content = download_file(f"{UPSTREAM_REPO}/contents/{img_path}")
        if not content:
            print(f"    下载失败，跳过")
            continue
        
        # 保存原始文件
        local_path = FORK_DIR / img_path
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)
        
        # 压缩
        ext = Path(img_path).suffix.lower()
        try:
            img = Image.open(io.BytesIO(content if isinstance(content, bytes) else content.encode()))
            
            if ext == ".png":
                # PNG → WebP
                out_name = img_path.replace(".png", ".webp")
                out_path = FORK_DIR / out_name
                img.save(out_path, "WEBP", quality=82)
            elif ext in (".jpg", ".jpeg"):
                # JPEG → 压缩 JPEG
                out_name = img_path.replace(".jpeg", ".jpg")
                out_path = FORK_DIR / out_name
                img.save(out_path, "JPEG", quality=80)
            else:
                out_name = img_path
                out_path = local_path
        except Exception as e:
            print(f"    压缩失败: {e}")
            out_name = img_path
            out_path = local_path
        
        # 上传到 COS
        if upload_to_cos(out_path, out_name):
            cos_map[img_path] = out_name
            print(f"    OK: {out_name}")
        else:
            print(f"    上传失败")
    
    save_cos_map(cos_map)
    return cos_map


def main():
    import argparse
    parser = argparse.ArgumentParser(description="同步 WPH 上游更新")
    parser.add_argument("--check", action="store_true", help="只检查是否有更新")
    parser.add_argument("--force", action="store_true", help="强制重新同步")
    args = parser.parse_args()
    
    # 检查上游
    commits = check_upstream()
    latest_sha = commits[0]["sha"][:7]
    
    # 获取本地最后同步的提交
    local_sha = get_local_last_commit()
    
    if args.check:
        if local_sha and local_sha.startswith(latest_sha):
            print("\n✅ 已是最新版本")
        else:
            print(f"\n⬆️  有新更新可用: {latest_sha}")
        return
    
    if not args.force and local_sha and local_sha.startswith(latest_sha):
        print("\n✅ 已是最新版本，无需同步（使用 --force 强制同步）")
        return
    
    # 加载 cos_map
    cos_map = load_cos_map()
    
    # 同步图片（新图片）
    cos_map = sync_images()
    
    # 同步 HTML
    sync_html(cos_map)
    
    # 同步 CSS/JS
    sync_assets(cos_map)
    
    # Git commit
    print("\n提交更改...")
    run("git add -A")
    run(f'git commit -m "sync: 同步 WPH 上游更新 ({latest_sha})"')
    run("git push origin main")
    
    print(f"\n✅ 同步完成！最新提交: {latest_sha}")
    print("   Cloudflare Pages 将自动部署")


if __name__ == "__main__":
    main()
