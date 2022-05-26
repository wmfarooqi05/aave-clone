from brownie import PhoenixToken
from scripts.helpful_scripts import get_account

def deploy_phoenix_token():
    account = get_account()
    return PhoenixToken.deploy(1000000000000000000000000, {"from": account })

def main():
    deploy_phoenix_token()
