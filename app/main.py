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

twitter_params =  {"screen_name": "", # 取得するユーザーのTwitter ID
                   "count": 5         # いいねしたツイートの取得数(最大200)
                   }

json_dictionary = []            # TwitterAPIから返ってくるJSON形式のstr型データをリストに内包される辞書型オブジェクトとして変換したものが入る = [{},{}...{}]
urls = []                       # json_dictionaryから抽出した画像のURLが入る
first_execution = True          # このプログラムの実行が初めてかどうかを示す
previous_latest_tweet_id = 0    # 前回の実行で取得したツイートの中で投稿日が最新のツイートのIDが入る。
                                # そのツイートからそれ以前の日付のJSONデータをlatest_tweet_check()関数で削除するために使う                           

def main():
  print("現在時刻：" + str(datetime.datetime.now()))

  global first_execution
  global previous_latest_tweet_id

  get_json_with_Twitter_API()

  if(first_execution == False ):
    print("二回目以降の処理のため、前回取得したツイートをチェックします")
    latest_tweet_check()
  else:
    print("初めての取得です")
    first_execution = False
    previous_latest_tweet_id = json_dictionary[0]["id"]
  
  if(json_dictionary == []):
    print("今日新しくいいねしたツイートはありません")
  else:
    url_extract()
    download_and_upload_image()
  print("----------------------------------------------------------")



def get_json_with_Twitter_API():
  global json_dictionary
  req = twitter.get("https://api.twitter.com/1.1/favorites/list.json", params = twitter_params)
  json_dictionary = json.loads(req.text)
  print("JSONを取得しました")


def latest_tweet_check():
  global previous_latest_tweet_id

  new_latest_tweet_id = json_dictionary[0]["id"] # 今回取得した最新のツイートIDが入る

  # 前回取得した最新のツイートからそれ以前のデータを削除し、次回のチェックのためにnew_latest_tweet_idをprevious_latest_tweet_idのに入れる
  for i in range(len(json_dictionary)):
    if(json_dictionary[i]["id"] == previous_latest_tweet_id):
      del json_dictionary[i:]
      previous_latest_tweet_id = new_latest_tweet_id
      break


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
  bucket = s3.Bucket('バケット名')

  upload_date = datetime.date.today()
  
  for url in urls:
    res = requests.get(url+":orig").content # 抽出したurlから原寸画像をダウンロード
    print(url + "：の画像をダウンロードしました")
    bucket.upload_fileobj(io.BytesIO(res), str(upload_date) + '/' + url[27:]) # バケット名/YYYY-MM-DD/xxx.jpg の形式でS3にアップロード
    print("ダウンロードした画像をアップロードしました")

  urls.clear() # 次回のために配列のデータを削除


schedule.every().day.at("23:59").do(main) # このプログラムを定期実行する時間帯を指定

while True:
  schedule.run_pending()
  time.sleep(1)