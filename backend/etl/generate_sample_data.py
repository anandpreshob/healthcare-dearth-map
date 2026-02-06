"""Generate realistic sample data for 5 states: CA, TX, NY, MS, MT.

Creates ~200 counties, ~1000 zipcodes, ~5000 providers with deliberate
dearth patterns: urban areas well-served, rural MS/MT in shortage.
"""

import random
import psycopg2
from psycopg2.extras import execute_values
from .taxonomy_mapping import SPECIALTY_TAXONOMIES

# ---------------------------------------------------------------------------
# Real county data: (fips, name, state_abbr, state_name, state_fips,
#                     population, centroid_lat, centroid_lon, land_area_sqmi,
#                     is_urban)
# ---------------------------------------------------------------------------

COUNTIES: list[tuple] = [
    # -- California (06) - 40 counties --
    ("06037", "Los Angeles", "CA", "California", "06", 10014009, 34.0522, -118.2437, 4058, True),
    ("06073", "San Diego", "CA", "California", "06", 3338330, 32.7157, -117.1611, 4204, True),
    ("06059", "Orange", "CA", "California", "06", 3186989, 33.7175, -117.8311, 791, True),
    ("06065", "Riverside", "CA", "California", "06", 2470546, 33.9533, -117.3962, 7206, True),
    ("06071", "San Bernardino", "CA", "California", "06", 2180085, 34.8414, -116.1776, 20057, True),
    ("06085", "Santa Clara", "CA", "California", "06", 1927852, 37.3541, -121.9552, 1290, True),
    ("06001", "Alameda", "CA", "California", "06", 1671329, 37.6017, -121.7195, 739, True),
    ("06075", "San Francisco", "CA", "California", "06", 873965, 37.7749, -122.4194, 47, True),
    ("06067", "Sacramento", "CA", "California", "06", 1552058, 38.5816, -121.4944, 966, True),
    ("06013", "Contra Costa", "CA", "California", "06", 1153526, 37.9735, -121.9018, 716, True),
    ("06029", "Kern", "CA", "California", "06", 900202, 35.3733, -118.7920, 8132, False),
    ("06019", "Fresno", "CA", "California", "06", 999101, 36.7378, -119.7871, 5958, False),
    ("06077", "San Joaquin", "CA", "California", "06", 762148, 37.9349, -121.2713, 1391, False),
    ("06107", "Tulare", "CA", "California", "06", 466195, 36.2274, -118.8018, 4824, False),
    ("06039", "Madera", "CA", "California", "06", 157327, 37.2181, -119.7631, 2138, False),
    ("06047", "Merced", "CA", "California", "06", 277680, 37.1948, -120.7178, 1929, False),
    ("06099", "Stanislaus", "CA", "California", "06", 550660, 37.5588, -120.9969, 1495, False),
    ("06083", "Santa Barbara", "CA", "California", "06", 446499, 34.4208, -119.6982, 2738, False),
    ("06111", "Ventura", "CA", "California", "06", 843843, 34.3705, -119.1391, 1843, True),
    ("06081", "San Mateo", "CA", "California", "06", 766573, 37.5630, -122.3255, 449, True),
    ("06041", "Marin", "CA", "California", "06", 258826, 38.0834, -122.7633, 520, False),
    ("06097", "Sonoma", "CA", "California", "06", 494336, 38.5110, -122.8378, 1576, False),
    ("06055", "Napa", "CA", "California", "06", 137744, 38.5025, -122.2654, 754, False),
    ("06045", "Mendocino", "CA", "California", "06", 86749, 39.4346, -123.3317, 3509, False),
    ("06023", "Humboldt", "CA", "California", "06", 135558, 40.7450, -123.8695, 3573, False),
    ("06089", "Shasta", "CA", "California", "06", 180080, 40.7637, -122.0409, 3785, False),
    ("06007", "Butte", "CA", "California", "06", 219186, 39.6667, -121.6006, 1640, False),
    ("06061", "Placer", "CA", "California", "06", 398329, 39.0916, -120.7180, 1407, False),
    ("06017", "El Dorado", "CA", "California", "06", 192843, 38.7786, -120.5247, 1708, False),
    ("06009", "Calaveras", "CA", "California", "06", 45905, 38.1964, -120.5560, 1020, False),
    ("06005", "Amador", "CA", "California", "06", 39752, 38.4464, -120.6511, 593, False),
    ("06003", "Alpine", "CA", "California", "06", 1129, 38.5966, -119.8207, 739, False),
    ("06027", "Inyo", "CA", "California", "06", 18039, 36.5115, -117.4109, 10181, False),
    ("06051", "Mono", "CA", "California", "06", 14444, 37.9390, -118.8865, 3044, False),
    ("06049", "Modoc", "CA", "California", "06", 8841, 41.5890, -120.7258, 3918, False),
    ("06093", "Siskiyou", "CA", "California", "06", 43539, 41.5925, -122.5417, 6278, False),
    ("06015", "Del Norte", "CA", "California", "06", 27812, 41.7432, -123.8964, 1006, False),
    ("06105", "Trinity", "CA", "California", "06", 12285, 40.6531, -123.0978, 3179, False),
    ("06033", "Lake", "CA", "California", "06", 64386, 39.0986, -122.7531, 1258, False),
    ("06011", "Colusa", "CA", "California", "06", 21547, 39.1777, -122.2375, 1151, False),

    # -- Texas (48) - 45 counties --
    ("48201", "Harris", "TX", "Texas", "48", 4713325, 29.7604, -95.3698, 1729, True),
    ("48113", "Dallas", "TX", "Texas", "48", 2613539, 32.7767, -96.7970, 871, True),
    ("48029", "Bexar", "TX", "Texas", "48", 2003554, 29.4241, -98.4936, 1240, True),
    ("48439", "Tarrant", "TX", "Texas", "48", 2084931, 32.7573, -97.3309, 864, True),
    ("48453", "Travis", "TX", "Texas", "48", 1290188, 30.2672, -97.7431, 990, True),
    ("48085", "Collin", "TX", "Texas", "48", 1064465, 33.1859, -96.5716, 848, True),
    ("48121", "Denton", "TX", "Texas", "48", 906422, 33.2148, -97.1331, 879, True),
    ("48215", "Hidalgo", "TX", "Texas", "48", 868707, 26.3963, -98.1811, 1571, False),
    ("48141", "El Paso", "TX", "Texas", "48", 839238, 31.7619, -106.4850, 1013, True),
    ("48157", "Fort Bend", "TX", "Texas", "48", 822779, 29.5272, -95.7718, 861, True),
    ("48339", "Montgomery", "TX", "Texas", "48", 607391, 30.3001, -95.4994, 1042, True),
    ("48491", "Williamson", "TX", "Texas", "48", 590551, 30.6483, -97.6014, 1124, True),
    ("48355", "Nueces", "TX", "Texas", "48", 361350, 27.8006, -97.3964, 836, False),
    ("48061", "Cameron", "TX", "Texas", "48", 423163, 26.1670, -97.5730, 906, False),
    ("48303", "Lubbock", "TX", "Texas", "48", 310569, 33.5779, -101.8552, 900, False),
    ("48367", "Parker", "TX", "Texas", "48", 148222, 32.7775, -97.8053, 904, False),
    ("48251", "Johnson", "TX", "Texas", "48", 175706, 32.3779, -97.3730, 729, False),
    ("48027", "Bell", "TX", "Texas", "48", 362924, 31.0382, -97.4781, 1059, False),
    ("48309", "McLennan", "TX", "Texas", "48", 256623, 31.5493, -97.1467, 1042, False),
    ("48041", "Brazos", "TX", "Texas", "48", 229211, 30.6614, -96.3004, 586, False),
    ("48245", "Jefferson", "TX", "Texas", "48", 256526, 29.8629, -94.1577, 904, False),
    ("48183", "Gregg", "TX", "Texas", "48", 123494, 32.4904, -94.8166, 274, False),
    ("48423", "Smith", "TX", "Texas", "48", 232751, 32.3752, -95.2735, 921, False),
    ("48375", "Potter", "TX", "Texas", "48", 118525, 35.1815, -101.7271, 909, False),
    ("48381", "Randall", "TX", "Texas", "48", 137713, 34.9625, -101.8974, 914, False),
    ("48227", "Howard", "TX", "Texas", "48", 36664, 32.3066, -101.4383, 900, False),
    ("48135", "Ector", "TX", "Texas", "48", 166223, 31.8657, -102.5410, 898, False),
    ("48329", "Midland", "TX", "Texas", "48", 164194, 31.9973, -102.0779, 900, False),
    ("48389", "Reeves", "TX", "Texas", "48", 15166, 31.3248, -103.6930, 2636, False),
    ("48043", "Brewster", "TX", "Texas", "48", 9232, 29.8106, -103.2534, 6193, False),
    ("48377", "Presidio", "TX", "Texas", "48", 7818, 29.9997, -104.2409, 3856, False),
    ("48243", "Jeff Davis", "TX", "Texas", "48", 2274, 30.7156, -104.1432, 2265, False),
    ("48229", "Hudspeth", "TX", "Texas", "48", 4571, 31.4566, -105.3869, 4571, False),
    ("48109", "Culberson", "TX", "Texas", "48", 2398, 31.4472, -104.5174, 3813, False),
    ("48301", "Loving", "TX", "Texas", "48", 64, 31.8489, -103.9852, 669, False),
    ("48269", "King", "TX", "Texas", "48", 272, 33.6164, -100.2558, 913, False),
    ("48261", "Kenedy", "TX", "Texas", "48", 404, 26.9308, -97.6319, 1457, False),
    ("48263", "Kent", "TX", "Texas", "48", 762, 33.1821, -100.7685, 902, False),
    ("48033", "Borden", "TX", "Texas", "48", 631, 32.7436, -101.4320, 899, False),
    ("48311", "McMullen", "TX", "Texas", "48", 707, 28.3525, -98.2374, 1143, False),
    ("48443", "Terrell", "TX", "Texas", "48", 862, 30.2250, -102.0759, 2358, False),
    ("48393", "Roberts", "TX", "Texas", "48", 885, 35.8386, -100.8155, 924, False),
    ("48155", "Foard", "TX", "Texas", "48", 1155, 33.9748, -99.7772, 708, False),
    ("48137", "Edwards", "TX", "Texas", "48", 2055, 29.9825, -100.3048, 2120, False),
    ("48413", "Schleicher", "TX", "Texas", "48", 2793, 30.8925, -100.5393, 1311, False),

    # -- New York (36) - 40 counties --
    ("36047", "Kings", "NY", "New York", "36", 2736074, 40.6782, -73.9442, 70, True),
    ("36081", "Queens", "NY", "New York", "36", 2405464, 40.7282, -73.7949, 109, True),
    ("36061", "New York", "NY", "New York", "36", 1694251, 40.7831, -73.9712, 23, True),
    ("36005", "Bronx", "NY", "New York", "36", 1472654, 40.8448, -73.8648, 42, True),
    ("36085", "Richmond", "NY", "New York", "36", 495747, 40.5795, -74.1502, 58, True),
    ("36103", "Suffolk", "NY", "New York", "36", 1525920, 40.9434, -72.6832, 912, True),
    ("36059", "Nassau", "NY", "New York", "36", 1395774, 40.7289, -73.5894, 287, True),
    ("36119", "Westchester", "NY", "New York", "36", 1004457, 41.1220, -73.7949, 431, True),
    ("36029", "Erie", "NY", "New York", "36", 954236, 42.7523, -78.7805, 1043, True),
    ("36055", "Monroe", "NY", "New York", "36", 759443, 43.2300, -77.6556, 659, True),
    ("36067", "Onondaga", "NY", "New York", "36", 476516, 43.0481, -76.1474, 778, False),
    ("36001", "Albany", "NY", "New York", "36", 314848, 42.6526, -73.7562, 523, False),
    ("36071", "Orange", "NY", "New York", "36", 401310, 41.4018, -74.3118, 812, False),
    ("36087", "Rockland", "NY", "New York", "36", 325789, 41.1489, -74.0260, 174, True),
    ("36091", "Saratoga", "NY", "New York", "36", 235509, 43.0901, -73.8641, 812, False),
    ("36027", "Dutchess", "NY", "New York", "36", 295911, 41.7650, -73.7430, 796, False),
    ("36111", "Ulster", "NY", "New York", "36", 181851, 41.8868, -74.2588, 1126, False),
    ("36007", "Broome", "NY", "New York", "36", 198683, 42.1600, -75.8196, 707, False),
    ("36109", "Tompkins", "NY", "New York", "36", 105740, 42.4440, -76.4737, 476, False),
    ("36063", "Niagara", "NY", "New York", "36", 212666, 43.1728, -78.8215, 523, False),
    ("36083", "Rensselaer", "NY", "New York", "36", 161130, 42.7137, -73.5107, 654, False),
    ("36093", "Schenectady", "NY", "New York", "36", 158061, 42.8142, -74.0568, 206, False),
    ("36043", "Herkimer", "NY", "New York", "36", 61319, 43.4197, -74.9646, 1411, False),
    ("36049", "Lewis", "NY", "New York", "36", 26719, 43.7844, -75.4489, 1276, False),
    ("36041", "Hamilton", "NY", "New York", "36", 5107, 43.6611, -74.4970, 1721, False),
    ("36033", "Franklin", "NY", "New York", "36", 50692, 44.5953, -74.3034, 1632, False),
    ("36019", "Clinton", "NY", "New York", "36", 80485, 44.7471, -73.6784, 1039, False),
    ("36035", "Fulton", "NY", "New York", "36", 53743, 43.1138, -74.4235, 496, False),
    ("36065", "Oneida", "NY", "New York", "36", 232125, 43.2414, -75.4328, 1213, False),
    ("36075", "Oswego", "NY", "New York", "36", 117525, 43.4637, -76.2107, 953, False),
    ("36037", "Genesee", "NY", "New York", "36", 58388, 43.0000, -78.1933, 495, False),
    ("36073", "Orleans", "NY", "New York", "36", 42883, 43.3117, -78.2206, 392, False),
    ("36121", "Wyoming", "NY", "New York", "36", 40531, 42.7023, -78.2268, 593, False),
    ("36009", "Cattaraugus", "NY", "New York", "36", 77686, 42.2550, -78.6793, 1310, False),
    ("36003", "Allegany", "NY", "New York", "36", 46091, 42.2571, -78.0269, 1030, False),
    ("36097", "Schuyler", "NY", "New York", "36", 17898, 42.3936, -76.8735, 329, False),
    ("36015", "Chemung", "NY", "New York", "36", 84148, 42.1426, -76.7623, 408, False),
    ("36023", "Cortland", "NY", "New York", "36", 48123, 42.5960, -76.0625, 499, False),
    ("36017", "Chenango", "NY", "New York", "36", 47220, 42.4935, -75.6116, 894, False),
    ("36025", "Delaware", "NY", "New York", "36", 44135, 42.1979, -74.9664, 1443, False),

    # -- Mississippi (28) - 40 counties --
    ("28049", "Hinds", "MS", "Mississippi", "28", 245285, 32.2988, -90.1848, 870, True),
    ("28033", "DeSoto", "MS", "Mississippi", "28", 184945, 34.8740, -89.9913, 478, True),
    ("28047", "Harrison", "MS", "Mississippi", "28", 208080, 30.4090, -89.0930, 576, True),
    ("28059", "Jackson", "MS", "Mississippi", "28", 143617, 30.4564, -88.6222, 727, False),
    ("28035", "Forrest", "MS", "Mississippi", "28", 74136, 31.1951, -89.2616, 467, False),
    ("28081", "Lee", "MS", "Mississippi", "28", 85436, 34.2917, -88.6822, 450, False),
    ("28089", "Madison", "MS", "Mississippi", "28", 111401, 32.4685, -90.1000, 718, False),
    ("28121", "Rankin", "MS", "Mississippi", "28", 155271, 32.2688, -89.9499, 775, False),
    ("28027", "Coahoma", "MS", "Mississippi", "28", 22124, 34.2260, -90.6032, 555, False),
    ("28011", "Bolivar", "MS", "Mississippi", "28", 30604, 33.7961, -90.8804, 876, False),
    ("28133", "Sunflower", "MS", "Mississippi", "28", 25110, 33.5541, -90.5760, 694, False),
    ("28151", "Washington", "MS", "Mississippi", "28", 43909, 33.2871, -90.9477, 724, False),
    ("28075", "Lauderdale", "MS", "Mississippi", "28", 78015, 32.4001, -88.6706, 704, False),
    ("28113", "Pike", "MS", "Mississippi", "28", 40404, 31.1747, -90.4049, 409, False),
    ("28073", "Lamar", "MS", "Mississippi", "28", 63343, 31.2073, -89.5229, 497, False),
    ("28045", "Hancock", "MS", "Mississippi", "28", 47632, 30.3792, -89.4717, 477, False),
    ("28109", "Pearl River", "MS", "Mississippi", "28", 55535, 30.7633, -89.5902, 812, False),
    ("28071", "Lafayette", "MS", "Mississippi", "28", 54019, 34.3600, -89.5006, 679, False),
    ("28083", "Leflore", "MS", "Mississippi", "28", 28436, 33.5510, -90.2865, 593, False),
    ("28087", "Lowndes", "MS", "Mississippi", "28", 59779, 33.4746, -88.4316, 502, False),
    ("28003", "Alcorn", "MS", "Mississippi", "28", 37057, 34.8809, -88.5802, 400, False),
    ("28093", "Marshall", "MS", "Mississippi", "28", 35294, 34.7613, -89.5007, 706, False),
    ("28107", "Panola", "MS", "Mississippi", "28", 34707, 34.3636, -89.9542, 684, False),
    ("28153", "Wayne", "MS", "Mississippi", "28", 20442, 31.6366, -88.6761, 810, False),
    ("28065", "Jefferson Davis", "MS", "Mississippi", "28", 11224, 31.5640, -89.8246, 408, False),
    ("28031", "Covington", "MS", "Mississippi", "28", 19168, 31.6300, -89.5499, 414, False),
    ("28067", "Jones", "MS", "Mississippi", "28", 68454, 31.6220, -89.1681, 694, False),
    ("28101", "Newton", "MS", "Mississippi", "28", 21720, 32.4000, -89.1187, 578, False),
    ("28129", "Smith", "MS", "Mississippi", "28", 15916, 32.0131, -89.5063, 636, False),
    ("28055", "Issaquena", "MS", "Mississippi", "28", 1338, 32.7413, -90.9898, 413, False),
    ("28125", "Sharkey", "MS", "Mississippi", "28", 4321, 32.8798, -90.7822, 428, False),
    ("28023", "Clarke", "MS", "Mississippi", "28", 15928, 32.0417, -88.6839, 691, False),
    ("28017", "Chickasaw", "MS", "Mississippi", "28", 17126, 33.9218, -88.9451, 502, False),
    ("28025", "Clay", "MS", "Mississippi", "28", 19816, 33.6543, -88.7790, 409, False),
    ("28161", "Yalobusha", "MS", "Mississippi", "28", 12273, 34.0101, -89.7110, 467, False),
    ("28013", "Calhoun", "MS", "Mississippi", "28", 14361, 33.9383, -89.3355, 586, False),
    ("28019", "Choctaw", "MS", "Mississippi", "28", 8210, 33.3467, -89.2497, 419, False),
    ("28009", "Benton", "MS", "Mississippi", "28", 8026, 34.8158, -89.1871, 407, False),
    ("28145", "Union", "MS", "Mississippi", "28", 28356, 34.5535, -89.0035, 416, False),
    ("28117", "Prentiss", "MS", "Mississippi", "28", 25276, 34.6174, -88.5207, 415, False),

    # -- Montana (30) - 40 counties --
    ("30111", "Yellowstone", "MT", "Montana", "30", 164731, 45.7833, -108.5007, 2635, True),
    ("30031", "Gallatin", "MT", "Montana", "30", 114434, 45.5589, -111.1817, 2506, False),
    ("30049", "Lewis and Clark", "MT", "Montana", "30", 69432, 46.5958, -112.0391, 3458, False),
    ("30063", "Missoula", "MT", "Montana", "30", 119600, 47.0660, -113.9940, 2593, False),
    ("30013", "Cascade", "MT", "Montana", "30", 81366, 47.3211, -111.3676, 2698, False),
    ("30029", "Flathead", "MT", "Montana", "30", 103806, 48.2288, -114.0609, 5087, False),
    ("30093", "Silver Bow", "MT", "Montana", "30", 34993, 45.9010, -112.6572, 718, False),
    ("30043", "Jefferson", "MT", "Montana", "30", 12088, 46.1530, -112.0960, 1656, False),
    ("30057", "Madison", "MT", "Montana", "30", 8600, 45.3009, -111.9239, 3587, False),
    ("30001", "Beaverhead", "MT", "Montana", "30", 9371, 45.1290, -113.0539, 5543, False),
    ("30023", "Deer Lodge", "MT", "Montana", "30", 9140, 46.0647, -113.0370, 737, False),
    ("30039", "Granite", "MT", "Montana", "30", 3389, 46.4058, -113.4531, 1727, False),
    ("30077", "Powell", "MT", "Montana", "30", 6844, 46.8552, -112.9490, 2326, False),
    ("30007", "Broadwater", "MT", "Montana", "30", 6311, 46.3308, -111.4412, 1192, False),
    ("30059", "Meagher", "MT", "Montana", "30", 1882, 46.5962, -110.8836, 2392, False),
    ("30107", "Wheatland", "MT", "Montana", "30", 2117, 46.4413, -109.8496, 1423, False),
    ("30041", "Hill", "MT", "Montana", "30", 16427, 48.6014, -109.9873, 2896, False),
    ("30015", "Chouteau", "MT", "Montana", "30", 5635, 47.8828, -110.4491, 3973, False),
    ("30005", "Blaine", "MT", "Montana", "30", 6727, 48.4334, -108.9611, 4226, False),
    ("30071", "Phillips", "MT", "Montana", "30", 3949, 48.2619, -107.8990, 5140, False),
    ("30105", "Valley", "MT", "Montana", "30", 7396, 48.3693, -106.6595, 4921, False),
    ("30019", "Daniels", "MT", "Montana", "30", 1690, 48.7850, -105.5553, 1426, False),
    ("30085", "Roosevelt", "MT", "Montana", "30", 11022, 48.2964, -105.0238, 2356, False),
    ("30091", "Sheridan", "MT", "Montana", "30", 3333, 48.7214, -104.5116, 1677, False),
    ("30083", "Richland", "MT", "Montana", "30", 11809, 47.6408, -104.5616, 2084, False),
    ("30021", "Dawson", "MT", "Montana", "30", 8613, 47.2782, -104.8997, 2373, False),
    ("30109", "Wibaux", "MT", "Montana", "30", 969, 46.9713, -104.2153, 889, False),
    ("30025", "Fallon", "MT", "Montana", "30", 2846, 46.8309, -104.4092, 1620, False),
    ("30079", "Prairie", "MT", "Montana", "30", 1077, 46.8595, -105.3779, 1737, False),
    ("30017", "Custer", "MT", "Montana", "30", 11402, 46.2470, -105.5716, 3783, False),
    ("30075", "Powder River", "MT", "Montana", "30", 1682, 45.3859, -105.6226, 3297, False),
    ("30003", "Big Horn", "MT", "Montana", "30", 13376, 45.4230, -107.5102, 4995, False),
    ("30095", "Stillwater", "MT", "Montana", "30", 9542, 45.6478, -109.3918, 1795, False),
    ("30009", "Carbon", "MT", "Montana", "30", 10669, 45.2124, -109.0286, 2048, False),
    ("30065", "Musselshell", "MT", "Montana", "30", 4651, 46.5186, -108.4280, 1867, False),
    ("30033", "Garfield", "MT", "Montana", "30", 1104, 47.2668, -106.9921, 4668, False),
    ("30055", "McCone", "MT", "Montana", "30", 1641, 47.6464, -105.9761, 2643, False),
    ("30069", "Petroleum", "MT", "Montana", "30", 487, 47.1175, -108.2504, 1654, False),
    ("30035", "Glacier", "MT", "Montana", "30", 13778, 48.6972, -112.9979, 2995, False),
    ("30099", "Teton", "MT", "Montana", "30", 6073, 47.8358, -112.2407, 2273, False),
]

