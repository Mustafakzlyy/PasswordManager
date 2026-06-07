# 🔒 PassManager - Local Password Manager

IronVault, yerel sisteminizde hassas verilerinizi ve şifrelerinizi en üst düzey güvenlik standartlarıyla saklamak için geliştirilmiş, grafik arayüze (GUI) sahip **sıfır bilgi (Zero-Knowledge)** tabanlı bir şifre yöneticisidir. 

Verileriniz buluta çıkmaz, tamamen sizin kontrolünüzde ve yerelinizde şifreli olarak muhafaza edilir.

---

## 🛠️ Siber Güvenlik Mimarisi & Özellikleri

Proje, basit bir veri saklama aracından ziyade bir siber güvenlik ürünü olarak tasarlanmıştır:

* **AES-256-GCM Şifreleme:** Veritabanındaki şifreler, endüstri standardı olan AES-256'nın GCM (Galois/Counter Mode) modu ile şifrelenir. Bu mod sadece gizlilik sağlamaz, aynı zamanda verinin bütünlüğünü (integrity) de doğrular. Dosya üzerinde el ile yapılacak herhangi bir değişiklik anında tespit edilir.
* **PBKDF2 Anahtar Türetme:** Belirlediğiniz Master Şifre asla diske kaydedilmez. Bunun yerine, kriptografik rastgele bir `Salt` ile birleştirilerek **PBKDF2HMAC** (SHA256, 100.000 iterasyon) algoritmasından geçirilir ve dinamik bir AES anahtarı türetilir.
* **Anti-Forensics Kendi Kendini İmha (Self-Destruct):** Kaba kuvvet (Brute-Force) saldırılarına karşı aktif savunma içerir. Üst üste 3 kez yanlış Master Şifre girilmesi durumunda, `vault.json` dosyasının içeriği `os.urandom` üzerinden gelen rastgele byte'larla tamamen ezilir (shredding) ve ardından dosya sistemden silinir. Bu sayede adli bilişim araçlarıyla verinin geri getirilmesi engellenir.
* **Pano Bellek Koruması (Clipboard Auto-Clear):** Bir şifre kopyalandığında arayüzde açık metin olarak gösterilmez. Doğrudan panoya aktarılır ve omuz sörfü (shoulder surfing) saldırılarını engellemek adına 15 saniye sonra bellekten otomatik olarak kazınır.
* **Kriptografik Şifre Üretici:** `secrets` kütüphanesini kullanarak tahmin edilmesi imkansız, yüksek entropili güçlü şifreler üretir.

---

## 🚀 Kurulum ve Çalıştırma

### Gereksinimler
Sisteminizde Python 3'ün ve ekran sunucunuza uygun pano araçlarının kurulu olması gerekir.

**Arch Linux / CachyOS tabanlı sistemler için:**
```bash
 # Sistem bağımlılıklarını kurun (Pano yönetimi için) 

sudo pacman -S wl-clipboard xclip --needed --noconfirm

 # Gerekli Python kütüphanelerini yükleyin
 pip install cryptography rich pyperclip --break-system-packages 
```
### Çalıştırma
```bash
python passmanager.py
