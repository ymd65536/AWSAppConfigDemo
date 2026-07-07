 # AWS AppConfigを試してみる

## 利用技術

バックエンド

- 言語: Python3.11
- ビルドツール: AWS SAM
- ビルドサービス: AWS CodeBuild
- IaC: CloudFormation
- AWS Lambda Exetension: AppConfig Extension
- パッケージ管理: uv
- フレームワーク: FastAPI
- API仕様: OpenAPI3.0

## スキーマ

スキーマはLookerのLookMLを参考に作成しています。LookerのLookMLは、データ分析のためのモデルを定義するための言語です。LookMLは独自の構文でデータ分析のためのモデルを定義できますが、このアプリではLookMLの構文を参考にして、JSON形式でデータ分析のためのモデルを定義できるようにしています。モデルの定義方法は以下のとおりです。

```json
[
  {
    "model_id": "sales_performance",
    "display_name": "売上・業績分析モデル",
    "description": "店舗別の売上合計、商品カテゴリ別の売れ行き、月次・日次の売上トレンド（いくら売れたか）を分析する文脈。売上金額（amount）の集計を伴う質問はすべてこのモデルが担当する。",
    "target_table": "sales_summary",
    "sample_queries": [
      "先月の店舗ごとの売上を教えて",
      "カテゴリ別の売上ランキングが知りたい"
    ]
  },
  {
    "model_id": "customer_demographics",
    "display_name": "顧客属性・会員分析モデル",
    "description": "会員の年齢層、性別、会員ランクの分布、アクティブユーザー数（何人いるか）を分析する文脈。顧客の『人数』や『属性の割合』に関する質問を担当する。※売上金額は含まない。",
    "target_table": "customer_master",
    "sample_queries": [
      "現在のアクティブ会員の男女比は？",
      "20代の会員は何人登録されている？"
    ]
  }
]
```

このスキーマを使って参照するデータはAWS Glue DataCatalogに登録されているテーブルを参照します。データ分析エージェントは、スキーマに定義されたモデルを使ってデータ分析のための質問に回答できます。スキーマに定義されたモデルは、データ分析エージェントがどのテーブルを参照して、どのような質問に回答できるかを決定します。

これはLookerの会話分析エージェントから着想を得ています。Lookerの会話分析エージェントはLookMLで定義されたモデルを使って、データ分析のための質問に回答できます。

## 認証認可

AWS IAMの認証認可を使って、データ分析エージェントのアクセス制御を行います。データ分析エージェントは、AWS IAMの認証認可を使って、データ分析のための質問に回答できます。データはAmazon Athenaを使ってクエリを実行して取得します。データ分析エージェントは、AWS IAMの認証認可を使ってAmazon Athenaのクエリを実行できます。

将来的にはAWS Lake Formation (LF-Tags) の活用やAmazon Verified Permissionsの活用も検討していますが、今回はAWS IAMの認証認可を使って、データ分析エージェントのアクセス制御を行います。

## アプリ作成時の注意点

- 必ずテストを行うこと
- 機密情報を扱う場合、アプリケーション上では環境変数を使うものとし、ローカル実行では.envを作成すること
  - クラウド上ではAWS Secrets Managerを使って管理して読み出すこと

## アプリの仕様

3つのStepを踏んで、AWS AppConfigを使ったアプリケーションの設定管理とデータ分析エージェントの作成を行います。

Step1では、AWS AppConfigとLambdaを連携させて、アプリケーションの設定を管理する仕組みを作ります。
Step2では、データ分析の基盤を作ります。データ分析の基盤はデータを収集・保存・分析するための仕組みです。
Step3では、データ分析エージェントを作ります。データ分析エージェントは、データ分析の基盤を使って、データを分析するための仕組みです。

データ分析エージェントをAWS AppConfigで管理することができることを確認することがこのアプリのゴールです。

### Step1: AWS AppConfigとLambdaの連携

まずはじめに、AWS AppConfigとLambdaを連携させて、アプリケーションの設定を管理する仕組みを作ります。
利用サービスは以下のとおりです。

- AWS AppConfig
- AWS Lambda

このステップのゴールはAWS AppConfigを使ってLambdaの設定を管理することができることです。

