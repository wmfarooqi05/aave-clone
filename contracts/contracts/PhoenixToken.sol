// SPDX-License-Identifier: MIT
pragma solidity ^0.8.14;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract PhoenixToken is ERC20 {

    constructor (uint256 initialSupply) ERC20("Phoenix Token", "PX") public {
        _mint(msg.sender, initialSupply);
    }
}