from requests_oauthlib import OAuth1Session
import boto3
import io
import os
import requests
import json
import datetime
import schedule
import time

twitter = OAuth1Session(os.environ['CONSUMER_KEY'], os.environ['CONSUMER_SECRET'], os.environ['ACCESS_TOKEN'], os.environ['ACCESS_TOKEN_SECRET'])

twitter_params =  {"screen_name": os.environ['TWITTER_USER_ID'], # 取得するユーザーのTwitter ID
                   "count": int(os.environ['TWITTER_API_COUNT'])      # 取得するツイート数(最大200)
                   }

json_dictionary = []            # TwitterAPIから返ってくるJSON形式のstr型データをリストに内包される辞書型オブジェクトとして変換したものが入る = [{},{}...{}]
urls = []                       # json_dictionaryから抽出した画像のURLが入る
first_execution = True          # このプログラムの実行が初めてか、二回目以降かを示す

latest_tweet_id = 0   # 前回の実行で取得したツイートの中で投稿日時が最新のツイートのIDが入る
                      # ツイートのIDは投稿した日時が遅い(より現在時刻に近くなる)ほど値が大きくなる
                      # 一度DLした画像を再度DLしてしまうのを避けるため、前回取得した最新時刻のツイートからそれ以前の日時に投稿されたツイートのJSONデータをlatest_tweet_check()関数で削除するために使う                           

new_tweets_flag = ""

def main():
  print("現在時刻：" + str(datetime.datetime.now()))

  global first_execution
  global latest_tweet_id
  global new_tweets_flag

  get_json_with_Twitter_API()

  if first_execution == True:
    print("初めての実行です")

    # 初回実行時にいいねが一つ以上存在する場合
    if json_dictionary:
      first_execution = False
      latest_tweet_id = json_dictionary[0]["id"]
      url_extract()
      download_and_upload_image()

    # 初回実行時にいいねが存在しない場合
    else:
      first_execution = False
      print("現在いいねしているツイートはありません")
      print("----------------------------------------------------------")

  elif first_execution == False:
    print("二回目以降の実行のため、前回取得したツイートをチェックします")
    new_tweets_flag = latest_tweet_check()

    if new_tweets_flag == "new-favtweet":
      latest_tweet_id = json_dictionary[0]["id"]
      url_extract()
      download_and_upload_image()
    elif new_tweets_flag == "no-new-favtweet":
      print("今日新しくいいねしたツイートはありませんでした")
      print("----------------------------------------------------------")
    elif new_tweets_flag == "no-favtweet":
      print("現在いいねしているツイートはありません")
      print("----------------------------------------------------------")


def get_json_with_Twitter_API():
  global json_dictionary
  req = twitter.get("https://api.twitter.com/1.1/favorites/list.json", params = twitter_params)
  json_dictionary = json.loads(req.text)
  print("JSONを取得しました")


def latest_tweet_check() -> str:
  global latest_tweet_id

  # 二回目以降の実行時でもいいねしているツイートが存在しない場合
  if json_dictionary == []:
    return "no-favtweet"

  # いいねしているツイートが一つ以上存在する場合
  for i in range(len(json_dictionary)):
    if json_dictionary[i]["id"] <= latest_tweet_id:
      del json_dictionary[i:]

      # 新しくいいねしたツイートが存在しなかった場合
      if json_dictionary == []:
        return "no-new-favtweet"
    
      break

  return "new-favtweet"
      

def url_extract():
  global urls

  # latest_tweet_check()で切り落とされたデータの数だけループして配列urlsに抽出した画像urlを入れる
  for i in range(len(json_dictionary)):
    print(str(i+1) + "番目のツイートから画像URLを抽出します")
    try:
      json_dictionary[i]["extended_entities"]["media"]
    except KeyError: # 取得したツイートに画像がない場合
      print(f"このツイート : 「{json_dictionary[i]['text']}」には画像が含まれていませんでした。")
    else:
      # gifや動画のツイートからサムネイル画像を取得してしまうのを防ぐための処理
      if json_dictionary[i]["extended_entities"]["media"][0]["type"] != "photo":
        continue
      image_num = len(json_dictionary[i]["extended_entities"]["media"])
      for j in range(image_num):
        urls.append(json_dictionary[i]["extended_entities"]["media"][j]["media_url"])


def download_and_upload_image():
  global urls
  s3 = boto3.resource('s3')
  bucket = s3.Bucket(os.environ['S3_BUCKET_NAME'])

  upload_date = datetime.date.today()
  
  for url in urls:
    res = requests.get(url+":orig").content # 抽出したurlから原寸画像をダウンロード
    print(url + "：の画像をダウンロードしました")
    bucket.upload_fileobj(io.BytesIO(res), str(upload_date) + '/' + url[27:]) # バケット名/YYYY-MM-DD/xxx.jpg の形式でS3にアップロード
    print("ダウンロードした画像をアップロードしました")
    print("----------------------------------------------------------")

  urls.clear() # 次回のために配列のデータを削除


schedule.every().day.at(os.environ['EXECUTION_DATE']).do(main) # このプログラムを定期実行する時間帯を指定

while True:
  schedule.run_pending()
  time.sleep(1)