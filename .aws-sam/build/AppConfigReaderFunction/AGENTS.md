## AWS CLIの操作

AWS CLIの操作は、AWS CLIのバージョン2を使って行います。基本的にはインストールされているはずですが、最初にインストールされていることを確認してください。なお、CLIのプロファイルは`default`です。

##　認証

以下のコマンドで認証を行います。`--profile`オプションでプロファイルを指定することができます。

```bash
aws sso login --profile default
```
