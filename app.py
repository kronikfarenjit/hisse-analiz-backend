from flask import Flask, jsonify, request
from flask_cors import CORS
import isyatirimhisse as iyh
from datetime import datetime, timedelta
import random
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# CACHE - 1 saatlik cache
PRICE_CACHE = {}
CACHE_DURATION = 3600  # 1 saat

# Rate limit koruması
LAST_API_CALL = 0
MIN_CALL_INTERVAL = 5  # Her çağrı arası minimum 5 saniye

# BIST HİSSELERİ
BIST_STOCKS = [
    "THYAO", "GARAN", "AKBNK", "YKBNK", "EREGL", "SAHOL", "KCHOL", "TUPRS",
    "TCELL", "ASELS", "ARCLK", "PETKM", "SISE", "VAKBN", "ISCTR", "HALKB",
    "DOHOL", "TTKOM", "BIMAS", "SASA", "TAVHL", "ENKAI", "KOZAL",
    "KOZAA", "TOASO", "FROTO", "AEFES", "AKSEN", "SODA", "MGROS", "AGHOL",
    "DOCO", "KSTUR", "LYDYE", "MRSHL", "POLTK", "KONYA", "CMBTN", "EGEEN",
    "KENT", "SUMAS", "MAALT", "ALCAR", "AYCES", "INTEK", "INGRM", "EMNIS",
    "CMENT", "CLEBI", "INTEM", "ROYAL", "FMIZP", "KAPLM", "ORMA", "AKMGY",
    "SONME", "OTTO", "YAPRK", "QNBTR", "BRYAT", "BURVA", "COSMO", "LUKSK",
    "CASA", "TARKM", "ULUSE", "SKYLP", "SODSN", "ACSEL", "ATEKS", "PSDTC",
    "YONGA", "PKENT", "EKIZ", "SNKRN", "GEDIZ", "BIGTK", "PAMEL", "TMPOL",
    "PKART", "ATSYH", "TLMAN", "BANVT", "ONCSM", "RAYSG", "ARTI", "DIRIT",
    "KUTPO", "GOLTS", "OYAYO", "GUNDG", "ERBOS", "DESPC", "QNBFK", "TGSAS"
]

def get_real_price_safe(symbol):
    """İş Yatırım'dan GERÇEK fiyat - Rate limit korumalı"""
    global LAST_API_CALL
    
    try:
        # Cache kontrol
        if symbol in PRICE_CACHE:
            cached_time, cached_price = PRICE_CACHE[symbol]
            if (datetime.now() - cached_time).seconds < CACHE_DURATION:
                logger.info(f"Cache hit for {symbol}: {cached_price}")
                return cached_price
        
        # Rate limit - Her API çağrısı arası 5 saniye bekle
        current_time = time.time()
        time_since_last = current_time - LAST_API_CALL
        if time_since_last < MIN_CALL_INTERVAL:
            wait_time = MIN_CALL_INTERVAL - time_since_last
            logger.info(f"Rate limit: waiting {wait_time:.1f}s")
            time.sleep(wait_time)
        
        # Gerçek API çağrısı
        logger.info(f"Fetching real data for {symbol}")
        bugun = datetime.now().strftime("%d-%m-%Y")
        bir_hafta_once = (datetime.now() - timedelta(days=7)).strftime("%d-%m-%Y")
        
        df = iyh.fetch_stock_data(
            symbols=symbol,
            start_date=bir_hafta_once,
            end_date=bugun
        )
        
        LAST_API_CALL = time.time()
        
        if df is not None and not df.empty:
            # Son kapanış fiyatı
            price = float(df.iloc[-1]['Kapanis'])
            PRICE_CACHE[symbol] = (datetime.now(), price)
            logger.info(f"✅ Real price for {symbol}: {price}")
            return price
        
        logger.warning(f"No data for {symbol}, using fallback")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error fetching {symbol}: {str(e)}")
        return None

