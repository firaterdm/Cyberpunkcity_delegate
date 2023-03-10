import ast
import time
from datetime import datetime
import requests

format_date = '%Y-%m-%d %H:%M:%S'

now = datetime.now()

last_snapshot_date_str = open("last_snap_shot_date.txt", "r")
last_snapshot_date_str = last_snapshot_date_str.read()

timestamp_now = time.mktime(datetime.strptime(str(datetime.strftime(now, format_date)), format_date).timetuple())
timestamp_last_ss = time.mktime(datetime.strptime(last_snapshot_date_str, format_date).timetuple())

last_snapshot_date = datetime.strptime(last_snapshot_date_str, format_date)
total_days = ((now - last_snapshot_date).total_seconds() / 86400)

url = f"https://api.elrond.com/accounts/erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqpzlllllshp8986/transactions?from=0&size=10000&status=success&function=delegate%2CunDelegate%2CreDelegateRewards&before={timestamp_now}&after={timestamp_last_ss}&order=asc"
url = requests.get(url).json()


def transaction_func(url, transaction):
    tx_hash = []
    for txhash in transaction:
        tx_hash.append(txhash['txHash'])
    for transfer in url:
        if transfer['txHash'] not in tx_hash:
            if transfer['function'] == 'reDelegateRewards':
                api_redelegate = f"https://api.elrond.com/transactions/{transfer['txHash']}"
                api_redelegate = requests.get(api_redelegate).json()
                value = round(float(api_redelegate["results"][0]["value"]) / 10 ** 18, 3)
            else:
                value = round(int(transfer["action"]["arguments"]["value"]) / 10 ** 18, 3)
            days = round((((now - datetime.fromtimestamp(transfer['timestamp'])).total_seconds()) / 86400), 3)
            transaction.append(
                {
                    "txHash": f"{transfer['txHash']}",
                    "address": f"{transfer['sender']}",
                    "function": f"{transfer['function']}",
                    "value": f"{value}",
                    "days": f"{days}"
                })
    return transaction


def delegate_func(snapshot, transfer):
    average = round(float(transfer['value']) * float(transfer['days']) / total_days, 3)
    if transfer['address'] not in snapshot.keys():
        snapshot[f"{transfer['address']}"] = {"average": f"{average}"}
    else:
        snapshot[transfer['address']][
            'average'] = f"{float(snapshot[transfer['address']]['average']) + float(average)}"
    return snapshot


def undelegate_func(snapshot, transfer):
    average = round(float(transfer['value']) * float(transfer['days']) / total_days, 3)
    if transfer['address'] not in snapshot.keys():
        snapshot[f"{transfer['address']}"] = {"average": f"{-average}"}
    else:
        snapshot[transfer['address']][
            'average'] = f"{float(snapshot[transfer['address']]['average']) - float(average)}"
    return snapshot


def reward_func(snapshot, transfer):
    average = round(float(transfer['value']) * float(transfer['days']) / total_days, 3)
    if transfer['address'] not in snapshot.keys():
        snapshot[f"{transfer['address']}"] = {"average": f"{average}"}
    else:
        snapshot[transfer['address']][
            'average'] = f"{float(snapshot[transfer['address']]['average']) + float(average)}"
    return snapshot


def wallet_func(snapshot, transaction, wallets_balance):
    for addr in snapshot.keys():
        if addr in wallets_balance.keys():
            snapshot[f"{addr}"][
                'average'] = f"{float(wallets_balance[addr]['balance']) + float(snapshot[addr]['average'])}"

    for wallet in transaction:
        if wallet['function'] == 'delegate':
            if wallet['address'] not in wallets_balance.keys():
                wallets_balance[f"{wallet['address']}"] = {"balance": f"{wallet['value']}"}
            else:
                wallets_balance[wallet['address']][
                    'balance'] = f"{float(wallets_balance[wallet['address']]['balance']) + float(wallet['value'])}"
        elif wallet['function'] == 'reDelegateRewards':
            if wallet['address'] not in wallets_balance.keys():
                wallets_balance[f"{wallet['address']}"] = {"balance": f"{wallet['value']}"}
            else:
                wallets_balance[wallet['address']][
                    'balance'] = f"{float(wallets_balance[wallet['address']]['balance']) + float(wallet['value'])}"
        elif wallet['function'] == 'unDelegate':
            wallets_balance[wallet['address']][
                'balance'] = f"{float(wallets_balance[wallet['address']]['balance']) - float(wallet['value'])}"
    return [snapshot, wallets_balance]


def main():
    snapshot = {}
    transaction = []
    wallets_balance = open("wallets_balance.txt", "r")
    wallets_balance = ast.literal_eval(wallets_balance.read())
    transaction_list = transaction_func(url, transaction)
    for transfer in transaction_list:
        if transfer['function'] == 'delegate':
            delegate_func(snapshot, transfer)
        elif transfer['function'] == 'unDelegate':
            undelegate_func(snapshot, transfer)
        elif transfer['function'] == 'reDelegateRewards':
            reward_func(snapshot, transfer)
    snapshot_balance = wallet_func(snapshot, transaction, wallets_balance)
    print(snapshot_balance[0])
    print(snapshot_balance[1])

    snapshot_txt = open("snapshot.txt", "w")
    snapshot_txt.write(f"{snapshot_balance[0]}")

    wallet_balance_txt = open("wallets_balance.txt", "w")
    wallet_balance_txt.write(f"{snapshot_balance[1]}")

    transaction_txt = open("transaction.txt", "w")
    transaction_txt.write(f"{transaction_list}")

    last_snapshot_date_txt = open("last_snap_shot_date.txt", "w")
    last_snapshot_date_txt.write(f"{datetime.strftime(now, format_date)}")


main()