# Specialty codes (must match schema seed)
SPECIALTY_CODES = [
    "primary_care", "cardiology", "neurology", "nephrology", "oncology",
    "psychiatry", "obgyn", "orthopedics", "general_surgery", "emergency",
    "radiology", "pathology", "dermatology", "ophthalmology", "pediatrics",
]

# Fake first/last names for provider generation
FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael",
    "Linda", "David", "Elizabeth", "William", "Barbara", "Richard", "Susan",
    "Joseph", "Jessica", "Thomas", "Sarah", "Christopher", "Karen", "Daniel",
    "Lisa", "Matthew", "Nancy", "Anthony", "Betty", "Mark", "Margaret",
    "Andrew", "Sandra", "Steven", "Ashley", "Paul", "Dorothy", "Joshua",
    "Kimberly", "Kenneth", "Emily", "Kevin", "Donna", "Brian", "Michelle",
    "Timothy", "Carol", "Ronald", "Amanda", "George", "Melissa", "Jason",
    "Deborah", "Priya", "Raj", "Wei", "Min", "Carlos", "Maria", "Ahmed",
    "Fatima", "Yuki", "Hiroshi", "Anna", "Ivan", "Olga", "Sanjay",
]
LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Patel", "Kim", "Chen", "Wang", "Singh", "Kumar", "Park",
    "Yamamoto", "Tanaka", "Petrov", "Ivanov", "Shah", "Gupta", "Das",
]


