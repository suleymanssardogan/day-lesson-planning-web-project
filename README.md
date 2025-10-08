# 📚 Ders Programı Yöneticisi — Web App

Modern Streamlit tabanlı ders planlama ve görev takip uygulaması. SQLite veritabanı (`ders_programi.db`) kullanır ve tek komutla çalışır.

## 🚀 Hızlı Başlangıç (Lokal)

1) Python 3.10+ kurulu olduğundan emin olun.
2) Gerekli paketleri yükleyin:
```bash
pip install -r requirements.txt
```
3) Uygulamayı başlatın:
```bash
streamlit run Subejct-PlaningV1.py
```
4) Tarayıcıdan açın: http://localhost:8501

- İlk giriş için yeni bir hesap oluşturabilirsiniz. Verileriniz `ders_programi.db` içinde saklanır.

## 🧩 Özellikler
- Kullanıcı girişi ve kayıt
- Ders programı oluşturma ve görüntüleme
- Görev ekleme, tamamlama ve silme
- Başarılar ve motivasyon rozetleri
- Son 7 gün istatistikleri (Plotly)

## 🎨 Tema ve Ayarlar
`.streamlit/config.toml` ile tema ve başlık ayarları yapılır.

## ☁️ Buluta Deploy

### Streamlit Community Cloud (en kolay)
1) Bu klasörü bir GitHub reposuna gönderin.
2) "New app" → repo ve `Subejct-PlaningV1.py` seçin → Deploy.

### Docker (Render/Railway/Heroku vb.)
1) İmajı oluşturun:
```bash
docker build -t subject-planning:latest .
```
2) Çalıştırın:
```bash
docker run -p 8501:8501 subject-planning:latest
```
3) Tarayıcıdan açın: http://localhost:8501

## 🗂️ Dosya Yapısı
- `Subejct-PlaningV1.py`: Streamlit uygulaması
- `ders_programi.db`: SQLite veritabanı (otomatik oluşturulur)
- `requirements.txt`: Python bağımlılıkları
- `.streamlit/config.toml`: Streamlit tema/başlık ayarları
- `Dockerfile`: Konteyner imajı için
- `Procfile`: PaaS platformları için süreç tanımı

## 🔒 Notlar
- Veritabanı dosyası yerelde saklanır. Buluta deploy ederken kalıcı depolama kullanın veya harici bir veritabanına geçin.

## 🧰 Sorun Giderme
- Port çakışması: `streamlit run ... --server.port 8502` kullanın.
- Paket uyumsuzlukları: `pip install --upgrade -r requirements.txt` deneyin.



