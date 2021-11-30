# 概要
  Twitterでアカウントが「いいね」したツイートの中から画像のみを抽出してクラウドストレージ(AWS S3)かローカルのファイルサーバに保存する処理を定期実行するアプリケーションです。

# 必要なもの
本アプリケーションは非営利かつ私的利用の範囲内で画像を保存することを目的としているため、利用者は自身の責任のもとでTwitterAPIキーやAWSアカウントを用意し、運用する必要があります。
- TwitterAPIキー
  - 本アプリの実行環境上に環境変数として設定したアクセストークンキーに紐づいているアカウントのいいね欄のみが取得できます。つまり、他者が所持するアカウントのいいね欄を本人の許可無しに本アプリを用いて取得することはできません
## AWS上で稼働させる場合
- AWSアカウント
  - VPC,EC2,S3等の作成およびアクセスが可能なIAMユーザーおよびそのアクセスキーとシークレットアクセスキー
- terraform(あると便利)
- [Cyberduck](https://cyberduck.io/)
  - S3バケットからローカルPCに一括でオブジェクト(画像)をダウンロードすることができます

# 仕様
## 取得可能な画像ツイートのタイプ
  - 画像のみ(1枚だけでも複数枚含まれていても取得可能)
  - 画像+テキスト(1枚だけでも複数枚含まれていても取得可能)

## 取得できない画像ツイートのタイプ
発見次第追記します
- 引用RTとして投稿したツイートに含まれている、引用者自身が添付した画像(つまり、引用されている側のツイートに含まれている画像ではなく、引用している側が引用RTに添付した画像)
- Twitter for Advertisersから投稿されたツイートに含まれる画像(2021/10/23時点)

## 動作
- TwitterAPIから対象のアカウントの「いいね」しているツイートの情報をJSONで受け取り、その中に含まれる画像URLを抽出した後、そのURLから画像をオリジナルサイズでダウンロードし、AWS S3バケットまたはローカルに保存します
- ダウンロードされた画像はデフォルトではその日ごとに日付をフォルダ名とするフォルダを作成し、その中にまとめて保存するようになっています(raspberry-pi4ブランチは未対応のため今後そうなるように変更予定)
- デフォルトでは一日に一回、利用者が指定した時間に保存処理を行うようにしています(/app/main.py 132行目)
  - 定期実行にはpythonの[schedule](https://schedule.readthedocs.io/en/stable/)ライブラリを使用しています
  - main.pyの132行目を変更することで柔軟な変更が可能です
- 一度保存した画像を次回以降の実行時に再度保存してしまうことを防ぐために、その時取得した中で最新の日時に投稿されたツイートのIDを変数latest_tweet_idに格納して、次回の実行時にはそのlatest_tweet_idとその時取得した各ツイートのIDの比較を行い、latest_tweet_idのツイート(つまり前回取得した最新の日時のツイート)より以前の日時の物はダウンロードリストから削除します
  - ツイートIDはより新しい日時に投稿されたツイートほど値(数値)が大きくなります
  - TwitterAPIの仕様上、「いいね」した順ではなく、「いいね」したツイートが投稿された順に取得されます
  - 上記のような理由で、「その日いいねしたツイートの画像をその日に保存する」といった形での使用が基本になるかと思います
  - 本アプリの実行を停止するとlatest_tweet_idの情報は失われます

## ブランチの説明
- 現状、masterブランチがAWSで稼働させる用、raspberry-pi4ブランチがローカルで稼働させる用です(今後変更する可能性有り)

# Deploy(AWS)
1. 本リポジトリをローカルPCへcloneする
 ```bash
$ git clone https://github.com/Qxhisl/Twitter-fav-image-downloader.git
```
2. terraformディレクトリにterraform.tfvarsファイルを作成して、以下のような変数を定義し、値に自身のIAMユーザーキーを設定する
```bash
aws_access_key = ""
aws_secret_key = ""
```

4. terraformコマンドを実行
```bash
$ terraform init
$ terraform validate
$ terraform apply
```
5. SSHでEC2インスタンスに接続し、aws configureコマンドでIAMユーザーキーを設定する
```bash
$ ssh ubuntu@x.x.x.x
ubuntu@ip-x-x-x-x:~$  cd Twitter-fav-image-downloader
ubuntu@ip-x-x-x-x:~/Twitter-fav-image-downloader$ aws configure
AWS Access Key ID [None]: #キーを入力
AWS Secret Access Key [None]: #キーを入力
Default region name [None]: ap-northeast-1
Default output format[None]:
```

6. setup.shに環境変数の値を設定して実行する
```bash
ubuntu@ip-x-x-x-x:~/Twitter-fav-image-downloader$ vi setup.sh
ubuntu@ip-x-x-x-x:~/Twitter-fav-image-downloader$ source setup.sh
```

7. main.pyを起動する(必要があればtmux上で)
```bash
ubuntu@ip-x-x-x-x:~/Twitter-fav-image-downloader$ cd app
# tmux上で実行する場合は起動する
ubuntu@ip-x-x-x-x:~/Twitter-fav-image-downloader$ tmux new -s Twitter-fav-image-downloader
ubuntu@ip-x-x-x-x:~/Twitter-fav-image-downloader/app$ python3 main.py
```
