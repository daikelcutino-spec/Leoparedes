from highrise import BaseBot, User, Position, AnchorPosition
from highrise.models import SessionMetadata, GetUserOutfitRequest, Error
import asyncio
import json

OWNER_ID = "662aae9b602b4a897557ec18"
ADMIN_ID = "669da7b73867bac51391c757"

# 224 emotes gratuitos
emotes = {
    1: {"id": "idle-loop-sitfloor", "name": "Sentado", "duration": 5, "is_free": True},
    2: {"id": "emote-bow", "name": "Reverencia", "duration": 3, "is_free": True},
    3: {"id": "emote-curtsy", "name": "Cortesía", "duration": 3, "is_free": True},
    4: {"id": "emote-snowangel", "name": "Ángel de Nieve", "duration": 5, "is_free": True},
    5: {"id": "emote-snowball", "name": "Bola de Nieve", "duration": 3, "is_free": True},
    6: {"id": "emote-confused", "name": "Confundido", "duration": 3, "is_free": True},
    7: {"id": "emote-wave", "name": "Saludar", "duration": 2, "is_free": True},
    8: {"id": "emote-headnod-yes", "name": "Asentir Sí", "duration": 2, "is_free": True},
    9: {"id": "emote-headnod-no", "name": "Negar No", "duration": 2, "is_free": True},
    10: {"id": "emote-clap", "name": "Aplaudir", "duration": 2, "is_free": True},
    11: {"id": "idle-dance-casual", "name": "Baile Casual", "duration": 5, "is_free": True},
    12: {"id": "emote-laughing", "name": "Riendo", "duration": 3, "is_free": True},
    13: {"id": "emote-hello", "name": "Hola", "duration": 2, "is_free": True},
    14: {"id": "emote-happy", "name": "Feliz", "duration": 3, "is_free": True},
    15: {"id": "emote-thumbsup", "name": "Pulgar Arriba", "duration": 2, "is_free": True},
    16: {"id": "dance-tiktok2", "name": "TikTok Dance 2", "duration": 5, "is_free": True},
    17: {"id": "emote-hot", "name": "Caliente", "duration": 3, "is_free": True},
    18: {"id": "emote-model", "name": "Modelo", "duration": 4, "is_free": True},
    19: {"id": "dance-blackpink", "name": "BlackPink", "duration": 6, "is_free": True},
    20: {"id": "emote-superpose", "name": "Super Pose", "duration": 3, "is_free": True},
    21: {"id": "emote-cute", "name": "Tierno", "duration": 3, "is_free": True},
    22: {"id": "dance-tiktok10", "name": "TikTok 10", "duration": 5, "is_free": True},
    23: {"id": "emote-pose7", "name": "Pose 7", "duration": 3, "is_free": True},
    24: {"id": "emote-pose8", "name": "Pose 8", "duration": 3, "is_free": True},
    25: {"id": "emote-pose1", "name": "Pose 1", "duration": 3, "is_free": True},
    26: {"id": "emote-pose3", "name": "Pose 3", "duration": 3, "is_free": True},
    27: {"id": "emote-pose5", "name": "Pose 5", "duration": 3, "is_free": True},
    28: {"id": "emote-cutey", "name": "Dulce", "duration": 3, "is_free": True},
    29: {"id": "dance-tiktok9", "name": "TikTok 9", "duration": 5, "is_free": True},
    30: {"id": "emote-kiss", "name": "Beso", "duration": 2, "is_free": True},
    31: {"id": "dance-tiktok8", "name": "TikTok 8", "duration": 5, "is_free": True},
    32: {"id": "emote-shy2", "name": "Tímido 2", "duration": 3, "is_free": True},
    33: {"id": "idle-enthusiastic", "name": "Entusiasta", "duration": 4, "is_free": True},
    34: {"id": "idle-wild", "name": "Salvaje", "duration": 4, "is_free": True},
    35: {"id": "idle-Loop-aerobics", "name": "Aeróbicos", "duration": 5, "is_free": True},
    36: {"id": "idle-nervous", "name": "Nervioso", "duration": 4, "is_free": True},
    37: {"id": "idle-toilet", "name": "Baño", "duration": 5, "is_free": True},
    38: {"id": "emote-lust", "name": "Deseo", "duration": 3, "is_free": True},
    39: {"id": "emote-greedy", "name": "Codicioso", "duration": 3, "is_free": True},
    40: {"id": "idle-floorsleeping2", "name": "Durmiendo", "duration": 6, "is_free": True},
    41: {"id": "idle-sad", "name": "Triste", "duration": 4, "is_free": True},
    42: {"id": "emote-celebrate", "name": "Celebrar", "duration": 3, "is_free": True},
    43: {"id": "emote-gagging", "name": "Náuseas", "duration": 3, "is_free": True},
    44: {"id": "emote-pose9", "name": "Pose 9", "duration": 3, "is_free": True},
    45: {"id": "emote-kpop_idle", "name": "KPop Idle", "duration": 4, "is_free": True},
    46: {"id": "dance-tiktok4", "name": "TikTok 4", "duration": 5, "is_free": True},
    47: {"id": "emote-shy", "name": "Tímido", "duration": 3, "is_free": True},
    48: {"id": "emote-tired", "name": "Cansado", "duration": 3, "is_free": True},
    49: {"id": "emote-pose10", "name": "Pose 10", "duration": 3, "is_free": True},
    50: {"id": "emote-boxer", "name": "Boxeador", "duration": 3, "is_free": True},
    51: {"id": "idle-sword", "name": "Espada", "duration": 4, "is_free": True},
    52: {"id": "idle-lookup", "name": "Mirar Arriba", "duration": 4, "is_free": True},
    53: {"id": "emote-punkguitar", "name": "Guitarra Punk", "duration": 4, "is_free": True},
    54: {"id": "idle-guitar", "name": "Guitarra", "duration": 5, "is_free": True},
    55: {"id": "idle-guitar-skill", "name": "Guitarra Pro", "duration": 5, "is_free": True},
    56: {"id": "dance-punk", "name": "Punk Dance", "duration": 5, "is_free": True},
    57: {"id": "idle-uwu", "name": "UwU", "duration": 3, "is_free": True},
    58: {"id": "idle-loop-happy", "name": "Feliz Loop", "duration": 5, "is_free": True},
    59: {"id": "emote-astronaut", "name": "Astronauta", "duration": 4, "is_free": True},
    60: {"id": "emote-teleporting", "name": "Teletransporte", "duration": 3, "is_free": True},
    61: {"id": "dance-wrong", "name": "Baile Equivocado", "duration": 5, "is_free": True},
    62: {"id": "emote-swordfight", "name": "Pelea Espadas", "duration": 4, "is_free": True},
    63: {"id": "emote-energyball", "name": "Bola Energía", "duration": 3, "is_free": True},
    64: {"id": "emote-snake", "name": "Serpiente", "duration": 4, "is_free": True},
    65: {"id": "emote-frog", "name": "Rana", "duration": 3, "is_free": True},
    66: {"id": "emote-superrun", "name": "Super Correr", "duration": 4, "is_free": True},
    67: {"id": "emote-superpunch", "name": "Super Golpe", "duration": 3, "is_free": True},
    68: {"id": "emote-sweating", "name": "Sudando", "duration": 3, "is_free": True},
    69: {"id": "dance-tiktok11", "name": "TikTok 11", "duration": 5, "is_free": True},
    70: {"id": "emote-timejump", "name": "Salto Tiempo", "duration": 4, "is_free": True},
    71: {"id": "emote-gift", "name": "Regalo", "duration": 3, "is_free": True},
    72: {"id": "idle-loop-tapdance", "name": "Tap Dance", "duration": 5, "is_free": True},
    73: {"id": "dance-tiktok13", "name": "TikTok 13", "duration": 5, "is_free": True},
    74: {"id": "dance-tiktok12", "name": "TikTok 12", "duration": 5, "is_free": True},
    75: {"id": "emote-viral", "name": "Viral", "duration": 4, "is_free": True},
    76: {"id": "idle-loop-zombie", "name": "Zombie", "duration": 5, "is_free": True},
    77: {"id": "emote-creepycute", "name": "Escalofriante", "duration": 3, "is_free": True},
    78: {"id": "emote-zombierun", "name": "Correr Zombie", "duration": 4, "is_free": True},
    79: {"id": "dance-russian", "name": "Ruso", "duration": 5, "is_free": True},
    80: {"id": "emote-icecream", "name": "Helado", "duration": 3, "is_free": True},
    81: {"id": "emote-relaxed", "name": "Relajado", "duration": 3, "is_free": True},
    82: {"id": "idle-wild2", "name": "Salvaje 2", "duration": 4, "is_free": True},
    83: {"id": "emote-telekinesis", "name": "Telequinesis", "duration": 4, "is_free": True},
    84: {"id": "emote-float", "name": "Flotar", "duration": 4, "is_free": True},
    85: {"id": "emote-spy", "name": "Espía", "duration": 3, "is_free": True},
    86: {"id": "dance-icecream", "name": "Baile Helado", "duration": 5, "is_free": True},
    87: {"id": "emote-iceskating", "name": "Patinar Hielo", "duration": 4, "is_free": True},
    88: {"id": "emote-penguin", "name": "Pingüino", "duration": 3, "is_free": True},
    89: {"id": "emote-sing", "name": "Cantar", "duration": 3, "is_free": True},
    90: {"id": "emote-sleigh", "name": "Trineo", "duration": 4, "is_free": True},
    91: {"id": "emote-hyped", "name": "Emocionado", "duration": 3, "is_free": True},
    92: {"id": "emote-christmas", "name": "Navidad", "duration": 3, "is_free": True},
    93: {"id": "emote-launch", "name": "Lanzar", "duration": 3, "is_free": True},
    94: {"id": "emote-bomb", "name": "Bomba", "duration": 3, "is_free": True},
    95: {"id": "emote-fishing", "name": "Pescar", "duration": 4, "is_free": True},
    96: {"id": "idle-singing", "name": "Cantando", "duration": 5, "is_free": True},
    97: {"id": "dance-aerobics", "name": "Aeróbicos", "duration": 5, "is_free": True},
    98: {"id": "emote-shopping", "name": "Compras", "duration": 3, "is_free": True},
    99: {"id": "emote-fashionista", "name": "Fashionista", "duration": 3, "is_free": True},
    100: {"id": "emote-proposing", "name": "Proponer", "duration": 3, "is_free": True},
    101: {"id": "emote-heartfingers", "name": "Corazón Dedos", "duration": 2, "is_free": True},
    102: {"id": "emote-bunnyhop", "name": "Salto Conejo", "duration": 3, "is_free": True},
    103: {"id": "emote-pushups", "name": "Flexiones", "duration": 4, "is_free": True},
    104: {"id": "emote-maniac", "name": "Maníaco", "duration": 3, "is_free": True},
    105: {"id": "emote-peace", "name": "Paz", "duration": 2, "is_free": True},
    106: {"id": "emote-jinglebell", "name": "Campana", "duration": 3, "is_free": True},
    107: {"id": "dance-tiktok3", "name": "TikTok 3", "duration": 5, "is_free": True},
    108: {"id": "dance-pennywise", "name": "Pennywise", "duration": 5, "is_free": True},
    109: {"id": "dance-tiktok7", "name": "TikTok 7", "duration": 5, "is_free": True},
    110: {"id": "emote-monkey", "name": "Mono", "duration": 3, "is_free": True},
    111: {"id": "dance-weird", "name": "Baile Raro", "duration": 5, "is_free": True},
    112: {"id": "emote-headblowup", "name": "Cabeza Explotar", "duration": 3, "is_free": True},
    113: {"id": "emote-theatrical", "name": "Teatral", "duration": 3, "is_free": True},
    114: {"id": "emote-snowball-fight", "name": "Guerra Nieve", "duration": 4, "is_free": True},
    115: {"id": "emote-pose6", "name": "Pose 6", "duration": 3, "is_free": True},
    116: {"id": "emote-charging", "name": "Cargar", "duration": 3, "is_free": True},
    117: {"id": "emote-think", "name": "Pensar", "duration": 3, "is_free": True},
    118: {"id": "emote-ropepull", "name": "Jalar Cuerda", "duration": 4, "is_free": True},
    119: {"id": "emote-sit1", "name": "Sentarse 1", "duration": 5, "is_free": True},
    120: {"id": "emote-sit2", "name": "Sentarse 2", "duration": 5, "is_free": True},
    121: {"id": "emote-sit3", "name": "Sentarse 3", "duration": 5, "is_free": True},
    122: {"id": "emote-sit4", "name": "Sentarse 4", "duration": 5, "is_free": True},
    123: {"id": "emote-sit5", "name": "Sentarse 5", "duration": 5, "is_free": True},
    124: {"id": "emote-sit6", "name": "Sentarse 6", "duration": 5, "is_free": True},
    125: {"id": "emote-sit7", "name": "Sentarse 7", "duration": 5, "is_free": True},
    126: {"id": "emote-sit8", "name": "Sentarse 8", "duration": 5, "is_free": True},
    127: {"id": "idle-loop-aerobics2", "name": "Aeróbicos 2", "duration": 5, "is_free": True},
    128: {"id": "idle-loop-aerobics3", "name": "Aeróbicos 3", "duration": 5, "is_free": True},
    129: {"id": "idle-loop-aerobics4", "name": "Aeróbicos 4", "duration": 5, "is_free": True},
    130: {"id": "emote-angry", "name": "Enojado", "duration": 3, "is_free": True},
    131: {"id": "emote-pose4", "name": "Pose 4", "duration": 3, "is_free": True},
    132: {"id": "emote-sitting", "name": "Sentado", "duration": 5, "is_free": True},
    133: {"id": "idle-sad2", "name": "Triste 2", "duration": 4, "is_free": True},
    134: {"id": "emote-crying", "name": "Llorando", "duration": 3, "is_free": True},
    135: {"id": "idle-loop-tired", "name": "Cansado Loop", "duration": 5, "is_free": True},
    136: {"id": "emote-sad", "name": "Triste", "duration": 3, "is_free": True},
    137: {"id": "emote-jump", "name": "Saltar", "duration": 2, "is_free": True},
    138: {"id": "idle-loop-sad", "name": "Triste Loop", "duration": 5, "is_free": True},
    139: {"id": "emote-embarrassed", "name": "Avergonzado", "duration": 3, "is_free": True},
    140: {"id": "emote-gravity", "name": "Gravedad", "duration": 4, "is_free": True},
    141: {"id": "emote-fashionweek", "name": "Semana Moda", "duration": 4, "is_free": True},
    142: {"id": "emote-faint", "name": "Desmayar", "duration": 3, "is_free": True},
    143: {"id": "emote-snowboard", "name": "Snowboard", "duration": 4, "is_free": True},
    144: {"id": "emote-skiing", "name": "Esquiar", "duration": 4, "is_free": True},
    145: {"id": "emote-holiday", "name": "Vacaciones", "duration": 3, "is_free": True},
    146: {"id": "emote-smooch", "name": "Besar", "duration": 3, "is_free": True},
    147: {"id": "dance-tiktok1", "name": "TikTok 1", "duration": 5, "is_free": True},
    148: {"id": "dance-tiktok5", "name": "TikTok 5", "duration": 5, "is_free": True},
    149: {"id": "dance-tiktok6", "name": "TikTok 6", "duration": 5, "is_free": True},
    150: {"id": "emote-airguitar", "name": "Guitarra Aire", "duration": 3, "is_free": True},
    151: {"id": "emote-splits", "name": "Split", "duration": 4, "is_free": True},
    152: {"id": "emote-backflip", "name": "Backflip", "duration": 3, "is_free": True},
    153: {"id": "emote-sayso", "name": "Say So", "duration": 4, "is_free": True},
    154: {"id": "dance-shoppingcart", "name": "Carrito Compras", "duration": 5, "is_free": True},
    155: {"id": "dance-weird2", "name": "Baile Raro 2", "duration": 5, "is_free": True},
    156: {"id": "emote-fistpump", "name": "Puño Arriba", "duration": 2, "is_free": True},
    157: {"id": "emote-shovel", "name": "Pala", "duration": 3, "is_free": True},
    158: {"id": "emote-sick", "name": "Enfermo", "duration": 3, "is_free": True},
    159: {"id": "emote-laughing2", "name": "Riendo 2", "duration": 3, "is_free": True},
    160: {"id": "emote-dizzy", "name": "Mareado", "duration": 3, "is_free": True},
    161: {"id": "emote-superrun2", "name": "Super Correr 2", "duration": 4, "is_free": True},
    162: {"id": "idle-loop-breakdancing", "name": "Breakdance", "duration": 5, "is_free": True},
    163: {"id": "emote-kawaii", "name": "Kawaii", "duration": 3, "is_free": True},
    164: {"id": "emote-unicorn", "name": "Unicornio", "duration": 4, "is_free": True},
    165: {"id": "emote-hero-entance", "name": "Entrada Héroe", "duration": 3, "is_free": True},
    166: {"id": "emote-hero-idle", "name": "Héroe Idle", "duration": 4, "is_free": True},
    167: {"id": "idle-loop-sitfloor2", "name": "Sentado Piso 2", "duration": 5, "is_free": True},
    168: {"id": "emote-snake2", "name": "Serpiente 2", "duration": 4, "is_free": True},
    169: {"id": "emote-froggy", "name": "Ranita", "duration": 3, "is_free": True},
    170: {"id": "emote-superpose2", "name": "Super Pose 2", "duration": 3, "is_free": True},
    171: {"id": "emote-cute2", "name": "Tierno 2", "duration": 3, "is_free": True},
    172: {"id": "emote-model2", "name": "Modelo 2", "duration": 4, "is_free": True},
    173: {"id": "emote-pose11", "name": "Pose 11", "duration": 3, "is_free": True},
    174: {"id": "emote-pose12", "name": "Pose 12", "duration": 3, "is_free": True},
    175: {"id": "emote-kiss2", "name": "Beso 2", "duration": 2, "is_free": True},
    176: {"id": "emote-shy3", "name": "Tímido 3", "duration": 3, "is_free": True},
    177: {"id": "emote-lust2", "name": "Deseo 2", "duration": 3, "is_free": True},
    178: {"id": "emote-greedy2", "name": "Codicioso 2", "duration": 3, "is_free": True},
    179: {"id": "emote-gagging2", "name": "Náuseas 2", "duration": 3, "is_free": True},
    180: {"id": "emote-tired2", "name": "Cansado 2", "duration": 3, "is_free": True},
    181: {"id": "emote-boxer2", "name": "Boxeador 2", "duration": 3, "is_free": True},
    182: {"id": "emote-astronaut2", "name": "Astronauta 2", "duration": 4, "is_free": True},
    183: {"id": "emote-teleporting2", "name": "Teletransporte 2", "duration": 3, "is_free": True},
    184: {"id": "emote-swordfight2", "name": "Pelea Espadas 2", "duration": 4, "is_free": True},
    185: {"id": "emote-energyball2", "name": "Bola Energía 2", "duration": 3, "is_free": True},
    186: {"id": "emote-sweating2", "name": "Sudando 2", "duration": 3, "is_free": True},
    187: {"id": "emote-timejump2", "name": "Salto Tiempo 2", "duration": 4, "is_free": True},
    188: {"id": "emote-gift2", "name": "Regalo 2", "duration": 3, "is_free": True},
    189: {"id": "emote-zombierun2", "name": "Correr Zombie 2", "duration": 4, "is_free": True},
    190: {"id": "emote-icecream2", "name": "Helado 2", "duration": 3, "is_free": True},
    191: {"id": "emote-relaxed2", "name": "Relajado 2", "duration": 3, "is_free": True},
    192: {"id": "emote-telekinesis2", "name": "Telequinesis 2", "duration": 4, "is_free": True},
    193: {"id": "emote-float2", "name": "Flotar 2", "duration": 4, "is_free": True},
    194: {"id": "emote-spy2", "name": "Espía 2", "duration": 3, "is_free": True},
    195: {"id": "emote-iceskating2", "name": "Patinar Hielo 2", "duration": 4, "is_free": True},
    196: {"id": "emote-penguin2", "name": "Pingüino 2", "duration": 3, "is_free": True},
    197: {"id": "emote-sing2", "name": "Cantar 2", "duration": 3, "is_free": True},
    198: {"id": "emote-sleigh2", "name": "Trineo 2", "duration": 4, "is_free": True},
    199: {"id": "emote-hyped2", "name": "Emocionado 2", "duration": 3, "is_free": True},
    200: {"id": "emote-christmas2", "name": "Navidad 2", "duration": 3, "is_free": True},
    201: {"id": "emote-launch2", "name": "Lanzar 2", "duration": 3, "is_free": True},
    202: {"id": "emote-bomb2", "name": "Bomba 2", "duration": 3, "is_free": True},
    203: {"id": "emote-fishing2", "name": "Pescar 2", "duration": 4, "is_free": True},
    204: {"id": "emote-shopping2", "name": "Compras 2", "duration": 3, "is_free": True},
    205: {"id": "emote-fashionista2", "name": "Fashionista 2", "duration": 3, "is_free": True},
    206: {"id": "emote-proposing2", "name": "Proponer 2", "duration": 3, "is_free": True},
    207: {"id": "emote-heartfingers2", "name": "Corazón Dedos 2", "duration": 2, "is_free": True},
    208: {"id": "emote-bunnyhop2", "name": "Salto Conejo 2", "duration": 3, "is_free": True},
    209: {"id": "emote-pushups2", "name": "Flexiones 2", "duration": 4, "is_free": True},
    210: {"id": "emote-maniac2", "name": "Maníaco 2", "duration": 3, "is_free": True},
    211: {"id": "emote-peace2", "name": "Paz 2", "duration": 2, "is_free": True},
    212: {"id": "emote-jinglebell2", "name": "Campana 2", "duration": 3, "is_free": True},
    213: {"id": "emote-monkey2", "name": "Mono 2", "duration": 3, "is_free": True},
    214: {"id": "emote-headblowup2", "name": "Cabeza Explotar 2", "duration": 3, "is_free": True},
    215: {"id": "emote-theatrical2", "name": "Teatral 2", "duration": 3, "is_free": True},
    216: {"id": "emote-snowball-fight2", "name": "Guerra Nieve 2", "duration": 4, "is_free": True},
    217: {"id": "emote-charging2", "name": "Cargar 2", "duration": 3, "is_free": True},
    218: {"id": "emote-think2", "name": "Pensar 2", "duration": 3, "is_free": True},
    219: {"id": "emote-ropepull2", "name": "Jalar Cuerda 2", "duration": 4, "is_free": True},
    220: {"id": "emote-angry2", "name": "Enojado 2", "duration": 3, "is_free": True},
    221: {"id": "emote-gravity2", "name": "Gravedad 2", "duration": 4, "is_free": True},
    222: {"id": "emote-fashionweek2", "name": "Semana Moda 2", "duration": 4, "is_free": True},
    223: {"id": "emote-faint2", "name": "Desmayar 2", "duration": 3, "is_free": True},
    224: {"id": "emote-snowboard2", "name": "Snowboard 2", "duration": 4, "is_free": True}
}

