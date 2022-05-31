from scripts.deploy import deploy_phoenix_token_and_token_farm, KEPT_BALANCE
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    INITIAL_PRICE_FEED_VALUE,
    DECIMALS,
    get_account,
    get_contract,
)
from brownie import network, exceptions, chain
import pytest
from web3 import Web3


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


def test_stake_tokens(amount_staked=KEPT_BALANCE, index=1):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    non_owner = get_account(index)
    token_farm, phoenix_token = deploy_phoenix_token_and_token_farm()
    phoenix_token.mint(non_owner, amount_staked, {"from": owner })
    assert phoenix_token.balanceOf(non_owner) == amount_staked
    # Act
    phoenix_token.approve(token_farm.address, amount_staked, {"from": non_owner})
    tx = token_farm.stake(phoenix_token.address, amount_staked, {"from": non_owner})
    userIndex = token_farm.stakeholderAdressToIndexMap(non_owner.address)
    (
        user,
        amount,
        since,
        claimable
    ) = token_farm.getStaker(
        userIndex,
        1
    )

    assert amount == amount_staked
    assert user == non_owner.address
    assert since == tx.timestamp
    assert claimable == 0

    return token_farm, phoenix_token


def test_stake_unapproved_tokens(random_erc20 = None, amount_staked=KEPT_BALANCE):
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


def test_unstake_tokens(amount_staked = KEPT_BALANCE):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    non_owner = get_account(1)
    token_farm, phoenix_token = test_stake_tokens(amount_staked, 1)

    userIndex = token_farm.stakeholderAdressToIndexMap(non_owner.address)
    (user, amount, since, claimable) = token_farm.getStaker(userIndex, 1)
    assert amount == amount_staked

    # Act
    token_farm.unstake(phoenix_token.address, 1, {"from": non_owner})
    # Assert
    assert phoenix_token.balanceOf(non_owner.address) == KEPT_BALANCE

    with pytest.raises(exceptions.VirtualMachineError):
        token_farm.getStaker(userIndex, 1)

def test_get_user_total_balance_with_different_tokens_and_amounts(
    amount_staked = KEPT_BALANCE, random_erc20 = None
):
    if random_erc20 is None:
        random_erc20 = get_contract("fau_token")

    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    non_owner = get_account(1)
    token_farm, phoenix_token = test_stake_tokens(amount_staked)
    # Act
    token_farm.addToAllowedTokens(random_erc20.address, {"from": owner})
    # The random_erc20 is going to represent DAI
    # Since the other mocks auto deploy
    token_farm.setPriceFeedContract(
        random_erc20.address, get_contract("eth_usd_price_feed"), {"from": owner}
    )
    
    random_erc20_stake_amount = amount_staked * 2

    # @TODO fix this, change mint to internal
    random_erc20.mint(non_owner, random_erc20_stake_amount, {"from": owner})
    
    random_erc20.approve(
        token_farm.address, random_erc20_stake_amount, {"from": non_owner}
    )
    token_farm.stake(
        random_erc20.address, random_erc20_stake_amount, {"from": non_owner}
    )

    # Act
    timestamp = chain.time();
    chain.sleep(3600337) # it's 31.3 seconds
    chain.mine(10)
    
    expectedAmountWithReward = ((amount_staked + 
                                random_erc20_stake_amount + 
                                token_farm.calculateStakeReward(amount_staked, timestamp, phoenix_token) + 
                                token_farm.calculateStakeReward(random_erc20_stake_amount, timestamp, random_erc20)
                                ) * INITIAL_PRICE_FEED_VALUE) / (10**DECIMALS)

    total_eth_balance = token_farm.getUserStakingEthAmountValue(non_owner.address)
    assert total_eth_balance == expectedAmountWithReward
    # Improve by adding different mock price feed default values

def test_get_token_eth_price():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    token_farm, phoenix_token = deploy_phoenix_token_and_token_farm()
    # Act / Assert
    assert token_farm.getTokenEthPrice(phoenix_token.address) == (
        INITIAL_PRICE_FEED_VALUE,
        DECIMALS,
    )

def test_get_user_token_staking_balance_eth_value(amount_staked=KEPT_BALANCE):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    non_owner = get_account(1)
    token_farm, phoenix_token = deploy_phoenix_token_and_token_farm()
    # Act
    phoenix_token.mint(non_owner, amount_staked, {"from": owner})
    phoenix_token.approve(token_farm.address, amount_staked, {"from": non_owner})
    token_farm.stake(phoenix_token.address, amount_staked, {"from": non_owner})
    # Assert
    eth_balance_token = token_farm.getUserStakingEthAmountValue(non_owner.address)
    assert eth_balance_token == (KEPT_BALANCE * INITIAL_PRICE_FEED_VALUE) / (10**DECIMALS)


def test_get_user_token_staking_balance_eth_value_roles(amount_staked=KEPT_BALANCE):
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    owner = get_account()
    non_owner = get_account(1)
    non_owner2 = get_account(2)
    token_farm, phoenix_token = deploy_phoenix_token_and_token_farm()
    # Act
    phoenix_token.mint(non_owner, amount_staked, {"from": owner})
    phoenix_token.approve(token_farm.address, amount_staked, {"from": non_owner})
    token_farm.stake(phoenix_token.address, amount_staked, {"from": non_owner})

    # Assert    
    assert token_farm.getUserStakingEthAmountValue(non_owner.address, {"from": non_owner}) != 0
    assert token_farm.getUserStakingEthAmountValue(non_owner.address, {"from": owner}) != 0

    with pytest.raises(exceptions.VirtualMachineError):
        token_farm.getUserStakingEthAmountValue(non_owner.address, {"from": non_owner2})


# Test unstake with index 0 
# It should release all the stakes