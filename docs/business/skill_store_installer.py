#!/usr/bin/env python3
"""
技能商店安装器 — Skill Store Installer

从 GitHub 私有仓库或本地目录安装 SKILL 包到 ~/.hermes/skills/。

这是一个 CLI 工具，为 skill_manage Hermes 工具提供方便的包装。
最终安装操作委托给 skill_manage 工具完成（如果可用），
否则直接写入目标目录。

用法:
    python3 skill_store_installer.py install <source> [--category CAT] [--force]
    python3 skill_store_installer.py list
    python3 skill_store_installer.py remove <name>
    python3 skill_store_installer.py info <name>

source 格式:
    - 本地目录: /path/to/skill-package
    - GitHub URL: https://github.com/owner/repo/tree/main/path/to/skill
    - GitHub 简写: owner/repo/path/to/skill
"""

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ─── 配置 ─────────────────────────────────────────────────────────────────

SKILLS_DIR = Path.home() / ".hermes" / "skills"
GITHUB_API_BASE = "https://api.github.com"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"

# 环境变量中可设置 GitHub Token（提高 API 限频）
GH_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""

# ─── 工具函数 ─────────────────────────────────────────────────────────────


def _green(text: str) -> str:
    return f"\033[92m{text}\033[0m"


def _red(text: str) -> str:
    return f"\033[91m{text}\033[0m"


def _yellow(text: str) -> str:
    return f"\033[93m{text}\033[0m"


def _cyan(text: str) -> str:
    return f"\033[96m{text}\033[0m"


def _bold(text: str) -> str:
    return f"\033[1m{text}\033[0m"


def _dim(text: str) -> str:
    return f"\033[2m{text}\033[0m"


