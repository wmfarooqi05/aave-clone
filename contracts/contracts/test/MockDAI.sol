// SPDX-License-Identifier: MIT
pragma solidity ^0.8.7;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract MockDAI is ERC20, Ownable {
    constructor() public ERC20("Mock DAI", "DAI") {
    }

    function mint(address account, uint256 amount)
        internal
        onlyOwner
        returns (bool)
    {
        _mint(account, amount);
        return true;
    }
}
