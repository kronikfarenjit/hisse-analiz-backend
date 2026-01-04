from flask import Flask, jsonify, request
from flask_cors import CORS
import random

app = Flask(__name__)
CORS(app)

# TÜM BIST HİSSELERİ - 629 ADET
BIST_STOCKS = [
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

def analyze_hisse(symbol):
    """Hisse analiz fonksiyonu - Pine Script mantığı basitleştirilmiş"""
    
    # Rastgele veri üret (gerçek analizde burası isyatirimhisse kullanacak)
    random.seed(hash(symbol))  # Her hisse için aynı sonuç
    
    # Skorlar hesapla
    early_bull = random.randint(0, 15)
    early_bear = random.randint(0, 15)
    confirm_bull = random.randint(0, 12)
    confirm_bear = random.randint(0, 12)
    
    # Yön belirleme
    early_total = early_bull - early_bear
    confirm_total = confirm_bull - confirm_bear
    
    if confirm_total >= 6:
        direction = "YUKARI"
        phase = "ONAY_ALINAN"
    elif confirm_total <= -6:
        direction = "ASAGI"
        phase = "ONAY_ALINAN"
    elif early_total >= 4:
        direction = "YUKARI"
        phase = "ERKEN_UYARI"
    elif early_total <= -4:
        direction = "ASAGI"
        phase = "ERKEN_UYARI"
    else:
        direction = "BELIRSIZ"
        phase = "BEKLEMEDE"
    
    # RSI ve diğer değerler
    rsi = 30 + random.random() * 40
    price = 10 + random.random() * 90
    
    # Sebepler oluştur
    reasons = []
    if early_bull > 8:
        reasons.append({
            "type": "VOLATILITY_SQUEEZE",
            "message": "Volatilite sıkışması tespit edildi",
            "value": "Düşük"
        })
    if confirm_bull > 5:
        reasons.append({
            "type": "TREND_STRONG",
            "message": "Güçlü yükseliş trendi",
            "value": "EMA uyumu"
        })
    if rsi < 35:
        reasons.append({
            "type": "RSI_OVERSOLD",
            "message": "RSI aşırı satım bölgesinde",
            "value": round(rsi, 2)
        })
    elif rsi > 65:
        reasons.append({
            "type": "RSI_OVERBOUGHT",
            "message": "RSI aşırı alım bölgesinde",
            "value": round(rsi, 2)
        })
    
    return {
        "kod": symbol,
        "phase": phase,
        "direction": direction,
        "early_bull_score": early_bull,
        "early_bear_score": early_bear,
        "confirm_bull_score": confirm_bull,
        "confirm_bear_score": confirm_bear,
        "early_reasons": reasons if direction != "BELIRSIZ" else [],
        "confirm_reasons": reasons if phase == "ONAY_ALINAN" else [],
        "current_price": round(price, 2),
        "rsi": round(rsi, 2),
        "ema20": round(price * 0.98, 2),
        "ema50": round(price * 0.96, 2),
        "ema200": round(price * 0.92, 2),
        "volume": random.randint(1000000, 50000000),
        "timestamp": "2025-01-04T19:00:00"
    }

@app.route('/')
def home():
    return jsonify({
        "status": "🚀 BIST API Çalışıyor!",
        "total_stocks": len(BIST_STOCKS),
        "endpoints": {
            "hisse_listesi": "/api/hisseler",
            "hisse_detay": "/api/hisse/<symbol>",
            "analiz": "/api/analiz/<symbol>",
            "filtre": "/api/filtre?direction=YUKARI",
            "arama": "/api/arama?q=THY"
        }
    })

@app.route('/api/hisseler')
def get_hisseler():
    """629 BIST hissesinin listesi"""
    hisseler = []
    for kod in BIST_STOCKS:
        hisseler.append({
            "kod": kod,
            "ad": kod
        })
    return jsonify({
        "count": len(hisseler),
        "hisseler": hisseler,
        "timestamp": "2025-01-04T19:00:00"
    })

@app.route('/api/hisse/<symbol>')
def get_hisse_detay(symbol):
    """100 günlük geçmiş veri"""
    symbol = symbol.upper()
    
    if symbol not in BIST_STOCKS:
        return jsonify({"error": f"{symbol} hissesi bulunamadı"}), 404
    
    data = []
    # Her hisse farklı fiyat aralığında
    base_price = 20.0 + random.uniform(0, 80)
    
    for i in range(100):
        change = random.uniform(-3, 3)
        price = max(1.0, base_price + change)
        
        data.append({
            "kod": symbol,
            "ad": symbol,
            "tarih": f"2024-{((i // 28) % 12) + 1:02d}-{(i % 28) + 1:02d}",
            "acilis": round(price - abs(change/2), 2),
            "yuksek": round(price + abs(change * 1.2), 2),
            "dusuk": round(price - abs(change * 1.2), 2),
            "kapanis": round(price, 2),
            "hacim": random.randint(500000, 20000000)
        })
        base_price = price
    
    return jsonify({"data": data})

# ========== YENİ ENDPOINT'LER ==========

@app.route('/api/analiz/<symbol>')
def analyze_single(symbol):
    """Tek hisse analizi"""
    symbol = symbol.upper()
    
    if symbol not in BIST_STOCKS:
        return jsonify({"error": f"{symbol} hissesi bulunamadı"}), 404
    
    result = analyze_hisse(symbol)
    return jsonify(result)

@app.route('/api/filtre')
def filter_stocks():
    """Hisseleri filtrele - direction=YUKARI/ASAGI/BELIRSIZ"""
    direction = request.args.get('direction', '').upper()
    limit = int(request.args.get('limit', 50))
    
    results = []
    for kod in BIST_STOCKS[:limit]:
        analysis = analyze_hisse(kod)
        
        # Filtreleme
        if direction and analysis['direction'] != direction:
            continue
        
        results.append(analysis)
    
    return jsonify({
        "count": len(results),
        "filter": direction if direction else "ALL",
        "results": results,
        "timestamp": "2025-01-04T19:00:00"
    })

@app.route('/api/arama')
def search_stocks():
    """Hisse arama - q parametresi ile"""
    query = request.args.get('q', '').upper()
    
    if not query or len(query) < 2:
        return jsonify({"error": "En az 2 karakter giriniz"}), 400
    
    # Arama yap
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
    app.run(debug=True)
