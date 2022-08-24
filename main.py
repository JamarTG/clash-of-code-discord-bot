import os
import aiosqlite
import codingame
import datetime
import discord

from discord.ext import commands
from keep_alive import keep_alive
from util_functions import try_except as try_exc
from util_functions import to_ordinal
from util_functions import get_obj_pos

# codingame api client and discord client respectively
client = codingame.Client(is_async=True)
bot = commands.Bot(command_prefix="!")

#===================================================================================
#SQL HELPER FUNCTIONS
#===================================================================================

async def mainRunner():
	await client.login(remember_me_cookie="REMEMBER ME COOKIE GOES HERE")

async def create_table():
    async with aiosqlite.connect("./coc_db.db") as connection:
        await connection.execute(
            """CREATE TABLE IF NOT EXISTS clash_of_code  (
      id TEXT PRIMARY KEY,
      coc_name TEXT NOT NULL,
      discord_name TEXT NOT NULL,
			all_time_score INTEGER NOT NULL,
	 		fm_score INTEGER NOT NULL,
			sm_score INTEGER NOT NULL,
			rm_score INTEGER NOT NULL 
	 		)
			"""
        )
        await connection.commit()

async def player_exists(id):
	async with aiosqlite.connect("./coc_db.db") as connection:
		result_with_id = await connection.execute(
			"""SELECT * from clash_of_code WHERE id=?""", (id,)
		)
		player_info = await result_with_id.fetchall()
		player_found = bool(player_info)
	return player_found


async def add_player(
    ctx, id, coc_name, discord_name, all_time_score, fm_score, sm_score, rm_score
):

	await create_table()
	
	if await player_exists(id):
		await ctx.send(f"the account `{coc_name}` is already registered")
		return -1
	
	async with aiosqlite.connect("./coc_db.db") as connection:
		await connection.execute(
			"""INSERT INTO clash_of_code(id,coc_name,discord_name,all_time_score,fm_score,sm_score,rm_score) VALUES (?,?,?,?,?,?,?)""",
			(id, coc_name, discord_name, all_time_score, fm_score, sm_score, rm_score),
		)
		await connection.commit()
	await ctx.send(f"{coc_name} added to database.")
	return 1




#===================================================================================
#DISCORD BOT COMMAND HANDLERS
#===================================================================================
@bot.listen("on_ready")
async def boot_seq():
    print("Bot is listening")
    await mainRunner()


@bot.command()
async def register(ctx, game_handle):
    """Add clash of code account to database"""
    try:
        codingamer = await client.get_codingamer(game_handle)
    except Exception as E:
        await ctx.send(f"{E}")
        return
    if (
        game_handle != codingamer.pseudo
        or game_handle != codingamer.game_handle
        or game_handle != codingamer.id
    ):
        await ctx.send(
            f"@{ctx.message.author} Register with your public handle or type your name correctly"
        )
        return
    success = await add_player(
        ctx,
        codingamer.public_handle,
        codingamer.pseudo,
        ctx.message.author.name,
        0,
        0,
        0,
        0,
    )

    if success == -1:
        return
    p = await try_exc(ctx, codingamer, ["rank", "avatar_url", "pseudo", "level", "bio"])

    rank = p["rank"]
    avatar_url = p["avatar_url"]
    pseudo = p["pseudo"]
    level = p["level"]
    bio = p["bio"]

    try:

        embed = discord.Embed(
            title=f"Clash Of Code",
            timestamp=datetime.datetime.utcnow(),
            color=discord.Color.blue(),
        )
        embed.set_thumbnail(url=avatar_url or ctx.author.avatar_url)
        embed.add_field(name="Username", value=pseudo)
        embed.add_field(name="Rank", value=rank)
        embed.add_field(name="Level", value=level)
        embed.add_field(name="Bio", value=bio)
        await ctx.send(embed=embed)
    except Exception as E:
        await ctx.send(E)


@bot.command()
async def unregister(ctx, handle):
    """Removes clash of code account from database"""
    async with aiosqlite.connect("./coc_db.db") as connection:
        await connection.execute(
            """DELETE FROM clash_of_code
	 WHERE id=? OR coc_name=?""",
            (handle, handle),
        )
        await connection.commit()
    await ctx.send(f"Account `{handle}` unregistered!")


@bot.command()
async def get_lvl(ctx, game_handle):
    """Gets the level of the player on codingamer"""
    codingamer = client.get_codingamer(game_handle)
    await ctx.send(f"`{codingamer.xp}`")


@bot.command()
async def clash(ctx, mode, lang):
    """Starts a clash in given mode or language"""
    if lang.lower() == "all":
        clash = ""
        try:
            clash = await client.request(
                "ClashOfCode", "createPrivateClash", [5024480, [], [mode]]
            )
            await ctx.send(
                f"https://www.codingame.com/clashofcode/clash/{clash['publicHandle']}"
            )
        except:
            await ctx.send(f"something is wrong with your request!")
            return
        embed = discord.Embed(
            title=f"**CLASH CREATED**",
            timestamp=datetime.datetime.utcnow(),
            color=discord.Color.green(),
        )

        embed.add_field(name="", value=f"{ctx.message.author} started a clash")
        embed.add_field(
            name="*JOIN URL*",
            value=f"https://www.codingame.com/clashofcode/clash/{clash['publicHandle']}",
        )
        await ctx.send(embed=embed)
        return
    print(f"pass {[mode]} {[lang]}")
    try:
        clash = await client.request(
            "ClashOfCode", "createPrivateClash", [client.codingamer.id, [lang], [mode]]
        )
        await ctx.send(
            f"https://www.codingame.com/clashofcode/clash/{clash['publicHandle']}"
        )
    except Exception as E:
        await ctx.send(f"{E}something is wrong with your request!")