def _bbox_polygon_wkt(lat: float, lon: float, size_deg: float = 0.15) -> str:
    """Create a bounding-box polygon WKT from centroid."""
    half = size_deg / 2
    coords = (
        f"{lon - half} {lat - half},"
        f"{lon + half} {lat - half},"
        f"{lon + half} {lat + half},"
        f"{lon - half} {lat + half},"
        f"{lon - half} {lat - half}"
    )
    return f"MULTIPOLYGON((({coords})))"


def _provider_density_for_county(
    population: int, is_urban: bool, state: str
) -> float:
    """Return a target provider count per 100k population.

    Urban areas: 50-80 per 100k (well-served)
    Rural CA/TX/NY: 25-50 per 100k (moderate)
    Rural MS: 8-20 per 100k (shortage)
    Rural MT: 3-12 per 100k (severe shortage)
    """
    if is_urban:
        return random.uniform(50, 80)
    if state in ("MS",):
        return random.uniform(8, 20)
    if state in ("MT",):
        return random.uniform(3, 12)
    # Rural CA/TX/NY
    return random.uniform(25, 50)


def generate_counties(cur) -> list[dict]:
    """Insert counties and return list of county dicts."""
    print(f"  Inserting {len(COUNTIES)} counties...")
    rows = []
    county_dicts = []
    for c in COUNTIES:
        fips, name, state_abbr, state_name, state_fips, pop, lat, lon, area, is_urban = c
        # Vary bbox size by land area (1 degree ≈ 69 miles)
        size_deg = min(2.0, max(0.08, (area ** 0.5) / 69))
        wkt = _bbox_polygon_wkt(lat, lon, size_deg)
        rows.append((
            fips, name, state_fips, state_abbr, state_name,
            pop, area,
            f"SRID=4326;POINT({lon} {lat})",
            f"SRID=4326;{wkt}",
        ))
        county_dicts.append({
            "fips": fips, "name": name, "state_abbr": state_abbr,
            "population": pop, "lat": lat, "lon": lon,
            "land_area_sqmi": area, "is_urban": is_urban,
        })

    execute_values(
        cur,
        """INSERT INTO counties (fips, name, state_fips, state_abbr, state_name,
           population, land_area_sqmi, centroid, boundary)
           VALUES %s ON CONFLICT (fips) DO NOTHING""",
        rows,
        template="(%s, %s, %s, %s, %s, %s, %s, ST_GeomFromEWKT(%s), ST_GeomFromEWKT(%s))",
    )
    return county_dicts


