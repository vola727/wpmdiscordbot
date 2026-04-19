import os
import json
import aiohttp
import random
import difflib
import asyncio
import re
import discord
import pymongo
from dotenv import load_dotenv

load_dotenv()

STATS_FILE = "stats.json"
MONGO_URI = os.getenv("MONGO_URI")

mongo_client = None
stats_collection = None

if MONGO_URI:
    try:
        mongo_client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = mongo_client["typeracediscordbot"]
        stats_collection = db["stats"]
        # test connection
        mongo_client.server_info()
        print("Connected to MongoDB Atlas!")
        
        # Migrate stats.json to MongoDB if the collection is empty
        if os.path.exists(STATS_FILE) and stats_collection.count_documents({}) == 0:
            print("Migrating stats from JSON to MongoDB...")
            try:
                with open(STATS_FILE, "r") as f:
                    local_stats = json.load(f)
                
                for user_id, user_data in local_stats.items():
                    update_data = user_data.copy()
                    update_data["user_id"] = user_id
                    stats_collection.update_one(
                        {"user_id": user_id},
                        {"$set": update_data},
                        upsert=True
                    )
                print("Migration complete!")
            except Exception as e:
                print(f"Migration failed: {e}")
                
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        mongo_client = None
        stats_collection = None


FALLBACK_QUOTES = [
    ("The quick brown fox jumps over the lazy dog.", "English pangram"),
    ("Python is an interpreted, high-level, general-purpose programming language.", "Guido van Rossum"),
    ("discord.py is an API wrapper for Discord written in Python.", "Rapptz"),
    ("Typing fast is not just about speed, it is about accuracy.", "Unknown"),
    ("A journey of a thousand miles begins with a single step.", "Laozi")
]

def load_stats():
    if stats_collection is not None:
        try:
            stats = {}
            for doc in stats_collection.find():
                user_id = doc.get("user_id", str(doc.get("_id")))
                stats[user_id] = {k: v for k, v in doc.items() if k not in ["_id", "user_id"]}
            return stats
        except Exception as e:
            print(f"Failed to load stats from MongoDB: {e}")
            
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_stats(data):
    if stats_collection is not None:
        try:
            for user_id, user_data in data.items():
                update_data = user_data.copy()
                update_data["user_id"] = user_id
                stats_collection.update_one(
                    {"user_id": user_id},
                    {"$set": update_data},
                    upsert=True
                )
        except Exception as e:
            print(f"Failed to save stats to MongoDB: {e}")
            
    try:
        with open(STATS_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Failed to save stats to JSON: {e}")

def update_user_stat(user_id, wpm, accuracy, won_race=False):
    uid = str(user_id)
    stats = load_stats()
    
    if uid not in stats:
        stats[uid] = {
            "tests_completed": 0,
            "total_wpm": 0.0,
            "highest_wpm": 0.0,
            "total_accuracy": 0.0,
            "races_won": 0
        }
    
    stats[uid]["tests_completed"] += 1
    stats[uid]["total_wpm"] += wpm
    stats[uid]["total_accuracy"] += accuracy
    if wpm > stats[uid].get("highest_wpm", 0.0):
        stats[uid]["highest_wpm"] = wpm
    if won_race:
        stats[uid]["races_won"] = stats[uid].get("races_won", 0) + 1
        
    save_stats(stats)

def calculate_accuracy(original: str, typed: str) -> float:
    return difflib.SequenceMatcher(None, original, typed).ratio() * 100

def fix_quote_casing(quote: str) -> str:
    quote = re.sub(r'\s+', ' ', quote).strip()
    words = quote.split()
    if not words:
        return quote
        
    upper_count = sum(1 for w in words if w.istitle() or w.isupper())
    if len(words) > 0 and (upper_count / len(words)) > 0.4:
        quote = quote.lower()
        
        def cap_match(match):
            return match.group(1) + match.group(2).upper()
            
        quote = quote[0].upper() + quote[1:]
        quote = re.sub(r'([.!?]\s+)([a-z])', cap_match, quote)
        quote = re.sub(r'\bi\b', 'I', quote)
        quote = re.sub(r'\bi\'', "I'", quote)
    
    return quote

async def countdown_reactions(msg, timeout):
    try:
        await asyncio.sleep(timeout - 3.0)
        for emoji in ["3️⃣", "2️⃣", "1️⃣"]:
            await msg.add_reaction(emoji)
            await asyncio.sleep(1.0)
        await msg.add_reaction("💥")
    except (asyncio.CancelledError, discord.HTTPException):
        pass

async def get_quote():
    url = "https://dummyjson.com/quotes/random"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('quote'), data.get('author')
    except Exception:
        pass
    
    url2 = "https://zenquotes.io/api/random"
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url2, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    return data[0]['q'], data[0]['a']
    except Exception:
        pass
        
    return random.choice(FALLBACK_QUOTES)