class CantineroBot(BaseBot):
    def __init__(self):
        super().__init__()
        self.bot_id = None
        self.emote_task = None
        self.mensaje_task = None
        self.punto_inicio = {"x": 9.5, "y": 0.0, "z": 9.5}
        self.load_config()
        
    def load_config(self):
        """Carga la configuración del bot"""
        try:
            with open("cantinero_config.json", "r") as f:
                config = json.load(f)
                self.punto_inicio = config.get("punto_inicio", self.punto_inicio)
                print(f"✅ Configuración cargada desde archivo:")
                print(f"   📍 X={self.punto_inicio['x']}, Y={self.punto_inicio['y']}, Z={self.punto_inicio['z']}")
        except FileNotFoundError:
            print("⚠️ No se encontró cantinero_config.json, creando con valores por defecto")
            self.save_config()
        except Exception as e:
            print(f"❌ Error leyendo configuración: {e}")
            self.save_config()
    
    def save_config(self):
        """Guarda la configuración del bot"""
        try:
            config_data = {"punto_inicio": self.punto_inicio}
            with open("cantinero_config.json", "w") as f:
                json.dump(config_data, f, indent=2)
            print(f"✅ Configuración guardada en cantinero_config.json:")
            print(f"   📍 X={self.punto_inicio['x']}, Y={self.punto_inicio['y']}, Z={self.punto_inicio['z']}")
            # Verificar que se guardó correctamente
            with open("cantinero_config.json", "r") as f:
                verificacion = json.load(f)
                if verificacion == config_data:
                    print("   ✓ Verificación exitosa: archivo guardado correctamente")
                else:
                    print("   ⚠️ Advertencia: el archivo guardado no coincide")
        except Exception as e:
            print(f"❌ Error guardando configuración: {e}")
    
    def is_admin_or_owner(self, user_id: str) -> bool:
        """Verifica si el usuario es admin o propietario"""
        return user_id == OWNER_ID or user_id == ADMIN_ID
        
    async def on_start(self, session_metadata: SessionMetadata) -> None:
        """Inicialización del bot cantinero"""
        print("🍷 Bot Cantinero iniciando...")
        self.bot_id = session_metadata.user_id
        
        # Recargar configuración para asegurar que tenemos la última posición guardada
        self.load_config()
        
        await asyncio.sleep(2)
        
        try:
            position = Position(
                float(self.punto_inicio["x"]), 
                float(self.punto_inicio["y"]), 
                float(self.punto_inicio["z"])
            )
            await self.highrise.teleport(self.bot_id, position)
            print(f"📍 Bot teletransportado a punto de inicio: X={self.punto_inicio['x']}, Y={self.punto_inicio['y']}, Z={self.punto_inicio['z']}")
        except Exception as e:
            print(f"❌ Error al teletransportar: {e}")
            print(f"   Punto de inicio configurado: {self.punto_inicio}")
        
        print("🎭 Iniciando ciclo automático de 224 emotes...")
        self.emote_task = asyncio.create_task(self.ciclo_automatico_emotes())
        
        print("📢 Iniciando mensajes automáticos...")
        self.mensaje_task = asyncio.create_task(self.mensajes_automaticos())
        
        print("🍷 ¡Bot Cantinero listo para servir!")
    
    async def ciclo_automatico_emotes(self):
        """Ejecuta un ciclo automático de 224 emotes gratuitos"""
        # Filtrar solo emotes gratuitos
        free_emotes = {num: data for num, data in emotes.items() if data.get("is_free", True)}
        
        print(f"🎭 INICIANDO CICLO AUTOMÁTICO DE {len(free_emotes)} EMOTES GRATUITOS...")
        
        ciclo = 0
        while True:
            try:
                ciclo += 1
                print(f"🔄 Ciclo #{ciclo} - Iniciando secuencia de {len(free_emotes)} emotes")
                
                for emote_num, emote_data in free_emotes.items():
                    try:
                        await self.highrise.send_emote(emote_data["id"], self.bot_id)
                        duration = emote_data.get("duration", 5)
                        
                        # Log cada 20 emotes
                        if emote_num % 20 == 0:
                            print(f"🎭 Emote #{emote_num}/{len(free_emotes)}: {emote_data['name']}")
                        
                        await asyncio.sleep(max(0.1, duration - 0.3))
                    except Exception as e:
                        print(f"⚠️ Error en emote {emote_data['name']}: {e}")
                        await asyncio.sleep(1.0)
                        continue
                
                print(f"✅ Ciclo #{ciclo} completado - Reiniciando...")
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ ERROR en ciclo automático: {e}")
                await asyncio.sleep(5)
    
    async def mensajes_automaticos(self):
        """Envía 1 mensaje automático cada 3 minutos, alternando entre los 3 mensajes"""
        mensajes = [
            "‼️¿Sugerencias o incomodidades? Contacta a un miembro superior de la sala: envía un mensaje a @Alber_JG_69 o a @baby__lax. ¡Estamos para ayudarte!‼️",
            "¡Consigue tu VIP Permanente!💎 Para ser un miembro eterno de 🕷️ NOCTURNO 🕷️, Mándale 100 de oro al bot: @NOCTURNO_BOT. ¡Gracias por apoyar la oscuridad!",
            "Acércate a la barra.🥃 Estoy para servirle. ¿Qué deseas hoy?🍻"
        ]
        indice = 0
        
        while True:
            try:
                await asyncio.sleep(180)
                
                mensaje_actual = mensajes[indice]
                
                response = await self.highrise.get_room_users()
                if not isinstance(response, Error):
                    for user, _ in response.content:
                        if user.id != self.bot_id:
                            try:
                                await self.highrise.send_whisper(user.id, mensaje_actual)
                            except Exception as e:
                                print(f"Error enviando mensaje a {user.username}: {e}")
                
                print(f"📢 Mensaje automático #{indice + 1} enviado: {mensaje_actual[:50]}...")
                indice = (indice + 1) % len(mensajes)
                
            except Exception as e:
                print(f"Error en mensajes automáticos: {e}")
                await asyncio.sleep(60)
    
    async def on_user_join(self, user: User, position: Position | AnchorPosition) -> None:
        """Mensaje de bienvenida personalizado"""
        try:
            await self.highrise.send_whisper(user.id, "🕷️ Bienvenido a NOCTURNO 🕷️")
            await self.highrise.send_whisper(user.id, "El velo se ha abierto solo para ti...")
            await asyncio.sleep(0.5)
            await self.highrise.send_whisper(user.id, "🍷 Soy tu cantinero. Usa !menu para la carta")
            await self.highrise.send_whisper(user.id, "💡 Comandos: !cantinero !receta !especiales !eventos")
            print(f"👤 {user.username} entró a la sala")
        except Exception as e:
            print(f"Error al enviar bienvenida: {e}")
    
    async def procesar_comando(self, user: User, message: str) -> None:
        """Procesa comandos del usuario (desde chat o whisper)"""
        msg = message.lower().strip()
        user_id = user.id
        
        if msg == "!menu" or msg == "!carta":
            await self.mostrar_menu(user)
            return
        
        if msg.startswith("!servir"):
            await self.servir_bebida(user, message)
            return
        
        if msg == "!cantinero" or msg == "!bar":
            await self.highrise.send_whisper(user_id, "🍷 A tus órdenes. Usa !menu para ver la carta")
            await self.highrise.send_whisper(user_id, "💡 Comandos: !receta, !recomendacion, !especial, !eventos")
            return
        
        if msg == "!receta" or msg.startswith("!receta "):
            await self.mostrar_receta(user, msg)
            return
        
        if msg == "!recomendacion" or msg == "!recomendar":
            await self.dar_recomendacion(user)
            return
        
        if msg == "!especial" or msg == "!especiales":
            await self.mostrar_especiales(user)
            return
        
        if msg == "!eventos" or msg == "!evento":
            await self.mostrar_eventos(user)
            return
        
        if msg == "!historia" or msg == "!story":
            await self.contar_historia(user)
            return
        
        if msg.startswith("!pedido "):
            await self.tomar_pedido(user, message)
            return
        
        if msg == "!happy" or msg == "!happyhour":
            await self.mostrar_happy_hour(user)
            return
        
        if msg == "!mixologia" or msg == "!mix":
            await self.mostrar_mixologia(user)
            return
        
        if msg.startswith("!heart"):
            await self.dar_corazones(user, message)
            return
        
        if msg == "!copy":
            if not self.is_admin_or_owner(user_id):
                await self.highrise.send_whisper(user_id, "❌ Solo admin y propietario pueden usar este comando")
                return
            
            try:
                outfit_request = await self.highrise.get_user_outfit(user_id)
                if outfit_request and not isinstance(outfit_request, Error):
                    await self.highrise.set_outfit(outfit_request.outfit)
                    await self.highrise.send_whisper(user_id, f"✅ Outfit copiado exitosamente de @{user.username}!")
                    print(f"👔 Outfit copiado de {user.username}")
            except Exception as e:
                await self.highrise.send_whisper(user_id, f"❌ Error al copiar outfit: {e}")
                print(f"Error copiando outfit: {e}")
            return
        
        if msg == "!inicio":
            if not self.is_admin_or_owner(user_id):
                await self.highrise.send_whisper(user_id, "❌ Solo admin y propietario pueden usar este comando")
                return
            
            try:
                response = await self.highrise.get_room_users()
                bot_position = None
                
                if not isinstance(response, Error):
                    for u, pos in response.content:
                        if u.id == self.bot_id:
                            bot_position = pos
                            break
                
                if bot_position and isinstance(bot_position, Position):
                    # Guardar coordenadas actuales
                    self.punto_inicio = {
                        "x": float(bot_position.x),
                        "y": float(bot_position.y),
                        "z": float(bot_position.z)
                    }
                    
                    # Guardar en archivo
                    self.save_config()
                    
                    # Esperar un momento y recargar para verificar
                    await asyncio.sleep(0.5)
                    self.load_config()
                    
                    # Confirmar al usuario
                    await self.highrise.send_whisper(user_id, "✅ PUNTO DE INICIO GUARDADO")
                    await self.highrise.send_whisper(user_id, f"📍 X={self.punto_inicio['x']:.2f}")
                    await self.highrise.send_whisper(user_id, f"📍 Y={self.punto_inicio['y']:.2f}")
                    await self.highrise.send_whisper(user_id, f"📍 Z={self.punto_inicio['z']:.2f}")
                    await self.highrise.send_whisper(user_id, "")
                    await self.highrise.send_whisper(user_id, "🔄 Reinicia el bot para verificar")
                    await self.highrise.send_whisper(user_id, "💡 Usa el workflow 'Bot Cantinero'")
                    
                    print(f"📍 PUNTO DE INICIO ACTUALIZADO:")
                    print(f"   X={self.punto_inicio['x']}, Y={self.punto_inicio['y']}, Z={self.punto_inicio['z']}")
                    
                elif bot_position and isinstance(bot_position, AnchorPosition):
                    await self.highrise.send_whisper(user_id, "⚠️ Posición tipo AnchorPosition detectada")
                    if bot_position.anchor:
                        await self.highrise.send_whisper(user_id, f"📍 Anchor: {bot_position.anchor}")
                    if bot_position.offset:
                        self.punto_inicio = {
                            "x": float(bot_position.offset.x),
                            "y": float(bot_position.offset.y),
                            "z": float(bot_position.offset.z)
                        }
                        self.save_config()
                        await asyncio.sleep(0.5)
                        self.load_config()
                        await self.highrise.send_whisper(user_id, "✅ Punto guardado usando offset")
                        await self.highrise.send_whisper(user_id, f"📍 X={self.punto_inicio['x']:.2f}, Y={self.punto_inicio['y']:.2f}, Z={self.punto_inicio['z']:.2f}")
                else:
                    await self.highrise.send_whisper(user_id, "❌ No se pudo obtener la posición del bot")
                    await self.highrise.send_whisper(user_id, f"Tipo de posición: {type(bot_position).__name__}")
                    print(f"❌ Bot position: {bot_position}, type: {type(bot_position)}")
            except Exception as e:
                await self.highrise.send_whisper(user_id, f"❌ Error: {str(e)[:100]}")
                print(f"❌ Error en !inicio: {e}")
                import traceback
                traceback.print_exc()
            return
        
        await self.detectar_bebida(user, msg)
    
    async def on_chat(self, user: User, message: str) -> None:
        """Maneja mensajes del chat público"""
        await self.procesar_comando(user, message)
    
    async def on_whisper(self, user: User, message: str) -> None:
        """Maneja mensajes whisper (privados)"""
        await self.procesar_comando(user, message)
    
    async def detectar_bebida(self, user: User, msg: str):
        """Detecta si el mensaje contiene el nombre de una bebida y la sirve automáticamente"""
        bebidas_respuestas = {
            "cerveza": "🍺 Aquí tienes una cerveza bien fría, @{user}! Salud! 🍻",
            "vino": "🍷 Un excelente vino tinto para ti, @{user}. ¡Buen provecho!",
            "whisky": "🥃 Whisky en las rocas para @{user}. Con clase! 🎩",
            "coctel": "🍹 Un cóctel especial de la casa para @{user}! 🌟",
            "cóctel": "🍹 Un cóctel especial de la casa para @{user}! 🌟",
            "champagne": "🍾 Champagne! Algo que celebrar, @{user}? 🎉",
            "cafe": "☕ Café recién hecho para @{user}. ¡Energía pura! ⚡",
            "café": "☕ Café recién hecho para @{user}. ¡Energía pura! ⚡",
            "refresco": "🥤 Refresco bien frío para @{user}! 🧊",
            "sombra": "🖤 Sombra Líquida... la especialidad NOCTURNO para @{user}. Oscuro y misterioso... 🕷️",
            "sangre": "🦇 Sangre de Murciélago para @{user}... dulce con un toque salvaje 🌙",
            "eclipse": "🌑 Eclipse Negro... la bebida más oscura para @{user}. Solo para los más valientes 🕸️"
        }
        
        for bebida, respuesta in bebidas_respuestas.items():
            if bebida in msg:
                respuesta_final = respuesta.replace("{user}", user.username)
                await self.highrise.send_whisper(user.id, respuesta_final)
                return
    
    async def mostrar_menu(self, user: User):
        """Muestra el menú de bebidas"""
        menu = [
            "🍷 === CARTA DEL CANTINERO === 🍷",
            "",
            "🍺 Cerveza",
            "🍷 Vino",
            "🥃 Whisky",
            "🍹 Cóctel",
            "🍾 Champagne",
            "☕ Café",
            "🥤 Refresco",
            "",
            "🕷️ Bebidas especiales NOCTURNO:",
            "🖤 Sombra Líquida",
            "🦇 Sangre de Murciélago",
            "🌑 Eclipse Negro",
            "",
            "💡 Solo di el nombre de la bebida o usa !servir [bebida]"
        ]
        
        for linea in menu:
            await self.highrise.send_whisper(user.id, linea)
    
    async def servir_bebida(self, user: User, mensaje: str):
        """Sirve la bebida solicitada"""
        bebida = mensaje[7:].strip().lower()
        
        bebidas = {
            "cerveza": "🍺 Aquí tienes una cerveza bien fría, @{user}! Salud! 🍻",
            "vino": "🍷 Un excelente vino tinto para ti, @{user}. ¡Buen provecho!",
            "whisky": "🥃 Whisky en las rocas para @{user}. Con clase! 🎩",
            "coctel": "🍹 Un cóctel especial de la casa para @{user}! 🌟",
            "champagne": "🍾 Champagne! Algo que celebrar, @{user}? 🎉",
            "cafe": "☕ Café recién hecho para @{user}. ¡Energía pura! ⚡",
            "refresco": "🥤 Refresco bien frío para @{user}! 🧊",
            "sombra": "🖤 Sombra Líquida... la especialidad NOCTURNO para @{user}. Oscuro y misterioso... 🕷️",
            "sangre": "🦇 Sangre de Murciélago para @{user}... dulce con un toque salvaje 🌙",
            "eclipse": "🌑 Eclipse Negro... la bebida más oscura para @{user}. Solo para los más valientes 🕸️"
        }
        
        if bebida in bebidas:
            respuesta = bebidas[bebida].replace("{user}", user.username)
            await self.highrise.send_whisper(user.id, respuesta)
        elif bebida == "":
            await self.highrise.send_whisper(user.id, "¿Qué bebida deseas? Usa !menu para ver la carta")
        else:
            await self.highrise.send_whisper(user.id, f"No tengo '{bebida}' en la carta. Usa !menu para ver opciones")
    
    async def mostrar_receta(self, user: User, mensaje: str):
        """Muestra recetas de cócteles"""
        recetas = {
            "sombra": {
                "nombre": "🖤 Sombra Líquida",
                "ingredientes": "• Vodka negro\n• Carbón activado\n• Jarabe de regaliz\n• Hielo oscuro",
                "preparacion": "Mezclar todo en coctelera con hielo. Servir en copa oscura."
            },
            "sangre": {
                "nombre": "🦇 Sangre de Murciélago",
                "ingredientes": "• Ron oscuro\n• Granadina\n• Jugo de granada\n• Esencia de vainilla",
                "preparacion": "Mezclar suavemente. Servir con hielo y decorar con cereza negra."
            },
            "eclipse": {
                "nombre": "🌑 Eclipse Negro",
                "ingredientes": "• Tequila reposado\n• Licor de café\n• Chocolate amargo\n• Crema de coco negra",
                "preparacion": "Batir con hielo. Decorar con polvo de cacao oscuro."
            }
        }
        
        if "sombra" in mensaje:
            receta = recetas["sombra"]
        elif "sangre" in mensaje:
            receta = recetas["sangre"]
        elif "eclipse" in mensaje:
            receta = recetas["eclipse"]
        else:
            await self.highrise.send_whisper(user.id, "📖 RECETAS DISPONIBLES:")
            await self.highrise.send_whisper(user.id, "!receta sombra\n!receta sangre\n!receta eclipse")
            return
        
        await self.highrise.send_whisper(user.id, f"📖 {receta['nombre']}")
        await self.highrise.send_whisper(user.id, f"🥃 Ingredientes:\n{receta['ingredientes']}")
        await self.highrise.send_whisper(user.id, f"👨‍🍳 Preparación:\n{receta['preparacion']}")
    
    async def dar_recomendacion(self, user: User):
        """Da recomendaciones personalizadas"""
        import random
        recomendaciones = [
            "🍷 Te recomiendo un vino tinto añejo... perfecto para la noche oscura",
            "🥃 Un whisky escocés de 18 años te vendría bien... sofisticado y fuerte",
            "🍹 Prueba nuestro cóctel Sombra Líquida... una experiencia única NOCTURNO",
            "🦇 La Sangre de Murciélago es ideal para ti... dulce pero salvaje",
            "🌑 El Eclipse Negro te espera... solo para los valientes",
            "☕ Un café expreso doble te dará la energía de la medianoche",
            "🍾 Champagne francés... porque esta noche merece celebrarse"
        ]
        recomendacion = random.choice(recomendaciones)
        await self.highrise.send_whisper(user.id, f"💡 RECOMENDACIÓN DEL CANTINERO:\n{recomendacion}")
    
    async def mostrar_especiales(self, user: User):
        """Muestra bebidas especiales del día"""
        await self.highrise.send_whisper(user.id, "⭐ ESPECIALES DE HOY:")
        await self.highrise.send_whisper(user.id, "🌙 Noche de Luna Nueva:")
        await self.highrise.send_whisper(user.id, "• Eclipse Negro (2x1)")
        await self.highrise.send_whisper(user.id, "• Sombra Líquida Premium")
        await self.highrise.send_whisper(user.id, "• Shot de Medianoche GRATIS")
        await self.highrise.send_whisper(user.id, "\n💫 Promoción válida hasta las 3 AM")
    
    async def mostrar_eventos(self, user: User):
        """Muestra eventos del bar"""
        await self.highrise.send_whisper(user.id, "🎉 EVENTOS NOCTURNO:")
        await self.highrise.send_whisper(user.id, "🕐 22:00 - Happy Hour Oscuro")
        await self.highrise.send_whisper(user.id, "🕑 23:00 - Concurso de Cócteles")
        await self.highrise.send_whisper(user.id, "🕒 00:00 - DJ Set + Bebidas Especiales")
        await self.highrise.send_whisper(user.id, "🕓 01:00 - Trivia del Bar (premios)")
        await self.highrise.send_whisper(user.id, "🕔 02:00 - Cierre con Shot de Despedida")
    
    async def contar_historia(self, user: User):
        """Cuenta la historia del bar"""
        historia = [
            "🕷️ LA LEYENDA DE NOCTURNO 🕷️",
            "",
            "Hace décadas, este bar era una cripta abandonada...",
            "Un misterioso cantinero la transformó en el refugio",
            "más exclusivo de la noche.",
            "",
            "Se dice que cada bebida tiene un toque de magia oscura,",
            "y que quien prueba el Eclipse Negro nunca olvida la noche.",
            "",
            "🌑 Bienvenido a la leyenda... bienvenido a NOCTURNO."
        ]
        for linea in historia:
            await self.highrise.send_whisper(user.id, linea)
            await asyncio.sleep(0.5)
    
    async def tomar_pedido(self, user: User, mensaje: str):
        """Toma pedidos personalizados"""
        pedido = mensaje[8:].strip()
        await self.highrise.send_whisper(user.id, f"📝 Pedido anotado: {pedido}")
        await self.highrise.send_whisper(user.id, "👨‍🍳 Preparando tu bebida especial...")
        await asyncio.sleep(2)
        await self.highrise.send_whisper(user.id, f"🍸 ¡Tu {pedido} está listo! Disfrútalo.")
    
    async def mostrar_happy_hour(self, user: User):
        """Muestra promociones de happy hour"""
        await self.highrise.send_whisper(user.id, "🎊 HAPPY HOUR NOCTURNO:")
        await self.highrise.send_whisper(user.id, "⏰ 22:00 - 23:00")
        await self.highrise.send_whisper(user.id, "🍺 Todas las cervezas: 50% OFF")
        await self.highrise.send_whisper(user.id, "🍷 Vinos premium: 2x1")
        await self.highrise.send_whisper(user.id, "🍹 Cócteles NOCTURNO: Precio especial")
        await self.highrise.send_whisper(user.id, "🎁 Shot de cortesía al primer pedido")
    
    async def mostrar_mixologia(self, user: User):
        """Muestra tips de mixología"""
        tips = [
            "🍸 TIP DE MIXOLOGÍA:",
            "• Siempre usa hielo de calidad",
            "• Los cócteles oscuros llevan más sabor",
            "• La temperatura perfecta es clave",
            "• Mezcla con pasión, no con prisa",
            "• El equilibrio de sabores es un arte",
            "",
            "💡 ¿Quieres aprender más? Pregunta al cantinero"
        ]
        for tip in tips:
            await self.highrise.send_whisper(user.id, tip)
    
    async def dar_corazones(self, user: User, message: str):
        """Da corazones a un usuario (solo admin/owner)"""
        if not self.is_admin_or_owner(user.id):
            await self.highrise.send_whisper(user.id, "❌ Solo admin y propietario pueden dar corazones")
            return
        
        parts = message.split()
        if len(parts) < 3:
            await self.highrise.send_whisper(user.id, "❌ Uso: !heart @usuario cantidad")
            return
        
        target_username = parts[1].replace("@", "")
        try:
            cantidad = int(parts[2])
        except ValueError:
            await self.highrise.send_whisper(user.id, "❌ La cantidad debe ser un número")
            return
        
        if cantidad <= 0:
            await self.highrise.send_whisper(user.id, "❌ La cantidad debe ser mayor a 0")
            return
        
        if cantidad > 100:
            await self.highrise.send_whisper(user.id, "❌ Máximo 100 corazones por comando")
            return
        
        # Buscar al usuario en la sala
        response = await self.highrise.get_room_users()
        if isinstance(response, Error):
            await self.highrise.send_whisper(user.id, "❌ Error obteniendo usuarios")
            return
        
        target_user = None
        for u, _ in response.content:
            if u.username == target_username:
                target_user = u
                break
        
        if not target_user:
            await self.highrise.send_whisper(user.id, f"❌ Usuario {target_username} no encontrado")
            return
        
        # Enviar corazones
        for _ in range(min(cantidad, 30)):
            try:
                await self.highrise.react("heart", target_user.id)
                await asyncio.sleep(0.05)
            except Exception as e:
                await self.highrise.send_whisper(user.id, f"⚠️ Error enviando corazones: {e}")
                break
        
        await self.highrise.send_whisper(user.id, f"💖 Enviaste {cantidad} corazones a @{target_username}")
        await self.highrise.send_whisper(target_user.id, f"💖 {user.username} te envió {cantidad} corazones 🍷")

if __name__ == "__main__":
    import sys
    
    print("🍷 Iniciando Bot Cantinero NOCTURNO...")
    print("🎭 Ciclo automático de 224 emotes activado")
    print("📢 Mensajes automáticos cada 3 minutos")
    print("🕷️ Listo para servir en la oscuridad...")
    print("=" * 50)
    
    bot = CantineroBot()
    print("🔧 Bot Cantinero inicializado. Esperando conexión...")
