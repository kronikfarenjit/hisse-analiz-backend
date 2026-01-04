from flask import Flask, jsonify, request
from isyatirimhisse import Hisse
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Logging ayarı
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Cache için
cache = {
    'hisseler': None,
    'last_update': None
}

def calculate_ema(prices, period):
    """EMA hesaplama"""
    if len(prices) < period:
        return []
    return prices.ewm(span=period, adjust=False).mean().tolist()

def calculate_rsi(prices, period=14):
    """RSI hesaplama"""
    if len(prices) < period + 1:
        return []
    
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50).tolist()

def calculate_macd(prices):
    """MACD hesaplama"""
    if len(prices) < 26:
        return [], [], []
    
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return macd_line.tolist(), signal_line.tolist(), histogram.tolist()

def calculate_atr(df, period=14):
    """ATR hesaplama"""
    if len(df) < 2:
        return []
    
    high = df['Yuksek']
    low = df['Dusuk']
    close = df['Kapanis']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr.fillna(0).tolist()

def analyze_hisse_detailed(kod, sensitivity="Orta"):
    """Detaylı analiz - Pine Script mantığı"""
    
    try:
        logger.info(f"Analyzing {kod} with sensitivity {sensitivity}")
        
        # Veri çek
        hisse_obj = Hisse(kod)
        df = hisse_obj.gunluk(baslangic=(datetime.now() - timedelta(days=200)).strftime("%d-%m-%Y"))
        
        if df is None or len(df) < 50:
            logger.warning(f"Insufficient data for {kod}")
            return None
        
        # Sütun isimlerini standardize et
        df.columns = df.columns.str.strip()
        
        # Gerekli hesaplamalar
        closes = pd.Series(df['Kapanis'].values)
        highs = pd.Series(df['Yuksek'].values)
        lows = pd.Series(df['Dusuk'].values)
        opens = pd.Series(df['Acilis'].values)
        volumes = pd.Series(df['Hacim'].values.astype(float))
        
        # İndikatörler
        ema20 = calculate_ema(closes, 20)
        ema50 = calculate_ema(closes, 50)
        ema200 = calculate_ema(closes, 200)
        rsi = calculate_rsi(closes, 14)
        macd_line, macd_signal, macd_hist = calculate_macd(closes)
        atr = calculate_atr(df, 14)
        
        # Eşik değerleri
        if sensitivity == "Yüksek":
            early_threshold, confirm_threshold = 4, 6
        elif sensitivity == "Düşük":
            early_threshold, confirm_threshold = 8, 10
        else:
            early_threshold, confirm_threshold = 6, 8
        
        # AŞAMA 1: ERKEN UYARI SKORU
        early_bull_score = 0
        early_bear_score = 0
        early_reasons = []
        
        # 1. Volatilite sıkışması
        if len(atr) > 20:
            atr_series = pd.Series(atr)
            atr_percentile = (atr_series.iloc[-1] - atr_series.min()) / (atr_series.max() - atr_series.min()) * 100
            
            if atr_percentile < 20:
                early_bull_score += 3
                early_bear_score += 3
                early_reasons.append({
                    "type": "EXTREME_SQUEEZE",
                    "message": "Aşırı volatilite sıkışması - patlama yakın!",
                    "value": round(atr_percentile, 2)
                })
            elif atr_percentile < 35:
                early_bull_score += 2
                early_bear_score += 2
                early_reasons.append({
                    "type": "MODERATE_SQUEEZE",
                    "message": "Volatilite sıkışması mevcut",
                    "value": round(atr_percentile, 2)
                })
        
        # 2. RSI erken dönüş
        if len(rsi) >= 4:
            rsi_last = rsi[-1]
            rsi_prev = rsi[-2]
            rsi_slope = rsi_last - rsi[-4]
            rsi_ma = np.mean(rsi[-5:])
            
            if rsi_last > rsi_ma and rsi_slope > 0 and 30 < rsi_last < 50:
                early_bull_score += 3
                early_reasons.append({
                    "type": "RSI_TURNING_UP",
                    "message": "RSI yukarı dönüyor",
                    "value": round(rsi_last, 2)
                })
            
            if rsi_last < rsi_ma and rsi_slope < 0 and 50 < rsi_last < 70:
                early_bear_score += 3
                early_reasons.append({
                    "type": "RSI_TURNING_DOWN",
                    "message": "RSI aşağı dönüyor",
                    "value": round(rsi_last, 2)
                })
        
        # 3. MACD erken sinyal
        if len(macd_hist) >= 3:
            hist_last = macd_hist[-1]
            hist_prev1 = macd_hist[-2]
            hist_prev2 = macd_hist[-3]
            
            if hist_last > hist_prev1 and hist_prev1 > hist_prev2 and hist_last < 0:
                early_bull_score += 3
                early_reasons.append({
                    "type": "MACD_EARLY_BULL",
                    "message": "MACD histogram dipten dönüyor",
                    "value": round(hist_last, 4)
                })
            
            if hist_last < hist_prev1 and hist_prev1 < hist_prev2 and hist_last > 0:
                early_bear_score += 3
                early_reasons.append({
                    "type": "MACD_EARLY_BEAR",
                    "message": "MACD histogram tepeden dönüyor",
                    "value": round(hist_last, 4)
                })
        
        # 4. Hacim anomalileri
        if len(volumes) >= 20:
            vol_ma = np.mean(volumes[-20:])
            vol_last = volumes.iloc[-1]
            vol_spike = vol_last > vol_ma * 1.5
            
            body_size = abs(closes.iloc[-1] - opens.iloc[-1])
            avg_body = np.mean([abs(closes.iloc[i] - opens.iloc[i]) for i in range(-20, 0)])
            small_body = body_size < avg_body * 0.6
            
            if vol_spike and small_body:
                if closes.iloc[-1] > opens.iloc[-1]:
                    early_bull_score += 2
                    early_reasons.append({
                        "type": "VOLUME_ACCUMULATION",
                        "message": "Yüksek hacim + küçük mum = birikim",
                        "value": round(vol_last / vol_ma, 2)
                    })
                else:
                    early_bear_score += 2
                    early_reasons.append({
                        "type": "VOLUME_DISTRIBUTION",
                        "message": "Yüksek hacim + küçük mum = dağıtım",
                        "value": round(vol_last / vol_ma, 2)
                    })
        
        # 5. Price action - coiling
        if len(closes) >= 5 and len(highs) >= 5 and len(lows) >= 5:
            ranges = [highs.iloc[-1-i] - lows.iloc[-1-i] for i in range(5)]
            range_narrowing = ranges[0] < ranges[2] and ranges[1] < ranges[3]
            higher_lows = lows.iloc[-1] > lows.iloc[-2] and lows.iloc[-2] > lows.iloc[-3]
            lower_highs = highs.iloc[-1] < highs.iloc[-2] and highs.iloc[-2] < highs.iloc[-3]
            
            if range_narrowing and higher_lows:
                early_bull_score += 3
                early_reasons.append({
                    "type": "BULLISH_COILING",
                    "message": "Bullish coiling pattern - dipler yükseliyor",
                    "value": "Pattern"
                })
            
            if range_narrowing and lower_highs:
                early_bear_score += 3
                early_reasons.append({
                    "type": "BEARISH_COILING",
                    "message": "Bearish coiling pattern - tepler düşüyor",
                    "value": "Pattern"
                })
        
        # AŞAMA 2: ONAY SKORU
        confirm_bull_score = 0
        confirm_bear_score = 0
        confirm_reasons = []
        
        # 1. Trend kontrolü
        if len(ema20) > 0 and len(ema50) > 0 and len(ema200) > 0:
            close_val = closes.iloc[-1]
            ema20_val = ema20[-1]
            ema50_val = ema50[-1]
            ema200_val = ema200[-1]
            
            if close_val > ema20_val and ema20_val > ema50_val and ema50_val > ema200_val:
                confirm_bull_score += 4
                confirm_reasons.append({
                    "type": "STRONG_UPTREND",
                    "message": "Güçlü yükseliş trendi",
                    "value": "EMA sıralaması mükemmel"
                })
            
            if close_val < ema20_val and ema20_val < ema50_val and ema50_val < ema200_val:
                confirm_bear_score += 4
                confirm_reasons.append({
                    "type": "STRONG_DOWNTREND",
                    "message": "Güçlü düşüş trendi",
                    "value": "EMA sıralaması mükemmel"
                })
        
        # 2. MACD crossover
        if len(macd_line) >= 2 and len(macd_signal) >= 2:
            macd_last = macd_line[-1]
            signal_last = macd_signal[-1]
            macd_prev = macd_line[-2]
            signal_prev = macd_signal[-2]
            
            if macd_last > signal_last and macd_prev <= signal_prev:
                confirm_bull_score += 3
                confirm_reasons.append({
                    "type": "MACD_CROSSOVER",
                    "message": "MACD yukarı kesti",
                    "value": round(macd_last - signal_last, 4)
                })
            
            if macd_last < signal_last and macd_prev >= signal_prev:
                confirm_bear_score += 3
                confirm_reasons.append({
                    "type": "MACD_CROSSUNDER",
                    "message": "MACD aşağı kesti",
                    "value": round(signal_last - macd_last, 4)
                })
        
        # 3. RSI onay
        if len(rsi) > 0:
            rsi_val = rsi[-1]
            if 50 < rsi_val < 70:
                confirm_bull_score += 2
                confirm_reasons.append({
                    "type": "RSI_CONFIRMED_BULL",
                    "message": "RSI yükseliş bölgesinde",
                    "value": round(rsi_val, 2)
                })
            
            if 30 < rsi_val < 50:
                confirm_bear_score += 2
                confirm_reasons.append({
                    "type": "RSI_CONFIRMED_BEAR",
                    "message": "RSI düşüş bölgesinde",
                    "value": round(rsi_val, 2)
                })
        
        # 4. Hacim onayı
        if len(volumes) >= 20:
            vol_ma = np.mean(volumes[-20:])
            vol_last = volumes.iloc[-1]
            
            if vol_last > vol_ma * 1.3:
                if closes.iloc[-1] > opens.iloc[-1]:
                    confirm_bull_score += 2
                    confirm_reasons.append({
                        "type": "VOLUME_CONFIRMED_BULL",
                        "message": "Yüksek hacim ile yükseliş",
                        "value": round(vol_last / vol_ma, 2)
                    })
                else:
                    confirm_bear_score += 2
                    confirm_reasons.append({
                        "type": "VOLUME_CONFIRMED_BEAR",
                        "message": "Yüksek hacim ile düşüş",
                        "value": round(vol_last / vol_ma, 2)
                    })
        
        # FİNAL KARAR
        early_total = early_bull_score - early_bear_score
        confirm_total = confirm_bull_score - confirm_bear_score
        
        early_warning_bull = early_total >= early_threshold
        early_warning_bear = early_total <= -early_threshold
        
        confirm_signal_bull = confirm_total >= confirm_threshold and early_warning_bull
        confirm_signal_bear = confirm_total <= -confirm_threshold and early_warning_bear
        
        # Faz belirleme
        if confirm_signal_bull or confirm_signal_bear:
            phase = "ONAY_ALINAN"
        elif early_warning_bull or early_warning_bear:
            phase = "ERKEN_UYARI"
        elif len(atr) > 0:
            atr_series = pd.Series(atr)
            atr_percentile = (atr_series.iloc[-1] - atr_series.min()) / (atr_series.max() - atr_series.min()) * 100
            if atr_percentile < 15:
                phase = "PATLAMAYA_HAZIR"
            else:
                phase = "BEKLEMEDE"
        else:
            phase = "BEKLEMEDE"
        
        # Yön
        if confirm_signal_bull or (early_warning_bull and phase == "ERKEN_UYARI"):
            direction = "YUKARI"
        elif confirm_signal_bear or (early_warning_bear and phase == "ERKEN_UYARI"):
            direction = "ASAGI"
        else:
            direction = "BELIRSIZ"
        
        result = {
            "kod": kod,
            "phase": phase,
            "direction": direction,
            "early_bull_score": early_bull_score,
            "early_bear_score": early_bear_score,
            "confirm_bull_score": confirm_bull_score,
            "confirm_bear_score": confirm_bear_score,
            "early_reasons": early_reasons,
            "confirm_reasons": confirm_reasons,
            "current_price": float(closes.iloc[-1]),
            "rsi": float(rsi[-1]) if len(rsi) > 0 else 50.0,
            "ema20": float(ema20[-1]) if len(ema20) > 0 else float(closes.iloc[-1]),
            "ema50": float(ema50[-1]) if len(ema50) > 0 else float(closes.iloc[-1]),
            "ema200": float(ema200[-1]) if len(ema200) > 0 else float(closes.iloc[-1]),
            "volume": float(volumes.iloc[-1]),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Analysis completed for {kod}: {phase} - {direction}")
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing {kod}: {str(e)}")
        return None

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/hisseler', methods=['GET'])
def get_all_hisseler():
    """Tüm hisselerin listesini döndür"""
    try:
        logger.info("Fetching all stocks...")
        
        # Cache kontrolü (5 dakika)
        if cache['hisseler'] and cache['last_update']:
            time_diff = datetime.now() - cache['last_update']
            if time_diff.total_seconds() < 300:
                logger.info("Returning cached data")
                return jsonify(cache['hisseler'])
        
        hisse_obj = Hisse()
        df = hisse_obj.semboller()
        
        if df is None or len(df) == 0:
            return jsonify({"error": "No stocks found"}), 404
        
        hisseler = []
        for _, row in df.iterrows():
            hisseler.append({
                "kod": row['Kod'],
                "ad": row.get('Ad', row['Kod'])
            })
        
        result = {
            "count": len(hisseler),
            "hisseler": hisseler,
            "timestamp": datetime.now().isoformat()
        }
        
        # Cache'e kaydet
        cache['hisseler'] = result
        cache['last_update'] = datetime.now()
        
        logger.info(f"Returning {len(hisseler)} stocks")
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error fetching stocks: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analiz/<kod>', methods=['GET'])
def analyze_single(kod):
    """Tek hisse analizi"""
    try:
        sensitivity = request.args.get('sensitivity', 'Orta')
        logger.info(f"Analyzing single stock: {kod}")
        
        result = analyze_hisse_detailed(kod.upper(), sensitivity)
        
        if result is None:
            return jsonify({"error": f"Could not analyze {kod}"}), 404
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in analyze_single: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analiz/toplu', methods=['POST'])
def analyze_bulk():
    """Toplu hisse analizi"""
    try:
        data = request.get_json()
        kodlar = data.get('kodlar', [])
        sensitivity = data.get('sensitivity', 'Orta')
        
        if not kodlar:
            return jsonify({"error": "No stock codes provided"}), 400
        
        logger.info(f"Bulk analyzing {len(kodlar)} stocks")
        
        results = []
        for kod in kodlar:
            result = analyze_hisse_detailed(kod.upper(), sensitivity)
            if result:
                results.append(result)
        
        return jsonify({
            "count": len(results),
            "results": results,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in analyze_bulk: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/filtre', methods=['GET'])
def filter_stocks():
    """Hisseleri filtrele - direction parametresi ile"""
    try:
        direction = request.args.get('direction', '').upper()  # YUKARI, ASAGI, BELIRSIZ
        sensitivity = request.args.get('sensitivity', 'Orta')
        limit = int(request.args.get('limit', 50))
        
        logger.info(f"Filtering stocks by direction: {direction}")
        
        # Önce tüm hisseleri al
        hisse_obj = Hisse()
        df = hisse_obj.semboller()
        
        if df is None or len(df) == 0:
            return jsonify({"error": "No stocks found"}), 404
        
        # İlk 'limit' kadar hisseyi analiz et
        kodlar = df['Kod'].tolist()[:limit]
        
        results = []
        for kod in kodlar:
            result = analyze_hisse_detailed(kod, sensitivity)
            if result:
                # Filtreleme
                if direction and result['direction'] != direction:
                    continue
                results.append(result)
        
        logger.info(f"Filtered {len(results)} stocks")
        
        return jsonify({
            "count": len(results),
            "filter": direction if direction else "ALL",
            "results": results,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in filter_stocks: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/arama', methods=['GET'])
def search_stocks():
    """Hisse arama"""
    try:
        query = request.args.get('q', '').upper()
        
        if not query or len(query) < 2:
            return jsonify({"error": "Query too short"}), 400
        
        logger.info(f"Searching stocks with query: {query}")
        
        hisse_obj = Hisse()
        df = hisse_obj.semboller()
        
        if df is None or len(df) == 0:
            return jsonify({"error": "No stocks found"}), 404
        
        # Filtreleme
        filtered = df[df['Kod'].str.contains(query, case=False, na=False)]
        
        results = []
        for _, row in filtered.iterrows():
            results.append({
                "kod": row['Kod'],
                "ad": row.get('Ad', row['Kod'])
            })
        
        logger.info(f"Found {len(results)} stocks matching '{query}'")
        
        return jsonify({
            "count": len(results),
            "query": query,
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Error in search_stocks: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
