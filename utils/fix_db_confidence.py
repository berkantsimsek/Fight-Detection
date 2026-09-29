import sqlite3

def fix_confidence(db_path):
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            # Confidence değerlerini al
            cursor.execute("SELECT id, confidence FROM events")
            rows = cursor.fetchall()

            for row in rows:
                event_id, confidence = row
                try:
                    # BLOB veya bytes ise decode et
                    if isinstance(confidence, bytes):
                        confidence = float(confidence.decode('utf-8'))
                    elif isinstance(confidence, str):
                        confidence = float(confidence)
                    # Güncelle
                    cursor.execute("UPDATE events SET confidence = ? WHERE id = ?", (confidence, event_id))
                except (ValueError, TypeError) as e:
                    print(f"ID {event_id} için confidence dönüşüm hatası: {confidence}, hata: {e}")
                    # Hatalı veriyi 0.0 yap
                    cursor.execute("UPDATE events SET confidence = 0.0 WHERE id = ?", (event_id,))

            conn.commit()
            print("Veritabanı güncellendi.")
    except Exception as e:
        print(f"Veritabanı düzeltme hatası: {e}")

if __name__ == "__main__":
    db_path = "/Users/ilkaygokbudak/PycharmProjects/RealTime-Violence-Detection/events.db"  # Veritabanı yolunu güncelleyin
    fix_confidence(db_path)