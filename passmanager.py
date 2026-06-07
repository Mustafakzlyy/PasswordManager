import os
import sys
import json
import time
import base64
import secrets
import string
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import pyperclip
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

VAULT_FILE = "vault.json"
MAX_ATTEMPTS = 3

class IronVaultGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🔒 PassManager")
        self.root.geometry("650x450")
        self.root.resizable(False, False)
        
        self.vault_data = None
        self.key = None
        self.attempts_left = MAX_ATTEMPTS
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.show_login_screen()

    def derive_key(self, master_password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
        return kdf.derive(master_password.encode())

    def self_destruct(self):
        messagebox.showerror("🚨Kasa imha ediliyor...")
        if os.path.exists(VAULT_FILE):
            file_size = os.path.getsize(VAULT_FILE)
            with open(VAULT_FILE, "wb") as f:
                f.write(os.urandom(file_size))
            os.remove(VAULT_FILE)
        self.root.destroy()
        sys.exit(1)

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_login_screen(self):
        self.clear_screen()
        
        frame = ttk.Frame(self.root, padding="30")
        frame.pack(expand=True)
        
        title_label = ttk.Label(frame, text="🔒 PassManager Yerel Şifre Kasası", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=10)
        
        if not os.path.exists(VAULT_FILE):
            status_text = "Mevcut kasa bulunamadı.Yeni bir Master Şifre oluşturun:"
            btn_text = "Kasa Oluştur ve Giriş Yap"
            self.is_first_run = True
        else:
            status_text = "Erişim için Master Şifrenizi giriniz:"
            btn_text = "Kasanın Kilidini Aç"
            self.is_first_run = False
            
        ttk.Label(frame, text=status_text, font=("Helvetica", 10)).pack(pady=5)
        
        self.password_entry = ttk.Entry(frame, show="*", width=30, font=("Helvetica", 12))
        self.password_entry.pack(pady=10)
        self.password_entry.focus()
        
        submit_btn = ttk.Button(frame, text=btn_text, command=self.handle_auth)
        submit_btn.pack(pady=10)
        
        self.root.bind('<Return>', lambda event: self.handle_auth())

    def handle_auth(self):
        mp = self.password_entry.get()
        if not mp:
            messagebox.showwarning("Uyarı", "Şifre alanı boş bırakılamaz!")
            return
            
        if self.is_first_run:
            salt = os.urandom(16)
            self.key = self.derive_key(mp, salt)
            aesgcm = AESGCM(self.key)
            nonce = os.urandom(12)
            encrypted_verifier = aesgcm.encrypt(nonce, b"VAULT_AUTH", None)
            
            self.vault_data = {
                "salt": base64.b64encode(salt).decode('utf-8'),
                "nonce": base64.b64encode(nonce).decode('utf-8'),
                "verifier": base64.b64encode(encrypted_verifier).decode('utf-8'),
                "attempts_left": MAX_ATTEMPTS,
                "entries": {}
            }
            with open(VAULT_FILE, "w") as f:
                json.dump(self.vault_data, f)
            messagebox.showinfo("Başarılı", "Kasa başarıyla oluşturuldu!")
            self.show_dashboard()
        else:
            with open(VAULT_FILE, "r") as f:
                self.vault_data = json.load(f)
                
            if self.vault_data.get("attempts_left", MAX_ATTEMPTS) <= 0:
                self.self_destruct()
                
            salt = base64.b64decode(self.vault_data["salt"])
            nonce = base64.b64decode(self.vault_data["nonce"])
            verifier = base64.b64decode(self.vault_data["verifier"])
            
            self.key = self.derive_key(mp, salt)
            aesgcm = AESGCM(self.key)
            
            try:
                aesgcm.decrypt(nonce, verifier, None)
                self.vault_data["attempts_left"] = MAX_ATTEMPTS
                with open(VAULT_FILE, "w") as f:
                    json.dump(self.vault_data, f)
                self.show_dashboard()
            except Exception:
                self.vault_data["attempts_left"] -= 1
                remaining = self.vault_data["attempts_left"]
                with open(VAULT_FILE, "w") as f:
                    json.dump(self.vault_data, f)
                    
                if remaining <= 0:
                    self.self_destruct()
                else:
                    messagebox.showerror("Hata", f"Hatalı Master Şifre! Kalan Hak: {remaining}")

    def show_dashboard(self):
        self.clear_screen()
        self.root.unbind('<Return>')
        
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill="x")
        
        ttk.Label(top_frame, text="🔑 Şifre Kasanız", font=("Helvetica", 14, "bold")).pack(side="left")
        
        self.countdown_label = ttk.Label(top_frame, text="", font=("Helvetica", 10, "italic"), foreground="orange")
        self.countdown_label.pack(side="right", padx=10)

        table_frame = ttk.Frame(self.root, padding="10")
        table_frame.pack(fill="both", expand=True)
        
        self.tree = ttk.Treeview(table_frame, columns=("Platform", "Kullanıcı Adı", "Şifre"), show="headings")
        self.tree.heading("Platform", text="Platform")
        self.tree.heading("Kullanıcı Adı", text="Kullanıcı Adı / E-posta")
        self.tree.heading("Şifre", text="Şifre (Çift Tıkla - Kopyala)")
        self.tree.column("Şifre", anchor="center")
        self.tree.pack(fill="both", expand=True)
        
        self.tree.bind("<Double-1>", self.copy_password)
       
        btn_frame = ttk.Frame(self.root, padding="10")
        btn_frame.pack(fill="x")
        
        ttk.Button(btn_frame, text="➕ Yeni Şifre Ekle", command=self.show_add_window).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🔄 Yenile", command=self.refresh_table).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🚪 Güvenli Çıkış", command=self.root.destroy).pack(side="right", padx=5)
        
        self.refresh_table()

    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        aesgcm = AESGCM(self.key)
        for platform, data in self.vault_data.get("entries", {}).items():
            self.tree.insert("", "end", iid=platform, values=(platform, data["username"], "********"))

    def copy_password(self, event):
        selected_item = self.tree.selection()
        if not selected_item:
            return
        
        platform = selected_item[0]
        data = self.vault_data["entries"][platform]
        
        nonce = base64.b64decode(data["nonce"])
        encrypted_password = base64.b64decode(data["password"])
        
        aesgcm = AESGCM(self.key)
        try:
            decrypted_password = aesgcm.decrypt(nonce, encrypted_password, None).decode('utf-8')
            pyperclip.copy(decrypted_password)
            
            threading.Thread(target=self.clipboard_countdown, daemon=True).start()
        except Exception:
            messagebox.showerror("Hata", "Şifre çözülemedi!")

    def clipboard_countdown(self):
        for i in range(15, 0, -1):
            self.countdown_label.config(text=f"⏱️ Şifre kopyalandı! Pano {i}sn içinde temizlenecek...")
            time.sleep(1)
        pyperclip.copy("")
        self.countdown_label.config(text="✅ Pano güvenli bir şekilde temizlendi.")

    def show_add_window(self):
        add_win = tk.Toplevel(self.root)
        add_win.title("Yeni Şifre Ekle")
        add_win.geometry("350x280")
        add_win.resizable(False, False)
        
        frame = ttk.Frame(add_win, padding="15")
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="Platform (örn: GitHub):").pack(anchor="w", pady=2)
        plat_ent = ttk.Entry(frame, width=30)
        plat_ent.pack(fill="x", pady=2)
        
        ttk.Label(frame, text="Kullanıcı Adı:").pack(anchor="w", pady=2)
        user_ent = ttk.Entry(frame, width=30)
        user_ent.pack(fill="x", pady=2)
        
        ttk.Label(frame, text="Şifre:").pack(anchor="w", pady=2)
        pass_ent = ttk.Entry(frame, width=30, show="*")
        pass_ent.pack(fill="x", pady=2)
        
        def auto_gen():
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            pwd = ''.join(secrets.choice(alphabet) for _ in range(16))
            pass_ent.delete(0, tk.END)
            pass_ent.insert(0, pwd)
            pass_ent.config(show="") 
            
        ttk.Button(frame, text="🎲 Güçlü Şifre Üret", command=auto_gen).pack(fill="x", pady=5)
        
        def save():
            p, u, s = plat_ent.get(), user_ent.get(), pass_ent.get()
            if not (p and u and s):
                messagebox.showwarning("Hata", "Tüm alanları doldurun!")
                return
                
            aesgcm = AESGCM(self.key)
            nonce = os.urandom(12)
            encrypted = aesgcm.encrypt(nonce, s.encode(), None)
            
            self.vault_data["entries"][p] = {
                "username": u,
                "nonce": base64.b64encode(nonce).decode('utf-8'),
                "password": base64.b64encode(encrypted).decode('utf-8')
            }
            with open(VAULT_FILE, "w") as f:
                json.dump(self.vault_data, f)
                
            self.refresh_table()
            add_win.destroy()
            messagebox.showinfo("Başarılı", "Şifre güvenli biçimde kaydedildi.")
            
        ttk.Button(frame, text="💾 Kaydet", command=save).pack(fill="x", pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = IronVaultGUI(root)
    root.mainloop()