from brownie import network
import pytest
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
    get_contract,
)
from scripts.deploy import deploy_phoenix_token_and_token_farm

def test_stake_and_issue_correct_amounts(amount_staked=100):
    print("test")
    # Arrange
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for integration testing")
    token_farm, phoenix_token = deploy_phoenix_token_and_token_farm()
    owner = get_account()
    # non_owner = get_account(1)
    phoenix_token.mint(owner.address, amount_staked, {"from": owner})
    print('balance', phoenix_token.balanceOf(owner.address))
    phoenix_token.approve(token_farm.address, amount_staked, {"from": owner})
    token_farm.stake(phoenix_token.address, amount_staked, {"from": owner})
    starting_balance = phoenix_token.balanceOf(owner.address)
    print("starting_balance", starting_balance)
    price_feed_contract = get_contract("dai_usd_price_feed")
    (_, price, _, _, _) = price_feed_contract.latestRoundData()
    amount_token_to_issue = (
        price / 10 ** price_feed_contract.decimals()
    ) * amount_staked
    # Act
    issue_tx = token_farm.issueAllTokens({"from": owner})
    issue_tx.wait(2)
    time_reward_buffer = 1000;
    # Assert
    assert (
        phoenix_token.balanceOf(owner.address) + time_reward_buffer
        > amount_token_to_issue + starting_balance and
        phoenix_token.balanceOf(owner.address) - time_reward_buffer
        < amount_token_to_issue + starting_balance
    )
