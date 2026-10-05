"""
ブログ画像変換スクリプト: PNG/JPG -> AVIF 一括変換

使い方:
    python scripts/convert_to_avif.py [--quality 85] [--src src_images] [--out public/avif]

機能:
    - src_images/ 内の PNG/JPG/JPEG を public/avif/ に AVIF 形式で変換
    - 更新日時を比較し、変換済みファイルはスキップ（インクリメンタル変換）
    - 元画像が削除された場合、対応する AVIF を自動クリーンアップ
    - public/ 配下の Markdown 内の画像パスを GitHub Raw URL に自動変換
"""

import argparse
import os
import re
import sys
import urllib.parse
from pathlib import Path

from PIL import Image

# --- 定数 ---
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg"}
DEFAULT_QUALITY = 85

# GitHub Raw URL テンプレート
# ユーザー名・リポジトリ名・ブランチ名を設定
GITHUB_USER = "tademushi2004"
GITHUB_REPO = "Qiita_Blog"
GITHUB_BRANCH = "main"
GITHUB_RAW_BASE = (
    f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{GITHUB_BRANCH}"
)


def get_project_root() -> Path:
    """スクリプトの場所からプロジェクトルートを自動解決する。"""
    return Path(__file__).resolve().parent.parent


def find_source_images(src_dir: Path) -> dict[str, Path]:
    """
    ソースディレクトリ内の対象画像を検索し、
    {拡張子なしファイル名: ファイルパス} の辞書で返す。
    """
    images = {}
    for file in src_dir.iterdir():
        if file.is_file() and file.suffix.lower() in SUPPORTED_EXTENSIONS:
            images[file.stem] = file
    return images


def needs_conversion(src_path: Path, avif_path: Path) -> bool:
    """
    変換が必要かどうかを判定する。
    - AVIF が存在しない -> 変換必要
    - AVIF が存在するが、元画像より古い -> 変換必要
    - AVIF が存在し、元画像より新しい -> スキップ
    """
    if not avif_path.exists():
        return True
    return os.path.getmtime(src_path) > os.path.getmtime(avif_path)


def convert_image(src_path: Path, avif_path: Path, quality: int) -> bool:
    """
    単一の画像を AVIF に変換する。
    成功時は True、失敗時は False を返す。
    """
    try:
        with Image.open(src_path) as img:
            # RGBA の場合は RGB に変換（AVIF は RGBA も対応するが念のため）
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGBA")
            elif img.mode != "RGB":
                img = img.convert("RGB")

            img.save(avif_path, "AVIF", quality=quality)
        return True
    except Exception as e:
        print(f"  [ERR] {src_path.name}: {e}", file=sys.stderr)
        return False


def cleanup_orphaned_avifs(out_dir: Path, source_stems: set[str]) -> int:
    """
    元画像が存在しない孤立した AVIF ファイルを削除する。
    削除したファイル数を返す。
    """
    deleted_count = 0
    for avif_file in out_dir.iterdir():
        if avif_file.is_file() and avif_file.suffix.lower() == ".avif":
            if avif_file.stem not in source_stems:
                avif_file.unlink()
                print(f"  [DEL] CLEANUP: {avif_file.name} (source not found)")
                deleted_count += 1
    return deleted_count


def update_markdown_image_paths(public_dir: Path, github_avif_url: str, is_local_mode: bool) -> int:
    """
    public/ 配下の Markdown ファイル内の画像パスを書き換える。
    is_local_mode = False (公開モード): images/xxx.(png|jpg) -> GitHub AVIF URL
    is_local_mode = True  (執筆モード): GitHub AVIF URL -> images/xxx.png
    """
    total_replacements = 0

    if is_local_mode:
        # 執筆モード: GitHub AVIF URL -> images/xxx.png に戻す
        pattern = re.compile(r'(^|\s|\(|\[)' + re.escape(github_avif_url) + r'/([^\)]+?)\.avif')
        def repl_local(m):
            filename = urllib.parse.unquote(m.group(2))
            return f"{m.group(1)}images/{filename}.png"
        
        for md_file in public_dir.glob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            new_content, count = pattern.subn(repl_local, content)
            if count > 0:
                md_file.write_text(new_content, encoding="utf-8")
                print(f"  [URL] {md_file.name}: {count} image path(s) updated")
                total_replacements += count
    else:
        # 公開モード: images/xxx.(png|jpg|jpeg) -> GitHub AVIF URL にする
        pattern = re.compile(r'(^|\s|\(|\[)images/([^\)]+?)\.(png|jpg|jpeg)')
        def repl_remote(m):
            filename = urllib.parse.quote(m.group(2))
            return f"{m.group(1)}{github_avif_url}/{filename}.avif"
        
        for md_file in public_dir.glob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            new_content, count = pattern.subn(repl_remote, content)
            if count > 0:
                md_file.write_text(new_content, encoding="utf-8")
                print(f"  [URL] {md_file.name}: {count} image path(s) updated")
                total_replacements += count

    return total_replacements

