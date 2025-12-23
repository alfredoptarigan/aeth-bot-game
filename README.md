# 🎮 Aetherion Game Bot

Discord RPG Bot dengan sistem leveling, inventory, PVP, hunting, dan shift system.

## 📋 Fitur

- **Leveling System** - Dapatkan EXP dari chat dan naik level
- **Daily Rewards** - Klaim hadiah harian
- **Dice Roll** - Lempar dadu untuk mendapatkan uang (5x/hari)
- **Monster Hunting** - Berburu monster untuk EXP dan Gold (5x/hari)
- **PVP Fight** - Bertarung melawan pemain lain
- **Shop System** - Beli weapon, armor, dan role
- **Inventory & Equipment** - Kelola item dan equip gear
- **Stat Upgrade** - Tingkatkan ATK, DEF, SPD, DEX, CRIT, MDMG, HP, MP
- **Shift System** - Sistem kerja shift untuk mendapatkan reward
- **Leaderboard** - Top 10 pemain

## 🗄️ Database Support

Bot ini mendukung 2 jenis database:
- **SQLite** (default) - `maingame.py`
- **MySQL** - `maingame_mysql.py`

---

## 🚀 Quick Start (SQLite)

### 1. Clone & Install Dependencies

```bash
git clone <repository-url>
cd aeth-bot-game
pip3 install -r requirements.txt
```

### 2. Setup Environment

Buat file `.env`:
```env
DISCORD_TOKEN=your_discord_bot_token_here
```

### 3. Jalankan Bot

```bash
python3 maingame.py
```

---

## 🔄 Migrasi ke MySQL

Jika ingin menggunakan MySQL untuk performa lebih baik dan skalabilitas:

### Prerequisites

1. **MySQL Server** terinstall dan berjalan
2. **Python 3.8+**

### Step 1: Install MySQL (macOS)

```bash
# Install dengan Homebrew
brew install mysql

# Start MySQL service
brew services start mysql

# Setup password (pertama kali)
mysql_secure_installation
```

Untuk OS lain:
- **Ubuntu/Debian**: `sudo apt install mysql-server`
- **Windows**: Download dari https://dev.mysql.com/downloads/mysql/

### Step 2: Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

Requirements sudah termasuk:
- `mysql-connector-python`
- `sqlalchemy`
- `alembic`

### Step 3: Konfigurasi Environment

Edit file `.env` dan tambahkan konfigurasi MySQL:

```env
DISCORD_TOKEN=your_discord_bot_token_here

# MySQL Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DATABASE=aethbotgame
```

### Step 4: Setup Database MySQL

Jalankan script untuk membuat database dan tabel:

```bash
python3 setup_mysql.py
```

Output yang diharapkan:
```
🚀 SETUP DATABASE MYSQL
==================================================
🔧 Membuat database...
✅ Database 'aethbotgame' berhasil dibuat/sudah ada
🔧 Membuat tabel...
  ✅ Tabel 'users' dibuat
  ✅ Tabel 'inventory' dibuat
  ✅ Tabel 'items' dibuat
  ✅ Tabel 'roles' dibuat
  ✅ Tabel 'shift_config' dibuat
  ✅ Tabel 'active_shifts' dibuat
🔧 Menambahkan default items...
  ✅ Default items dan roles ditambahkan
==================================================
✅ SETUP SELESAI!
```

### Step 5: Migrasi Data dari SQLite (Opsional)

Jika sudah memiliki data di SQLite dan ingin memindahkannya:

```bash
python3 migrate_sqlite_to_mysql.py
```

Output yang diharapkan:
```
🚀 MIGRASI DATA SQLITE KE MYSQL
==================================================
✅ Koneksi MySQL berhasil!
📦 Migrasi tabel users...
  ✅ X users berhasil dimigrasi
📦 Migrasi tabel inventory...
  ✅ X inventory items berhasil dimigrasi
📦 Migrasi tabel items...
  ✅ X items berhasil dimigrasi
📦 Migrasi tabel roles...
  ✅ X roles berhasil dimigrasi
📦 Migrasi tabel shift_config...
  ✅ X shift configs berhasil dimigrasi
📦 Migrasi tabel active_shifts...
  ✅ X active shifts berhasil dimigrasi
==================================================
✅ MIGRASI SELESAI!
```