### Step2: データ分析の基盤

次にデータ分析の基盤を作ります。データ分析の基盤はデータを収集・保存・分析するための仕組みです。このリポジトリではサンプルデータでデータカタログを作成し、分析するための基盤を構築します。
利用サービスは以下のとおりです。

- AWS Glue DataCatalog
- Amazon Athena
- Amazon S3
- AWS Lambda
- AWS AppConfig

このステップのゴールはAWS LambdaとAWS AppConfigを使ってAmazon AthenaのAPIによるクエリ実行ができることを確認することです。

### Step3: データ分析エージェントを作る

次にデータ基盤を探索するデータ分析エージェントを作ります。データ分析エージェントは、データ分析の基盤を使って、データを分析するための仕組みです。利用サービスは以下のとおりです。

- AWS AppConfig
- AWS Lambda
- AWS Glue DataCatalog
- Amazon Athena
- Amazon S3
- Amazon Bedrock
  - AgentCore

このステップのゴールはAWS AppConfigを使ってデータ分析エージェントの設定を管理できることを確認することです。

### Step4: データ分析エージェントを触ることができる画面を作る

最後にフロントエンドの画面を作成して、データ分析エージェントを触ることができるようにします。利用サービスは以下のとおりです。

- AWS AppConfig
- AWS Lambda
- AWS Amplify
- AWS Glue DataCatalog
- Amazon Athena
- Amazon S3
- Amazon Bedrock
  - AgentCore

## ブログ

以下、このリポジトリの内容をブログにまとめています。設計についての考え方や実装のポイントなどをまとめています。
実装には関係ありません。

## はじめに

## どうしてAppConfigなのか

実際のところ、アプリケーションの設定をキャッシュしたい！そんなときは相乗りしているキャッシュサービスやパラメーターストアをを使ってしまいそうになります。

しかし、この実装をしてしまうといくつかの問題が発生します。
- データキャッシュの区別がつかない
- パラメーターを更新したらアプリも更新する必要がある

順番に見ていきましょう。

## データキャッシュの区別がつかない

## パラメーターを更新したらアプリも更新する必要がある

## 課金要素

https://aws.amazon.com/jp/systems-manager/pricing/

## ハンズオン

今回はAppConfigを使った小さいLambdaを作ったあと、簡単なデータ分析エージェントを作ります。
おおまかな手順としては以下のとおりです。

- AppConfigの作成
- Lambdaの作成
- AppConfig+Lambdaの動作確認
- 分析エージェントの土台構築
- 分析エージェントの設定をAppConfigで変えてみる動作確認

### Step1の実行手順

### 1. 前提条件

- AWS CLI がインストールされ、認証済みであること
- AWS SAM CLI がインストールされていること
- `sam` コマンドが利用できること

### 2. ローカルでのテスト

```bash
make test
```

### 3. AWS へデプロイ

```bash
chmod +x scripts/deploy.sh
make deploy
```

必要に応じて、以下の環境変数でスタック名やリージョンを上書きできます。

```bash
export STACK_NAME=aws-appconfig-demo
export AWS_REGION=ap-northeast-1
export AWS_PROFILE=your-profile-name
make deploy
```

### 4. デプロイ後の確認

デプロイ後、AWS CloudFormation の出力値から以下を確認できます。

- AppConfigApplicationId
- AppConfigEnvironmentId
- AppConfigConfigurationProfileId
- AppConfigReaderFunctionName

Lambda 関数を実行すると、AppConfig の設定が返ることを確認できます。

```bash
aws lambda invoke \
  --function-name <AppConfigReaderFunctionName> \
  --payload '{}' \
  /tmp/appconfig-response.json
cat /tmp/appconfig-response.json
```

## ハンズオンの続き（Step1の内容を踏まえた流れ）

このサンプルでは、まず Step1 として AWS AppConfig で管理した設定を Lambda から取得する構成を実装しました。ここまでの内容を前提に、ハンズオンを続ける場合は次の流れで進めると分かりやすいです。

### 1. まずはローカルで動作確認する

変更を加えたら、まずはテストを実行して期待どおりに動くか確認します。

