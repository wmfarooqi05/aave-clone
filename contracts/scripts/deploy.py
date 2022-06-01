from brownie import PhoenixToken, TokenFarm, config, network
from scripts.helpful_scripts import get_account, get_contract
import shutil
import os
import yaml
import json
from web3 import Web3

KEPT_BALANCE = Web3.toWei(100, "ether")

def deploy_phoenix_token_and_token_farm(update_front_end_flag=False):
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
    if update_front_end_flag:
        update_front_end()
    return token_farm, phoenix_token

def add_allowed_tokens(token_farm, dict_of_allowed_token, account):
    for token in dict_of_allowed_token:
        token_farm.addToAllowedTokens(token.address, {"from": account})
        tx = token_farm.setPriceFeedContract(
            token.address, dict_of_allowed_token[token], {"from": account}
        )
        tx.wait(1)
    return token_farm

def update_front_end():
    print("Updating front end...")
    # The Build
    copy_folders_to_front_end("./build/contracts", "../client/src/smart-contracts/chain-info")

    # The Contracts
    copy_folders_to_front_end("./contracts", "../client/src/smart-contracts/contracts")

    # The ERC20
    copy_files_to_front_end(
        "./build/contracts/dependencies/OpenZeppelin/openzeppelin-contracts@4.6.0/ERC20.json",
        "../client/src/smart-contracts/chain-info/ERC20.json",
    )
    # The Map
    copy_files_to_front_end(
        "./build/deployments/map.json",
        "../client/src/smart-contracts/chain-info/map.json",
    )

    # The Config, converted from YAML to JSON
    with open("brownie-config.yaml", "r") as brownie_config:
        config_dict = yaml.load(brownie_config, Loader=yaml.FullLoader)
        with open(
            "../client/src/smart-contracts/brownie-config-json.json", "w"
        ) as brownie_config_json:
            json.dump(config_dict, brownie_config_json)
    print("Front end updated!")


def copy_folders_to_front_end(src, dest):
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def copy_files_to_front_end(src, dest):
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copyfile(src, dest)


def main():
    deploy_phoenix_token_and_token_farm()
