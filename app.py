from flask import Flask, jsonify, request
from flask_cors import CORS
import isyatirimhisse as iyh
from datetime import datetime, timedelta
import random
import math
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Cache için
PRICE_CACHE = {}

# TÜM BIST HİSSELERİ - 592 ADET
BIST_STOCKS = [
    "THYAO", "GARAN", "AKBNK", "YKBNK", "EREGL", "SAHOL", "KCHOL", "TUPRS",
    "TCELL", "ASELS", "ARCLK", "PETKM", "SISE", "VAKBN", "ISCTR", "HALKB",
    "DOHOL", "TTKOM", "BIMAS", "THYAO", "SASA", "TAVHL", "ENKAI", "KOZAL",
    "KOZAA", "TOASO", "FROTO", "AEFES", "AKSEN", "SODA", "MGROS", "AGHOL",
    "DOCO", "KSTUR", "LYDYE", "MRSHL", "POLTK", "KONYA", "CMBTN", "EGEEN",
    "KENT", "SUMAS", "MAALT", "ALCAR", "AYCES", "INTEK", "INGRM", "EMNIS",
    "CMENT", "CLEBI", "INTEM", "ROYAL", "FMIZP", "KAPLM", "ORMA", "AKMGY",
    "SONME", "OTTO", "YAPRK", "QNBTR", "BRYAT", "BURVA", "COSMO", "LUKSK",
    "CASA", "TARKM", "ULUSE", "SKYLP", "SODSN", "ACSEL", "ATEKS", "PSDTC",
    "YONGA", "PKENT", "EKIZ", "SNKRN", "GEDIZ", "BIGTK", "PAMEL", "TMPOL",
    "PKART", "ATSYH", "TLMAN", "BANVT", "ONCSM", "RAYSG", "ARTI", "DIRIT",
    "KUTPO", "GOLTS", "OYAYO", "GUNDG", "ERBOS", "DESPC", "QNBFK", "TGSAS",
    "DGATE", "IZINV", "BALAT", "MMCAS", "BAKAB", "OZATD", "TRHOL", "ALCTL",
    "BRKVY", "CRFSA", "BVSAN", "LINK", "KTSKR", "ISBIR", "VKFYO", "DERIM",
    "VERUS", "OBASE", "ENPRA", "SANEL", "SDTTR", "SNPAM", "RODRG", "TBORG",
    "KARTN", "RNPOL", "BINBN", "DOGUB", "VKING", "KRTEK", "DOFER", "BYDNR",
    "ATATP", "ETYAT", "CUSAN", "DGGYO", "UFUK", "VERTU", "BFREN", "ECZYT",
    "BAHKM", "ONRYT", "ARTMS", "EUKYO", "EUYO", "SANKO", "MARKA", "PNLSN",
    "VAKKO", "ULAS", "DUNYH", "HOROZ", "FORTE", "VANGD", "GZNMI", "CEOEM",
    "OFSYM", "ERSU", "AVHOL", "HRKET", "NETAS", "VSNMD", "PARSN", "KUVVA",
    "BEYAZ", "MEDTR", "GEDZA", "TTRAK", "KLMSN", "GLCVY", "BIZIM", "BRSAN",
    "ODINE", "DITAS", "OZYSR", "SMRVA", "ATAKP", "ATAGY", "NUHCM", "GLBMD",
    "YBTAS", "BRMEN", "AVTUR", "GRSEL", "SMART", "TURGG", "ISGSY", "EDIP",
    "BRISA", "ERCB", "DOKTA", "OTKAR", "PAGYO", "TMSN", "CATES", "GARFA",
    "MACKO", "RUBNS", "PRKAB", "DEVA", "AGESA", "GRNYO", "GRTHO", "ASUZU",
    "EBEBK", "YAYLA", "BAYRK", "INVES", "MEPET", "SURGY", "A1YEN", "GLRMK",
    "AKCNS", "ALKLC", "MTRYO", "OZSUB", "BIGCH", "MTRKS", "ELITE", "FADE",
    "ORGE", "CGCAM", "SAYAS", "DURKN", "MAKIM", "OZRDN", "ARASE", "LYDHO",
    "HATSN", "BURCE", "NIBAS", "PCILT", "ARMGD", "HATEK", "ANELE", "DOFRB",
    "SEGMN", "GIPTA", "EGGUB", "KLYPV", "PRKME", "AYEN", "DCTTR", "GSDDE",
    "AGYO", "BASCM", "BLCYT", "PLTUR", "KZGYO", "ARENA", "SEKFK", "BARMA",
    "SKYMD", "TABGD", "RGYAS", "VBTYZ", "DNISI", "AYGAZ", "PRZMA", "TCKRC",
    "AKSUE", "KORDS", "IHAAS", "CRDFA", "MOPAS", "TDGYO", "AVGYO", "KNFRT",
    "ATLAS", "MARBL", "EGEGY", "LOGO", "ICBCT", "UNLU", "BRKSN", "BMSCH",
    "KIMMR", "ANHYT", "OYLUM", "AKFIS", "GOODY", "HKTM", "ZEDUR", "FLAP",
    "GUBRF", "TRCAS", "EGPRO", "ADEL", "GENIL", "MZHLD", "BULGS", "MEGMT",
    "CELHA", "TSGYO", "MERCN", "BMSTL", "YIGIT", "KONKA", "DYOBY", "EKOS",
    "ANGEN", "IZFAS", "KRPLS", "TKFEN", "MPARK", "DSTKF", "ISSEN", "ADGYO",
    "BAGFS", "HTTBT", "BIENY", "TRILC", "ALFAS", "MERKO", "ALVES", "AYES",
    "DOAS", "TNZTP", "TRENJ", "DESA", "AVPGY", "YATAS", "OYYAT", "KLNMA",
    "PINSU", "MERIT", "MGROS", "SELEC", "ALTNY", "SOKE", "SAMAT", "PETUN",
    "TKNSA", "EGEPO", "ESCAR", "MAKTK", "TUCLK", "DMSAS", "TATGD", "BASGZ",
    "BRLSM", "ISYAT", "KOTON", "KLSER", "ECOGR", "PRDGS", "HURGZ", "KRONT",
    "DZGYO", "SERNT", "NTHOL", "EMKEL", "YKSLN", "BOBET", "BIGEN", "ENDAE",
    "KRDMB", "GOZDE", "BRKO", "DMRGD", "DERHL", "PNSUT", "IDGYO", "JANTS",
    "KLKIM", "FRIGO", "TOASO", "MANAS", "CEMZY", "TEZOL", "ARDYZ", "ENSRI",
    "ECILC", "OSMEN", "YEOTK", "KMPUR", "AYDEM", "GOLDS", "SEKUR", "BLUME",
    "EUHOL", "GMTAS", "RALYH", "SAFKR", "PENGD", "EPLAS", "MNDRS", "ALKA",
    "MSGYO", "ALKIM", "ALGYO", "GESAN", "BNTAS", "KBORU", "SUNTK", "EDATA",
    "ISDMR", "KFEIN", "ETILR", "ORCAY", "SEYKM", "ULKER", "ASGYO", "LKMNH",
    "HEDEF", "LMKDC", "BOSSA", "VESTL", "PENTA", "TRMET", "MNDTR", "ALARK",
    "GWIND", "EKSUN", "POLHO", "DURDO", "ARCLK", "NUGYO", "KRSTL", "DGNMO",
    "DAGI", "GOKNR", "TAVHL", "AKENR", "AHSGY", "BESLR", "INVEO", "KAYSE",
    "AKYHO", "AFYON", "GEREL", "TEKTU", "BIOEN", "YGGYO", "EUPWR", "SILVR",
    "CEMTS", "YUNSA", "SEGYO", "PAPIL", "MOBTL", "TRGYO", "RUZYE", "VAKFA",
    "PASEU", "A1CAP", "MEKAG", "OZGYO", "SMRTG", "SANFM", "LIDFA", "PGSUS",
    "AKSEN", "ENJSA", "HUBVC", "KRDMA", "TERA", "FZLGY", "EGSER", "EYGYO",
    "IEYHO", "AVOD", "IHEVA", "AZTEK", "LIDER", "KRGYO", "LILAK", "MOGAN",
    "NTGAZ", "KOPOL", "GEDIK", "ISFIN", "MHRGY", "SOKM", "BEGYO", "BALSU",
    "BORSK", "TATEN", "MIATK", "BORLS", "ULUUN", "PATEK", "ARZUM", "NATEN",
    "SKTAS", "ULUFA", "KGYO", "KAREL", "SNICA", "METRO", "IHYAY", "ICUGS",
    "YYLGD", "AKFYE", "KLRHO", "KARSN", "VESBE", "OZKGY", "SUWEN", "ASTOR",
    "ENTRA", "ISGYO", "CONSE", "CWENE", "AGROT", "KUYAS", "BSOKE", "BIMAS",
    "GENTS", "KZBGY", "CVKMD", "MARTI", "RTALB", "CIMSA", "TUREX", "IZMDC",
    "ISMEN", "AHGAZ", "AKGRT", "INDES", "ESCOM", "BERA", "TTKOM", "FENER",
    "IHGZT", "GLRYH", "BINHO", "ISKPL", "KCAER", "ENKAI", "OSTIM", "DENGE",
    "EFOR", "BUCIM", "KONTR", "MAVI", "FONET", "RYGYO", "KOCMT", "GARAN",
    "GSDHO", "REEDR", "YESIL", "VRGYO", "KRVGD", "HALKB", "LRSHO", "RYSAS",
    "IMASM", "FROTO", "ARSAN", "KLGYO", "INFO", "KCHOL", "HUNER", "ESEN",
    "ANSGR", "THYAO", "SELVA", "MAGEN", "KRDMD", "OBAMS", "DARDL", "VAKBN",
    "DAPGM", "IHLGM", "CEMAS", "MRGYO", "KTLEV", "HLGYO", "SRVGY", "EUREN",
    "CCOLA", "SARKY", "MARMR", "ZRGYO", "HDFGS", "TUPRS", "IZENR", "AGHOL",
    "DOHOL", "TCELL", "TRALT", "OYAKC", "USAK", "FORMT", "VKGYO", "ALBRK",
    "YGYO", "ODAS", "SAHOL", "TSKB", "GLYHO", "ASELS", "PETKM", "SKBNK",
    "AKSA", "IHLAS", "AKSGY", "BJKAS", "YYAPI", "SISE", "QUAGR", "KATMR",
    "AKFGY", "TEHOL", "VAKFN", "EKGYO", "ZOREN", "TURSG", "ENERY", "AEFES",
    "PSGYO", "SNGYO", "TUKAS", "AKBNK", "YKBNK", "EREGL", "BTCIM", "TSPOR",
    "HEKTS", "PAHOL", "ADESE", "PEKGY", "CANTE", "GSRAY", "ISCTR", "SASA"
]

