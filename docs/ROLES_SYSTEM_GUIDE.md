# 🎭 Roles System Guide

## Overview
Sistem roles telah berhasil dibuat dengan table `roles` dan `user_roles` untuk mengelola role-role yang dapat dibeli pemain dalam game Discord bot.

## 📊 Database Structure

### Table: `roles`
```sql
CREATE TABLE roles (
    role_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    price INT DEFAULT 0,
    description TEXT,
    color VARCHAR(7) DEFAULT '#000000',
    created_at DATETIME
);
```

### Table: `user_roles`
```sql
CREATE TABLE user_roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    purchased_at DATETIME,
    is_active INT DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);
```

## 🔧 Query Functions

File: `database/queries/role_queries.py`

### Role Management Functions
- `get_all_roles()` - Mendapatkan semua role yang tersedia
- `get_role_by_id(role_id)` - Mendapatkan role berdasarkan ID
- `get_role_by_name(role_name)` - Mendapatkan role berdasarkan nama
- `create_role(name, price, description, color)` - Membuat role baru
- `update_role(role_id, **kwargs)` - Update informasi role
- `delete_role(role_id)` - Hapus role (dan semua user_roles terkait)

### User Role Functions
- `get_user_roles(user_id, active_only=True)` - Mendapatkan semua role user
- `user_has_role(user_id, role_id)` - Cek apakah user memiliki role tertentu
- `user_has_role_by_name(user_id, role_name)` - Cek role berdasarkan nama
- `purchase_role(user_id, role_id)` - Beli role untuk user
- `activate_user_role(user_id, role_id)` - Aktifkan role user
- `deactivate_user_role(user_id, role_id)` - Nonaktifkan role user
- `remove_user_role(user_id, role_id)` - Hapus role dari user
- `get_role_owners(role_id, active_only=True)` - Mendapatkan semua pemilik role
- `count_role_owners(role_id, active_only=True)` - Hitung jumlah pemilik role

## 🚀 Migration History

1. **f4c0b64585f3** - Add user_roles table with correct data types
2. **89eded433a9f** - Add auto increment to role_id
3. **6fdbf9369526** - Fix role_id auto increment with foreign key

## 📝 Usage Examples

### Membuat Role Baru
```python
from database.queries.role_queries import create_role

role_id = create_role(
    name="Premium Member",
    price=50000,
    description="Premium membership with exclusive benefits",
    color="#FFD700"
)
```

### Membeli Role untuk User
```python
from database.queries.role_queries import purchase_role

success, message = purchase_role(user_id=123456789, role_id=1)
if success:
    print("Role purchased successfully!")
else:
    print(f"Failed: {message}")
```

### Cek Role User
```python
from database.queries.role_queries import get_user_roles, user_has_role

# Mendapatkan semua role user
user_roles = get_user_roles(user_id=123456789)
for role in user_roles:
    print(f"Role: {role[5]}, Price: {role[6]}")

# Cek role tertentu
has_vip = user_has_role(user_id=123456789, role_id=1)
```

## 🎮 Sample Roles

Script `setup_sample_roles.py` telah membuat role-role berikut:

### Membership Tiers
- **Bronze Member** - 5,000 ACR - Basic membership
- **Silver Member** - 15,000 ACR - Moderate perks
- **Gold Member** - 30,000 ACR - Great perks
- **Platinum Member** - 50,000 ACR - Premium perks
- **Diamond Member** - 100,000 ACR - Exclusive perks

### Class Roles
- **Warrior** - 25,000 ACR - Combat specialist
- **Mage** - 25,000 ACR - Magic specialist
- **Archer** - 25,000 ACR - Ranged combat specialist

### Special Roles
- **Veteran** - 75,000 ACR - Experienced player
- **Guild Leader** - 200,000 ACR - Leadership role

## 🔄 Running Migrations

### Untuk menjalankan migration:
```bash
python3 -m alembic upgrade head
```

### Untuk membuat migration baru:
```bash
python3 -m alembic revision --autogenerate -m "Description of changes"
```

### Untuk rollback migration:
```bash
python3 -m alembic downgrade -1
```

## 🛠️ Integration dengan Bot Commands

Untuk mengintegrasikan dengan bot commands, Anda dapat:

1. **Update shop commands** untuk menampilkan dan menjual roles
2. **Tambahkan role commands** untuk melihat role yang dimiliki
3. **Implementasi role benefits** dalam game mechanics
4. **Tambahkan role display** di profile/stat commands

### Contoh implementasi di shop command:
```python
from database.queries.role_queries import get_all_roles, purchase_role
from database.queries.user_queries import get_user_data, update_user_money

async def handle_buy_role(message, role_name):
    user_id = message.author.id
    role = get_role_by_name(role_name)
    
    if not role:
        await message.channel.send("❌ Role tidak ditemukan!")
        return
    
    user_data = get_user_data(user_id)
    if user_data[2] < role[2]:  # Check money
        await message.channel.send("❌ Uang tidak cukup!")
        return
    
    success, msg = purchase_role(user_id, role[0])
    if success:
        # Deduct money
        new_money = user_data[2] - role[2]
        update_user_money(user_id, new_money)
        await message.channel.send(f"✅ Berhasil membeli role {role[1]}!")
    else:
        await message.channel.send(f"❌ {msg}")
```

## 🎯 Next Steps

1. **Implementasi role benefits** - Tambahkan bonus stats atau privileges untuk role tertentu
2. **Role display system** - Tampilkan role di profile dan leaderboard
3. **Role-based permissions** - Implementasi akses khusus berdasarkan role
4. **Role expiration** - Sistem role sementara dengan durasi tertentu
5. **Role upgrade system** - Sistem upgrade dari role rendah ke tinggi

## 🔍 Troubleshooting

### Foreign Key Errors
Jika mendapat error foreign key constraint, pastikan:
- User ID exists di table `users`
- Role ID exists di table `roles`

### Migration Errors
Jika migration gagal:
1. Check database connection di `.env`
2. Pastikan MySQL server running
3. Check alembic version table: `SELECT * FROM alembic_version`

### Query Errors
Jika query functions error:
1. Check import statements
2. Verify database connection
3. Check table structure dengan `DESCRIBE table_name`