## TextageParser

textageのhtmlを解析してLSTMへの入力へ符号化します。

1小節を96分割してBMS化しているので、
それ以上に細かい譜面は正確に再現されません。

## セットアップ

必須環境は恐らくruby2.0以上のみ。

最初にこのディレクトリ内で次のコマンドを実行しておく。

```
  $ bundle install --path vendor/bundle
```

## 使い方

```
  $ bundle exec ruby main_for_gmm_all.rb
```

chart_encodedディレクトリに結果が出力されます。
