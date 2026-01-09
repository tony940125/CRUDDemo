import sys
import os
import sqlite3
import getpass
from flask import Flask, jsonify, request, render_template, g

# ==========================================
# 1. 環境偵測與路徑設定
# ==========================================

# 判斷是否在 Google Colab
IS_COLAB = 'google.colab' in sys.modules

# 設定路徑變數
Curr_Path = None
ngrok = None  # 先預設為 None，稍後嘗試匯入

if IS_COLAB:
    print("☁️ 偵測到環境：Google Colab")
    from google.colab import drive
    from pyngrok import ngrok  # Colab 通常都有安裝，直接匯入

    # Colab 專用設定
    GOOGLE_PROJECT_PATH = "GRUDDemo/"
    GOOGLE_HOME_PATH = "My Drive/"
    GOOGLE_DEFAULT_PATH = "/content/drive/"

    # 掛載雲端硬碟
    drive.mount(GOOGLE_DEFAULT_PATH, force_remount=True)

    # 組合路徑
    GOOGLE_MY_PATH = os.path.join(GOOGLE_DEFAULT_PATH, GOOGLE_HOME_PATH, GOOGLE_PROJECT_PATH)

    # 切換目錄
    try:
        if not os.path.exists(GOOGLE_MY_PATH):
            print(f"找不到路徑 {GOOGLE_MY_PATH}，嘗試切換到 My Drive")
            GOOGLE_MY_PATH = os.path.join(GOOGLE_DEFAULT_PATH, GOOGLE_HOME_PATH)

        os.chdir(GOOGLE_MY_PATH)
        Curr_Path = os.getcwd()
        print(f"成功切換目錄 (Colab)：{Curr_Path}")
    except Exception as e:
        print(f"路徑設定失敗：{e}")
        sys.exit()

else:
    print(f" 偵測到環境：Local ({sys.platform})")
    # 本機環境 (Windows / macOS)
    try:
        Curr_Path = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        Curr_Path = os.getcwd()

    os.chdir(Curr_Path)
    print(f"工作目錄設定為 (Local)：{Curr_Path}")

    # 嘗試在本機匯入 pyngrok，如果沒裝也不會報錯，只是 ngrok 變數維持 None
    try:
        from pyngrok import ngrok
    except ImportError:
        ngrok = None

# ==========================================
# 2. 設定 Flask 路徑
# ==========================================
TEMPLATE_DIR = os.path.join(Curr_Path, 'templates')
STATIC_DIR = os.path.join(Curr_Path, 'static')
DB_PATH = os.path.join(Curr_Path, 'pharmacy.db')

print(f"📂 Templates: {TEMPLATE_DIR}")
print(f"📂 Database : {DB_PATH}")

# 檢查 index.html
if not os.path.exists(os.path.join(TEMPLATE_DIR, 'index.html')):
    print(f"警告：找不到 index.html！請確認檔案位於：{os.path.join(TEMPLATE_DIR, 'index.html')}")
else:
    print("index.html 檢查存在！")

# ==========================================
# 3. Ngrok Token 輸入 (已修改：強制詢問)
# ==========================================
NGROK_AUTH_TOKEN = ""

# 修改點：不管環境為何，一律詢問 (讓 Mac/Win 使用者也有機會輸入)
print("\n" + "=" * 40)
print("Ngrok 設定")
print("請輸入 Ngrok Authtoken：")
print("(若不想使用 Ngrok，請直接按 [Enter] 跳過)")
print("=" * 40)

if IS_COLAB:
    NGROK_AUTH_TOKEN = getpass.getpass("Token: ")
else:
    NGROK_AUTH_TOKEN = input("Token: ")

# 防呆檢查：如果使用者輸入了 Token，但電腦其實沒裝 pyngrok
if NGROK_AUTH_TOKEN.strip() and (ngrok is None):
    print("\n警告：你輸入了 Token，但系統未偵測到 'pyngrok' 套件。")
    print("將忽略 Ngrok 設定，強制使用 Localhost 模式。")
    print("若想使用 Ngrok，請先在終端機執行：pip install pyngrok")

# 初始化 Flask
app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)