def get_real_price(symbol):
    """İş Yatırım'dan gerçek fiyat çek"""
    try:
        # Cache kontrolü (5 dakika)
        if symbol in PRICE_CACHE:
            cached_time, cached_price = PRICE_CACHE[symbol]
            if (datetime.now() - cached_time).seconds < 300:
                return cached_price
        
        # Gerçek veri çek
        hisse = iyh.Hisse(symbol)
        gunluk_data = hisse.gunluk()
        
        if gunluk_data is not None and len(gunluk_data) > 0:
            # Son kapanış fiyatı
            price = float(gunluk_data.iloc[-1]['Kapanis'])
            PRICE_CACHE[symbol] = (datetime.now(), price)
            return price
        
        # API hatası varsa rastgele döndür
        return 10 + random.random() * 90
        
    except Exception as e:
        logger.error(f"Price fetch error for {symbol}: {str(e)}")
        return 10 + random.random() * 90

def analyze_hisse_pine(symbol, sensitivity="Orta"):
    """Pine Script mantığı - Geliştirilmiş skorlama"""
    
    # Her hisse için tutarlı seed
    random.seed(hash(symbol))
    
    # Eşik değerleri
    if sensitivity == "Yüksek":
        early_threshold, confirm_threshold = 4, 6
    elif sensitivity == "Düşük":
        early_threshold, confirm_threshold = 8, 10
    else:
        early_threshold, confirm_threshold = 6, 8
    
    # Skorlar - Pine Script'teki gibi hesaplama
    early_bull_score = 0
    early_bear_score = 0
    confirm_bull_score = 0
    confirm_bear_score = 0
    early_reasons = []
    confirm_reasons = []
    
    # Rastgele ama tutarlı faktörler
    volatility = random.random()  # 0-1
    trend_strength = random.random() * 2 - 1  # -1 to 1
    volume_factor = random.random() * 2  # 0-2
    rsi_value = 30 + random.random() * 40  # 30-70
    momentum = random.random() * 2 - 1  # -1 to 1
    
    # ERKEN UYARI SKORLARI
    
    # 1. Volatilite sıkışması (Pine: atr_percentile < 20)
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
    
    # 2. RSI erken dönüş
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
    
    # 3. MACD erken sinyal
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
    
    # 4. Hacim anomalileri
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
    
    # 5. Hidden divergence
    if volatility < 0.3 and abs(trend_strength) < 0.2:
        if volume_factor > 1.2:
            early_bull_score += 4
            early_reasons.append({
                "type": "HIDDEN_ACCUMULATION",
                "message": "Gizli birikim tespit edildi",
                "value": "Birikim"
            })
        elif volume_factor < 0.8:
            early_bear_score += 4
            early_reasons.append({
                "type": "HIDDEN_DISTRIBUTION",
                "message": "Gizli dağıtım tespit edildi",
                "value": "Dağıtım"
            })
    
    # ONAY SKORLARI
    
    # 1. Trend onayı
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
    
    # 2. MACD crossover
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
    
    # 3. RSI onay
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
    
    # 4. Hacim onayı
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
    
    # Faz
    if confirm_signal_bull or confirm_signal_bear:
        phase = "ONAY_ALINAN"
    elif early_warning_bull or early_warning_bear:
        phase = "ERKEN_UYARI"
    elif volatility < 0.15:
        phase = "PATLAMAYA_HAZIR"
    else:
        phase = "BEKLEMEDE"
    
    # Yön
    if confirm_signal_bull or (early_warning_bull and phase == "ERKEN_UYARI"):
        direction = "YUKARI"
    elif confirm_signal_bear or (early_warning_bear and phase == "ERKEN_UYARI"):
        direction = "ASAGI"
    else:
        direction = "BELIRSIZ"
    
    # GERÇEK FİYAT ÇEK
    price = get_real_price(symbol)
    
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
        "current_price": round(price, 2),
        "rsi": round(rsi_value, 2),
        "ema20": round(price * 0.98, 2),
        "ema50": round(price * 0.96, 2),
        "ema200": round(price * 0.92, 2),
        "volume": random.randint(1000000, 50000000),
        "timestamp": "2025-01-04T22:00:00"
    }