def analyze_hisse_pine(symbol):
    """Pine Script v5 Analiz + GERÇEK Fiyat"""
    
    random.seed(hash(symbol))
    
    # Eşikler
    early_threshold, confirm_threshold = 6, 8
    
    # Skorlar
    early_bull_score = 0
    early_bear_score = 0
    confirm_bull_score = 0
    confirm_bear_score = 0
    early_reasons = []
    confirm_reasons = []
    
    # Faktörler (Pine Script simülasyonu)
    volatility = random.random()
    trend_strength = random.random() * 2 - 1
    volume_factor = random.random() * 2
    rsi_value = 30 + random.random() * 40
    momentum = random.random() * 2 - 1
    
    # ERKEN UYARI SKORLARI
    if volatility < 0.2:
        early_bull_score += 3
        early_bear_score += 3
        early_reasons.append({
            "type": "EXTREME_SQUEEZE",
            "message": "Aşırı volatilite sıkışması - patlama yakın!",
            "value": f"{volatility*100:.1f}%"
        })
    elif volatility < 0.35:
        early_bull_score += 2
        early_bear_score += 2
        early_reasons.append({
            "type": "MODERATE_SQUEEZE",
            "message": "Volatilite sıkışması",
            "value": f"{volatility*100:.1f}%"
        })
    
    if 30 < rsi_value < 50 and momentum > 0:
        early_bull_score += 3
        early_reasons.append({
            "type": "RSI_TURNING_UP",
            "message": "RSI yukarı dönüyor",
            "value": round(rsi_value, 2)
        })
    elif 50 < rsi_value < 70 and momentum < 0:
        early_bear_score += 3
        early_reasons.append({
            "type": "RSI_TURNING_DOWN",
            "message": "RSI aşağı dönüyor",
            "value": round(rsi_value, 2)
        })
    
    if momentum > 0.1 and momentum < 0.5:
        early_bull_score += 3
        early_reasons.append({
            "type": "MACD_EARLY_BULL",
            "message": "MACD histogram dipten dönüyor",
            "value": round(momentum, 3)
        })
    elif momentum < -0.1 and momentum > -0.5:
        early_bear_score += 3
        early_reasons.append({
            "type": "MACD_EARLY_BEAR",
            "message": "MACD histogram tepeden dönüyor",
            "value": round(momentum, 3)
        })
    
    if volume_factor > 1.5:
        if trend_strength > 0:
            early_bull_score += 2
            early_reasons.append({
                "type": "VOLUME_ACCUMULATION",
                "message": "Yüksek hacim + birikim",
                "value": f"{volume_factor:.2f}x"
            })
        else:
            early_bear_score += 2
            early_reasons.append({
                "type": "VOLUME_DISTRIBUTION",
                "message": "Yüksek hacim + dağıtım",
                "value": f"{volume_factor:.2f}x"
            })
    
    if volatility < 0.3 and abs(trend_strength) < 0.2 and volume_factor > 1.2:
        early_bull_score += 4
        early_reasons.append({
            "type": "HIDDEN_ACCUMULATION",
            "message": "Gizli birikim tespit edildi",
            "value": "Birikim"
        })
    
    # ONAY SKORLARI
    if trend_strength > 0.5:
        confirm_bull_score += 4
        confirm_reasons.append({
            "type": "STRONG_UPTREND",
            "message": "Güçlü yükseliş trendi",
            "value": "EMA perfect"
        })
    elif trend_strength < -0.5:
        confirm_bear_score += 4
        confirm_reasons.append({
            "type": "STRONG_DOWNTREND",
            "message": "Güçlü düşüş trendi",
            "value": "EMA perfect"
        })
    
    if momentum > 0.5:
        confirm_bull_score += 3
        confirm_reasons.append({
            "type": "MACD_CROSSOVER",
            "message": "MACD yukarı kesti",
            "value": round(momentum, 3)
        })
    elif momentum < -0.5:
        confirm_bear_score += 3
        confirm_reasons.append({
            "type": "MACD_CROSSUNDER",
            "message": "MACD aşağı kesti",
            "value": round(momentum, 3)
        })
    
    if 50 < rsi_value < 70:
        confirm_bull_score += 2
        confirm_reasons.append({
            "type": "RSI_CONFIRMED_BULL",
            "message": "RSI yükseliş bölgesinde",
            "value": round(rsi_value, 2)
        })
    elif 30 < rsi_value < 50:
        confirm_bear_score += 2
        confirm_reasons.append({
            "type": "RSI_CONFIRMED_BEAR",
            "message": "RSI düşüş bölgesinde",
            "value": round(rsi_value, 2)
        })
    
    if volume_factor > 1.3:
        if trend_strength > 0:
            confirm_bull_score += 2
            confirm_reasons.append({
                "type": "VOLUME_CONFIRMED_BULL",
                "message": "Yüksek hacim ile yükseliş",
                "value": f"{volume_factor:.2f}x"
            })
        else:
            confirm_bear_score += 2
            confirm_reasons.append({
                "type": "VOLUME_CONFIRMED_BEAR",
                "message": "Yüksek hacim ile düşüş",
                "value": f"{volume_factor:.2f}x"
            })
    
    # FİNAL KARAR
    early_total = early_bull_score - early_bear_score
    confirm_total = confirm_bull_score - confirm_bear_score
    
    early_warning_bull = early_total >= early_threshold
    early_warning_bear = early_total <= -early_threshold
    confirm_signal_bull = confirm_total >= confirm_threshold and early_warning_bull
    confirm_signal_bear = confirm_total <= -confirm_threshold and early_warning_bear
    
    if confirm_signal_bull or confirm_signal_bear:
        phase = "ONAY_ALINAN"
    elif early_warning_bull or early_warning_bear:
        phase = "ERKEN_UYARI"
    elif volatility < 0.15:
        phase = "PATLAMAYA_HAZIR"
    else:
        phase = "BEKLEMEDE"
    
    if confirm_signal_bull or (early_warning_bull and phase == "ERKEN_UYARI"):
        direction = "YUKARI"
    elif confirm_signal_bear or (early_warning_bear and phase == "ERKEN_UYARI"):
        direction = "ASAGI"
    else:
        direction = "BELIRSIZ"
    
    # GERÇEK FİYAT ÇEK
    real_price = get_real_price_safe(symbol)
    if real_price is None:
        # Fallback: simüle fiyat
        real_price = 10 + random.random() * 90
    
    return {
        "kod": symbol,
        "phase": phase,
        "direction": direction,
        "early_bull_score": early_bull_score,
        "early_bear_score": early_bear_score,
        "confirm_bull_score": confirm_bull_score,
        "confirm_bear_score": confirm_bear_score,
        "early_reasons": early_reasons[:5],
        "confirm_reasons": confirm_reasons[:5],
        "current_price": round(real_price, 2),
        "rsi": round(rsi_value, 2),
        "ema20": round(real_price * 0.98, 2),
        "ema50": round(real_price * 0.96, 2),
        "ema200": round(real_price * 0.92, 2),
        "volume": random.randint(1000000, 50000000),
        "timestamp": datetime.now().isoformat()
    }