def main() -> None:
    parser = argparse.ArgumentParser(
        description="PNG/JPG -> AVIF converter with GitHub URL rewriting"
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=DEFAULT_QUALITY,
        help=f"AVIF quality (0-100, default: {DEFAULT_QUALITY})",
    )
    parser.add_argument(
        "--src",
        type=str,
        default=None,
        help="Source directory (default: <project_root>/src_images)",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Output directory (default: <project_root>/public/avif)",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="執筆モード: Revert GitHub URLs back to local images/xxx.png paths (does not run conversion)",
    )
    parser.add_argument(
        "--no-url-rewrite",
        action="store_true",
        help="Skip Markdown image path rewriting",
    )
    # lint-staged から渡されるファイルリストを受け取って無視するための引数
    parser.add_argument(
        "files",
        nargs="*",
        help="List of files (ignored, script processes the whole public/ dir)",
    )
    args = parser.parse_args()

    # パスの解決
    project_root = get_project_root()
    src_dir = Path(args.src) if args.src else project_root / "src_images"
    out_dir = Path(args.out) if args.out else project_root / "public" / "avif"
    public_dir = project_root / "public"

    avif_rel = out_dir.relative_to(public_dir)
    github_avif_url = f"{GITHUB_RAW_BASE}/public/{avif_rel}"

    # ヘッダー表示
    print("=" * 60)
    print("  Image Pipeline" + (" [LOCAL MODE]" if args.local else ""))
    print("=" * 60)

    url_updates = 0

    if args.local:
        # --local が指定された場合は URL 置換のみ行って終了
        print("  Reverting GitHub AVIF URLs to local images/ paths...")
        url_updates = update_markdown_image_paths(public_dir, github_avif_url, is_local_mode=True)
        print("=" * 60)
        print(f"  URL rewrite: {url_updates} path(s) reverted to local")
        print("=" * 60)
        return

    # ディレクトリの存在確認
    if not src_dir.exists():
        print(f"[ERR] Source directory not found: {src_dir}")
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)

    # ソース画像を検索
    source_images = find_source_images(src_dir)

    if not source_images:
        print("\n  No source images found.")
        print("  Place PNG or JPG files in src_images/")
        print("=" * 60)
        # 画像がなくてもクリーンアップは実行
        deleted = cleanup_orphaned_avifs(out_dir, set())
        if deleted:
            print(f"\n  Cleanup: {deleted} orphaned AVIF(s) deleted")
            print("=" * 60)
        
        if not args.no_url_rewrite and public_dir.exists():
            url_updates = update_markdown_image_paths(public_dir, github_avif_url, is_local_mode=False)
            if url_updates:
                print(f"  URL rewrite: {url_updates} path(s) updated in Markdown")
                print("=" * 60)
        return

    # 変換処理
    converted = 0
    skipped = 0
    errors = 0

    print(f"\n  Processing {len(source_images)} image(s)...\n")

    for stem, src_path in sorted(source_images.items()):
        avif_path = out_dir / f"{stem}.avif"

        if not needs_conversion(src_path, avif_path):
            print(f"  [SKIP] {src_path.name} (already converted)")
            skipped += 1
            continue

        print(f"  [CONV] {src_path.name} -> {avif_path.name} ...", end=" ")
        if convert_image(src_path, avif_path, args.quality):
            # ファイルサイズを表示
            src_size = src_path.stat().st_size / 1024
            avif_size = avif_path.stat().st_size / 1024
            ratio = (1 - avif_size / src_size) * 100 if src_size > 0 else 0
            print(f"OK ({src_size:.0f}KB -> {avif_size:.0f}KB, {ratio:.0f}% reduced)")
            converted += 1
        else:
            errors += 1

    # クリーンアップ
    source_stems = set(source_images.keys())
    deleted = cleanup_orphaned_avifs(out_dir, source_stems)

    # Markdown 内の画像パスを GitHub Raw URL に変換
    if not args.no_url_rewrite and public_dir.exists():
        url_updates = update_markdown_image_paths(public_dir, github_avif_url, is_local_mode=False)

    # サマリー表示
    print("\n" + "=" * 60)
    print(f"  Done: converted {converted} / skipped {skipped} / errors {errors}")
    if deleted:
        print(f"  Cleanup: {deleted} orphaned AVIF(s) deleted")
    if url_updates:
        print(f"  URL rewrite: {url_updates} path(s) updated in Markdown")
    print("=" * 60)

    if errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
