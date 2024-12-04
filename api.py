import aiohttp
import asyncio
from config import *


async def get_promo(promo_name: str):
    url = f"https://gambler-panel.com/api/me/promo/{promo_name}"
    headers = {
        "Authorization": API_TOKEN
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                return "Ошибка:", response.status, await response.text()


async def create_promo(data: dict):
    url = "https://gambler-panel.com/api/me/promo"
    headers = {
        "Authorization": API_TOKEN,  
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                return await response.json()
            else:
                return "Ошибка:", response.status, await response.text()


async def edit_promo(data: dict):
    url = "https://gambler-panel.com/api/me/promo" 
    headers = {
        "Authorization": API_TOKEN,  
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.patch(url, headers=headers, json=data) as response:
            if response.status == 200:
                return await response.json()
            else:
                return "Ошибка:", response.status, await response.text()


async def get_promo_stats(promo_name: str):
    url = f"https://gambler-panel.com/api/me/stats/promo/{promo_name}"
    headers = {
        "Authorization": API_TOKEN,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                return "Ошибка:", response.status, await response.text()


async def delete_promo(promo_name: str):
    url = "https://gambler-panel.com/api/me/promo"
    headers = {
        "Authorization": API_TOKEN,
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.delete(url, headers=headers, json={"name": promo_name}) as response:
            if response.status == 200:
                return await response.json()
            else:
                return "Ошибка:", response.status, await response.text()


async def get_profile_stats():
    url = "https://gambler-panel.com/api/me/stats/global?time=all"
    headers = {
        "Authorization": API_TOKEN
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                return "Ошибка:", response.status, await response.text()


async def test_deposit():
    url = "https://gambler-panel.com/api/me/deposits/test?mammothId=7254653982138696554&amount=500&promo=testpromo&token=bnb_bep20"
    headers = {
        "Authorization": API_TOKEN
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return True
            else:
                return "Ошибка:", response.status, await response.text()