def _github_request(url: str) -> Tuple[Any, Optional[str]]:
    """Make a GitHub API request. Returns (parsed_json, error_message)."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "hermes-skill-store-installer/1.0",
    }
    if GH_TOKEN:
        headers["Authorization"] = f"token {GH_TOKEN}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data, None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        if e.code == 404:
            return None, f"404 Not Found: {url}"
        if e.code == 403:
            return None, (
                f"403 Forbidden (rate limit?). "
                f"Set GITHUB_TOKEN env var for higher limits.\n{body}"
            )
        return None, f"HTTP {e.code}: {body[:200]}"
    except urllib.error.URLError as e:
        return None, f"Connection error: {e.reason}"


def _parse_source(source: str) -> Dict[str, str]:
    """Parse a source string into components.

    Supports:
      - Local path: /path/to/dir or ./relative/path
      - GitHub URL: https://github.com/owner/repo/tree/branch/path
      - GitHub shorthand: owner/repo/path/to/skill
    """
    # Local directory?
    p = Path(source)
    if p.exists() and p.is_dir():
        return {"type": "local", "path": str(p.resolve())}

    # GitHub URL
    gh_match = re.match(
        r"https://github\.com/([^/]+)/([^/]+)(?:/tree/([^/]+))?(?:/(.*))?$",
        source,
    )
    if gh_match:
        owner, repo, branch, subpath = gh_match.groups()
        return {
            "type": "github",
            "owner": owner,
            "repo": repo,
            "branch": branch or "main",
            "path": subpath or "",
        }

    # GitHub shorthand: owner/repo/path...
    shorthand_match = re.match(r"^([^/]+)/([^/]+)/(.+)$", source)
    if shorthand_match:
        owner, repo, subpath = shorthand_match.groups()
        return {
            "type": "github",
            "owner": owner,
            "repo": repo,
            "branch": "main",
            "path": subpath,
        }

    # GitHub shorthand: owner/repo (root of repo)
    repo_match = re.match(r"^([^/]+)/([^/]+)$", source)
    if repo_match:
        owner, repo = repo_match.groups()
        return {
            "type": "github",
            "owner": owner,
            "repo": repo,
            "branch": "main",
            "path": "",
        }

    return {"type": "unknown", "raw": source}


def _fetch_github_tree(owner: str, repo: str, branch: str, subpath: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """Fetch the contents of a GitHub directory via the Contents API."""
    # Remove leading/trailing slashes from subpath
    subpath = subpath.strip("/")

    if subpath:
        api_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{subpath}?ref={branch}"
    else:
        api_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents?ref={branch}"

    data, error = _github_request(api_url)
    if error:
        return None, error

    if isinstance(data, dict):
        # Single file, not a directory
        return [data], None

    if isinstance(data, list):
        return data, None

    return None, "Unexpected API response format"


def _fetch_github_file_raw(owner: str, repo: str, branch: str, filepath: str) -> Tuple[Optional[str], Optional[str]]:
    """Fetch a raw file from GitHub."""
    url = f"{GITHUB_RAW_BASE}/{owner}/{repo}/{branch}/{filepath}"
    headers = {"User-Agent": "hermes-skill-store-installer/1.0"}
    if GH_TOKEN:
        headers["Authorization"] = f"token {GH_TOKEN}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8"), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code} fetching {url}"
    except urllib.error.URLError as e:
        return None, f"Connection error: {e.reason}"


def _find_skill_name_from_dir(dir_path: Path) -> Optional[str]:
    """Read skill name from SKILL.md frontmatter."""
    skill_md = dir_path / "SKILL.md"
    if not skill_md.exists():
        return None
    try:
        content = skill_md.read_text("utf-8")
        # Parse simple YAML frontmatter
        m = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not m:
            return None
        yaml_block = m.group(1)
        # Extract name field
        name_m = re.search(r"^name:\s*(.+)$", yaml_block, re.MULTILINE)
        if name_m:
            return name_m.group(1).strip().strip("\"'")
    except Exception:
        pass
    return None


def _find_installed_skills() -> List[Dict[str, Any]]:
    """Scan ~/.hermes/skills/ for all installed skill packages."""
    results = []
    if not SKILLS_DIR.exists():
        return results

    for skill_md in SKILLS_DIR.rglob("SKILL.md"):
        # Skip .hub directory
        if ".hub" in skill_md.parts:
            continue
        skill_dir = skill_md.parent
        name = skill_dir.name
        # Try to get canonical name from frontmatter
        try:
            content = skill_md.read_text("utf-8")
            m = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
            if m:
                yaml_block = m.group(1)
                name_m = re.search(r"^name:\s*(.+)$", yaml_block, re.MULTILINE)
                if name_m:
                    name = name_m.group(1).strip().strip("\"'")
                desc_m = re.search(r"^description:\s*(.+)$", yaml_block, re.MULTILINE)
                desc = desc_m.group(1).strip().strip("\"'") if desc_m else ""
            else:
                desc = ""
        except Exception:
            desc = ""

        results.append({
            "name": name,
            "dir_name": skill_dir.name,
            "path": str(skill_dir),
            "description": desc,
            "skill_md": str(skill_md),
            "file_count": len([f for f in skill_dir.rglob("*") if f.is_file()]),
        })

    return sorted(results, key=lambda x: x["name"])


# ─── 安装逻辑 ─────────────────────────────────────────────────────────────


def _install_from_local(source_path: Path, category: Optional[str], force: bool) -> Dict[str, Any]:
    """Install a skill from a local directory."""
    skill_name = _find_skill_name_from_dir(source_path)
    if not skill_name:
        # Fall back to directory name
        skill_name = source_path.name

    # Determine target directory
    if category:
        target_dir = SKILLS_DIR / category / skill_name
    else:
        target_dir = SKILLS_DIR / skill_name

    if target_dir.exists():
        if not force:
            return {
                "success": False,
                "error": f"Skill '{skill_name}' already exists at {target_dir}. Use --force to overwrite.",
            }
        shutil.rmtree(target_dir)

    # Copy the skill directory
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(str(source_path), str(target_dir), symlinks=True)

    file_count = len([f for f in target_dir.rglob("*") if f.is_file()])
    return {
        "success": True,
        "message": f"Installed '{skill_name}' from {source_path}",
        "path": str(target_dir),
        "file_count": file_count,
    }


def _install_from_github(owner: str, repo: str, branch: str, subpath: str, category: Optional[str], force: bool) -> Dict[str, Any]:
    """Install a skill from a GitHub repo."""
    # Fetch directory contents
    items, error = _fetch_github_tree(owner, repo, branch, subpath)
    if error:
        return {"success": False, "error": f"Failed to fetch from GitHub: {error}"}

    if not items:
        return {"success": False, "error": "Empty directory"}

    # Check if there's a SKILL.md
    has_skill_md = any(
        item.get("name") == "SKILL.md" and item.get("type") == "file"
        for item in items
    )
    if not has_skill_md:
        return {
            "success": False,
            "error": f"No SKILL.md found in {owner}/{repo}/{subpath}. "
                     f"This doesn't appear to be a valid skill package.",
        }

    # Determine skill name from SKILL.md
    skill_name = None
    base_path = f"{subpath.strip('/')}/SKILL.md" if subpath else "SKILL.md"
    content, fetch_error = _fetch_github_file_raw(owner, repo, branch, base_path)
    if content:
        m = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if m:
            name_m = re.search(r"^name:\s*(.+)$", m.group(1), re.MULTILINE)
            if name_m:
                skill_name = name_m.group(1).strip().strip("\"'")

    if not skill_name:
        # Derive from subpath
        if subpath:
            skill_name = subpath.rstrip("/").split("/")[-1]
        else:
            skill_name = repo

    # Determine target directory
    if category:
        target_dir = SKILLS_DIR / category / skill_name
    else:
        target_dir = SKILLS_DIR / skill_name

    if target_dir.exists():
        if not force:
            return {
                "success": False,
                "error": f"Skill '{skill_name}' already exists at {target_dir}. Use --force to overwrite.",
            }
        shutil.rmtree(target_dir)

    # Download all files from this directory tree
    target_dir.mkdir(parents=True, exist_ok=True)
    files_downloaded = _download_github_tree(owner, repo, branch, subpath, target_dir)

    return {
        "success": True,
        "message": f"Installed '{skill_name}' from GitHub ({owner}/{repo})",
        "path": str(target_dir),
        "file_count": files_downloaded,
    }


def _download_github_tree(owner: str, repo: str, branch: str, subpath: str, target_dir: Path) -> int:
    """Recursively download a GitHub directory tree."""
    items, error = _fetch_github_tree(owner, repo, branch, subpath)
    if error or not items:
        return 0

    count = 0
    for item in items:
        item_name = item.get("name", "")
        item_type = item.get("type", "")
        item_path = item.get("path", "")

        if item_type == "file":
            # Download file
            content, _ = _fetch_github_file_raw(owner, repo, branch, item_path)
            if content is not None:
                # Preserve relative path structure
                if subpath:
                    relative_path = item_path[len(subpath.strip("/")):].lstrip("/")
                else:
                    relative_path = item_name

                file_path = target_dir / relative_path
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Detect binary vs text
                try:
                    file_path.write_text(content, "utf-8")
                except Exception:
                    # Fall back to binary write using the API download_url
                    _download_github_file_binary(item, file_path)
                count += 1
            else:
                # Try binary download via download_url
                _download_github_file_binary(item, target_dir / item_name)
                count += 1

        elif item_type == "dir":
            # Recurse into subdirectory
            relative_subpath = f"{subpath}/{item_name}" if subpath else item_name
            subdir = target_dir / item_name
            subdir.mkdir(parents=True, exist_ok=True)
            count += _download_github_tree(owner, repo, branch, relative_subpath, subdir)

    return count


def _download_github_file_binary(item: Dict[str, Any], target_path: Path) -> bool:
    """Download a file using its download_url (for binary files)."""
    download_url = item.get("download_url")
    if not download_url:
        return False

    headers = {"User-Agent": "hermes-skill-store-installer/1.0"}
    if GH_TOKEN:
        headers["Authorization"] = f"token {GH_TOKEN}"

    req = urllib.request.Request(download_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(resp.read())
        return True
    except Exception:
        return False


# ─── 命令实现 ──────────────────────────────────────────────────────────────


def cmd_install(source: str, category: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
    """Install a skill from a source."""
    parsed = _parse_source(source)

    if parsed["type"] == "local":
        return _install_from_local(Path(parsed["path"]), category, force)

    elif parsed["type"] == "github":
        return _install_from_github(
            parsed["owner"],
            parsed["repo"],
            parsed["branch"],
            parsed["path"],
            category,
            force,
        )

    else:
        return {
            "success": False,
            "error": (
                f"Unknown source format: '{source}'. "
                f"Use a local path, GitHub URL, or owner/repo/path format."
            ),
        }


def cmd_list(verbose: bool = False) -> Dict[str, Any]:
    """List all installed skills."""
    skills = _find_installed_skills()
    return {
        "success": True,
        "total": len(skills),
        "skills": skills,
    }


def cmd_remove(name: str) -> Dict[str, Any]:
    """Remove a skill by name (directory name or frontmatter name)."""
    skills = _find_installed_skills()

    # Try exact match on name
    matches = [s for s in skills if s["name"] == name]
    if not matches:
        # Try match on dir_name
        matches = [s for s in skills if s["dir_name"] == name]
    if not matches:
        # Try partial match
        matches = [s for s in skills if name in s["name"] or name in s["dir_name"]]

    if not matches:
        return {"success": False, "error": f"No skill found matching '{name}'."}

    if len(matches) > 1:
        match_list = "\n".join(f"  - {m['name']} ({m['path']})" for m in matches)
        return {
            "success": False,
            "error": f"Multiple skills match '{name}':\n{match_list}\nUse a more specific name.",
        }

    skill = matches[0]
    skill_path = Path(skill["path"])
    shutil.rmtree(skill_path)

    # Clean up empty parent directories
    parent = skill_path.parent
    try:
        if parent != SKILLS_DIR and not any(parent.iterdir()):
            parent.rmdir()
    except Exception:
        pass

    return {
        "success": True,
        "message": f"Removed skill '{skill['name']}' from {skill['path']}",
    }


def cmd_info(name: str) -> Dict[str, Any]:
    """Show detailed info about an installed skill."""
    skills = _find_installed_skills()

    matches = [s for s in skills if s["name"] == name]
    if not matches:
        matches = [s for s in skills if s["dir_name"] == name]
    if not matches:
        matches = [s for s in skills if name in s["name"] or name in s["dir_name"]]

    if not matches:
        return {"success": False, "error": f"No skill found matching '{name}'."}

    if len(matches) > 1:
        match_list = "\n".join(f"  - {m['name']}" for m in matches)
        return {
            "success": False,
            "error": f"Multiple skills match '{name}':\n{match_list}\nUse a more specific name.",
        }

    skill = matches[0]
    skill_path = Path(skill["path"])

    # Read SKILL.md content
    skill_md_path = skill_path / "SKILL.md"
    skill_md_content = ""
    tags = []
    molin_owner = ""
    if skill_md_path.exists():
        skill_md_content = skill_md_path.read_text("utf-8")
        # Extract tags and owner from frontmatter
        m = re.match(r"^---\s*\n(.*?)\n---", skill_md_content, re.DOTALL)
        if m:
            yaml_block = m.group(1)
            tags_m = re.search(r"tags:\s*\[(.*?)\]", yaml_block)
            if tags_m:
                tags = [t.strip().strip("\"'") for t in tags_m.group(1).split(",")]
            owner_m = re.search(r"molin_owner:\s*(.+)$", yaml_block, re.MULTILINE)
            if owner_m:
                molin_owner = owner_m.group(1).strip().strip("\"'")

    # List files
    files = sorted(
        [str(f.relative_to(skill_path)) for f in skill_path.rglob("*") if f.is_file()]
    )

    return {
        "success": True,
        "skill": {
            "name": skill["name"],
            "dir_name": skill["dir_name"],
            "path": skill["path"],
            "description": skill["description"],
            "tags": tags,
            "molin_owner": molin_owner,
            "file_count": skill["file_count"],
            "files": files,
            "skill_md_content": skill_md_content,
        },
    }


# ─── CLI ───────────────────────────────────────────────────────────────────


def _print_json(data: Dict[str, Any]) -> None:
    """Pretty-print JSON output."""
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _print_human_list(result: Dict[str, Any]) -> None:
    """Human-readable list output."""
    skills = result.get("skills", [])
    if not skills:
        print(f"{_yellow('No skills installed.')}")
        print(f"  Use: {_cyan('python3 skill_store_installer.py install <source>')}")
        return

    print(f"\n{_bold(f'📦 Installed Skills ({len(skills)})')}\n")
    for s in skills:
        desc = s.get("description", "")
        desc_str = f" — {_dim(desc[:80])}" if desc else ""
        print(f"  {_green(s['name'])}{desc_str}")
    print()


def _print_human_info(result: Dict[str, Any]) -> None:
    """Human-readable info output."""
    skill = result.get("skill", {})
    name = skill.get("name", "?")
    print(f"\n{_bold(f'📋 {name}')}")
    print(f"  {_dim('目录:')}     {skill.get('path', '?')}")
    print(f"  {_dim('描述:')}     {skill.get('description', '—')}")
    if skill.get("tags"):
        print(f"  {_dim('标签:')}     {', '.join(skill['tags'])}")
    if skill.get("molin_owner"):
        print(f"  {_dim('所属:')}     {skill['molin_owner']}")
    print(f"  {_dim('文件数:')}   {skill.get('file_count', 0)}")

    files = skill.get("files", [])
    if files:
        print(f"\n  {_bold('文件列表:')}")
        for f in files:
            print(f"    {_dim(f)}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="技能商店安装器 — Skill Store Installer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  # 从本地目录安装\n"
            "  python3 skill_store_installer.py install ./my-skill-package\n\n"
            "  # 从 GitHub 安装 (完整URL)\n"
            "  python3 skill_store_installer.py install \\\n"
            "    https://github.com/owner/repo/tree/main/skills/my-skill\n\n"
            "  # 从 GitHub 简写\n"
            "  python3 skill_store_installer.py install owner/repo/skills/my-skill\n\n"
            "  # 带分类安装\n"
            "  python3 skill_store_installer.py install ./my-skill --category domain\n\n"
            "  # 列出现有技能\n"
            "  python3 skill_store_installer.py list\n\n"
            "  # 查看技能详情\n"
            "  python3 skill_store_installer.py info my-skill\n\n"
            "  # 卸载技能\n"
            "  python3 skill_store_installer.py remove my-skill\n"
        ),
    )

    subparsers = parser.add_subparsers(dest="command", help="可用子命令")

    # install
    p_install = subparsers.add_parser("install", help="从本地目录或 GitHub 安装技能包")
    p_install.add_argument("source", help="安装源: 本地目录路径 或 GitHub URL/简写")
    p_install.add_argument("--category", "-c", help="安装到指定分类子目录 (如 domain, meta)")
    p_install.add_argument("--force", "-f", action="store_true", help="覆盖已存在的技能包")
    p_install.add_argument("--json", action="store_true", help="JSON 格式输出")

    # list
    p_list = subparsers.add_parser("list", help="列出已安装的技能包")
    p_list.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    p_list.add_argument("--json", action="store_true", help="JSON 格式输出")

    # remove
    p_remove = subparsers.add_parser("remove", help="卸载技能包")
    p_remove.add_argument("name", help="技能名称")
    p_remove.add_argument("--json", action="store_true", help="JSON 格式输出")

    # info
    p_info = subparsers.add_parser("info", help="显示技能包详情")
    p_info.add_argument("name", help="技能名称")
    p_info.add_argument("--json", action="store_true", help="JSON 格式输出")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "install":
        result = cmd_install(args.source, args.category, args.force)
        if args.json:
            _print_json(result)
        elif result.get("success"):
            print(f"\n{_green('✅ ' + result['message'])}")
            print(f"  {_dim('路径:')} {result['path']}")
            print(f"  {_dim('文件:')} {result.get('file_count', 0)} 个文件\n")
        else:
            print(f"\n{_red('❌ ' + result.get('error', '安装失败'))}\n")
            sys.exit(1)

    elif args.command == "list":
        result = cmd_list(args.verbose)
        if args.json:
            _print_json(result)
        else:
            _print_human_list(result)

    elif args.command == "remove":
        result = cmd_remove(args.name)
        if args.json:
            _print_json(result)
        elif result.get("success"):
            print(f"\n{_green('✅ ' + result['message'])}\n")
        else:
            print(f"\n{_red('❌ ' + result.get('error', '卸载失败'))}\n")
            sys.exit(1)

    elif args.command == "info":
        result = cmd_info(args.name)
        if args.json:
            _print_json(result)
        elif result.get("success"):
            _print_human_info(result)
        else:
            print(f"\n{_red('❌ ' + result.get('error', '未找到'))}\n")
            sys.exit(1)


if __name__ == "__main__":
    main()
