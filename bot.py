import xml.etree.ElementTree as ET
import requests
import os
import re

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

def ekstrak_koordinat_dari_teks(teks):
    # Mencari pola koordinat seperti "7.00 LS, 106.95 BT" atau sejenisnya di dalam deskripsi
    try:
        # Contoh pola: Lok:6.03 LS, 131.62 BT atau 7.00 LS, 106.95 BT
        match = re.search(r'([\d.]+)\s*LS[,\s]+([\d.]+)\s*BT', teks, re.IGNORECASE)
        if match:
            lat = -float(match.group(1)) # LS (Lintang Selatan) bernilai negatif
            lon = float(match.group(2))  # BT (Bujur Timur) bernilai positif
            return lat, lon
        
        match_general = re.search(r'(-?[\d.]+)[,\s]+(-?[\d.]+)', teks)
        if match_general:
            return float(match_general.group(1)), float(match_general.group(2))
    except Exception:
        pass
    return None, None

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
                elif tag == "areaDesc" and elem.text:
                    if area_desc:
                        if elem.text.strip() not in area_desc:
                            area_desc += ", " + elem.text.strip()
                    else:
                        area_desc = elem.text.strip()
                elif tag == "point" and elem.text and not lat:
                    coords = elem.text.strip().split()
                    if len(coords) >= 2:
                        try:
                            lat = float(coords[0])
                            lon = float(coords[1])
                        except ValueError:
                            pass
            
            if not identifier:
                identifier = "BMKG_EVENT"

            if identifier != last_sent_id:
                last_sent_id = identifier
                
                # Jika area_desc kosong, ambil dari deskripsi atau beri default
                if not area_desc or area_desc.lower() == "none":
                    area_desc = "Wilayah Indonesia"

                # Jika koordinat titik dari XML tidak ada, ekstrak langsung dari teks deskripsi gempa
                if not lat or not lon:
                    if description:
                        lat, lon = ekstrak_koordinat_dari_teks(description)

                pesan = (
                    "🚨 *PERINGATAN DINI / WARNING GEMPA BMKG* 🚨\n\n"
                    f"📌 *Headline:* {headline}\n\n"
                    f"📝 *Deskripsi:* {description}\n\n"
                    f"📍 *Wilayah Terdampak:* {area_desc}\n\n"
                    "_Sumber: InaTEWS BMKG_"
                )
                
                kirim_telegram_teks(pesan)
                
                # Kirim lokasi jika koordinat berhasil didapatkan
                if lat and lon:
                    kirim_telegram_lokasi(lat, lon)
                else:
                    # Koordinat cadangan default (misal: pusat Jakarta) jika benar-benar tidak ditemukan
                    kirim_telegram_lokasi(-6.2088, 106.8456)
                
                print("Alert, wilayah, dan lokasi berhasil dikirim!")
            else:
                print("Tidak ada data peringatan baru.")
        else:
            print(f"Gagal mengambil XML, status code: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    cek_warning_bmkg()
