# Gesture Data Generator (手勢辨識 AI 資料生成器)

**Gesture Data Generator** 是一個專為 ISP 晶片 NPU 模型訓練設計的高效數據增強工具。它利用 Google Gemini 2.5 Flash Image 模型的強大生成能力，協助開發者快速建立多樣化、高品質的手勢訓練數據集。

本工具特別針對 NPU 訓練需求優化，所有輸出皆自動標準化為 **320x180 灰階** 格式，並內建 **AI 視覺品質分析 (QC)** 功能，確保數據的有效性。

![App Screenshot](https://via.placeholder.com/800x450?text=Gesture+Data+Generator+UI) *(請自行替換為實際截圖)*

## 🚀 核心功能 (Key Features)

1.  **情境變異生成 (Variation Generation)**
    *   基於種子圖片 (Seed Image)，保留原始手勢動作。
    *   自動變換背景 (如：辦公室、戶外、極地)、光影條件 (逆光、側光) 與手部特徵 (膚色、紋理)。
    *   增加數據集的多樣性，提升模型的泛化能力。

2.  **手勢動作修改 (Gesture Modification)**
    *   結合「種子圖片的風格」與「參考圖片的動作」。
    *   用於快速擴充特定風格下的不同手勢類別。

3.  **AI 視覺品質分析 (AI Vision QC)**
    *   **自動化品質控管**：生成後立即分析圖片品質。
    *   **檢測項目**：
        *   手指數量 (Finger Count)：確保解剖結構正確 (5指)。
        *   真實度評分 (Realism Score)：1-10 分。
        *   光照分析 (Lighting)：確認光影是否符合訓練需求。
        *   潛在問題 (Issues)：偵測模糊、偽影或遮擋。

4.  **NPU 專用格式優化**
    *   自動輸出 **320x180** 解析度。
    *   自動轉換為 **L 模式 (8-bit Grayscale)**。
    *   模擬真實感測器噪點 (Sensor Noise) 與動態模糊 (Motion Blur)。

## 🛠️ 技術棧 (Tech Stack)

*   **Backend**: Python, Flask
*   **AI Model**: Google Gemini 2.5 Flash Image (via `google-generativeai`)
*   **Image Processing**: Pillow (PIL)
*   **Frontend**: HTML5, CSS3 (Dark Mode), Vanilla JavaScript
*   **Deployment**: Localhost (開發環境)

## 📦 安裝與執行 (Installation & Setup)

### 1. 克隆專案或下載程式碼
```bash
git clone <repository-url>
cd gesture_gen
```

### 2. 建立虛擬環境 (建議)
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows
```

### 3. 安裝依賴套件
```bash
pip install -r requirements.txt
```

### 4. 啟動應用程式
```bash
python3 app.py
```
伺服器將啟動於 `http://127.0.0.1:5000`。

## 📖 使用指南 (Usage Guide)

1.  **設定 API Key**：
    *   開啟網頁，在左上角輸入您的 **Google Gemini API Key**。
    *   金鑰僅暫存於瀏覽器，不會上傳至伺服器儲存。

2.  **選擇模式**：
    *   **情境變異生成**：上傳一張種子圖片，輸入 Prompt (如 "cyberpunk neon background")，生成不同背景的相同手勢。
    *   **手勢動作修改**：上傳種子圖片 (風格來源) 與參考圖片 (動作來源)，進行風格遷移。

3.  **生成與分析**：
    *   點擊「開始生成圖片」。
    *   生成結果將顯示於下方畫廊。
    *   點擊圖片下方的 **"🔍 AI 分析"** 按鈕，查看 Gemini 對該圖片的品質評估報告。

4.  **下載數據**：
    *   點擊「下載圖片」將符合需求的訓練資料儲存至本機。

## 📂 專案結構 (Project Structure)

```
gesture_gen/
├── app.py              # Flask 應用程式主入口 (API Endpoints)
├── gemini_client.py    # Gemini API 封裝 (生成與分析邏輯)
├── utils.py            # 影像處理工具 (灰階、縮放)
├── requirements.txt    # Python 依賴列表
├── static/
│   ├── css/
│   │   └── style.css   # 樣式表 (Dark Theme)
│   └── js/
│       └── main.js     # 前端邏輯 (API 串接、UI 互動)
└── templates/
    └── index.html      # 主要使用者介面
```

## ⚠️ 注意事項

*   本工具依賴 Google Gemini API，使用時請確保網路連線正常。
*   生成的圖片僅供 AI 模型訓練使用，請遵守 Google Generative AI 的使用條款。
*   建議定期檢查 API 使用量 (Quota)。

---
**Developed for NPU AI Model Training**