def generate_zipcodes(cur, county_dicts: list[dict]) -> list[dict]:
    """Generate ~5 zipcodes per county, ~1000 total."""
    print("  Generating zipcodes...")
    random.seed(42)
    zip_counter = 10001
    zip_rows = []
    zip_dicts = []

    for cd in county_dicts:
        n_zips = random.randint(3, 8)
        for _ in range(n_zips):
            zcta = str(zip_counter).zfill(5)
            zip_counter += 1
            # Offset from county centroid
            lat = cd["lat"] + random.uniform(-0.1, 0.1)
            lon = cd["lon"] + random.uniform(-0.1, 0.1)
            pop = max(100, int(cd["population"] / n_zips * random.uniform(0.5, 1.5)))
            area = max(1, cd["land_area_sqmi"] / n_zips * random.uniform(0.5, 1.5))

            zip_rows.append((
                zcta, cd["fips"], cd["state_abbr"], pop, area,
                f"SRID=4326;POINT({lon} {lat})",
            ))
            zip_dicts.append({
                "zcta": zcta, "county_fips": cd["fips"],
                "state_abbr": cd["state_abbr"], "lat": lat, "lon": lon,
            })

    print(f"  Inserting {len(zip_rows)} zipcodes...")
    execute_values(
        cur,
        """INSERT INTO zipcodes (zcta, county_fips, state_abbr, population,
           land_area_sqmi, centroid)
           VALUES %s ON CONFLICT (zcta) DO NOTHING""",
        zip_rows,
        template="(%s, %s, %s, %s, %s, ST_GeomFromEWKT(%s))",
    )
    return zip_dicts


