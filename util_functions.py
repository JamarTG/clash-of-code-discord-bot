import inflect
# ctx would be passed from the command 

engine = inflect.engine()

def to_ordinal(number):
	return engine.ordinal(number)

def get_obj_pos(player):
	return player.rank



async def try_except(ctx,codingamer, attributes):

	try:
	 avatar_url = codingamer.avatar_url+'&format=codingamercard_avatar'
	except:
	 avatar_url = ctx.message.author.avatar_url
	try:
	 pseudo = f"`{codingamer.pseudo}`"
	except:
	 pseudo = '`unknown`'            
	try:
	 rank = f"`{await codingamer.get_clash_of_code_rank()}`"
	except:
	 rank = '`unranked`'
	try:
	 level = f'`{codingamer.level}`'
	except:
	 level = 'unknown'
	try:
	 bio = f'`{codingamer.biography}`'
	except:
	 bio = "`no bio`"
	 
	thingies = {
	 "avatar_url" : avatar_url,
	 "bio" : bio,
	 "level" : level,
	 "pseudo" : pseudo,
	 "rank" : rank
	}

	requested_props  = {}
	for attr in attributes:
		requested_props[attr] = thingies[attr]
		
	return requested_props

def numbering(list):
	numbers = ['1️⃣','2️⃣','3️⃣','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟']
	
	