from scripts.deploy import deploy_phoenix_token
from scripts.helpful_scripts import (
    LOCAL_BLOCKCHAIN_ENVIRONMENTS,
    get_account,
)
from brownie import network, PhoenixToken
import pytest

def test_phoenix_token_deploy():
    # Arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip("Only for local testing")
    account = get_account()
    non_owner = get_account(index=1)
    # Act
    phoenix_token = deploy_phoenix_token()
    # Assert
    assert PhoenixToken.at(phoenix_token).name() == "Phoenix Token"
