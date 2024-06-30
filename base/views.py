import os
import time
import requests
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.shortcuts import render
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from tqdm import tqdm

def get_sui_address_from_seed(seed_phrase):
    try:
        # Generate seed from BIP39 mnemonic
        seed_bytes = Bip39SeedGenerator(seed_phrase).Generate()

        # Derive Sui address from the seed
        bip44_mst = Bip44.FromSeed(seed_bytes, Bip44Coins.SUI)
        bip44_acc = bip44_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
        return bip44_acc.PublicKey().ToAddress()
    except Exception as e:
        print(f"Error generating address for seed phrase: {seed_phrase}. Error: {e}")
        return None

def get_balance(address, api_key, retries=5):
    url = f"https://api.blockberry.one/sui/v1/accounts/{address}/balance"
    headers = {
        "accept": "*/*",
        "x-api-key": api_key
    }

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error fetching balance for address {address}: {response.status_code}")
                return None
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error on attempt {attempt + 1} for address {address}: {e}")
            time.sleep(2)

    print(f"Failed to fetch balance for address {address} after {retries} attempts")
    return None

def process_seed_phrases_and_fetch_balances(input_path, output_path, api_key):
    with open(input_path, 'r') as file:
        seed_phrases = file.readlines()

    total_checked = 0
    total_saved = 0

    print("Processing seed phrases and fetching balances...")
    with open(output_path, 'w') as file:
        for seed_phrase in tqdm(seed_phrases, desc="Progress", unit="phrase"):
            seed_phrase = seed_phrase.strip()
            if seed_phrase:
                print(f"Processing seed phrase: {seed_phrase}")
                address = get_sui_address_from_seed(seed_phrase)
                if address:
                    print(f"Generated address: {address}")
                    total_checked += 1
                    balance_info = get_balance(address, api_key)
                    if balance_info is not None:
                        print(f"Fetched balance for address {address}: {balance_info}")
                        file.write(f"{balance_info}\n")
                        total_saved += 1
                    else:
                        print(f"Failed to fetch balance for address: {address}")
                else:
                    print(f"Failed to generate address for seed phrase: {seed_phrase}")

    print(f"Total balances checked: {total_checked}")
    print(f"Total balances saved: {total_saved}")

def upload_file(request):
    if request.method == 'POST' and request.FILES['file']:
        uploaded_file = request.FILES['file']
        fs = FileSystemStorage()
        input_path = fs.save(uploaded_file.name, uploaded_file)
        input_path = os.path.join(settings.MEDIA_ROOT, input_path)
        output_path = os.path.join(settings.MEDIA_ROOT, 'main2.txt')
        api_key = "w8SDGmfLywxzZAyUp7h7nZXwJq9Mnl"
        process_seed_phrases_and_fetch_balances(input_path, output_path, api_key)
        return render(request, 'results.html', {'output_file': 'main2.txt'})
    return render(request, 'upload.html')

def download_file(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, filename)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.ms-excel")
            response['Content-Disposition'] = f'inline; filename={os.path.basename(file_path)}'
            return response
    return HttpResponse(status=404)