@bot.command()
async def get_rank(ctx, coc_player, mode):
    """Shows the rank of codingamer against other registered player in the chosen mode"""
    async with aiosqlite.connect("./coc_db.db") as connection:
        results = await connection.execute("""SELECT * FROM clash_of_code""")
        results = await results.fetchall()
    if mode == "at":
        results.sort(key=lambda x: x[3], reverse=True)
    if mode == "fm":
        results.sort(key=lambda x: x[4], reverse=True)
    if mode == "sm":
        results.sort(key=lambda x: x[5], reverse=True)
    if mode == "rm":
        results.sort(key=lambda x: x[6], reverse=True)
    for idx, player in enumerate(results):
        if coc_player == player[1]:
            await ctx.send(f"{to_ordinal(idx+1)}")
    print(results)


@bot.command()  # incomplete
async def t10(ctx, mode):
    """get the top 10 players in the mode specified"""
    async with aiosqlite.connect("./coc_db.db") as connection:
        results = await connection.execute("""SELECT * from clash_of_code""")
        results = await results.fetchall()

        if mode == "at":
            results.sort(key=lambda x: x[-4], reverse=True)
        elif mode == "fm":
            results.sort(key=lambda x: x[-3], reverse=True)
        elif mode == "sm":
            results.sort(key=lambda x: x[-2], reverse=True)
        elif mode == "rm":
            results.sort(key=lambda x: x[-1], reverse=True)
        else:
            await ctx.send("!t10 should be followed by at,fm,sm or rm ")
            return
        if len(results) >= 10:
            num = 10
        else:
            num = len(results)
        final_output = ""
        if mode == "at":
            final_output = "\n".join(
                [
                    """{7}. **{1}** {3}""".format(*results[item] + (item + 1,))
                    for item in range(num)
                ]
            )
        elif mode == "fm":
            final_output = "\n".join(
                [
                    """**{7}. {1}{7}** {4}""".format(*results[item] + (item + 1,))
                    for item in range(num)
                ]
            )
        elif mode == "sm":
            final_output = "\n".join(
                [
                    """{7}. **{1}** {5}""".format(*results[item] + (item + 1,))
                    for item in range(num)
                ]
            )
        elif mode == "rm":
            final_output = "\n".join(
                [
                    """{7}. **{1}** {6}""".format(*results[item] + (item + 1,))
                    for item in range(num)
                ]
            )
        await ctx.send(final_output)


@bot.command()  # function to update player scores
async def rg(ctx, game_handle):
	"""registers a game that have already been player"""
	# get the game
	coc = await client.get_clash_of_code(game_handle[-39:])
	game_mode = coc.mode
	owner = ""
	
	for player in coc.players:
		if player.status == "OWNER":
			owner = player.pseudo
	# sort the players based on their rank
	sortedPlayers = sorted(coc.players, key=get_obj_pos)
	
	# leave if all the players are not in the database
	for each_player in sortedPlayers:
		existence = await player_exists(each_player.public_handle)
		if not (existence):
			await ctx.send(f"{each_player.pseudo} is not registered")
			return
	# we need to look for the players in the database
	
	async with aiosqlite.connect("./coc_db.db") as connection:
	
		for each_player in sortedPlayers:
			points = (len(sortedPlayers) - (each_player.rank + 1)) * 5
			if game_mode == "FASTEST":
	
				await connection.execute(
					"""UPDATE clash_of_code SET fm_score = fm_score+? WHERE id=?""",
					(points, each_player.public_handle),
				)
			elif game_mode == "SHORTEST":
	
				await connection.execute(
					"""UPDATE clash_of_code SET sm_score = sm_score+? WHERE id=?""",
					(points, each_player.public_handle),
				)
			elif game_mode == "REVERSE":
	
				await connection.execute(
					"""UPDATE clash_of_code SET rm_score = rm_score+? WHERE id=?""",
					(points, each_player.public_handle),
				)
			await connection.commit()
	
			await connection.execute(
				"""UPDATE clash_of_code SET all_time_score = all_time_score+? WHERE id=?""",
				(points, each_player.public_handle),
			)
			await connection.commit()
	# displays game results
	output = ""
	for index, each_player in enumerate(sortedPlayers):
		points = (len(sortedPlayers) - (each_player.rank + 1)) * 5
		if index == 0:
			medal = "🥇"
		elif index == 1:
			medal = "🥈"
		else:
			medal = ""
		sign = "+" if points >= 0 else ""
	
		output += (
			"&"
			+ f"**{to_ordinal(each_player.rank)}** *{each_player.pseudo}* Score({each_player.score}%) {medal} {sign}{points}"
		)
	output = f"game mode: **{game_mode}** owner: **{owner}**" + "&" + output
	await ctx.send("\n".join(output.split("&")))


keep_alive()
bot.run(os.environ["token"])
