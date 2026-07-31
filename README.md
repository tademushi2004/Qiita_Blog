# Qiita Blog Publishing Pipeline

このリポジトリは、Qiitaの記事執筆から画像最適化（AVIF変換）、そして自動公開までをシームレスに行うための専用パイプラインです。`qiita-cli` をベースにしつつ、画像管理の手間を極限まで減らす独自の Husky pre-commit フックを搭載しています。

## 🌟 主な特徴

1. **`npm run new` による安全な記事作成**
   - 記事を作成すると自動的に `private: true` とデフォルトタグ（Draft）が付与され、誤って未完成の記事が全世界に公開される事故を防ぎます。
2. **画像の完全自動最適化 (PNG → AVIF)**
   - 執筆中はローカルのPNG画像を使ってプレビューし、Gitでコミットした瞬間に裏側で自動的に軽量なAVIFに変換されます。
3. **Markdown URLの自動書き換え**
   - コミット時に、ローカルの `images/xxx.png` というパスが、自動的に GitHub 上の AVIF 画像を指す Raw URL（`https://raw...`）に置換されます。
4. **執筆モードへの巻き戻し機能**
   - 過去の記事の画像を直したい時は、VSCodeのタスクからワンクリックでパスをローカル用に巻き戻すことができます。

## 🛠 前提条件 (Prerequisites)

- Node.js (v18以上推奨)
- Python 3.10+
- Git

## 📦 セットアップ (Setup)

1. **Node.js 依存関係のインストール**
   Husky, lint-staged, qiita-cli などがインストールされます。
   ```bash
   npm install
   ```

2. **Python 仮想環境の構築**
   画像変換スクリプト用に仮想環境を作成し、Pillow をインストールします。
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install Pillow
   ```
   ※VSCode のターミナル等で有効化して実行してください。

## ✍️ 執筆から公開までのワークフロー

### 1. 記事の作成
必ず以下のコマンドで記事を作成します。
```bash
npm run new "記事のタイトル"
```

### 2. 執筆とプレビュー
- 文章は VSCode などで Markdown を記述します。
- 画像を使う場合、まずは画像を `public/images/`（または `src_images/`）に配置します。
- Markdownには **ローカルのPNGパス** を記述します。
  ```markdown
  ![画像の説明](images/my_image.png)
  ```
- VSCode のマークダウンプレビュー（`Ctrl+Shift+V`）でレイアウトを確認しながら執筆します。

### 3. コミット（ここで魔法が起きます）
記事が完成したら、通常通り Git でコミットします。
```bash
git add "public/記事ファイル.md"
git commit -m "feat: 新しい記事を追加"
```
**【裏側で起きること】**
Husky の pre-commit フックが起動し、以下の処理が自動で行われます。
1. PNG が AVIF に一括変換される
2. Markdown の画像パスが GitHub の公開用 URL に書き換わる
3. 変換後のファイルが自動でコミットに追加される

### 4. 公開
そのままプッシュすると、GitHub Actions が起動し、**限定共有記事（private）としてQiitaに公開**されます。
```bash
git push
```
Qiita上で最終的な完成図を確認し、問題なければ Markdown の `private: true` を `private: false` に変更して再度コミット＆プッシュすることで、全体公開となります。

## 🔧 過去の記事の画像を修正したい場合

公開後の記事は画像パスが GitHub の URL になっています。画像を差し替えたい場合は以下の手順を踏みます。

1. VSCode 上で `Ctrl+Shift+P` > `Tasks: Run Task` > **`画像の差し替え（執筆モードへ）`** を実行します。
2. Markdown内の URL が一瞬で `images/xxx.png` に戻ります。
3. 画像を差し替えて、プレビューで確認します。
4. 再度 `git commit` を行えば、また自動的に変換・URL書き換えが行われます。

## 📁 ディレクトリ構成

- `public/`: Qiita記事（.md）が格納されるディレクトリ。プレビュー用画像は `public/images/` に、変換済みAVIFは `public/avif/` に入ります。
- `src_images/`: 大元の高画質な画像（PNG/JPG）を格納しておくディレクトリ。
- `scripts/`: パイプラインを支えるスクリプト群。
  - `convert_to_avif.py`: 画像変換およびMarkdownのURL書き換えを行う中核スクリプト。
  - `new_article.js`: `npm run new` の実体。安全なデフォルトメタデータを付与します。
- `SKILLBLOG.md`: AI（Gemini等）とペアプログラミング・執筆を行う際のルールを定めたマスタープロンプト（仕様書）。
