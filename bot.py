import xml.etree.ElementTree as ET
import requests
import os

TOKEN_BOT = os.environ.get("TOKEN_BOT")
CHAT_ID = os.environ.get("CHAT_ID")
URL_XML = "https://bmkg-content-inatews.storage.googleapis.com/warninggeof.xml"

# Variabel penyaring untuk mencegah pesan duplikat
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
                tag = elem.tag.split('}')[-1]
                if tag == "identifier" and elem.text and not identifier:
                    identifier = elem.text.strip()
                elif tag == "headline" and elem.text and not headline:
                    headline = elem.text.strip()
                elif tag == "description" and elem.text and not description:
                    description = elem.text.strip()
                elif tag == "areaDesc" and elem.text and not area_desc:
                    area_desc = elem.text.strip()
                elif tag == "point" and elem.text and not lat:
                    coords = elem.text.strip().split()
                    if len(coords) >= 2:
                        try:
                            lat = float(coords[0])
                            lon = float(coords[1])
                        except ValueError:
                            pass
            
            # Jika ditemukan data identifier dan ID-nya belum pernah dikirim sebelumnya
            if identifier and identifier != last_sent_id:
                last_sent_id = identifier
                
                pesan = (
                    "🚨 *PERINGATAN DINI / WARNING GEMPA BMKG* 🚨\n\n"
                    f"{headline}\n\n"
                    f"{description}\n\n"
                    f"📍 *Wilayah Terdampak:* {area_desc}\n\n"
                    "_Sumber: InaTEWS BMKG_"
                )
                
                kirim_telegram_teks(pesan)
                
                if lat and lon:
                    kirim_telegram_lokasi(lat, lon)
                
                print("Alert baru berhasil dikirim ke Telegram!")
            else:
                print("Tidak ada data peringatan baru atau ID masih sama.")
        else:
            print(f"Gagal mengambil XML, status code: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    cek_warning_bmkg()
