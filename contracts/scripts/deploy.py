from brownie import PhoenixToken, TokenFarm, config, network
from scripts.helpful_scripts import get_account, get_contract
from web3 import Web3
KEPT_BALANCE = Web3.toWei(100, "ether")

def deploy_phoenix_token_and_token_farm():
    owner = get_account()
    phoenix_token = PhoenixToken.deploy({"from": owner })
    # @TODO check network verify parameter
    token_farm = TokenFarm.deploy(
        phoenix_token, 
        { "from": owner }, 
        # publish_source=config["networks"][network.show_active()]["verify"]
    )
    tx = phoenix_token.transfer(
        token_farm.address,
        phoenix_token.totalSupply() - KEPT_BALANCE,
        {"from": owner},
    )

    tx.wait(1)
    add_allowed_tokens(
        token_farm,
        {
            phoenix_token: get_contract("dai_usd_price_feed"),
            # Add other tokens here to listed tokens
        },
        owner,
    )
    # update front end
    return token_farm, phoenix_token

def add_allowed_tokens(token_farm, dict_of_allowed_token, account):
    for token in dict_of_allowed_token:
        token_farm.addToAllowedTokens(token.address, {"from": account})
        tx = token_farm.setPriceFeedContract(
            token.address, dict_of_allowed_token[token], {"from": account}
        )
        tx.wait(1)
    return token_farm

def main():
    deploy_phoenix_token_and_token_farm()