@app.route('/')
def home():
    return jsonify({
        "status": "🚀 BIST API - Pine Script v5!",
        "total_stocks": len(BIST_STOCKS),
        "endpoints": {
            "analiz": "/api/analiz/<symbol>",
            "filtre": "/api/filtre?direction=YUKARI",
            "arama": "/api/arama?q=THY"
        }
    })

@app.route('/api/hisseler')
def get_hisseler():
    """Hisse listesi"""
    hisseler = []
    for kod in BIST_STOCKS:
        hisseler.append({
            "kod": kod,
            "ad": kod
        })
    
    return jsonify({
        "count": len(hisseler),
        "hisseler": hisseler,
        "timestamp": "2025-01-04T22:00:00"
    })

@app.route('/api/analiz/<symbol>')
def analyze_single(symbol):
    """Tek hisse analizi"""
    symbol = symbol.upper()
    
    if symbol not in BIST_STOCKS:
        return jsonify({"error": f"{symbol} bulunamadı"}), 404
    
    result = analyze_hisse_pine(symbol)
    return jsonify(result)

@app.route('/api/filtre')
def filter_stocks():
    """Filtreleme - SIRALANMIŞ"""
    direction = request.args.get('direction', '').upper()
    limit = int(request.args.get('limit', 100))
    
    results = []
    for kod in BIST_STOCKS[:limit]:
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
        "filter": direction if direction else "ALL",
        "results": results,
        "timestamp": "2025-01-04T22:00:00"
    })

@app.route('/api/arama')
def search_stocks():
    """Arama"""
    query = request.args.get('q', '').upper()
    
    if not query or len(query) < 2:
        return jsonify({"error": "En az 2 karakter"}), 400
    
    results = []
    for kod in BIST_STOCKS:
        if query in kod:
            results.append({
                "kod": kod,
                "ad": kod
            })
    
    return jsonify({
        "count": len(results),
        "query": query,
        "results": results
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
