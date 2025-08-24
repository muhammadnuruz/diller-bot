import asyncio
from datetime import datetime, timedelta

import aiohttp

from db.model import TelegramUser


def get_login_task(session, telegram_users):
    tasks = []
    for user in telegram_users:
        tasks.append(
            session.post(
                user.url,
                json={
                    "method": "login",
                    "auth": {
                        "login": user.login,
                        "password": user.password
                    }
                }
            )
        )
    return tasks


def get_orders_task(session, telegram_users, login_datas):
    tasks = []
    now = datetime.now()
    five_min_ago = now - timedelta(minutes=10)
    date_format = "%Y-%m-%d %H:%M:%S"

    for user, login_data in zip(telegram_users, login_datas):
        if not (login_data and login_data.get("status")):
            continue

        try:
            user_id = login_data["result"]["userId"]
            token = login_data["result"]["token"]
        except KeyError:
            continue
        payload = {
            "auth": {
                "userId": user_id,
                "token": token
            },
            "method": "getOrder",
            "params": {
                "page": 1,
                "limit": 1000,
                "filter": {
                    "include": "all",
                    "status": [1, 2, 3],
                    "period": {
                        "orderCreated": {
                            "from": five_min_ago.strftime(date_format),
                            "to": now.strftime(date_format)
                        }
                    }
                }
            }
        }

        tasks.append(session.post(user.url, json=payload))
    return tasks


def get_agent_tasks(session, telegram_users, login_datas):
    tasks = []

    for user, login_data in zip(telegram_users, login_datas):
        if not (login_data and login_data.get("status")):
            continue

        try:
            user_id = login_data["result"]["userId"]
            token = login_data["result"]["token"]
        except KeyError:
            continue
        payload = {
            "auth": {
                "userId": user_id,
                "token": token
            },
            "method": "getAgent",
            "params": {
                "page": 1,
                "limit": 1000
            }
        }

        tasks.append(session.post(user.url, json=payload))
    return tasks


def get_client_tasks(session, telegram_users, login_datas, client_IDs):
    tasks = []

    for user, login_data, client_ids in zip(telegram_users, login_datas, client_IDs):
        user_tasks = []
        if not (login_data and login_data.get("status")):
            tasks.append(user_tasks)
            continue
        try:
            user_id = login_data["result"]["userId"]
            token = login_data["result"]["token"]
        except KeyError:
            tasks.append(user_tasks)
            continue

        for client in client_ids:
            payload = {
                "auth": {"userId": user_id, "token": token},
                "method": "getClient",
                "params": {
                    "page": 1,
                    "limit": 1000,
                    "filter": {"client": {"CS_id": client}}
                }
            }
            user_tasks.append(session.post(user.url, json=payload))
        tasks.append(user_tasks)
    return tasks


async def validate_data(tasks):
    raw_responses = await asyncio.gather(*tasks, return_exceptions=True)
    results = []
    json_tasks = []

    for resp in raw_responses:
        if isinstance(resp, Exception):
            results.append({})
        else:
            json_tasks.append(resp.json())

    if json_tasks:
        json_results = await asyncio.gather(*json_tasks, return_exceptions=True)
        for r in json_results:
            if isinstance(r, Exception):
                results.append({})
            else:
                results.append(r)

    return results


async def nested_validate_data(nested_tasks):
    results = []

    for tasks in nested_tasks:
        raw_responses = await asyncio.gather(*tasks, return_exceptions=True)
        user_results = []
        json_tasks = []

        for resp in raw_responses:
            if isinstance(resp, Exception):
                user_results.append({})
            else:
                json_tasks.append(resp.json())

        if json_tasks:
            json_results = await asyncio.gather(*json_tasks, return_exceptions=True)
            for r in json_results:
                if isinstance(r, Exception):
                    user_results.append({})
                else:
                    user_results.append(r)

        results.append(user_results)

    return results


async def main_function():
    await TelegramUser.check_and_update_purchases()
    telegram_users = await TelegramUser().get_by(is_diller=True, is_purchase=True)
    async with aiohttp.ClientSession() as session:
        login_datas = await validate_data(get_login_task(session, telegram_users))
        new_orders = await validate_data(get_orders_task(session, telegram_users, login_datas))
        agents = await validate_data(get_agent_tasks(session, telegram_users, login_datas))
        clients = await nested_validate_data(
            get_client_tasks(session, telegram_users, login_datas, get_clients_id_function(new_orders)))
        data = []
        print(new_orders)
        for user, orders, agent, client in zip(telegram_users, new_orders, agents, clients):
            data.append({
                "user": user,
                "orders": orders,
                "agents": agent,
                "clients": client
            })
        return data


def get_clients_id_function(new_orders):
    client_IDs = []
    for orders in new_orders:
        num = len(client_IDs)
        client_IDs.append([])
        if not orders or not orders.get("status"):
            continue
        for order in orders.get("result", {}).get("order", []):
            client_IDs[num].append(order.get("client", {}).get("CS_id"))
    return client_IDs
