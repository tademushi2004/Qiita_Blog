---
title: Test Blog Pipeline
tags:
  - 'Test'
private: true
updated_at: ''
id: null
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
# テスト記事：自動画像パイプラインの検証

これは新しい自動画像変換パイプライン（Husky pre-commit hook版）のテスト記事です。
執筆中はローカルの `images/` ディレクトリの PNG を指定します。

![テスト画像](https://raw.githubusercontent.com/tademushi2004/Qiita_Blog/main/public/avif/1000brains-06_image.avif)

VSCode 上で問題なくプレビューが表示されていれば成功です。
この状態で `git commit` を行うと、裏で AVIF に変換され、上記のパスが GitHub の Raw URL に自動的に書き換わります。
