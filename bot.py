import xml.etree.ElementTree as ET
import requests
import os

TOKEN_BOT = os.environ.get("TOKEN_BOT")
CHAT_ID = os.environ.get("CHAT_ID")
URL_XML = "https://bmkg-content-inatews.storage.googleapis.com/warninggeof.xml"

# Variabel sederhana untuk mencegah pesan duplikat dalam satu kali run
last_sent_id = None

def kirim_telegram_teks(pesan):
    url = f"https://api.telegram.org/bot{TOKEN_BOT}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error Telegram Teks: {e}")

def kirim_telegram_lokasi(lat, lon):
    url = f"https://api.telegram.org/bot{TOKEN_BOT}/sendLocation"
    payload = {"chat_id": CHAT_ID, "latitude": lat, "longitude": lon}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error Telegram Lokasi: {e}")

def cek_warning_bmkg():
    global last_sent_id
    try:
        response = requests.get(URL_XML, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            
            identifier = ""
            headline = ""
            description = ""
            area_desc = ""
            lat = None
            lon = None
            
            for elem in root.iter():
                if elem.tag.endswith("identifier") and not identifier:
                    identifier = elem.text
                elif elem.tag.endswith("headline") and not headline:
                    headline = elem.text
                elif elem.tag.endswith("description") and not description:
                    description = elem.text
                elif elem.tag.endswith("areaDesc") and not area_desc:
                    area_desc = elem.text
                # Format CAP biasanya menyimpan titik koordinat dalam tag <point> "lat lon"
                elif elem.tag.endswith("point") and not lat:
                    coords = elem.text.split()
                    if len(coords) >= 2:
                        lat = float(coords[0])
                        lon = float(coords[1])
            
            # Jika ada headline dan datanya baru (belum dikirim sebelumnya)
            if headline and identifier != last_sent_id:
                last_sent_id = identifier
                
                pesan = (
                    "🚨 *PERINGATAN DINI / WARNING GEMPA BMKG* 🚨\n\n"
                    f"{headline}\n\n"
                    f"📝 *Deskripsi:* {description}\n\n"
                    f"📍 *Wilayah Terdampak:* {area_desc}\n\n"
                    "_Sumber: InaTEWS BMKG_"
                )
                
                # Kirim pesan teks detail gempa
                kirim_telegram_teks(pesan)
                
                # Kirim titik lokasi peta jika koordinat ditemukan
                if lat and lon:
                    kirim_telegram_lokasi(lat, lon)
                    
                print("Alert dan titik lokasi berhasil dikirim!")
            else:
                print("Tidak ada data peringatan baru.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    cek_warning_bmkg()
