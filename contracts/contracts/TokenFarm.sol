// SPDX-License-Identifier: MIT
pragma solidity 0.8.14;

import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";
import "@chainlink/contracts/src/v0.8/ChainlinkClient.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract TokenFarm is ChainlinkClient, Ownable {
    string public name = "Phoenix Token Farm";
    IERC20 public dappToken;

    struct Stake {
        address user;
        address token;
        uint256 amount;
        uint256 since;
        uint256 claimable;
    }

    struct Stakeholder {
        address user;
        Stake[] stake_addresses;
    }

    mapping(address => uint256) public stakeholderAdressToIndexMap;

    Stakeholder[] public stakeholders;

    event Staked(
        address indexed user,
        uint256 amount,
        uint256 index,
        uint256 timestamp
    );

    // token > address
    // mapping(address => mapping(address => uint256)) public tokenStakingAmount;
    // mapping(address => uint256) public uniqueTokensStaked;
    mapping(address => address) public tokenPriceFeedMap;
    mapping(address => bool) public allowedTokens;

    // @TODO Add a mapping to give different reward based on token
    uint256 internal rewardPerHour = 1000;

    modifier tokenIsAllowed(address token) {
        require(allowedTokens[token] == true, "Token currently isn't allowed");
        _;
    }

    constructor(address _dappTokenAddress) {
        dappToken = IERC20(_dappTokenAddress);
        stakeholders.push();
    }

    function stake(address token, uint256 _amount)
        external
        tokenIsAllowed(token)
    {
        _stake(msg.sender, token, _amount);
    }

    function _stake(
        address _user,
        address token,
        uint256 _amount
    ) internal {
        // Simple check so that user does not stake 0
        require(_amount > 0, "Stake amount must be greater than 0");

        uint256 userIndex = stakeholderAdressToIndexMap[_user];
        if (userIndex == 0) {
            // stakeholder is empty
            userIndex = _addStakeholder(_user);
        }

        /**
         * Even if user has already staked this token, add new row
         */
        stakeholders[userIndex].stake_addresses.push(
            Stake(_user, token, _amount, block.timestamp, 0)
        );

        uint256 index = stakeholders[userIndex].stake_addresses.length - 1;

        // Note: Update all balances before calling payable function
        IERC20(token).transferFrom(msg.sender, address(this), _amount);

        // Emit an event that the stake has occured
        emit Staked(msg.sender, _amount, index, block.timestamp);
    }

    function getMyToken(address token) public view returns (IERC20 mytoken) {
        return IERC20(token);
    }

    function unstake(address _token, uint256 index) public {
        // If index is 0, we will unstake all the coins
        Stakeholder storage stakeholder = stakeholders[
            stakeholderAdressToIndexMap[msg.sender]
        ];
        if (index != 0) {
            // @TODO this can have reentrancy attack
            _unstake(_token, stakeholder.stake_addresses[index]);
            removeStakeByIndex(stakeholder.stake_addresses, index);
        } 
        // else {
        //     // @TODO: for now return 0
        //     // run a loop
        // }
    }

    function _unstake(address _token, Stake storage stakeElement) internal {
        require(stakeElement.amount > 0, "Staking balance cannot be 0");
        stakeElement.claimable = calculateStakeReward(
            stakeElement.amount,
            stakeElement.since,
            stakeElement.token
        );
        IERC20(_token).transfer(stakeElement.user, stakeElement.amount + stakeElement.claimable);
    }

    function removeStakeByIndex(Stake[] storage stake_addresses, uint256 index)
        internal
    {
        delete stake_addresses[index];
        stake_addresses[index] = stake_addresses[stake_addresses.length - 1];
        stake_addresses.pop();
    }

    function calculateStakeReward(
        uint256 amount,
        uint256 since,
        address token
    ) internal view returns (uint256) {
        // @TODO add logic to give different reward depending upon token
        return (((block.timestamp - since) / 1 hours) * amount) / rewardPerHour;
    }

    function _addStakeholder(address staker) internal returns (uint256) {
        stakeholders.push();
        uint256 userIndex = stakeholders.length - 1;
        stakeholders[userIndex].user = staker;
        stakeholderAdressToIndexMap[staker] = userIndex;
        stakeholders[userIndex].stake_addresses.push(); // First index will be empty
        // stakingHistoryStakesMapToIndex[staker] = userIndex;
        return userIndex;
    }

    function getStacker(uint256 index, uint256 stackIndex)
        public
        view
        returns (
            address user,
            uint256 amount,
            uint256 since,
            uint256 claimable
        )
    {
        Stake storage cuurent_stake = stakeholders[index].stake_addresses[
            stackIndex
        ];
        return (
            cuurent_stake.user,
            cuurent_stake.amount,
            cuurent_stake.since,
            cuurent_stake.claimable
        );
    }

    function addToListedToken(address token) external onlyOwner {
        allowedTokens[token] = true;
    }

    function setPriceFeedContract(address token, address priceFeed)
        external
        onlyOwner
    {
        tokenPriceFeedMap[token] = priceFeed;
    }

    // function updateStakingBalance(
    //     address _user,
    //     address _token,
    //     uint256 _amount
    // ) internal {
    //     stakingBalance[_token][_user] = stakingBalance[_token][_user] + _amount;
    // }

    // function updateUniqueTokensStaked(address user, address token) internal {
    //     if (stakingBalance[token][user] <= 0) {
    //         uniqueTokensStaked[user] = uniqueTokensStaked[user] + 1;
    //     } else if (uniqueTokensStaked[user] == 1) {
    //         stakers.push(user);
    //     }
    // }

    // function getTotalTokensStaked() public view return (uint256 amount) {
    //     uint256 count = 0;
    //     for (uint256 i=0; i<array.length; i++) {
    //         count =
    //     }
    //     return count;
    // }

    function getTokenEthPrice(address token)
        public
        view
        returns (uint256, uint8)
    {
        address priceFeedAddress = tokenPriceFeedMap[token];
        AggregatorV3Interface priceFeed = AggregatorV3Interface(
            priceFeedAddress
        );
        (, int256 price, , , ) = priceFeed.latestRoundData();
        return (uint256(price), priceFeed.decimals());
    }

}
