from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd
import random

app = Flask(__name__)
CORS(app)

# Gerçek BIST hisse kodları
BIST_STOCKS = [
    "THYAO", "GARAN", "AKBNK", "EREGL", "SAHOL", "PETKM", "SISE", "TTKOM",
    "KCHOL", "VAKBN", "TCELL", "TUPRS", "BIMAS", "ASELS", "SASA", "KOZAL",
    "KOZAA", "TAVHL", "PGSUS", "ENKAI", "FROTO", "TOASO", "ARCLK", "DOHOL"
]

@app.route('/')
def home():
    return jsonify({"status": "API Çalışıyor! 🚀"})

@app.route('/api/hisseler')
def get_hisseler():
    """Test için dummy hisse listesi"""
    hisseler = []
    for kod in BIST_STOCKS:
        hisseler.append({
            "kod": kod,
            "ad": kod,
            "kapanis": round(10 + random.uniform(0, 100), 2)
        })
    return jsonify({"data": hisseler})

@app.route('/api/hisse/<symbol>')
def get_hisse_detay(symbol):
    """Test için dummy geçmiş veri"""
    data = []
    base_price = 50.0
    
    for i in range(100):
        change = random.uniform(-2, 2)
        price = base_price + change
        
        data.append({
            "kod": symbol,
            "ad": symbol,
            "tarih": f"2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
            "acilis": round(price - abs(change/2), 2),
            "yuksek": round(price + abs(change), 2),
            "dusuk": round(price - abs(change), 2),
            "kapanis": round(price, 2),
            "hacim": random.randint(1000000, 10000000)
        })
        base_price = price
    
    return jsonify({"data": data})

if __name__ == '__main__':
    app.run(debug=True)
