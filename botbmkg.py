import xml.etree.ElementTree as ET
import requests
import os

TOKEN_BOT = os.environ.get("TOKEN_BOT")
CHAT_ID = os.environ.get("CHAT_ID")
URL_XML = "https://data.bmkg.go.id/DataMKG/TEWS/autogempa.xml"
FILE_LOG = "last_id.txt"

def baca_last_id():
    if os.path.exists(FILE_LOG):
        try:
            with open(FILE_LOG, "r") as f:
                return f.read().strip()
        except Exception:
            pass
    return ""

def simpan_last_id(new_id):
    try:
        with open(FILE_LOG, "w") as f:
            f.write(new_id)
    except Exception as e:
        print(f"Gagal menyimpan last_id: {e}")

def kirim_telegram_teks(pesan):
    url = f"https://api.telegram.org/bot{TOKEN_BOT}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": pesan, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error Telegram Teks: {e}")

def kirim_telegram_foto(foto_url, caption):
    url = f"https://api.telegram.org/bot{TOKEN_BOT}/sendPhoto"
    payload = {"chat_id": CHAT_ID, "photo": foto_url, "caption": caption, "parse_mode": "Markdown"}
    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code != 200:
            kirim_telegram_teks(caption)
    except Exception as e:
        print(f"Error Telegram Foto: {e}")
        kirim_telegram_teks(caption)

def kirim_telegram_lokasi(lat, lon):
    url = f"https://api.telegram.org/bot{TOKEN_BOT}/sendLocation"
    payload = {"chat_id": CHAT_ID, "latitude": lat, "longitude": lon}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error Telegram Lokasi: {e}")

def cek_warning_bmkg():
    last_sent_id = baca_last_id()
    try:
        response = requests.get(URL_XML, timeout=10)
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            
            gempa_elem = root.find("gempa")
            if not gempa_elem:
                print("Format XML tidak sesuai.")
                return

            tanggal = gempa_elem.findtext("Tanggal", "").strip()
            jam = gempa_elem.findtext("Jam", "").strip()
            datetime_val = gempa_elem.findtext("DateTime", "").strip()
            coordinates = gempa_elem.findtext("Coordinates", "").strip()
            lintang = gempa_elem.findtext("Lintang", "").strip()
            bujur = gempa_elem.findtext("Bujur", "").strip()
            magnitude = gempa_elem.findtext("Magnitude", "").strip()
            kedalaman = gempa_elem.findtext("Kedalaman", "").strip()
            wilayah = gempa_elem.findtext("Wilayah", "").strip()
            potensi = gempa_elem.findtext("Potensi", "").strip()
            dirasakan = gempa_elem.findtext("Dirasakan", "-").strip()
            shakemap_file = gempa_elem.findtext("Shakemap", "").strip()
            
            unique_id = datetime_val if datetime_val else f"{tanggal}_{jam}"

            if unique_id and unique_id != last_sent_id:
                simpan_last_id(unique_id)
                
                lat, lon = None, None
                try:
                    if "LS" in lintang:
                        lat = -float(lintang.replace("LS", "").strip())
                    elif "LU" in lintang:
                        lat = float(lintang.replace("LU", "").strip())
                        
                    if "BT" in bujur:
                        lon = float(bujur.replace("BT", "").strip())
                    elif "BB" in bujur:
                        lon = -float(bujur.replace("BB", "").strip())
                except Exception:
                    if coordinates:
                        parts = coordinates.split(",")
                        if len(parts) == 2:
                            lat = float(parts[0].strip())
                            lon = float(parts[1].strip())

                # Format teks pesan diperbarui dengan menambahkan baris Koordinat
                pesan = (
                    "🚨 *INFORMASI GEMPA BMKG* 🚨\n\n"
                    f"📅 *Waktu :* {tanggal}, {jam}\n"
                    f"⚡ *Magnitudo :* {magnitude}\n"
                    f"🌊 *Kedalaman :* {kedalaman}\n"
                    f"🌐 *Koordinat :* {lintang}, {bujur}\n"
                    f"📍 *Pusat Gempa :* {wilayah}\n"
                    f"👥 *Dirasakan :* {dirasakan}\n"
                    f"⚠️ *Potensi :* {potensi}\n\n"
                    "_Sumber: Data Resmi BMKG_"
                )
                
                if shakemap_file:
                    shakemap_url = f"https://data.bmkg.go.id/DataMKG/TEWS/{shakemap_file}"
                    kirim_telegram_foto(shakemap_url, pesan)
                else:
                
                    kirim_telegram_teks(pesan)
                
                if lat and lon:
                    kirim_telegram_lokasi(lat, lon)
                else:
                    kirim_telegram_lokasi(-6.2088, 106.8456)
                
                print(f"Gempa baru berhasil dikirim lengkap dengan Koordinat! ID: {unique_id}")
            else:
                print("Data gempa masih sama dengan sebelumnya. Tidak mengirim ulang.")
        else:
            print(f"Gagal mengambil XML, status code: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    cek_warning_bmkg()