### Step 6: Jalankan Bot dengan MySQL

```bash
python3 maingame_mysql.py
```

---

## 📁 Struktur Project

```
aeth-bot-game/
├── .env                        # Environment variables
├── .gitignore                  # Git ignore file
├── README.md                   # Dokumentasi ini
├── requirements.txt            # Python dependencies
├── monsters.json               # Data monster untuk hunting
│
├── maingame.py                 # Bot utama (SQLite)
├── maingame_mysql.py           # Bot utama (MySQL)
│
├── setup_mysql.py              # Script setup database MySQL
├── migrate_sqlite_to_mysql.py  # Script migrasi SQLite → MySQL
│
├── database/                   # Database module
│   ├── __init__.py
│   ├── models.py               # SQLAlchemy models
│   └── connection.py           # MySQL connection helper
│
├── alembic/                    # Database migrations (opsional)
│   ├── env.py
│   └── versions/
│
└── aethbotgame.db              # SQLite database file
```

---

## 🎮 Commands

| Command | Deskripsi |
|---------|-----------|
| `ag!stat` / `ag!level` | Lihat statistik karakter |
| `ag!daily` | Klaim hadiah harian |
| `ag!roll` / `ag!dice` | Lempar dadu (5x/hari) |
| `ag!hunt` | Berburu monster (5x/hari) |
| `ag!fight @user` | PVP melawan pemain lain |
| `ag!leaderboard` | Top 10 pemain |
| `ag!shop [weapon/armor/role]` | Lihat toko |
| `ag!buy [kategori] [nama]` | Beli item/role |
| `ag!inventory` | Lihat inventaris |
| `ag!equip [item]` | Pasang equipment |
| `ag!unequip [item]` | Lepas equipment |
| `ag!upgrade [stat] [amount]` | Upgrade stat |
| `ag!sell [item] [jumlah]` | Jual item |
| `ag!givemoney @user [amount]` | Transfer uang |
| `ag!shift` | Mulai/cek shift |
| `ag!help` | Tampilkan bantuan |

### Admin Commands (Owner/Cybersurge)

| Command | Deskripsi |
|---------|-----------|
| `ag!setshift [durasi] [money] [exp] [max] [detail]` | Atur konfigurasi shift |
| `ag!finishshift @user` | Paksa selesaikan shift user |

---

## 🔧 Troubleshooting

### MySQL Connection Error

**Error**: `Access denied for user 'root'@'localhost'`
- Pastikan password di `.env` sudah benar
- Coba login manual: `mysql -u root -p`

**Error**: `Can't connect to MySQL server`
- Pastikan MySQL service berjalan
- macOS: `brew services list` → `brew services start mysql`
- Linux: `sudo systemctl status mysql`

**Error**: `Unknown database 'aethbotgame'`
- Jalankan `python3 setup_mysql.py` terlebih dahulu

### Bot Not Responding

1. Pastikan token Discord valid di `.env`
2. Pastikan bot sudah di-invite ke server dengan permission yang benar
3. Cek log error di terminal

### Rollback ke SQLite

Jika ingin kembali ke SQLite:
```bash
python3 maingame.py
```

---

## 📝 Environment Variables

| Variable | Deskripsi | Default |
|----------|-----------|---------|
| `DISCORD_TOKEN` | Token bot Discord | (required) |
| `MYSQL_HOST` | MySQL host | `localhost` |
| `MYSQL_PORT` | MySQL port | `3306` |
| `MYSQL_USER` | MySQL username | `root` |
| `MYSQL_PASSWORD` | MySQL password | (required for MySQL) |
| `MYSQL_DATABASE` | Nama database | `aethbotgame` |

---

## 📄 License

MIT License

---

## 🤝 Contributing

Pull requests are welcome!