```bash
make test
```

### 2. AWS へデプロイする

SAM を使って AppConfig、Lambda、IAM ロールをデプロイします。

```bash
chmod +x scripts/deploy.sh
make deploy
```

必要に応じて、以下の環境変数でスタック名やリージョン、AWS プロファイルを指定できます。

```bash
export STACK_NAME=aws-appconfig-demo
export AWS_REGION=ap-northeast-1
export AWS_PROFILE=your-profile-name
make deploy
```

### 3. デプロイ後に Lambda から設定を確認する

CloudFormation の出力値から関数名を取得し、Lambda を実行して AppConfig から返された設定を確認します。

```bash
aws lambda invoke \
  --function-name <AppConfigReaderFunctionName> \
  --payload '{}' \
  /tmp/appconfig-response.json
cat /tmp/appconfig-response.json
```

期待する結果として、`source: "appconfig"` を含む JSON が返れば成功です。

### 4. 注意点

このハンズオンでは、次の点に注意するとスムーズに進められます。

- 変更後は必ずテストを行い、デプロイ前に動作を確認する
- AppConfig の設定は「ホスト設定の作成」だけではなく、必ず「デプロイ」まで行う
- Lambda 実行ロールには AppConfig Data API を呼び出すための権限が必要である
- リージョン、AWS プロファイル、AppConfig の Application / Environment / Configuration Profile の ID が一致しているか確認する
- 機密情報はコードに直接書かず、環境変数または Secrets Manager で管理する

### 5. 次のステップ

## Step2: データ分析基盤を作る

Step2 では、サンプルデータを S3 に配置し、Glue Data Catalog に登録したうえで、Athena を Lambda から実行できる構成を作ります。ここでは「最小構成で動かす」ことを意識して、必要最低限の IAM 権限だけを付与します。

### 1. まずは Step1 のデプロイ結果を前提にする

Step2 を試す前に、Step1 で作った AppConfig / Lambda のスタックが AWS 上にデプロイされていることを確認してください。

```bash
make deploy
```

### 2. サンプルデータを作成して S3 にアップロードする

Step2 用の Lambda を実行すると、ダミーの CSV ファイルを S3 バケットへ配置し、Glue のテーブル定義も作成します。

```bash
aws lambda invoke \
  --function-name <Step2DataPreparationFunctionName> \
  --payload '{}' \
  /tmp/step2-data.json
cat /tmp/step2-data.json
```

### 3. S3 と Glue の登録結果を確認する

アップロードされたファイルと Glue のテーブルが作成されているか確認します。

```bash
aws s3 ls s3://<DataBucketName>/raw/
aws glue get-tables --database-name appconfig_demo --query 'TableList[].Name' --output table
```

### 4. Athena からクエリを実行する

別の Lambda から Athena の API を呼び出し、登録済みデータに対してクエリを実行します。

```bash
aws lambda invoke \
  --function-name <Step2AthenaQueryFunctionName> \
  --payload '{"table_name":"customers"}' \
  /tmp/step2-athena.json --cli-binary-format raw-in-base64-out
cat /tmp/step2-athena.json
```

### 5. ここで学ぶポイント

- S3 にアップロードしたデータを Glue Data Catalog に登録すると、Athena から SQL で扱える
- Athena の実行は別 Lambda から行うことで、データ基盤とアプリケーションロジックを分離できる
- IAM は「S3 への読み書き」「Glue へのテーブル作成」「Athena の実行」だけに絞ることで、最小構成にできる

この流れを押さえておくと、次に Step3 でデータ分析エージェントを追加しやすくなります。

Step1 が完了したら、次は以下を進める構成が自然です。

- Step2: Glue DataCatalog / Athena / S3 を使ったデータ分析基盤を構築する
- Step3: Bedrock や AgentCore を使ってデータ分析エージェントを作る
- Step4: フロントエンド画面からエージェントを操作できるようにする

## まとめ

このハンズオンでは、AppConfig を使って設定を外だしし、Lambda から安全に取得する流れを実装しました。次のステップでは、この構成をデータ分析基盤やエージェントへ広げて、実運用に近い体験を作っていきます。

## 参考

## おわり
