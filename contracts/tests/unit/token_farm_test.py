from scripts.deploy import deploy_phoenix_token_and_token_farm, KEPT_BALANCE
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    INITIAL_PRICE_FEED_VALUE,
    DECIMALS,
    get_account,
    get_contract,
)
from brownie import network, exceptions
import pytest
from web3 import Web3

# needs testing
# test isTokenAllowed modifier in staking function


def test_add_allowed_tokens():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    account = get_account()
    non_owner = get_account(index=1)
    token_farm, phoenix_token = deploy_phoenix_token_and_token_farm()
    # Act
    token_farm.addToAllowedTokens(phoenix_token.address, {"from": account})
    # Assert
    token_farm.allowedTokens(phoenix_token.address) == True
    with pytest.raises(exceptions.VirtualMachineError):
        token_farm.addToAllowedTokens(phoenix_token.address, {"from": non_owner})

def test_set_price_feed_contract():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    account = get_account()
    non_owner = get_account(index=1)
    token_farm, phoenix_token = deploy_phoenix_token_and_token_farm()
    # Act
    token_farm.setPriceFeedContract(
        phoenix_token.address, get_contract("eth_usd_price_feed"), {"from": account}
    )
    # Assert
    assert token_farm.tokenPriceFeedMap(phoenix_token.address) == get_contract(
        "eth_usd_price_feed"
    )
    with pytest.raises(exceptions.VirtualMachineError):
        token_farm.setPriceFeedContract(
            phoenix_token.address, get_contract("eth_usd_price_feed"), {"from": non_owner}
        )


def test_stake_tokens(amount_staked=100):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    account = get_account()
    token_farm, phoenix_token = deploy_phoenix_token_and_token_farm()
    # Act
    phoenix_token.approve(token_farm.address, amount_staked, {"from": account})
    tx = token_farm.stake(phoenix_token.address, amount_staked, {"from": account})
    
    (
        user,
        amount,
        since,
        claimable
    ) = token_farm.getStacker(
        token_farm.stakeholderAdressToIndexMap(account.address),
        1
    )

    assert amount == amount_staked
    assert user == account.address
    assert since == tx.timestamp
    assert claimable == 0

    return token_farm, phoenix_token


def test_stake_unapproved_tokens(random_erc20 = None, amount_staked=100):
    if random_erc20 is None:
        random_erc20 = get_contract("fau_token")
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    account = get_account()
    token_farm, phoenix_token = deploy_phoenix_token_and_token_farm()
    # Act
    random_erc20.approve(token_farm.address, amount_staked, {"from": account})
    # Assert
    with pytest.raises(exceptions.VirtualMachineError):
        token_farm.stake(random_erc20.address, amount_staked, {"from": account})


def test_unstake_tokens(amount_staked = 100):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    account = get_account()
    token_farm, phoenix_token = test_stake_tokens(amount_staked)

    userIndex = token_farm.stakeholderAdressToIndexMap(account.address)
    (user, amount, since, claimable) = token_farm.getStacker(userIndex, 1)
    assert amount == amount_staked

    # Act
    token_farm.unstake(phoenix_token.address, 1, {"from": account})
    # Assert
    assert phoenix_token.balanceOf(account.address) == KEPT_BALANCE

    with pytest.raises(exceptions.VirtualMachineError):
        token_farm.getStacker(userIndex, 1)

# def test_get_user_total_balance_with_different_tokens_and_amounts(
#     amount_staked = 1000, random_erc20 = None
# ):
#     if random_erc20 is None:
#         random_erc20 = get_contract("fau_token")

#     # Arrange
#     if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
#         pytest.skip("Only for local testing")
#     account = get_account()
#     token_farm, phoenix_token = test_stake_tokens(amount_staked)
#     # Act
#     token_farm.addToAllowedTokens(random_erc20.address, {"from": account})
#     # The random_erc20 is going to represent DAI
#     # Since the other mocks auto deploy
#     token_farm.setPriceFeedContract(
#         random_erc20.address, get_contract("eth_usd_price_feed"), {"from": account}
#     )
    
#     random_erc20_stake_amount = amount_staked * 2
#     random_erc20.approve(
#         token_farm.address, random_erc20_stake_amount, {"from": account}
#     )
#     token_farm.stake(
#         random_erc20.address, random_erc20_stake_amount, {"from": account}
#     )
#     # Act
#     total_eth_balance = token_farm.getUserTotalValue(account.address)
#     assert total_eth_balance == INITIAL_PRICE_FEED_VALUE * 3
    # Improve by adding different mock price feed default values


# def test_get_token_eth_price():
#     # Arrange
#     if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
#         pytest.skip("Only for local testing")
#     token_farm, phoenix_token = deploy_phoenix_token_and_token_farm()
#     # Act / Assert
#     assert token_farm.getTokenEthPrice(phoenix_token.address) == (
#         INITIAL_PRICE_FEED_VALUE,
#         DECIMALS,
#     )


# def test_get_user_token_staking_balance_eth_value(amount_staked):
#     # Arrange
#     if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
#         pytest.skip("Only for local testing")
#     account = get_account()
#     token_farm, phoenix_token = deploy_phoenix_token_and_token_farm()
#     # Act
#     phoenix_token.approve(token_farm.address, amount_staked, {"from": account})
#     token_farm.stakeTokens(amount_staked, phoenix_token.address, {"from": account})
#     # Assert
#     eth_balance_token = token_farm.getUserTokenStakingBalanceEthValue(
#         account.address, phoenix_token.address
#     )
#     assert eth_balance_token == Web3.toWei(2000, "ether")


# def test_issue_tokens(amount_staked):
#     # Arrange
#     if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
#         pytest.skip("Only for local testing")
#     account = get_account()
#     token_farm, phoenix_token = test_stake_tokens(amount_staked)
#     starting_balance = phoenix_token.balanceOf(account.address)
#     # Act
#     token_farm.issueTokens({"from": account})
#     # Assert
#     assert (
#         phoenix_token.balanceOf(account.address)
#         == starting_balance + INITIAL_PRICE_FEED_VALUE
#     )