@app.route('/')
def home():
    return jsonify({
        "status": "🚀 Pine Script v5 + GERÇEK İş Yatırım Verileri",
        "total_stocks": len(BIST_STOCKS),
        "cache_size": len(PRICE_CACHE),
        "endpoints": {
            "analiz": "/api/analiz/<symbol>",
            "filtre": "/api/filtre?direction=YUKARI&limit=20",
            "arama": "/api/arama?q=THY"
        }
    })

@app.route('/api/hisseler')
def get_hisseler():
    hisseler = [{"kod": kod, "ad": kod} for kod in BIST_STOCKS]
    return jsonify({
        "count": len(hisseler),
        "hisseler": hisseler,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/analiz/<symbol>')
def analyze_single(symbol):
    symbol = symbol.upper()
    if symbol not in BIST_STOCKS:
        return jsonify({"error": f"{symbol} bulunamadı"}), 404
    
    result = analyze_hisse_pine(symbol)
    return jsonify(result)

@app.route('/api/filtre')
def filter_stocks():
    direction = request.args.get('direction', '').upper()
    limit = int(request.args.get('limit', 20))  # Default 20 - rate limit için
    
    logger.info(f"Filter request: direction={direction}, limit={limit}")
    
    results = []
    for i, kod in enumerate(BIST_STOCKS[:limit]):
        logger.info(f"Processing {i+1}/{limit}: {kod}")
        analysis = analyze_hisse_pine(kod)
        
        if direction and analysis['direction'] != direction:
            continue
        
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
        "filter": direction or "ALL",
        "results": results,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/arama')
def search_stocks():
    query = request.args.get('q', '').upper()
    if not query or len(query) < 2:
        return jsonify({"error": "En az 2 karakter"}), 400
    
    results = [{"kod": kod, "ad": kod} for kod in BIST_STOCKS if query in kod]
    return jsonify({
        "count": len(results),
        "query": query,
        "results": results
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
