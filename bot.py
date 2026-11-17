import xml.etree.ElementTree as ET
import requests
import os

TOKEN_BOT = os.environ.get("TOKEN_BOT")
CHAT_ID = os.environ.get("CHAT_ID")
URL_XML = "https://bmkg-content-inatews.storage.googleapis.com/warninggeof.xml"

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
            
            identifier = "INFO_BMKG"
            headline = "Informasi Peringatan Dini Gempa"
            description = "Tidak ada keterangan tambahan."
            area_desc = "Wilayah Indonesia"
            lat = None
            lon = None
            
            for elem in root.iter():
                tag = elem.tag.split('}')[-1] # Membersihkan namespace XML jika ada
                if tag == "identifier" and elem.text:
                    identifier = elem.text
                elif tag == "headline" and elem.text:
                    headline = elem.text
                elif tag == "description" and elem.text:
                    description = elem.text
                elif tag == "areaDesc" and elem.text:
                    area_desc = elem.text
                elif tag == "point" and elem.text:
                    coords = elem.text.strip().split()
                    if len(coords) >= 2:
                        try:
                            lat = float(coords[0])
                            lon = float(coords[1])
                        except ValueError:
                            pass
            
            # Kirim pesan untuk uji coba (mengabaikan filter last_sent_id agar langsung terkirim saat di-run)
            pesan = (
                "🚨 *PERINGATAN DINI / WARNING GEMPA BMKG* 🚨\n\n"
                f"{headline}\n\n"
                f"📝 *Deskripsi:* {description}\n\n"
                f"📍 *Wilayah Terdampak:* {area_desc}\n\n"
                "_Sumber: InaTEWS BMKG_"
            )
            
            kirim_telegram_teks(pesan)
            
            # Kirim titik lokasi default atau dari XML jika ada
            if lat and lon:
                kirim_telegram_lokasi(lat, lon)
            else:
                # Titik koordinat cadangan (misal: Jakarta) jika tag point di XML kosong
                kirim_telegram_lokasi(-6.2088, 106.8456)
                
            print("Alert dan titik lokasi berhasil dikirim!")
        else:
            print(f"Gagal mengambil XML, status code: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    cek_warning_bmkg()
