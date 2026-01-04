from flask import Flask, jsonify, request
from flask_cors import CORS
from isyatirimhisse import fetch_stock_data
from datetime import datetime, timedelta
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

# Cache için basit dictionary
cache = {}
CACHE_DURATION = timedelta(hours=1)

def get_cached_data(key):
    if key in cache:
        data, timestamp = cache[key]
        if datetime.now() - timestamp < CACHE_DURATION:
            return data
    return None

def set_cached_data(key, data):
    cache[key] = (data, datetime.now())

@app.route('/')
def home():
    return jsonify({
        "status": "OK",
        "message": "Hisse Analiz API v1.0",
        "endpoints": {
            "/api/historical": "Geçmiş veri çek",
            "/api/symbols": "BIST hisse listesi",
            "/health": "Sağlık kontrolü"
        }
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/symbols', methods=['GET'])
def get_symbols():
    cached = get_cached_data('symbols')
    if cached:
        return jsonify(cached)
    
    try:
        symbols = [
            "THYAO", "GARAN", "AKBNK", "ISCTR", "YKBNK", "SAHOL", "PETKM",
            "SISE", "KCHOL", "TUPRS", "ASELS", "TCELL", "EREGL", "KOZAL",
            "ARCLK", "BIMAS", "FROTO", "HEKTS", "TAVHL", "PGSUS", "EKGYO",
            "MGROS", "TOASO", "TTKOM", "VESTL", "DOHOL", "ENKAI", "KOZAA",
            "SODA", "KRDMD", "TKFEN", "AEFES", "AKSA", "ALARK", "ANACM"
        ]
        
        result = {
            "success": True,
            "count": len(symbols),
            "symbols": symbols
        }
        
        set_cached_data('symbols', result)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/historical', methods=['GET', 'POST'])
def get_historical_data():
    try:
        if request.method == 'POST':
            data = request.get_json()
            symbol = data.get('symbol')
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            period = data.get('period')
        else:
            symbol = request.args.get('symbol')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            period = request.args.get('period')
        
        if not symbol:
            return jsonify({
                "success": False,
                "error": "symbol parametresi gerekli"
            }), 400
        
        if period and not (start_date and end_date):
            end_date = datetime.now().strftime("%d-%m-%Y")
            
            if period == '1m':
                start = datetime.now() - timedelta(days=30)
            elif period == '3m':
                start = datetime.now() - timedelta(days=90)
            elif period == '6m':
                start = datetime.now() - timedelta(days=180)
            elif period == '1y':
                start = datetime.now() - timedelta(days=365)
            elif period == '2y':
                start = datetime.now() - timedelta(days=730)
            elif period == '5y':
                start = datetime.now() - timedelta(days=1825)
            else:
                return jsonify({
                    "success": False,
                    "error": "Geçersiz period. Kullanılabilir: 1m, 3m, 6m, 1y, 2y, 5y"
                }), 400
            
            start_date = start.strftime("%d-%m-%Y")
        
        if not start_date or not end_date:
            return jsonify({
                "success": False,
                "error": "start_date ve end_date veya period gerekli"
            }), 400
        
        cache_key = f"{symbol}_{start_date}_{end_date}"
        cached = get_cached_data(cache_key)
        if cached:
            return jsonify(cached)
        
        df = fetch_stock_data(
            symbols=symbol,
            start_date=start_date,
            end_date=end_date,
            save_to_excel=False
        )
        
        if df is None or df.empty:
            return jsonify({
                "success": False,
                "error": "Veri bulunamadı"
            }), 404
        
        df_normalized = df.rename(columns={
            'Açılış': 'acilis',
            'Yüksek': 'yuksek',
            'Düşük': 'dusuk',
            'Kapanış': 'kapanis',
            'Hacim': 'hacim',
            'Tarih': 'tarih'
        })
        
        data_list = df_normalized.to_dict('records')
        
        for item in data_list:
            if 'tarih' in item and isinstance(item['tarih'], pd.Timestamp):
                item['tarih'] = item['tarih'].strftime('%Y-%m-%d')
        
        result = {
            "success": True,
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "count": len(data_list),
            "data": data_list
        }
        
        set_cached_data(cache_key, result)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
