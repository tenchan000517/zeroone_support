# DJアイズ - ZERO to ONE サポートBot 🤖

起業家・イノベーター向けDiscordコミュニティBot

## 🎮 機能一覧

### 💬 基本機能
- **AI対話**: メンションして質問すると、Gemini AIが回答
- **天気予報**: 全国の天気情報をリアルタイム取得
- **Wikipedia検索**: 気になる言葉を即座に検索
- **なろう小説検索**: 人気Web小説を検索

### 🔮 占い・エンタメ
- **ZERO to ONE星座占い**: 起業家向け運勢（1日1回）
- **スタートアップおみくじ**: ビジネス運を占う
- **サイコパス診断**: 犯罪係数チェック
- **ランブル**: 最大50人参加のバトルロイヤルゲーム
- **じゃんけん**: 本田圭佑との勝率3%勝負
- **マインスイーパー**: Discord上で楽しめるパズルゲーム
- **ダイスロール**: nDn形式でサイコロを振る

### 💰 ポイントシステム
- **デイリーボーナス**: 毎日100ポイント獲得
- **ランキング**: メンバー間競争
- **ロール購入**: ポイントで特別ロール獲得
- **ポイント管理**: 管理者によるポイント付与・削除

### 📰 定期配信（毎朝7時）
- **月曜**: 💎 起業家格言
- **火曜**: 📊 ビジネストレンド
- **水曜**: 🛠️ スキルアップTips
- **木曜**: 🌐 テックニュース（Googleニュース連携）
- **金曜**: 🎯 今日のチャレンジ
- **土曜**: 🎪 地域イベント情報（Doorkeeper API連携）
- **日曜**: 🚀 成功マインドセット

## 🚀 使い方

### 一般ユーザー向けコマンド

#### スラッシュコマンド
```
/help              # 全機能の使い方表示
/point check       # ポイント確認
/point daily       # デイリーボーナス獲得
/point ranking     # ランキング表示
/rumble           # バトルロイヤル開始
```

#### テキストコマンド
```
今日の運勢         # ZERO to ONE占い（1日1回）
おみくじ          # スタートアップおみくじ
犯罪係数          # サイコパス診断

@DJアイズ 天気     # 天気予報（県名を聞かれます）
@DJアイズ って何？  # Wikipedia検索
@DJアイズ 慰めて   # 励ましの名言
@DJアイズ グー     # じゃんけん勝負
@DJアイズ 1d6     # ダイスロール
@DJアイズ マインスイーパ  # ゲーム開始
```

### 管理者向けコマンド

#### 設定管理
```
/help_admin           # 管理者ガイド表示
/weekly_config show   # 現在の設定確認
/weekly_config channel #チャンネル名  # 送信先設定
/weekly_config mention @ロール名      # メンション設定
/weekly_config regions 愛知県,東京都   # 地域設定
/weekly_config schedule weekday:monday hour:9 minute:0  # スケジュール変更
```

#### テスト機能
```
/weekly_test quotes   # 起業家格言テスト
/weekly_test events   # イベント情報テスト
/weekly_test tech     # テックニュース（リアルタイム）
/welcome_test        # ウェルカムメッセージプレビュー
```

#### ポイント管理
```
/point give @ユーザー 1000    # ポイント付与
/point remove @ユーザー 500   # ポイント削除
/point set @ユーザー 2000     # ポイント設定
/role_panel create           # ロール購入パネル作成
```

## 📋 必要権限

Bot招待時に以下の権限が必要です：
- ✅ メッセージ送信・読取
- ✅ 埋め込みリンク
- ✅ スラッシュコマンド使用
- ✅ ロール管理（ロールパネル機能用）
- ✅ メンション送信（@everyone, @here, ロール）
- ✅ メッセージ履歴を読む
- ✅ リアクションを追加

**権限整数値**: 537133184

詳細: [DISCORD_PERMISSIONS.md](DISCORD_PERMISSIONS.md)

## 🔧 セットアップ

管理者向けの詳細なセットアップ手順：
[ADMIN_GUIDE.md](ADMIN_GUIDE.md)

--

2019/05/22: first commit.

2019/06/14: add some function.

2019/12/02: add some function, and refactor file structure.

2019/12/16: modify waruiko-point.py and keisuke-honda.py.

2019/12/20: modify about token management.

2020/03/19: add setup process to README.md and requirements.txt, and make minor changes.

--

