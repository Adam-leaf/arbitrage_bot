erc20_abi = [
  { "inputs": [], "stateMutability": "nonpayable", "type": "constructor" },
  { "inputs": [], "name": "AdapterParamsMustBeEmpty", "type": "error" },
  {
    "inputs": [],
    "name": "AdditionToPoolIsBelowPerTransactionMinimum",
    "type": "error"
  },
  {
    "inputs": [],
    "name": "AdditionToPoolWouldExceedPerAddressCap",
    "type": "error"
  },
  { "inputs": [], "name": "AdditionToPoolWouldExceedPoolCap", "type": "error" },
  { "inputs": [], "name": "AddressAlreadySet", "type": "error" },
  {
    "inputs": [
      { "internalType": "address", "name": "target", "type": "address" }
    ],
    "name": "AddressEmptyCode",
    "type": "error"
  },
  {
    "inputs": [
      { "internalType": "address", "name": "account", "type": "address" }
    ],
    "name": "AddressInsufficientBalance",
    "type": "error"
  },
  { "inputs": [], "name": "AllowanceDecreasedBelowZero", "type": "error" },
  { "inputs": [], "name": "AlreadyInitialised", "type": "error" },
  {
    "inputs": [],
    "name": "ApprovalCallerNotOwnerNorApproved",
    "type": "error"
  },
  { "inputs": [], "name": "ApprovalQueryForNonexistentToken", "type": "error" },
  { "inputs": [], "name": "ApproveFromTheZeroAddress", "type": "error" },
  { "inputs": [], "name": "ApproveToTheZeroAddress", "type": "error" },
  { "inputs": [], "name": "AuctionStatusIsNotEnded", "type": "error" },
  { "inputs": [], "name": "AuctionStatusIsNotOpen", "type": "error" },
  {
    "inputs": [
      { "internalType": "address[]", "name": "modules", "type": "address[]" },
      { "internalType": "uint256", "name": "value", "type": "uint256" },
      { "internalType": "bytes", "name": "data", "type": "bytes" },
      { "internalType": "uint256", "name": "txGas", "type": "uint256" }
    ],
    "name": "AuxCallFailed",
    "type": "error"
  },
  { "inputs": [], "name": "BalanceMismatch", "type": "error" },
  { "inputs": [], "name": "BalanceQueryForZeroAddress", "type": "error" },
  {
    "inputs": [],
    "name": "BidMustBeBelowTheFloorForRefundDuringAuction",
    "type": "error"
  },
  {
    "inputs": [],
    "name": "BidMustBeBelowTheFloorWhenReducingQuantity",
    "type": "error"
  },
  {
    "inputs": [
      {
        "internalType": "enum IErrors.BondingCurveErrorType",
        "name": "error",
        "type": "uint8"
      }
    ],
    "name": "BondingCurveError",
    "type": "error"
  },
  { "inputs": [], "name": "BurnExceedsBalance", "type": "error" },
  { "inputs": [], "name": "BurnFromTheZeroAddress", "type": "error" },
  { "inputs": [], "name": "CallerIsNotAdminNorFactory", "type": "error" },
  { "inputs": [], "name": "CallerIsNotDepositBoxOwner", "type": "error" },
  { "inputs": [], "name": "CallerIsNotFactory", "type": "error" },
  { "inputs": [], "name": "CallerIsNotFactoryOrProjectOwner", "type": "error" },
  {
    "inputs": [],
    "name": "CallerIsNotFactoryProjectOwnerOrPool",
    "type": "error"
  },
  {
    "inputs": [
      { "internalType": "address", "name": "caller", "type": "address" }
    ],
    "name": "CallerIsNotPlatformAdmin",
    "type": "error"
  },
  {
    "inputs": [
      { "internalType": "address", "name": "caller", "type": "address" }
    ],
    "name": "CallerIsNotSuperAdmin",
    "type": "error"
  },
  { "inputs": [], "name": "CallerIsNotTheManager", "type": "error" },
  { "inputs": [], "name": "CallerIsNotTheOwner", "type": "error" },
  { "inputs": [], "name": "CallerMustBeLzApp", "type": "error" },
  { "inputs": [], "name": "CanOnlyReduce", "type": "error" },
  {
    "inputs": [],
    "name": "CannotAddLiquidityOnCreateAndUseDRIPool",
    "type": "error"
  },
  {
    "inputs": [],
    "name": "CannotSetNewManagerToTheZeroAddress",
    "type": "error"
  },
  {
    "inputs": [],
    "name": "CannotSetNewOwnerToTheZeroAddress",
    "type": "error"
  },
  { "inputs": [], "name": "CannotSetToZeroAddress", "type": "error" },
  { "inputs": [], "name": "CannotWithdrawThisToken", "type": "error" },
  { "inputs": [], "name": "CollectionAlreadyRevealed", "type": "error" },
  { "inputs": [], "name": "ContractIsDecommissioned", "type": "error" },
  { "inputs": [], "name": "ContractIsNotPaused", "type": "error" },
  { "inputs": [], "name": "ContractIsPaused", "type": "error" },
  { "inputs": [], "name": "DecreasedAllowanceBelowZero", "type": "error" },
  { "inputs": [], "name": "DeployerOnly", "type": "error" },
  { "inputs": [], "name": "DeploymentError", "type": "error" },
  { "inputs": [], "name": "DepositBoxIsNotOpen", "type": "error" },
  { "inputs": [], "name": "DestinationIsNotTrustedSource", "type": "error" },
  {
    "inputs": [],
    "name": "DriPoolAddressCannotBeAddressZero",
    "type": "error"
  },
  { "inputs": [], "name": "FailedInnerCall", "type": "error" },
  { "inputs": [], "name": "GasLimitIsTooLow", "type": "error" },
  { "inputs": [], "name": "IncorrectConfirmationValue", "type": "error" },
  { "inputs": [], "name": "IncorrectPayment", "type": "error" },
  { "inputs": [], "name": "InitialLiquidityAlreadyAdded", "type": "error" },
  { "inputs": [], "name": "InitialLiquidityNotYetAdded", "type": "error" },
  { "inputs": [], "name": "InsufficientAllowance", "type": "error" },
  { "inputs": [], "name": "InvalidAdapterParams", "type": "error" },
  { "inputs": [], "name": "InvalidAddress", "type": "error" },
  { "inputs": [], "name": "InvalidEndpointCaller", "type": "error" },
  { "inputs": [], "name": "InvalidInitialization", "type": "error" },
  { "inputs": [], "name": "InvalidMinGas", "type": "error" },
  { "inputs": [], "name": "InvalidOracleSignature", "type": "error" },
  { "inputs": [], "name": "InvalidPayload", "type": "error" },
  { "inputs": [], "name": "InvalidReceiver", "type": "error" },
  { "inputs": [], "name": "InvalidSourceSendingContract", "type": "error" },
  { "inputs": [], "name": "InvalidTotalShares", "type": "error" },
  { "inputs": [], "name": "LPLockUpMustFitUint88", "type": "error" },
  { "inputs": [], "name": "LimitsCanOnlyBeRaised", "type": "error" },
  { "inputs": [], "name": "LiquidityPoolCannotBeAddressZero", "type": "error" },
  {
    "inputs": [],
    "name": "LiquidityPoolMustBeAContractAddress",
    "type": "error"
  },
  { "inputs": [], "name": "ListLengthMismatch", "type": "error" },
  {
    "inputs": [],
    "name": "MachineAddressCannotBeAddressZero",
    "type": "error"
  },
  { "inputs": [], "name": "ManagerUnauthorizedAccount", "type": "error" },
  { "inputs": [], "name": "MaxBidQuantityIs255", "type": "error" },
  {
    "inputs": [
      { "internalType": "uint256", "name": "requested", "type": "uint256" },
      { "internalType": "uint256", "name": "alreadyMinted", "type": "uint256" },
      { "internalType": "uint256", "name": "maxAllowance", "type": "uint256" }
    ],
    "name": "MaxPublicMintAllowanceExceeded",
    "type": "error"
  },
  { "inputs": [], "name": "MaxSupplyTooHigh", "type": "error" },
  { "inputs": [], "name": "MaxTokensPerTxnExceeded", "type": "error" },
  { "inputs": [], "name": "MaxTokensPerWalletExceeded", "type": "error" },
  { "inputs": [], "name": "MetadataIsLocked", "type": "error" },
  { "inputs": [], "name": "MinGasLimitNotSet", "type": "error" },
  { "inputs": [], "name": "MintERC2309QuantityExceedsLimit", "type": "error" },
  { "inputs": [], "name": "MintToZeroAddress", "type": "error" },
  { "inputs": [], "name": "MintZeroQuantity", "type": "error" },
  { "inputs": [], "name": "MintingIsClosedForever", "type": "error" },
  {
    "inputs": [],
    "name": "NewBuyTaxBasisPointsExceedsMaximum",
    "type": "error"
  },
  {
    "inputs": [],
    "name": "NewSellTaxBasisPointsExceedsMaximum",
    "type": "error"
  },
  { "inputs": [], "name": "NoETHForLiquidityPair", "type": "error" },
  { "inputs": [], "name": "NoPaymentDue", "type": "error" },
  { "inputs": [], "name": "NoRefundForCaller", "type": "error" },
  { "inputs": [], "name": "NoStoredMessage", "type": "error" },
  { "inputs": [], "name": "NoTokenForLiquidityPair", "type": "error" },
  { "inputs": [], "name": "NoTrustedPathRecord", "type": "error" },
  { "inputs": [], "name": "NotInitializing", "type": "error" },
  { "inputs": [], "name": "NothingToClaim", "type": "error" },
  { "inputs": [], "name": "OperationDidNotSucceed", "type": "error" },
  { "inputs": [], "name": "OracleSignatureHasExpired", "type": "error" },
  {
    "inputs": [
      { "internalType": "address", "name": "owner", "type": "address" }
    ],
    "name": "OwnableInvalidOwner",
    "type": "error"
  },
  {
    "inputs": [
      { "internalType": "address", "name": "account", "type": "address" }
    ],
    "name": "OwnableUnauthorizedAccount",
    "type": "error"
  },
  { "inputs": [], "name": "OwnerQueryForNonexistentToken", "type": "error" },
  {
    "inputs": [],
    "name": "OwnershipNotInitializedForExtraData",
    "type": "error"
  },
  { "inputs": [], "name": "ParamTooLargeEndDate", "type": "error" },
  { "inputs": [], "name": "ParamTooLargeMinETH", "type": "error" },
  { "inputs": [], "name": "ParamTooLargePerAddressMax", "type": "error" },
  { "inputs": [], "name": "ParamTooLargePoolPerTxnMinETH", "type": "error" },
  { "inputs": [], "name": "ParamTooLargePoolSupply", "type": "error" },
  { "inputs": [], "name": "ParamTooLargeStartDate", "type": "error" },
  { "inputs": [], "name": "ParamTooLargeVestingDays", "type": "error" },
  {
    "inputs": [],
    "name": "ParametersDoNotMatchSignedMessage",
    "type": "error"
  },
  { "inputs": [], "name": "PassedConfigDoesNotMatchApproved", "type": "error" },
  { "inputs": [], "name": "PauseCutOffHasPassed", "type": "error" },
  { "inputs": [], "name": "PaymentMustCoverPerMintFee", "type": "error" },
  { "inputs": [], "name": "PermitDidNotSucceed", "type": "error" },
  { "inputs": [], "name": "PlatformAdminCannotBeAddressZero", "type": "error" },
  {
    "inputs": [],
    "name": "PlatformTreasuryCannotBeAddressZero",
    "type": "error"
  },
  { "inputs": [], "name": "PoolIsAboveMinimum", "type": "error" },
  { "inputs": [], "name": "PoolIsBelowMinimum", "type": "error" },
  { "inputs": [], "name": "PoolPhaseIsClosed", "type": "error" },
  { "inputs": [], "name": "PoolPhaseIsNotAfter", "type": "error" },
  { "inputs": [], "name": "PoolVestingNotYetComplete", "type": "error" },
  { "inputs": [], "name": "ProjectOwnerCannotBeAddressZero", "type": "error" },
  { "inputs": [], "name": "ProofInvalid", "type": "error" },
  {
    "inputs": [],
    "name": "QuantityExceedsMaxPossibleCollectionSupply",
    "type": "error"
  },
  {
    "inputs": [],
    "name": "QuantityExceedsRemainingCollectionSupply",
    "type": "error"
  },
  {
    "inputs": [],
    "name": "QuantityExceedsRemainingPhaseSupply",
    "type": "error"
  },
  { "inputs": [], "name": "ReferralIdAlreadyUsed", "type": "error" },
  {
    "inputs": [],
    "name": "RequestingMoreThanAvailableBalance",
    "type": "error"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "previouslyMinted",
        "type": "uint256"
      },
      { "internalType": "uint256", "name": "requested", "type": "uint256" },
      {
        "internalType": "uint256",
        "name": "remainingAllocation",
        "type": "uint256"
      }
    ],
    "name": "RequestingMoreThanRemainingAllocation",
    "type": "error"
  },
  { "inputs": [], "name": "RoyaltyFeeWillExceedSalePrice", "type": "error" },
  {
    "inputs": [
      { "internalType": "address", "name": "token", "type": "address" }
    ],
    "name": "SafeERC20FailedOperation",
    "type": "error"
  },
  { "inputs": [], "name": "ShareTotalCannotBeZero", "type": "error" },
  { "inputs": [], "name": "SliceOutOfBounds", "type": "error" },
  { "inputs": [], "name": "SliceOverflow", "type": "error" },
  { "inputs": [], "name": "SuperAdminCannotBeAddressZero", "type": "error" },
  { "inputs": [], "name": "SupplyTotalMismatch", "type": "error" },
  { "inputs": [], "name": "SupportWindowIsNotOpen", "type": "error" },
  {
    "inputs": [],
    "name": "TaxFreeAddressCannotBeAddressZero",
    "type": "error"
  },
  { "inputs": [], "name": "TaxPeriodStillInForce", "type": "error" },
  { "inputs": [], "name": "TemplateCannotBeAddressZero", "type": "error" },
  { "inputs": [], "name": "TemplateNotFound", "type": "error" },
  { "inputs": [], "name": "ThisMintIsClosed", "type": "error" },
  { "inputs": [], "name": "TotalSharesMustMatchDenominator", "type": "error" },
  { "inputs": [], "name": "TransferAmountExceedsBalance", "type": "error" },
  {
    "inputs": [],
    "name": "TransferCallerNotOwnerNorApproved",
    "type": "error"
  },
  { "inputs": [], "name": "TransferFailed", "type": "error" },
  { "inputs": [], "name": "TransferFromIncorrectOwner", "type": "error" },
  { "inputs": [], "name": "TransferFromZeroAddress", "type": "error" },
  {
    "inputs": [],
    "name": "TransferToNonERC721ReceiverImplementer",
    "type": "error"
  },
  { "inputs": [], "name": "TransferToZeroAddress", "type": "error" },
  { "inputs": [], "name": "URIQueryForNonexistentToken", "type": "error" },
  { "inputs": [], "name": "UnrecognisedVRFMode", "type": "error" },
  {
    "inputs": [],
    "name": "VRFCoordinatorCannotBeAddressZero",
    "type": "error"
  },
  { "inputs": [], "name": "ValueExceedsMaximum", "type": "error" },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "address",
        "name": "owner",
        "type": "address"
      },
      {
        "indexed": True,
        "internalType": "address",
        "name": "spender",
        "type": "address"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "value",
        "type": "uint256"
      }
    ],
    "name": "Approval",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "oldThreshold",
        "type": "uint256"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "newThreshold",
        "type": "uint256"
      }
    ],
    "name": "AutoSwapThresholdUpdated",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "identifier",
        "type": "uint256"
      }
    ],
    "name": "ExternalCallError",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "tokenA",
        "type": "uint256"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "tokenB",
        "type": "uint256"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "lpToken",
        "type": "uint256"
      }
    ],
    "name": "InitialLiquidityAdded",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": False,
        "internalType": "uint64",
        "name": "version",
        "type": "uint64"
      }
    ],
    "name": "Initialized",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "oldMaxTokensPerTransaction",
        "type": "uint256"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "newMaxTokensPerTransaction",
        "type": "uint256"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "oldMaxTokensPerWallet",
        "type": "uint256"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "newMaxTokensPerWallet",
        "type": "uint256"
      }
    ],
    "name": "LimitsUpdated",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": False,
        "internalType": "address",
        "name": "addedPool",
        "type": "address"
      }
    ],
    "name": "LiquidityPoolAdded",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": False,
        "internalType": "address",
        "name": "addedPool",
        "type": "address"
      }
    ],
    "name": "LiquidityPoolCreated",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": False,
        "internalType": "address",
        "name": "removedPool",
        "type": "address"
      }
    ],
    "name": "LiquidityPoolRemoved",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "address",
        "name": "previousOwner",
        "type": "address"
      },
      {
        "indexed": True,
        "internalType": "address",
        "name": "newOwner",
        "type": "address"
      }
    ],
    "name": "OwnershipTransferStarted",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "address",
        "name": "previousOwner",
        "type": "address"
      },
      {
        "indexed": True,
        "internalType": "address",
        "name": "newOwner",
        "type": "address"
      }
    ],
    "name": "OwnershipTransferred",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "oldBuyBasisPoints",
        "type": "uint256"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "newBuyBasisPoints",
        "type": "uint256"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "oldSellBasisPoints",
        "type": "uint256"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "newSellBasisPoints",
        "type": "uint256"
      }
    ],
    "name": "ProjectTaxBasisPointsChanged",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": False,
        "internalType": "address",
        "name": "treasury",
        "type": "address"
      }
    ],
    "name": "ProjectTaxRecipientUpdated",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [],
    "name": "RevenueAutoSwap",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "address",
        "name": "from",
        "type": "address"
      },
      {
        "indexed": True,
        "internalType": "address",
        "name": "to",
        "type": "address"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "value",
        "type": "uint256"
      }
    ],
    "name": "Transfer",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": False,
        "internalType": "bytes32",
        "name": "addedValidCaller",
        "type": "bytes32"
      }
    ],
    "name": "ValidCallerAdded",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": False,
        "internalType": "bytes32",
        "name": "removedValidCaller",
        "type": "bytes32"
      }
    ],
    "name": "ValidCallerRemoved",
    "type": "event"
  },
  {
    "inputs": [],
    "name": "acceptOwnership",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      { "internalType": "address", "name": "lpOwner", "type": "address" }
    ],
    "name": "addInitialLiquidity",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "newLiquidityPool_",
        "type": "address"
      }
    ],
    "name": "addLiquidityPool",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "bytes32",
        "name": "newValidCallerHash_",
        "type": "bytes32"
      }
    ],
    "name": "addValidCaller",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      { "internalType": "address", "name": "owner", "type": "address" },
      { "internalType": "address", "name": "spender", "type": "address" }
    ],
    "name": "allowance",
    "outputs": [{ "internalType": "uint256", "name": "", "type": "uint256" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      { "internalType": "address", "name": "spender", "type": "address" },
      { "internalType": "uint256", "name": "amount", "type": "uint256" }
    ],
    "name": "approve",
    "outputs": [{ "internalType": "bool", "name": "", "type": "bool" }],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      { "internalType": "address", "name": "account", "type": "address" }
    ],
    "name": "balanceOf",
    "outputs": [{ "internalType": "uint256", "name": "", "type": "uint256" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "botProtectionDurationInSeconds",
    "outputs": [{ "internalType": "uint256", "name": "", "type": "uint256" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      { "internalType": "uint256", "name": "value", "type": "uint256" }
    ],
    "name": "burn",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      { "internalType": "address", "name": "account", "type": "address" },
      { "internalType": "uint256", "name": "value", "type": "uint256" }
    ],
    "name": "burnFrom",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "decimals",
    "outputs": [{ "internalType": "uint8", "name": "", "type": "uint8" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      { "internalType": "address", "name": "spender", "type": "address" },
      {
        "internalType": "uint256",
        "name": "subtractedValue",
        "type": "uint256"
      }
    ],
    "name": "decreaseAllowance",
    "outputs": [{ "internalType": "bool", "name": "", "type": "bool" }],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "distributeTaxTokens",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "fundedDate",
    "outputs": [{ "internalType": "uint32", "name": "", "type": "uint32" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      { "internalType": "address", "name": "spender", "type": "address" },
      { "internalType": "uint256", "name": "addedValue", "type": "uint256" }
    ],
    "name": "increaseAllowance",
    "outputs": [{ "internalType": "bool", "name": "", "type": "bool" }],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address[3]",
        "name": "integrationAddresses_",
        "type": "address[3]"
      },
      { "internalType": "bytes", "name": "baseParams_", "type": "bytes" },
      { "internalType": "bytes", "name": "supplyParams_", "type": "bytes" },
      { "internalType": "bytes", "name": "taxParams_", "type": "bytes" }
    ],
    "name": "initialize",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      { "internalType": "address", "name": "queryAddress_", "type": "address" }
    ],
    "name": "isLiquidityPool",
    "outputs": [{ "internalType": "bool", "name": "", "type": "bool" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      { "internalType": "bytes32", "name": "queryHash_", "type": "bytes32" }
    ],
    "name": "isValidCaller",
    "outputs": [{ "internalType": "bool", "name": "", "type": "bool" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "liquidityPools",
    "outputs": [
      {
        "internalType": "address[]",
        "name": "liquidityPools_",
        "type": "address[]"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "name",
    "outputs": [{ "internalType": "string", "name": "", "type": "string" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "owner",
    "outputs": [{ "internalType": "address", "name": "", "type": "address" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "pairToken",
    "outputs": [{ "internalType": "address", "name": "", "type": "address" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "pendingOwner",
    "outputs": [{ "internalType": "address", "name": "", "type": "address" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "projectBuyTaxBasisPoints",
    "outputs": [{ "internalType": "uint16", "name": "", "type": "uint16" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "projectSellTaxBasisPoints",
    "outputs": [{ "internalType": "uint16", "name": "", "type": "uint16" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "projectTaxPendingSwap",
    "outputs": [{ "internalType": "uint128", "name": "", "type": "uint128" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "projectTaxRecipient",
    "outputs": [{ "internalType": "address", "name": "", "type": "address" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "removedLiquidityPool_",
        "type": "address"
      }
    ],
    "name": "removeLiquidityPool",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "bytes32",
        "name": "removedValidCallerHash_",
        "type": "bytes32"
      }
    ],
    "name": "removeValidCaller",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "renounceOwnership",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint16",
        "name": "newProjectBuyTaxBasisPoints_",
        "type": "uint16"
      },
      {
        "internalType": "uint16",
        "name": "newProjectSellTaxBasisPoints_",
        "type": "uint16"
      }
    ],
    "name": "setProjectTaxRates",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "projectTaxRecipient_",
        "type": "address"
      }
    ],
    "name": "setProjectTaxRecipient",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint16",
        "name": "swapThresholdBasisPoints_",
        "type": "uint16"
      }
    ],
    "name": "setSwapThresholdBasisPoints",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "swapThresholdBasisPoints",
    "outputs": [{ "internalType": "uint16", "name": "", "type": "uint16" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "symbol",
    "outputs": [{ "internalType": "string", "name": "", "type": "string" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "totalBuyTaxBasisPoints",
    "outputs": [{ "internalType": "uint256", "name": "", "type": "uint256" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "totalSellTaxBasisPoints",
    "outputs": [{ "internalType": "uint256", "name": "", "type": "uint256" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "totalSupply",
    "outputs": [{ "internalType": "uint256", "name": "", "type": "uint256" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      { "internalType": "address", "name": "to", "type": "address" },
      { "internalType": "uint256", "name": "amount", "type": "uint256" }
    ],
    "name": "transfer",
    "outputs": [{ "internalType": "bool", "name": "", "type": "bool" }],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      { "internalType": "address", "name": "from", "type": "address" },
      { "internalType": "address", "name": "to", "type": "address" },
      { "internalType": "uint256", "name": "amount", "type": "uint256" }
    ],
    "name": "transferFrom",
    "outputs": [{ "internalType": "bool", "name": "", "type": "bool" }],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      { "internalType": "address", "name": "newOwner", "type": "address" }
    ],
    "name": "transferOwnership",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "uniswapV2Pair",
    "outputs": [{ "internalType": "address", "name": "", "type": "address" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "validCallers",
    "outputs": [
      {
        "internalType": "bytes32[]",
        "name": "validCallerHashes_",
        "type": "bytes32[]"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "vault",
    "outputs": [{ "internalType": "address", "name": "", "type": "address" }],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      { "internalType": "address", "name": "token_", "type": "address" },
      { "internalType": "uint256", "name": "amount_", "type": "uint256" }
    ],
    "name": "withdrawERC20",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      { "internalType": "uint256", "name": "amount_", "type": "uint256" }
    ],
    "name": "withdrawETH",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  { "stateMutability": "payable", "type": "receive" }
]