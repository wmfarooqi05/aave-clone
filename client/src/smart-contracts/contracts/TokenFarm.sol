// SPDX-License-Identifier: MIT
pragma solidity 0.8.14;

import "@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";
import "@chainlink/contracts/src/v0.8/ChainlinkClient.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract TokenFarm is ChainlinkClient, Ownable {
    string public name = "Phoenix Token Farm";
    IERC20 public phoenixToken;

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

    mapping(address => address) public tokenPriceFeedMap;
    mapping(address => bool) public allowedTokens;

    // @TODO Add a mapping to give different reward based on token
    uint256 internal rewardPerHour = 1;

    modifier tokenIsAllowed(address token) {
        require(allowedTokens[token] == true, "Token currently isn't allowed");
        _;
    }

    constructor(address _phoenixTokenAddress) {
        phoenixToken = IERC20(_phoenixTokenAddress);
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

    function unstake(address _token, uint256 stakeIndex) public {
        require (stakeIndex > 0, "stakeIndex must be greater than 0");
        _unstake(_token, stakeholderAdressToIndexMap[msg.sender], stakeIndex);
        // @TODO It will still be called in case of failed unstake
        removeStakeByIndex(stakeholderAdressToIndexMap[msg.sender], stakeIndex);
    }

    function _unstake(address _token, uint256 stakeholderIndex, uint256 stakeIndex) internal {
        Stake storage stakeElement = stakeholders[stakeholderIndex].stake_addresses[stakeIndex];
        require(stakeElement.amount > 0, "Staking balance cannot be 0");
        uint256 _claimable = stakeElement.amount +
            calculateStakeReward(
                stakeElement.amount,
                stakeElement.since
            );
        stakeholders[stakeholderIndex].stake_addresses[stakeIndex].amount = 0; // To Prevent Reentrancy attack
        IERC20(_token).transfer(stakeElement.user, _claimable);
    }

    function removeStakeByIndex(uint256 stakeholderIndex, uint256 stakeIndex)
        internal
    {
        Stake[] storage stakeArray = stakeholders[stakeholderIndex].stake_addresses;
        delete stakeArray[stakeIndex];
        stakeArray[stakeIndex] = stakeArray[stakeArray.length - 1];
        stakeArray.pop();
    }

    // A user can view his reward
    function calculateStakeReward(
        uint256 amount,
        uint256 since
    ) public view returns (uint256) {
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

    function getStaker(uint256 index, uint256 stackIndex)
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

    function addToAllowedTokens(address token) external onlyOwner {
        allowedTokens[token] = true;
    }

    function setPriceFeedContract(address token, address priceFeed)
        external
        onlyOwner
    {
        tokenPriceFeedMap[token] = priceFeed;
    }

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

    // @TODO make this owner and user visible
    // This user only calculate current amount
    // Upgrade and make it calculate claimable amount
    function getUserStakingEthAmountValue(address user)
        public
        view
        returns (uint256 value)
    {
        require(
            msg.sender == this.owner() || user == msg.sender,
            "Only User or Owner can check balance"
        );
        uint256 totalValue = 0;
        Stake[] storage stakes = stakeholders[stakeholderAdressToIndexMap[user]]
            .stake_addresses;
        for (uint256 i = 1; i < stakes.length; i++) {
            (uint256 price, uint8 decimals) = getTokenEthPrice(stakes[i].token);
            uint256 rewardValue = stakes[i].amount +
                calculateStakeReward(
                    stakes[i].amount,
                    stakes[i].since
                );
            totalValue += (rewardValue * price) / (10**uint256(decimals));
        }

        return totalValue;
    }

    function issueAllTokens() public onlyOwner {
        for (uint256 i = 1; i < stakeholders.length; i++) {
            for (
                uint256 j = 1;
                j < stakeholders[i].stake_addresses.length;
                j++
            ) {
                _unstake(stakeholders[i].stake_addresses[j].token, i,j);
            }
            delete stakeholders[i].stake_addresses;
        }
        delete stakeholders;
    }
}