## セットアップ手順
1. github([kumo-san](https://github.com/TakaseIkegami/KUMOSAN))からコードをダウンロードします。
    - `$ git clone https://github.com/TakaseIkegami/KUMOSAN`

2. Python3(v3.6.0)を利用できるようにします。
    - おすすめは[こちら](https://github.com/TakaseIkegami/setup_scripts/blob/master/pyenv/pyenv_setup.sh)をダウンロードしてきて、pyenvの環境を自動でセットアップ！
        - `$ git clone https://github.com/TakaseIkegami/setup_scripts`
        - `$ source pyenv/pyenv_setup.sh`
            - ※このとき、 `sh` や `bash` ではなく、 `source` で実行しましょう。
        - `$ pyenv global 3.6.0`

3. pipに必要なパッケージの導入
    - pyenv環境の場合
        - `$ pip install -r requirements.txt`
        - (サーバで `$ pip freeze > requirements.txt` してきたものを、そのまま置いてるので不要なものも入ってると思いますがご容赦下さい^^;)
    - Ubuntu等にデフォルトで入っているPython3を使う場合
        - `$ pip3 install -r requirements.txt`

4. ご自身のDiscord環境用に設定ファイルを書き換えます。
    - `$ vim config.ini` 等、好きなエディタで開いて編集していきます。
    - トークンは[Discord Developer Portal](https://discordapp.com/developers/applications/)から取得できます。 
        - `Discord Developer Portal > (ご自身が新規作成したアプリ(bot)) > Bot > Build-A-bot > TOKEN` から `Copy` をクリックしてクリップボードにコピー。
    - 管理者用IDは、ご自身のDiscordサーバでご自身のアカウントを右クリック(右側のユーザ一覧) > 「IDをコピー」で取得できます。
    - チャンネルIDは、ご自身のDiscordサーバで建てた任意のテキストチャンネルを右クリック(左側のチャンネル一覧) > 「IDをコピー」で取得できます。

5. 雲さんの起動チェック
    - pyenv環境の場合
        - `$ python kumosan.py`
    - Ubuntu等にデフォルトで入っているPython3を使う場合
        - `$ python3 kumosan.py`

6. 無事起動できたら、デーモンで動かすなりして常駐させましょう。
    - おすすめはscreen内での実行です。
        - `$ screen -S kumosan`
        - `$ python kumosan.py`
        - (screenを出るには「(Ctrl + a) + d」)



## いまのところ雲さんができること一覧
### 通常機能
- 挨拶
  - 挨拶はコミュニケーションの基本！
  - `雲さんおはよ`

- 全国の詳細な天気情報を提供
  - 空に浮かぶ雲さんにとって天気予報なんてものは朝飯前だ！
  - `雲さん東京の天気教えて`
  - ([livedoor天気情報API](http://weather.livedoor.com)を使用させていただいています。)

- wikipedia検索
  - 「なんでもは知らないよ。wikipediaに載ってることだけっ♡」
  - `雲さん RWBYって何？`

- おみくじ
  - 雲さんは神聖術の心得があるので皆さんの運勢を占ってくれます。
  - `雲さんおみくじ引かせて！`

- 占い
  - 雲さんは占星術の心得もあるので皆さんの運勢を占ってくれます。
  - `雲さん 双子座の今日の運勢は？`
  - ([Web ad Fortune 無料版API](http://jugemkey.jp/api/waf/api_free.php)を使用させていただいております。)
    - powerd by <a href="http://jugemkey.jp/api/">JugemKey</a>
    - 【PR】<a href="http://www.tarim.co.jp/">原宿占い館 塔里木</a>

- Miller-Rabin-Algorithmによる超巨大素数の高速判定
  - `雲さん 6700417は素数？`

- 同サーバで稼働中のMinecraftへの kick シグナル送信
  - 寝落ちされて(現実)、寝れない(仮想)！困った！そんな時は雲さんにお願いだ！
  - `雲さん minecraft kick マイクラID名`
  - ※ Minecraftをscreenにて起動している状態を想定しています。

- 名言  - 雲さんは大変博識なので、たくさんの名言知っているのである。
  - `雲さん助言ちょうだい`
  - (※注意※ 尚、本プログラムは[名言集.com](http://www.meigensyu.com/)様をスクレイピングさせていただいております。ご使用の際はサイトへ不可が掛からないようリクエスト数にご注意下さい。)

- ドミネーター起動
  - 雲さんはお空からあなた達の色相を毎日チェックしています。
  - `雲さん @雲さん#2134 の犯罪係数はいくつ？`

- 悪い子ポイント
  - 雲さんは皆の悪い子ポイントを数えているのです。
  - `雲さん wp +1 @雲さん#2134` 
  - `users/` ディレクトリ内にユーザ別のファイルを自動生成することで保持します。

- マインスイーパー
  - 暇な時は雲さんとマインスイーパーであそぼう！
  - `雲さんあそぼ`

- 勝率3%のじゃんけん
  - 本田圭佑
  - `雲さん グー`

- nDnのダイスロール
  - いっぱいサイコロを振ってくれる
  - `雲さん 10d100`

- テキストチャンネルのログ一掃
  - 特定のチャンネルのチャットログを一掃してくれるのだ！
  - `雲さん おそうじして`
  - `removed_chat_logs/` ディレクトリ内に日付別のファイルを自動生成し、消去したチャットログを残します。

### 管理者用機能
- 雲さんから投稿する
  - 管理者の言葉を雲さんが代弁してくれるぞ！全体へのアナウンス等に使おう！
  - 【使い方】
    - `config.ini > [USE_CHANNELS] > back_mode` に雲さんを操る用のチャンネルIDを格納する。(雲さん　が入れるなら、プライベートチャンネルでも可)
    - `(同上) > main_chat, bot_salon, grave, storm, dev, pokemon` に代弁先のチャンネルIDを格納する。
    - Discordのback_modeのチャンネルにて、 `storm こちら雲さんです！` という風に書き込むと `[USE_CHANNELS]` で設定しておいた対応チャンネル(この場合storm)で、雲さんが発言してくれるのだ！