def generate_providers(cur, county_dicts: list[dict], zip_dicts: list[dict]):
    """Generate ~5000 providers with realistic dearth patterns."""
    random.seed(42)
    print("  Generating providers...")

    # Build county -> zipcodes map
    county_zips: dict[str, list[dict]] = {}
    for z in zip_dicts:
        county_zips.setdefault(z["county_fips"], []).append(z)

    provider_rows = []
    npi_counter = 1000000001

    for cd in county_dicts:
        density = _provider_density_for_county(
            cd["population"], cd["is_urban"], cd["state_abbr"]
        )
        target_count = max(1, int(cd["population"] * density / 100_000))
        # Cap to keep total around ~5000
        target_count = min(target_count, 50)

        zips_for_county = county_zips.get(cd["fips"], [])
        if not zips_for_county:
            continue

        for _ in range(target_count):
            npi = str(npi_counter)
            npi_counter += 1

            # Pick random specialty (weighted: more primary care)
            weights = [30] + [5] * 14  # primary_care heavy
            spec_code = random.choices(SPECIALTY_CODES, weights=weights, k=1)[0]
            taxonomy_list = SPECIALTY_TAXONOMIES.get(spec_code, [])
            taxonomy = random.choice(taxonomy_list) if taxonomy_list else "207Q00000X"

            # Pick a zip in this county
            z = random.choice(zips_for_county)
            lat = z["lat"] + random.uniform(-0.03, 0.03)
            lon = z["lon"] + random.uniform(-0.03, 0.03)

            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)

            provider_rows.append((
                npi, 1, f"{first} {last}",
                f"{random.randint(100, 9999)} Main St",
                cd["name"], cd["state_abbr"], z["zcta"],
                f"SRID=4326;POINT({lon} {lat})",
                [taxonomy], [spec_code],
                True,
            ))

    print(f"  Inserting {len(provider_rows)} providers...")
    # Insert in batches
    batch_size = 500
    for i in range(0, len(provider_rows), batch_size):
        batch = provider_rows[i:i + batch_size]
        execute_values(
            cur,
            """INSERT INTO providers (npi, entity_type, name, address_line1,
               city, state, zipcode, location, taxonomy_codes, specialties,
               is_active)
               VALUES %s ON CONFLICT (npi) DO NOTHING""",
            batch,
            template="(%s, %s, %s, %s, %s, %s, %s, ST_GeomFromEWKT(%s), %s, %s, %s)",
        )

    print(f"  Total providers generated: {len(provider_rows)}")
    return len(provider_rows)


def run(conn):
    """Run the sample data generation pipeline."""
    print("=== Generating Sample Data ===")
    with conn.cursor() as cur:
        # Clear existing data (idempotent re-runs)
        cur.execute("DELETE FROM dearth_scores")
        cur.execute("DELETE FROM providers")
        cur.execute("DELETE FROM zipcodes")
        cur.execute("DELETE FROM counties")
        conn.commit()

        county_dicts = generate_counties(cur)
        conn.commit()

        zip_dicts = generate_zipcodes(cur, county_dicts)
        conn.commit()

        generate_providers(cur, county_dicts, zip_dicts)
        conn.commit()

    print("=== Sample Data Generation Complete ===")
