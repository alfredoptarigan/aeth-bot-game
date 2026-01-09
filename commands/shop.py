"""
Shop-related commands (buy, sell, shop)
"""
import discord
from commands.base import BaseCommand
from database.queries.user_queries import get_user_data, update_full_user_data
from database.queries.inventory_queries import get_user_inventory, update_inventory
from database.queries.shop_queries import get_shop_items, get_item_details, get_shop_roles, get_role_details

class ShopCommands(BaseCommand):
    """Handle shop-related commands"""
    
    async def handle_buy_menu(self, message):
        """Handle buy menu command"""
        menu_text = (
        f"Selamat datang di Toko Aetherion Game!\n"
        f"Silakan pilih kategori pembelian:\n"
        f"1. **{self.prefix}buy weapon <Nama_Senjata>**: Beli Senjata (Lihat daftar: `{self.prefix}shop weapon`)\n"
        f"2. **{self.prefix}buy armor <Nama_Armor>**: Beli Baju Zirah (Lihat daftar: `{self.prefix}shop armor`)\n"
        f"3. **{self.prefix}buy role <Nama_Role>**: Beli Role Discord (Lihat daftar: `{self.prefix}shop role`)\n"

        f"\n"

        f"**Lainnya:**\n"
        f"1. **{self.prefix}sell <Item_Name> <Jumlah>**: Jual item (50% harga beli).\n"
        f"2. **{self.prefix}inventory**: Lihat semua item yang Anda miliki.\n"
        
        f"Contoh: `{self.prefix}buy role Knight`"
        )
        embed = discord.Embed(
            title="🛒 KATEGORI TOKO (SHOP)",
            description=menu_text,
            color=discord.Color.gold()
        )
        await message.channel.send(embed=embed)
    
    async def handle_shop_list(self, message, item_type):
        """Handle shop list command"""
        if item_type == 'role':
            shop_roles = get_shop_roles()
            if not shop_roles:
                await message.channel.send(f"❌ Toko saat ini tidak menjual ROLE.")
                return
                
            max_name_len = max(len(name) for _, name, _ in shop_roles)
            max_price_len = max(len(f"{price:,}") for _, _, price in shop_roles)
            header_name = "ROLE".ljust(max_name_len)
            header_price = "PRICE".rjust(max_price_len + 1)
            header_line = f"{header_name} | {header_price}"
            
            role_list = []
            for _, name, price in shop_roles:
                name_padded = name.ljust(max_name_len)
                price_padded = f"${price:,} ACR".rjust(max_price_len + 1)
                role_list.append(f"{name_padded} | {price_padded}")
                
            final_content = (
                f"═{'═'*len(header_line)}\n"
                f"{header_line}\n"
                f"═{'═'*len(header_line)}\n"
                + "\n".join(role_list)
            )
            
            embed = discord.Embed(
                title=f"🛒 ROLE SHOP",
                description=f"Daftar role yang tersedia. Gunakan `{self.prefix}buy role <Role_Name>`.\n**Pastikan Anda menyebutkan nama role persis seperti yang tertera.**",
                color=discord.Color.blue()
            )
            embed.add_field(name="Role dan Harga (ACR)", 
                             value=f"```fix\n{final_content}\n```", 
                             inline=False)
            await message.channel.send(embed=embed)
            return

        shop_items = get_shop_items(item_type)
        if not shop_items:
            await message.channel.send(f"❌ Toko saat ini tidak menjual {item_type.upper()}.")
            return
        
        max_name_len = max(len(name.replace('_', ' ')) for name, *_, _ in shop_items)
        max_price_len = max(len(f"{price:,}") for _, price, *_, _ in shop_items)

        STAT_COL_WIDTH = 1
        header_name = "ITEM".ljust(max_name_len)
        header_stats_phys = "ATK|DEF|SPD".replace('|', ' ' * (STAT_COL_WIDTH))
        header_stats_magic = "DEX|CRT|MDMG".replace('|', ' ' * (STAT_COL_WIDTH))
        header_stats_tambah = "HP|MP".replace('|', ' ' * (STAT_COL_WIDTH))
        header_price = "PRICE".rjust(max_price_len)
        
        header_line = f"{header_name} | {header_stats_phys} | {header_stats_magic} | {header_stats_tambah} | {header_price}"

        item_list = []
        for item_data in shop_items:
            name_db, price, atk, def_stat, spd, dex, crit, mdmg, hp, mp = item_data
            
            stats_phys_str = f"{atk:03}|{def_stat:03}|{spd:03}"
            stats_magic_str = f"{dex:03}|{crit:03}|{mdmg:03}"
            stats_tambah = f"{hp:03}|{mp:03}"
            
            name_display = name_db.replace('_', ' ')
            name_padded = name_display.ljust(max_name_len)
            price_padded = f"${price:,}".rjust(max_price_len + 1)
            
            item_list.append(f"{name_padded} | {stats_phys_str} | {stats_magic_str} |{stats_tambah}| {price_padded}")
            
        final_content = (
            f"═{'═'*len(header_line)}\n"
            f"{header_line}\n"
            f"═{'═'*len(header_line)}\n"
            + "\n".join(item_list)
        )

        embed = discord.Embed(
            title=f"🛒 {item_type.upper()} SHOP",
            color=discord.Color.blue()
        )
        embed.add_field(name="Item, Stat, dan Harga", 
                         value=f"```fix\n{final_content}\n```", 
                         inline=False)
        await message.channel.send(embed=embed)
    
    async def handle_buy_item(self, message, item_type):
        """Handle buy item command"""
        user_id = message.author.id
        parts = message.content.lower().split()
        if len(parts) < 3:
            await message.channel.send(f"❌ Format: `{self.prefix}buy {item_type} <Item_Name>`")
            return
            
        item_name_raw = " ".join(parts[2:])
        item_name_db = item_name_raw.replace(' ', '_')
        details = get_item_details(item_name_db)
        
        if not details:
            await message.channel.send(f"❌ Item `{item_name_raw}` tidak ditemukan!")
            return
            
        item_id, name_db, item_db_type, price, *_ = details
        if item_db_type != item_type:
            await message.channel.send(f"❌ `{name_db.replace('_', ' ')}` adalah {item_db_type.upper()}, bukan {item_type.upper()}.")
            return

        user_data = get_user_data(user_id)
        exp, level, current_currency, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, max_slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset = user_data
        
        if current_currency < price:
            await message.channel.send(f"❌ Uang tidak cukup! Butuh **💵 {price:,} ACR**.")
            return
            
        inventory_items = get_user_inventory(user_id)
        total_unique_items = len(inventory_items)
        is_new_item = name_db not in [item[0] for item in inventory_items]
        
        if total_unique_items >= max_slots and is_new_item:
            await message.channel.send(f"❌ Inventaris penuh!")
            return
            
        new_currency = current_currency - price
        update_inventory(user_id, name_db, 1)
        update_full_user_data(user_id, exp, level, new_currency, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, max_slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset)
        
        await message.channel.send(f"✅ {message.author.mention} membeli **{name_db.replace('_', ' ')}** seharga **💵 {price:,} ACR**. Sisa: **💵 {new_currency:,} ACR**.")
    
    async def handle_buy_role(self, message):
        """Handle buy role command"""
        user_id = message.author.id
        parts = message.content.lower().split()
        if len(parts) < 3:
            await message.channel.send(f"❌ Format: `{self.prefix}buy role <Role_Name>`")
            return
            
        role_name_raw = " ".join(parts[2:])
        role_name = role_name_raw.title()
        details = get_role_details(role_name)
        
        if not details:
            await message.channel.send(f"❌ Role `{role_name}` tidak ditemukan!")
            return
            
        role_discord_id, role_db_name, price = details
        user_data = get_user_data(user_id)
        exp, level, current_currency, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset = user_data

        if current_currency < price:
            await message.channel.send(f"❌ Uang tidak cukup! Butuh **💵 {price:,} ACR**.")
            return
            
        try:
            guild = message.guild
            if guild is None:
                await message.channel.send("❌ Hanya bisa di server.")
                return
                
            role_to_give = guild.get_role(role_discord_id)
            if role_to_give is None:
                await message.channel.send(f"❌ Role tidak ditemukan di server.")
                return
                
            if role_to_give in message.author.roles:
                await message.channel.send(f"❌ Anda sudah memiliki role **{role_db_name}**!")
                return
                
            new_currency = current_currency - price
            await message.author.add_roles(role_to_give)
            update_full_user_data(user_id, exp, level, new_currency, last_daily_str, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset)
            await message.channel.send(f"🎉 {message.author.mention} membeli role **{role_db_name}** seharga **💵 {price:,} ACR**!")
        except discord.Forbidden:
            await message.channel.send("❌ Bot tidak punya izin memberikan role.")
    
    async def handle_sell_command(self, message):
        """Handle sell command"""
        user_id = message.author.id
        parts = message.content.lower().split()
        if len(parts) < 3:
            await message.channel.send(f"❌ Format: `{self.prefix}sell <Item_Name> <Jumlah>`")
            return
            
        try:
            amount = int(parts[-1])
            if amount <= 0: raise ValueError
            item_name_raw = " ".join(parts[1:-1])
            item_name_db = item_name_raw.replace(' ', '_')
        except ValueError:
            await message.channel.send(f"❌ Jumlah harus angka positif!")
            return
            
        details = get_item_details(item_name_db)
        if not details:
            await message.channel.send(f"❌ Item `{item_name_raw}` tidak valid!")
            return
            
        name_db, price = details[1], details[3]
        sell_price = int(price * 0.5)
        
        inventory = get_user_inventory(user_id)
        item_in_inventory = next((item for item in inventory if item[0].lower() == item_name_db.lower()), None)
        
        if not item_in_inventory or item_in_inventory[1] < amount:
            await message.channel.send(f"❌ Anda tidak punya cukup `{item_name_raw}`.")
            return

        user_data = get_user_data(user_id)
        exp, level, money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset = user_data
        
        total_revenue = amount * sell_price
        new_currency = money + total_revenue
        
        update_inventory(user_id, name_db, -amount)
        update_full_user_data(user_id, exp, level, new_currency, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset)
        
        await message.channel.send(f"✅ {message.author.mention} menjual **{amount}x {name_db.replace('_', ' ')}** seharga **💵 {total_revenue:,} ACR**.")