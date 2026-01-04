from flask import Flask, jsonify, request
from flask_cors import CORS
from isyatirimhisse import Hisse
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Cache
cache = {}

def calculate_ema(data, period):
    """EMA hesaplama"""
    if len(data) < period:
        return []
    
    multiplier = 2 / (period + 1)
    ema = [np.mean(data[:period])]
    
    for price in data[period:]:
        ema.append((price - ema[-1]) * multiplier + ema[-1])
    
    return ema

def calculate_rsi(data, period=14):
    """RSI hesaplama"""
    if len(data) < period + 1:
        return []
    
    deltas = np.diff(data)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    rsi_values = []
    for i in range(period - 1, len(deltas)):
        avg_gain = np.mean(gains[i-period+1:i+1])
        avg_loss = np.mean(losses[i-period+1:i+1])
        
        if avg_loss == 0:
            rsi_values.append(100)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100 - (100 / (1 + rs)))
    
    return rsi_values

def calculate_atr(highs, lows, closes, period=14):
    """ATR hesaplama"""
    if len(highs) < 2:
        return []
    
    tr = []
    for i in range(1, len(highs)):
        tr.append(max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i-1]),
            abs(lows[i] - closes[i-1])
        ))
    
    return calculate_ema(tr, period)

def calculate_bb_width(data, period=20):
    """Bollinger Bands Width"""
    if len(data) < period:
        return []
    
    bb_width = []
    for i in range(period - 1, len(data)):
        window = data[i-period+1:i+1]
        sma = np.mean(window)
        std = np.std(window)
        bb_width.append((std / sma * 100) if sma != 0 else 0)
    
    return bb_width