# ==========================================
# 4. 資料庫與 API 邏輯 (CRUD)
# ==========================================

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''
                       CREATE TABLE IF NOT EXISTS medicines
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           name
                           TEXT
                           NOT
                           NULL,
                           category
                           TEXT,
                           price
                           REAL,
                           stock
                           INTEGER,
                           expiry_date
                           TEXT
                       )
                       ''')
        db.commit()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/medicines', methods=['GET'])
def get_medicines():
    try:
        cur = get_db().cursor()
        cur.execute("SELECT * FROM medicines ORDER BY id DESC")
        rows = cur.fetchall()
        data = [dict(row) for row in rows]
        return jsonify({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/medicines/<int:medicine_id>', methods=['GET'])
def get_single_medicine(medicine_id):
    cur = get_db().cursor()
    cur.execute("SELECT * FROM medicines WHERE id = ?", (medicine_id,))
    row = cur.fetchone()
    if row:
        return jsonify({"status": "success", "data": dict(row)}), 200
    return jsonify({"status": "error", "message": "找不到該藥品"}), 404


@app.route('/api/medicines', methods=['POST'])
def add_medicine():
    new_data = request.get_json()
    name = new_data.get('name')
    category = new_data.get('category')
    price = new_data.get('price')
    stock = new_data.get('stock')
    expiry_date = new_data.get('expiry_date')

    if not name:
        return jsonify({"status": "error", "message": "藥品名稱為必填"}), 400

    try:
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO medicines (name, category, price, stock, expiry_date) VALUES (?, ?, ?, ?, ?)",
            (name, category, price, stock, expiry_date)
        )
        db.commit()
        return jsonify({"status": "success", "message": "藥品新增成功", "id": cur.lastrowid}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/medicines/<int:medicine_id>', methods=['PUT'])
def update_medicine(medicine_id):
    update_data = request.get_json()
    name = update_data.get('name')
    category = update_data.get('category')
    price = update_data.get('price')
    stock = update_data.get('stock')
    expiry_date = update_data.get('expiry_date')

    try:
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT id FROM medicines WHERE id = ?", (medicine_id,))
        if not cur.fetchone():
            return jsonify({"status": "error", "message": "找不到該藥品"}), 404

        cur.execute(
            '''UPDATE medicines
               SET name=?,
                   category=?,
                   price=?,
                   stock=?,
                   expiry_date=?
               WHERE id = ?''',
            (name, category, price, stock, expiry_date, medicine_id)
        )
        db.commit()
        return jsonify({"status": "success", "message": "藥品更新成功"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/medicines/<int:medicine_id>', methods=['DELETE'])
def delete_medicine(medicine_id):
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute("DELETE FROM medicines WHERE id = ?", (medicine_id,))
        if cur.rowcount == 0:
            return jsonify({"status": "error", "message": "找不到該藥品或已刪除"}), 404
        db.commit()
        return jsonify({"status": "success", "message": "藥品已刪除"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================================
# 5. 啟動伺服器
# ==========================================
if __name__ == '__main__':
    # 初始化資料庫
    init_db()

    use_ngrok = False

    # 判斷使用者是否有輸入 Token (且系統有支援 ngrok)
    if NGROK_AUTH_TOKEN and NGROK_AUTH_TOKEN.strip():
        if ngrok:
            print(f"\n偵測到 Token，正在啟動 Ngrok...")
            try:
                # 這裡不需要重複 kill，因為下面直接連線
                ngrok.set_auth_token(NGROK_AUTH_TOKEN)
                ngrok.kill()
                public_url = ngrok.connect(5000).public_url
                print(f"\n======== 你的公開網址如下 (Ngrok) ========")
                print(f"{public_url}")
                print(f"==========================================\n")
                use_ngrok = True
            except Exception as e:
                print(f"Ngrok 啟動失敗: {e}")
                print("將自動切換回 Localhost 模式...")
        else:
            # 這裡就是上面防呆檢查後，真正執行時的邏輯
            print("未安裝 pyngrok 套件，跳過 Ngrok 啟動。")
    else:
        print("\n使用者未輸入 Token (或輸入空白)，跳過 Ngrok 設定。")

    # 如果沒有使用 Ngrok，顯示 Localhost 資訊
    if not use_ngrok:
        print(f"\n======== 本機伺服器模式 ========")
        print(f"http://127.0.0.1:5000")
        print(f"================================\n")

    # 啟動 Flask
    app.run(port=5005, host='0.0.0.0', debug=True, use_reloader=False)
