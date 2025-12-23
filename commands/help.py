"""
Help command handler
"""
import discord
from commands.base import BaseCommand
from config.constants import (
    MAX_DAILY_DICE, MAX_DAILY_HUNT, FIGHT_COOLDOWN, STAT_UPGRADE_COST
)

class HelpCommands(BaseCommand):
    """Handle help command"""
    
    async def handle_help_command(self, message):
        """Handle help command"""
        help_text = f"""
        **{self.prefix}stat** atau **{self.prefix}level** [opsional: @user]
        > Melihat semua statistik (termasuk DEX, CRIT, MDMG, HP, MP).
        
        **{self.prefix}daily**
        > Klaim hadiah uang harian.

        **{self.prefix}roll** atau **{self.prefix}dice**
        > Melempar dadu untuk hadiah uang. Jatah: {MAX_DAILY_DICE}x per hari.
        
        **{self.prefix}hunt**
        > Berburu monster untuk mendapatkan EXP dan Gold. Jatah: {MAX_DAILY_HUNT}x per hari.
        
        **{self.prefix}loophunt**
        > Menjalankan semua sisa hunt Anda sekaligus (maks {MAX_DAILY_HUNT} per hari) dan mengirim ringkasan sekali.

        **{self.prefix}fight <@user>**
        > Bertarung melawan pemain lain. Cooldown: {int(FIGHT_COOLDOWN/60)} menit.
        
        **{self.prefix}leaderboard**
        > Menampilkan 10 pemain teratas.
        
        **{self.prefix}buy** [kategori] [item/role] & **{self.prefix}shop** [weapon/armor/role]
        > Menu dan daftar item/role di toko.
        
        **{self.prefix}inventory**
        > Melihat item yang Anda miliki (Slot: 10 item unik).
        
        **{self.prefix}equip <Item_Name>**
        > Equip item dari inventaris (cth:, `{self.prefix}equip Iron Sword`).

        **{self.prefix}unequip <Item_Name>**
        > Lepas item yang di-equip (cth:, `{self.prefix}unequip Iron Sword`).

        **{self.prefix}upgrade <stat> <amount>**
        > Tingkatkan stat dengan uang ({STAT_UPGRADE_COST} ACR per poin).
        > Stat yang dapat di-upgrade: `atk`, `spd`, `def`, `dex`, `crit`, `mdmg`, `hp`, `mp`.
        
        **{self.prefix}sell <Item_Name> <Jumlah>**
        > Jual item Anda (50% harga beli).

        **{self.prefix}givemoney <@user> <amount>**
        > Kirim sejumlah uang (ACR) kepada pengguna lain

        **{self.prefix}help**
        > Menampilkan daftar perintah ini.
        """
        embed = discord.Embed(
            title="📚 Bantuan Komando Aetherion Game",
            description=help_text,
            color=discord.Color.red()
        )
        await message.channel.send(embed=embed)