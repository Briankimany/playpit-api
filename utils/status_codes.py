from enum import Enum


class BatchRequestStatus(Enum):
    BP101 = "BP101", "New batch or request, reading in progress"
    BF102 = "BF102", "Batch/request failed"
    BP103 = "BP103", "Batch/request waiting approval"
    BP104 = "BP104", "Queued to check for float balance"
    BF105 = "BF105", "Failed checking float balance"
    BP106 = "BP106", "Float/balance check in progress"
    BF107 = "BF107", "Failed advance float check issue"
    BP108 = "BP108", "Advance internal validations in progress"
    BP109 = "BP109", "Payment to beneficiary in progress"
    BP110 = "BP110", "Sending payments to beneficiary in progress"
    BC100 = "BC100", "Completed sending all transactions. Results ready for review"
    BE111 = "BE111", "Batch/request ended or cancelled early"

    def __str__(self):
        return f"{self.name} - {self.value[1]}"


class TransactionStatus(Enum):
    TP101 = "TP101", "New transaction. Processing is pending"
    TP102 = "TP102", "Transaction processing started"
    TF103 = "TF103", "Failed to initiate or process transaction. Check failed reason for more details"
    TF104 = "TF104", "Transaction results processing in progress"
    TF105 = "TF105", "Transaction status cannot be determined. Contact support for further check."
    TS100 = "TS100", "Transaction is successful"
    TF106 = "TF106", "Transaction failed, see failed reasons for more details"
    TH107 = "TH107", "Transaction is under observation"
    TC108 = "TC108", "Transaction canceled"
    TR109 = "TR109", "Transaction is queued for retry"

    def __str__(self):
        return f"{self.name} - {self.value[1]}"
