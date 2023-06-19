def handle_close_code(code):
    match code:
        case 1000:
            status = "Normal closure"
        case 1001:
            status = "Going away"
        case 1002:
            status = "Protocol error"
        case 1003:
            status = "Unsupported data"
        case 1004:
            status = "Reserved"
        case 1005:
            status = "No status"
        case 1006:
            status = "Abnormal closure"
        case 1007:
            status = "Unsupported payload"
        case 1008:
            status = "Policy violation"
        case 1009:
            status = "Message too big"
        case 1010:
            status = "Mandatory extension"
        case 1011:
            status = "Server error"
        case 1012:
            status = "Service restart"
        case 1013:
            status = "Try again later"
        case 1014:
            status = "Bad gateway"
        case 1015:
            status = "TLS handshake fail"
        case _:
            status = f"Unknown close code: {code} or no status = code"
    return status
