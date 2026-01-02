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
        """Handle help command with paginated embeds (Prev / Next / Close buttons)

        The pagination restricts control to the command author and times out after 120s.
        """
        author = message.author

        # Build pages as embeds to avoid very long single embed
        pages = []

        # Page 1: core commands
        e1 = discord.Embed(title="📚 Help Command Aetherion Game — (1/3)", color=discord.Color.red())
        e1.add_field(name=f"{self.prefix}stat / {self.prefix}level [@user]",
                     value="> Melihat semua statistik (DEX, CRIT, MDMG, HP, MP).", inline=False)
        e1.add_field(name=f"{self.prefix}daily", value="> Klaim hadiah uang harian.", inline=False)
        e1.add_field(name=f"{self.prefix}roll / {self.prefix}dice",
                     value=f"> Melempar dadu untuk hadiah uang. Jatah: {MAX_DAILY_DICE}x per hari.", inline=False)
        e1.add_field(name=f"{self.prefix}hunt / {self.prefix}loophunt",
                     value=f"> Berburu monster untuk EXP & Gold. Jatah: {MAX_DAILY_HUNT}x per hari.\n{self.prefix}loophunt = jalankan sisa hunt sekaligus (kirim ringkasan sekali).",
                     inline=False)
        e1.add_field(name=f"{self.prefix}fight <@user>", value=f"> Bertarung melawan pemain lain. Cooldown: {int(FIGHT_COOLDOWN/60)} menit.", inline=False)
        pages.append(e1)

        # Page 2: shop & inventory & equip
        e2 = discord.Embed(title="📚 Help Command Aetherion Game — (2/3)", color=discord.Color.red())
        e2.add_field(name=f"{self.prefix}leaderboard", value="> Menampilkan 10 pemain teratas.", inline=False)
        e2.add_field(name=f"{self.prefix}buy [kategori] [item/role] / {self.prefix}shop [weapon/armor/role]",
                     value="> Menu dan daftar item/role di toko.", inline=False)
        e2.add_field(name=f"{self.prefix}inventory", value="> Melihat item yang Anda miliki (Slot: 10 item unik).", inline=False)
        e2.add_field(name=f"{self.prefix}equip <Item_Name>", value=f"> Equip item dari inventaris (cth: `{self.prefix}equip Iron Sword`).", inline=False)
        e2.add_field(name=f"{self.prefix}unequip <Item_Name>", value=f"> Lepas item yang di-equip (cth: `{self.prefix}unequip Iron Sword`).", inline=False)
        pages.append(e2)

        # Page 3: upgrade / sell / give / help
        e3 = discord.Embed(title="📚 Help Command Aetherion Game — (3/3)", color=discord.Color.red())
        e3.add_field(name=f"{self.prefix}upgrade <stat> <amount>",
                     value=f"> Tingkatkan stat dengan uang ({STAT_UPGRADE_COST} ACR per poin).\nStat yang dapat di-upgrade: `atk`, `spd`, `def`, `dex`, `crit`, `mdmg`, `hp`, `mp`.", inline=False)
        e3.add_field(name=f"{self.prefix}sell <Item_Name> <Jumlah>", value="> Jual item Anda (50% harga beli).", inline=False)
        e3.add_field(name=f"{self.prefix}givemoney <@user> <amount>", value="> Kirim sejumlah uang (ACR) kepada pengguna lain.", inline=False)
        e3.add_field(name=f"{self.prefix}help", value="> Menampilkan daftar perintah ini.", inline=False)
        pages.append(e3)

        # View for buttons
        class HelpView(discord.ui.View):
            def __init__(self, author_id: int, pages: list, timeout: int = 120):
                super().__init__(timeout=timeout)
                self.author_id = author_id
                self.pages = pages
                self.index = 0

            async def update_message(self, interaction: discord.Interaction):
                # update embed and button states
                embed = self.pages[self.index]
                # update title to reflect page number
                embed.title = embed.title.split("—")[0].strip() + f" — ({self.index+1}/{len(self.pages)})"
                for child in self.children:
                    if isinstance(child, discord.ui.Button):
                        if child.custom_id == "prev":
                            child.disabled = (self.index == 0)
                        if child.custom_id == "next":
                            child.disabled = (self.index == len(self.pages)-1)
                # primary: use interaction.response.edit_message (discord.py v2)
                try:
                    await interaction.response.edit_message(embed=embed, view=self)
                    return
                except Exception:
                    # fallback: edit the original message object
                    try:
                        if hasattr(interaction, 'message') and interaction.message:
                            await interaction.message.edit(embed=embed, view=self)
                    except Exception:
                        # last resort: edit stored view message if available
                        try:
                            if hasattr(self, 'message') and self.message:
                                await self.message.edit(embed=embed, view=self)
                        except Exception:
                            pass

            async def interaction_check(self, interaction: discord.Interaction) -> bool:
                # only allow the original author to control the pagination
                if interaction.user.id != self.author_id:
                    # try primary method; fallback to followup if needed
                    try:
                        await interaction.response.send_message("Anda tidak dapat mengontrol help ini.", ephemeral=True)
                    except Exception:
                        try:
                            await interaction.followup.send("Anda tidak dapat mengontrol help ini.", ephemeral=True)
                        except Exception:
                            pass
                    return False
                return True

            @discord.ui.button(label="◀️ Prev", style=discord.ButtonStyle.secondary, custom_id="prev")
            async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.index > 0:
                    self.index -= 1
                    await self.update_message(interaction)

            @discord.ui.button(label="Next ▶️", style=discord.ButtonStyle.secondary, custom_id="next")
            async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if self.index < len(self.pages)-1:
                    self.index += 1
                    await self.update_message(interaction)


            async def on_timeout(self):
                # disable all buttons when view times out
                for child in self.children:
                    if isinstance(child, discord.ui.Button):
                        child.disabled = True
                # try to edit the original message to update disabled buttons (best-effort)
                try:
                    if hasattr(self, 'message') and self.message:
                        await self.message.edit(view=self)
                except Exception:
                    # ignore failures; timeout cleanup is best-effort
                    pass

        view = HelpView(author.id, pages)
        # Prepare initial embed copy to avoid shared state issues
        initial = pages[0]
        # set initial button disabled states
        for child in view.children:
            if isinstance(child, discord.ui.Button):
                if child.custom_id == "prev":
                    child.disabled = True
                if child.custom_id == "next":
                    child.disabled = (len(pages) == 1)

        sent = await message.channel.send(embed=initial, view=view)
        # store sent message on the view so on_timeout can edit it
        try:
            view.message = sent
        except Exception:
            pass
