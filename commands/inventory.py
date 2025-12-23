"""
Inventory-related commands (inventory, equip, unequip)
"""
import discord
from commands.base import BaseCommand
from database.queries.user_queries import get_user_data, update_full_user_data
from database.queries.inventory_queries import get_user_inventory
from database.queries.shop_queries import get_item_details
from utils.helpers import format_item_name

class InventoryCommands(BaseCommand):
    """Handle inventory-related commands"""
    
    async def handle_inventory_command(self, message):
        """Handle inventory command"""
        user_id = message.author.id
        user_data = get_user_data(user_id)
        max_slots = user_data[12]
        equipped_weapon = user_data[13]
        equipped_armor = user_data[14]
        
        inventory_items = get_user_inventory(user_id)
        total_unique_items = len(inventory_items)
        
        embed = discord.Embed(
            title=f"🎒 Inventory {message.author.display_name}",
            description=f"Slot Terpakai: **{total_unique_items} / {max_slots}** (Item Unik)\nEquipped: Weapon - **{format_item_name(equipped_weapon)}**, Armor - **{format_item_name(equipped_armor)}**",
            color=discord.Color.dark_green()
        )
        
        if inventory_items:
            item_list = []
            for name_db, quantity in inventory_items:
                name_display = format_item_name(name_db)
                equipped_status = ""
                if name_db == equipped_weapon:
                    equipped_status = " (Equipped - Weapon)"
                elif name_db == equipped_armor:
                    equipped_status = " (Equipped - Armor)"
                item_list.append(f"**{name_display}** x{quantity}{equipped_status}")
            embed.add_field(name="Item Anda", value="\n".join(item_list), inline=False)
        else:
            embed.add_field(name="Item Anda", value="Inventaris kosong.", inline=False)
        
        await message.channel.send(embed=embed)
    
    async def handle_equip_command(self, message):
        """Handle equip command"""
        user_id = message.author.id
        parts = message.content.lower().split()
        if len(parts) < 2:
            await message.channel.send(f"❌ Format: `{self.prefix}equip <Item_Name>` (e.g., `{self.prefix}equip Iron Sword`)")
            return
        
        item_name_raw = " ".join(parts[1:]) 
        item_name_db = item_name_raw.replace(' ', '_')
        inventory = get_user_inventory(user_id)
        item_in_inventory = any(item[0].lower() == item_name_db.lower() and item[1] > 0 for item in inventory)

        if not item_in_inventory:
            await message.channel.send(f"❌ Anda tidak memiliki `{item_name_raw}` di inventaris! Pastikan Anda sudah membelinya.")
            return
        
        details = get_item_details(item_name_db)
        if not details:
            await message.channel.send(f"❌ Item `{item_name_raw}` tidak valid atau tidak ada di database!")
            return

        _, name_db, item_type, _, bonus_atk, bonus_def, bonus_spd, bonus_dex, bonus_crit, bonus_mdmg, bonus_hp, bonus_mp = details
        user_data = get_user_data(user_id)
        exp, level, money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset = user_data

        old_item_name = None
        if item_type == 'weapon':
            old_item_name = equipped_weapon
            equipped_weapon = name_db 
            slot_display = "Senjata (Weapon)"
        elif item_type == 'armor':
            old_item_name = equipped_armor
            equipped_armor = name_db
            slot_display = "Baju Zirah (Armor)"
        else:
            await message.channel.send(f"❌ Item `{item_name_raw}` tidak dapat di-equip (tipe: {item_type})!")
            return

        update_full_user_data(user_id, exp, level, money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset)

        item_name_display = format_item_name(name_db)
        description_text = f"Item **{item_name_display}** berhasil dipasang di slot **{slot_display}**."
        if old_item_name:
            description_text += f"\n(Item lama **{format_item_name(old_item_name)}** telah dilepas ke inventaris.)"
        
        embed = discord.Embed(
            title="⚔️ ITEM TERPASANG (EQUIPPED) 🛡️",
            description=description_text,
            color=discord.Color.dark_teal()
        )

        stats_list = []
        if bonus_atk != 0: stats_list.append(f"⚔️ ATK: +{bonus_atk}" if bonus_atk > 0 else f"⚔️ ATK: {bonus_atk}")
        if bonus_def != 0: stats_list.append(f"🛡️ DEF: +{bonus_def}" if bonus_def > 0 else f"🛡️ DEF: {bonus_def}")
        if bonus_spd != 0: stats_list.append(f"👟 SPD: +{bonus_spd}" if bonus_spd > 0 else f"👟 SPD: {bonus_spd}")
        if bonus_dex != 0: stats_list.append(f"🎯 DEX: +{bonus_dex}" if bonus_dex > 0 else f"🎯 DEX: {bonus_dex}")
        if bonus_crit != 0: stats_list.append(f"💥 CRIT: +{bonus_crit}" if bonus_crit > 0 else f"💥 CRIT: {bonus_crit}")
        if bonus_mdmg != 0: stats_list.append(f"⚛️ MDMG: +{bonus_mdmg}" if bonus_mdmg > 0 else f"⚛️ MDMG: {bonus_mdmg}")
        if bonus_hp != 0: stats_list.append(f"❤️ HP: +{bonus_hp}" if bonus_hp > 0 else f"❤️ HP: {bonus_hp}")
        if bonus_mp != 0: stats_list.append(f"🌀 MP: +{bonus_mp}" if bonus_mp > 0 else f"🌀 MP: {bonus_mp}")

        embed.add_field(
            name=f"✨ {item_name_display.upper()} ({item_type.capitalize()})",
            value='\n'.join(stats_list) if stats_list else "Tidak ada bonus statistik.",
            inline=True
        )

        if old_item_name:
            embed.add_field(
                name="Item Sebelumnya Dilepas",
                value=f"{format_item_name(old_item_name)}",
                inline=True
            )

        await message.channel.send(embed=embed)
    
    async def handle_unequip_command(self, message):
        """Handle unequip command"""
        user_id = message.author.id
        parts = message.content.lower().split()
        
        if len(parts) < 2:
            await message.channel.send(f"❌ Format: `{self.prefix}unequip <Item_Name>` (e.g., `{self.prefix}unequip Iron Sword`)")
            return

        item_name_raw = " ".join(parts[1:])
        item_name_db = item_name_raw.replace(' ', '_')
        user_data = get_user_data(user_id)
        exp, level, money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset = user_data

        item_unequipped = None
        slot_affected = None

        if equipped_weapon and equipped_weapon.lower() == item_name_db.lower():
            item_unequipped = equipped_weapon
            equipped_weapon = None
            slot_affected = "Weapon"
        elif equipped_armor and equipped_armor.lower() == item_name_db.lower():
            item_unequipped = equipped_armor
            equipped_armor = None
            slot_affected = "Armor"

        if item_unequipped:
            item_name_display = format_item_name(item_unequipped)

            update_full_user_data(user_id, exp, level, money, last_daily, atk, spd, def_stat, dex, crit, mdmg, hp, mp, slots, equipped_weapon, equipped_armor, dice_rolls, last_dice_reset, last_fight_time, hunt_count, hunt_reset)

            embed = discord.Embed(
                description=f"{message.author.mention} berhasil melepas item **{item_name_display}**.",
                color=discord.Color.gold()
            )
            embed.add_field(
                name="Slot Terpengaruh",
                value=slot_affected,
                inline=True
            )
            embed.add_field(
                name="Status Terbaru",
                value="Item sekarang berada di inventaris Anda.",
                inline=True
            )
            
            await message.channel.send(embed=embed)
        else:
            await message.channel.send(f"❌ Item `{item_name_raw}` tidak terpasang di slot `weapon` maupun `armor`.")