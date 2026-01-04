from flask import Flask, jsonify
from flask_cors import CORS
from isyatirimhisse import Hisse
import pandas as pd

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({"status": "API Çalışıyor! 🚀"})

@app.route('/api/hisseler')
def get_hisseler():
    try:
        hisse = Hisse()
        df = hisse.tum_hisseler()
        
        hisseler = []
        for _, row in df.iterrows():
            hisseler.append({
                "kod": row['Kod'],
                "ad": row['Kod'],
                "kapanis": float(row['Kapanis']) if pd.notna(row['Kapanis']) else 0.0
            })
        
        return jsonify({"data": hisseler})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/hisse/<symbol>')
def get_hisse_detay(symbol):
    try:
        hisse = Hisse()
        df = hisse.gunluk(sembol=symbol, baslangic='01-01-2024', bitis='04-01-2026')
        
        if df.empty:
            return jsonify({"error": "Veri bulunamadı"}), 404
        
        data = []
        for _, row in df.iterrows():
            data.append({
                "kod": symbol,
                "ad": symbol,
                "tarih": str(row['Tarih']),
                "acilis": float(row['Acilis']) if pd.notna(row['Acilis']) else 0.0,
                "yuksek": float(row['Yuksek']) if pd.notna(row['Yuksek']) else 0.0,
                "dusuk": float(row['Dusuk']) if pd.notna(row['Dusuk']) else 0.0,
                "kapanis": float(row['Kapanis']) if pd.notna(row['Kapanis']) else 0.0,
                "hacim": int(row['Hacim']) if pd.notna(row['Hacim']) else 0
            })
        
        return jsonify({"data": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