def analyze_hisse_real(symbol, sensitivity="Orta"):
    """GERÇEK Pine Script Analizi - İş Yatırım verisi"""
    
    try:
        logger.info(f"Analyzing {symbol}")
        
        # Veri çek
        hisse = Hisse(symbol)
        df = hisse.gunluk(baslangic=(datetime.now() - timedelta(days=200)).strftime("%d-%m-%Y"))
        
        if df is None or len(df) < 100:
            logger.warning(f"Insufficient data for {symbol}")
            return None
        
        # Numpy array'lere çevir
        closes = df['Kapanis'].values
        opens = df['Acilis'].values
        highs = df['Yuksek'].values
        lows = df['Dusuk'].values
        volumes = df['Hacim'].values.astype(float)
        
        # Eşik değerleri
        if sensitivity == "Yüksek":
            early_threshold, confirm_threshold = 4, 6
        elif sensitivity == "Düşük":
            early_threshold, confirm_threshold = 8, 10
        else:
            early_threshold, confirm_threshold = 6, 8
        
        # İndikatörler
        ema20 = calculate_ema(closes, 20)
        ema50 = calculate_ema(closes, 50)
        ema200 = calculate_ema(closes, 200)
        rsi = calculate_rsi(closes, 14)
        atr = calculate_atr(highs, lows, closes, 14)
        bb_width = calculate_bb_width(closes, 20)
        
        # MACD
        ema12 = calculate_ema(closes, 12)
        ema26 = calculate_ema(closes, 26)
        macd_line = [ema12[i] - ema26[i] for i in range(len(ema26))]
        macd_signal = calculate_ema(macd_line, 9)
        macd_hist = [macd_line[i] - macd_signal[i] for i in range(len(macd_signal))]
        
        # OBV
        obv = [0]
        for i in range(1, len(closes)):
            if closes[i] > closes[i-1]:
                obv.append(obv[-1] + volumes[i])
            elif closes[i] < closes[i-1]:
                obv.append(obv[-1] - volumes[i])
            else:
                obv.append(obv[-1])
        
        # ========== AŞAMA 1: ERKEN UYARI ==========
        early_bull_score = 0
        early_bear_score = 0
        early_reasons = []
        
        # 1. Volatilite sıkışması
        if len(atr) > 20 and len(bb_width) > 20:
            atr_min, atr_max = min(atr), max(atr)
            atr_percentile = ((atr[-1] - atr_min) / (atr_max - atr_min) * 100) if atr_max != atr_min else 50
            
            bb_min, bb_max = min(bb_width), max(bb_width)
            bb_percentile = ((bb_width[-1] - bb_min) / (bb_max - bb_min) * 100) if bb_max != bb_min else 50
            
            extreme_squeeze = atr_percentile < 20 and bb_percentile < 20
            moderate_squeeze = atr_percentile < 35 and bb_percentile < 35
            
            if extreme_squeeze:
                early_bull_score += 3
                early_bear_score += 3
                early_reasons.append({
                    "type": "EXTREME_SQUEEZE",
                    "message": "Aşırı volatilite sıkışması - patlama yakın!",
                    "value": f"ATR: {atr_percentile:.1f}%"
                })
            elif moderate_squeeze:
                early_bull_score += 2
                early_bear_score += 2
                early_reasons.append({
                    "type": "MODERATE_SQUEEZE",
                    "message": "Volatilite sıkışması",
                    "value": f"ATR: {atr_percentile:.1f}%"
                })
        
        # 2. RSI erken dönüş
        if len(rsi) >= 5:
            rsi_last = rsi[-1]
            rsi_ma = np.mean(rsi[-5:])
            rsi_slope = rsi_last - rsi[-4]
            
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
            vol_last = volumes[-1]
            vol_spike = vol_last > vol_ma * 1.5
            
            body_size = abs(closes[-1] - opens[-1])
            avg_body = np.mean([abs(closes[i] - opens[i]) for i in range(-20, 0)])
            small_body = body_size < avg_body * 0.6
            
            if vol_spike and small_body:
                if closes[-1] > opens[-1]:
                    early_bull_score += 2
                    early_reasons.append({
                        "type": "VOLUME_ACCUMULATION",
                        "message": "Yüksek hacim + küçük mum = birikim",
                        "value": f"{vol_last/vol_ma:.2f}x"
                    })
                else:
                    early_bear_score += 2
                    early_reasons.append({
                        "type": "VOLUME_DISTRIBUTION",
                        "message": "Yüksek hacim + küçük mum = dağıtım",
                        "value": f"{vol_last/vol_ma:.2f}x"
                    })
        
        # 5. OBV gizli birikim/dağıtım
        if len(obv) >= 20:
            obv_ma = np.mean(obv[-20:])
            obv_slope = (obv[-1] - obv[-6]) / 5
            
            price_range = (max(highs[-10:]) - min(lows[-10:])) / closes[-1] * 100
            tight_range = price_range < 3
            
            if tight_range and obv[-1] > obv_ma and obv_slope > 0:
                early_bull_score += 4
                early_reasons.append({
                    "type": "HIDDEN_ACCUMULATION",
                    "message": "Fiyat dar ama OBV artıyor - gizli birikim!",
                    "value": "Birikim"
                })
            
            if tight_range and obv[-1] < obv_ma and obv_slope < 0:
                early_bear_score += 4
                early_reasons.append({
                    "type": "HIDDEN_DISTRIBUTION",
                    "message": "Fiyat dar ama OBV azalıyor - gizli dağıtım!",
                    "value": "Dağıtım"
                })
        
        # 6. Price action coiling
        if len(closes) >= 5:
            ranges = [highs[-1-i] - lows[-1-i] for i in range(5)]
            range_narrowing = ranges[0] < ranges[2] and ranges[1] < ranges[3]
            higher_lows = lows[-1] > lows[-2] and lows[-2] > lows[-3]
            lower_highs = highs[-1] < highs[-2] and highs[-2] < highs[-3]
            
            if range_narrowing and higher_lows:
                early_bull_score += 3
                early_reasons.append({
                    "type": "BULLISH_COILING",
                    "message": "Bullish coiling - dipler yükseliyor",
                    "value": "Pattern"
                })
            
            if range_narrowing and lower_highs:
                early_bear_score += 3
                early_reasons.append({
                    "type": "BEARISH_COILING",
                    "message": "Bearish coiling - tepler düşüyor",
                    "value": "Pattern"
                })
        
        # 7. Rejection wicks
        upper_wick = highs[-1] - max(opens[-1], closes[-1])
        lower_wick = min(opens[-1], closes[-1]) - lows[-1]
        body = abs(closes[-1] - opens[-1])
        
        if lower_wick > body * 2 and closes[-1] > opens[-1]:
            early_bull_score += 3
            early_reasons.append({
                "type": "REJECTION_LOW",
                "message": "Güçlü alt fitil - reddedilme",
                "value": f"{lower_wick:.2f}"
            })
        
        if upper_wick > body * 2 and closes[-1] < opens[-1]:
            early_bear_score += 3
            early_reasons.append({
                "type": "REJECTION_HIGH",
                "message": "Güçlü üst fitil - reddedilme",
                "value": f"{upper_wick:.2f}"
            })
        
        # ========== AŞAMA 2: ONAY ==========
        confirm_bull_score = 0
        confirm_bear_score = 0
        confirm_reasons = []
        
        # 1. Trend kontrolü
        if len(ema20) > 0 and len(ema50) > 0 and len(ema200) > 0:
            close_val = closes[-1]
            ema20_val = ema20[-1]
            ema50_val = ema50[-1]
            ema200_val = ema200[-1]
            
            if close_val > ema20_val and ema20_val > ema50_val and ema50_val > ema200_val:
                confirm_bull_score += 4
                confirm_reasons.append({
                    "type": "STRONG_UPTREND",
                    "message": "Güçlü yükseliş trendi - EMA sıralaması perfect",
                    "value": "Trend OK"
                })
            
            if close_val < ema20_val and ema20_val < ema50_val and ema50_val < ema200_val:
                confirm_bear_score += 4
                confirm_reasons.append({
                    "type": "STRONG_DOWNTREND",
                    "message": "Güçlü düşüş trendi - EMA sıralaması perfect",
                    "value": "Trend OK"
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
            vol_last = volumes[-1]
            
            if vol_last > vol_ma * 1.3:
                if closes[-1] > opens[-1]:
                    confirm_bull_score += 2
                    confirm_reasons.append({
                        "type": "VOLUME_CONFIRMED_BULL",
                        "message": "Yüksek hacim ile yükseliş",
                        "value": f"{vol_last/vol_ma:.2f}x"
                    })
                else:
                    confirm_bear_score += 2
                    confirm_reasons.append({
                        "type": "VOLUME_CONFIRMED_BEAR",
                        "message": "Yüksek hacim ile düşüş",
                        "value": f"{vol_last/vol_ma:.2f}x"
                    })
        
        # 5. EMA kırılması
        if len(ema20) >= 2 and len(closes) >= 2:
            if closes[-1] > ema20[-1] and closes[-2] <= ema20[-2]:
                confirm_bull_score += 2
                confirm_reasons.append({
                    "type": "EMA20_BREAK_UP",
                    "message": "EMA20 yukarı kırıldı",
                    "value": "Breakout"
                })
            
            if closes[-1] < ema20[-1] and closes[-2] >= ema20[-2]:
                confirm_bear_score += 2
                confirm_reasons.append({
                    "type": "EMA20_BREAK_DOWN",
                    "message": "EMA20 aşağı kırıldı",
                    "value": "Breakdown"
                })
        
        # FİNAL KARAR
        early_total = early_bull_score - early_bear_score
        confirm_total = confirm_bull_score - confirm_bear_score
        
        early_warning_bull = early_total >= early_threshold
        early_warning_bear = early_total <= -early_threshold
        
        confirm_signal_bull = confirm_total >= confirm_threshold and early_warning_bull
        confirm_signal_bear = confirm_total <= -confirm_threshold and early_warning_bear
        
        # Faz
        if confirm_signal_bull or confirm_signal_bear:
            phase = "ONAY_ALINAN"
        elif early_warning_bull or early_warning_bear:
            phase = "ERKEN_UYARI"
        elif len(atr) > 0:
            atr_min, atr_max = min(atr), max(atr)
            atr_percentile = ((atr[-1] - atr_min) / (atr_max - atr_min) * 100) if atr_max != atr_min else 50
            phase = "PATLAMAYA_HAZIR" if atr_percentile < 15 else "BEKLEMEDE"
        else:
            phase = "BEKLEMEDE"
        
        # Yön
        if confirm_signal_bull or (early_warning_bull and phase == "ERKEN_UYARI"):
            direction = "YUKARI"
        elif confirm_signal_bear or (early_warning_bear and phase == "ERKEN_UYARI"):
            direction = "ASAGI"
        else:
            direction = "BELIRSIZ"
        
        return {
            "kod": symbol,
            "phase": phase,
            "direction": direction,
            "early_bull_score": early_bull_score,
            "early_bear_score": early_bear_score,
            "confirm_bull_score": confirm_bull_score,
            "confirm_bear_score": confirm_bear_score,
            "early_reasons": early_reasons[:5],  # İlk 5 sebep
            "confirm_reasons": confirm_reasons[:5],
            "current_price": float(closes[-1]),
            "rsi": float(rsi[-1]) if len(rsi) > 0 else 50.0,
            "ema20": float(ema20[-1]) if len(ema20) > 0 else float(closes[-1]),
            "ema50": float(ema50[-1]) if len(ema50) > 0 else float(closes[-1]),
            "ema200": float(ema200[-1]) if len(ema200) > 0 else float(closes[-1]),
            "volume": float(volumes[-1]),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error analyzing {symbol}: {str(e)}")
        return None

@app.route('/')
def home():
    return jsonify({
        "status": "🚀 BIST API - GERÇEK Pine Script!",
        "total_stocks": 592,
        "endpoints": {
            "analiz": "/api/analiz/<symbol>",
            "filtre": "/api/filtre?direction=YUKARI",
            "arama": "/api/arama?q=THY"
        }
    })

@app.route('/api/hisseler')
def get_hisseler():
    """Hisse listesi"""
    try:
        hisse = Hisse()
        df = hisse.semboller()
        
        hisseler = []
        for _, row in df.iterrows():
            hisseler.append({
                "kod": row['Kod'],
                "ad": row.get('Ad', row['Kod'])
            })
        
        return jsonify({
            "count": len(hisseler),
            "hisseler": hisseler,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analiz/<symbol>')
def analyze_single(symbol):
    """Tek hisse analizi"""
    try:
        result = analyze_hisse_real(symbol.upper())
        if result is None:
            return jsonify({"error": f"Could not analyze {symbol}"}), 404
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/filtre')
def filter_stocks():
    """Filtreleme - GERÇEK ANALİZ"""
    try:
        direction = request.args.get('direction', '').upper()
        limit = int(request.args.get('limit', 50))  # 50 hisseyle başla
        
        hisse = Hisse()
        df = hisse.semboller()
        kodlar = df['Kod'].tolist()[:limit]
        
        results = []
        for kod in kodlar:
            analysis = analyze_hisse_real(kod)
            if analysis and (not direction or analysis['direction'] == direction):
                results.append(analysis)
        
        # Sıralama
        if direction == "YUKARI":
            results.sort(key=lambda x: x['confirm_bull_score'] + x['early_bull_score'], reverse=True)
        elif direction == "ASAGI":
            results.sort(key=lambda x: x['confirm_bear_score'] + x['early_bear_score'], reverse=True)
        else:
            results.sort(key=lambda x: x['confirm_bull_score'] + x['early_bull_score'], reverse=True)
        
        return jsonify({
            "count": len(results),
            "filter": direction if direction else "ALL",
            "results": results,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/arama')
def search_stocks():
    """Arama"""
    try:
        query = request.args.get('q', '').upper()
        if not query or len(query) < 2:
            return jsonify({"error": "En az 2 karakter"}), 400
        
        hisse = Hisse()
        df = hisse.semboller()
        filtered = df[df['Kod'].str.contains(query, case=False, na=False)]
        
        results = []
        for _, row in filtered.iterrows():
            results.append({
                "kod": row['Kod'],
                "ad": row.get('Ad', row['Kod'])
            })
        
        return jsonify({
            "count": len(results),
            "query": query,
            "results": results
        })
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
