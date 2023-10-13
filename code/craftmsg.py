import crud
from date_handling import is_valid_date
from telegram import ReplyKeyboardMarkup


def get_multi_date_string(given_dates):
    date_string = ""
    error_msg = "Error, invalid dates given"
    date_count = 0
    date_grps = str(given_dates.rstrip(",")).split(",")
    for date_grp in date_grps:
        dates = date_grp.split("-")
        if len(dates) > 1:
            start_date = is_valid_date(dates[0])
            end_date = is_valid_date(dates[-1])
            if start_date and end_date and end_date > start_date:
                if date_string:
                    date_string += f",\n{start_date.strftime('%d %b %Y %a')} \- {end_date.strftime('%d %b %Y %a')}"
                else:
                    date_string += f"{start_date.strftime('%d %b %Y %a')} \- {end_date.strftime('%d %b %Y %a')}"
                date_count += (end_date - start_date).days + 1
            else:
                return error_msg
        else:
            if cur_date := is_valid_date(date_grp):
                if date_string:
                    date_string += f",\n{cur_date.strftime('%d %b %Y %a')}"
                else:
                    date_string += f"{cur_date.strftime('%d %b %Y %a')}"
                date_count += 1
            else:
                return error_msg
    return (date_string, date_count)


def MarkdownParser(given_string):
    ESCAPE_CHAR_LIST = [
        "_",
        "*",
        "[",
        "]",
        "(",
        ")",
        "~",
        "`",
        ">",
        "#",
        "+",
        "-",
        "=",
        "|",
        "{",
        "}",
        ".",
        "!",
    ]
    for char in ESCAPE_CHAR_LIST:
        given_string = given_string.replace(char, f"\{char}")
    return given_string


def request_msg(dates, duration, reason, admin):
    if dates:
        dates_str, date_count = get_multi_date_string(dates)
    else:
        dates_str = date_count = ""
    msg = (
        "__*REQUEST INFO*__\n"
        f"_Date of Off\(s\):_ {dates_str}\n"
        f"_No\. Dates Off:_ {date_count}\n"
        f"_Duration of Off\(s\):_ {duration}\n"
        f"_Reason for Off\(s\):_ {MarkdownParser(reason)}\n"
        f"_Approving Admin:_ {admin}\n\n"
        "Please select an option to add/edit info\. Use \/cancel to return to the main menu\.\n"
        "Ensure all info is accurate before submitting\."
    )
    return msg


def OffDurationExplanation():
    msg = (
        "_Note about half days_\n"
        "For AM Offs you book out the day before after last parade and book in at 1300\.\n"
        "For PM Offs you book out at 1300 and book in at 2215\."
    )
    return msg


def getReqListMarkup(req_dict, back_button=True):
    ViewReqList = [[req_dict[key]] for key in req_dict]
    ViewReqList.append(["Refresh \U0001F503"])
    if back_button:
        ViewReqList.append(["Back"])
    return ReplyKeyboardMarkup(
        ViewReqList, one_time_keyboard=True, resize_keyboard=True
    )


def ViewReq(plat, req_id):
    #'REQUESTER','OFF DATES','DURATION','REASON','DATETIME OF REQUEST'
    req_info = crud.getReqInfo(plat, req_id)
    dates_str, date_count = get_multi_date_string(req_info["OFF DATES"])
    status = req_info["STATUS"]
    msg = (
        "__*REQUEST INFO*__\n"
        f"_Requester:_ {req_info['REQUESTER']}\n"
        f"_Date of Off\(s\):_ {dates_str}\n"
        f"_No\. Off Date\(s\):_ {date_count}\n"
        f"_Duration of Off\(s\):_ {req_info['DURATION']}\n"
        f"_Reason for Off\(s\):_ {MarkdownParser(req_info['REASON'])}\n"
        f"_Request submitted on {req_info['DATETIME OF REQUEST']}_\n"
    )
    if status == "PENDING":
        msg += "_Request still pending approval_\n\n"
    elif status == "CANCELLED":
        msg += f"_Request was cancelled by {req_info['REQUESTER']} on {req_info['LAST MODIFIED']}_\n\n"
    else:
        msg += f"_Request was {status.lower()} by {req_info['APPROVING ADMIN']} on {req_info['LAST MODIFIED']}_\n\n"
    return msg


def ReqSubmissionNotif(admin, requester, req_dur, req_date, date_count):
    msg = (
        "*OFF REQUEST*\n"
        f"Hi {admin}, {requester} has submitted a request for {date_count} {req_dur}\(s\) for the following date\(s\)\:\n"
        f"{get_multi_date_string(req_date)[0]}"
        "\n_Please login to view the full request and approve/reject it\._"
    )
    return msg


def ReqCancelNotif(plat, req_id):
    req_info = crud.getReqInfo(plat, req_id)
    dates_str, date_count = get_multi_date_string(req_info["OFF DATES"])
    msg = (
        "*REQUEST CANCELLED*\n"
        f"Hi {req_info['APPROVING ADMIN']}, {req_info['REQUESTER']}'s request to take"
        f"{date_count} {req_info['DURATION'].lower()}\(s\) on {dates_str} "
    )
    if date_count > 1:
        msg += f":\n\n{dates_str}\n\n"
    else:
        msg += f" {dates_str} "
    msg += "has been cancelled\."
    return msg


def ApprovalNotif(plat, req_id):
    req_info = crud.getReqInfo(plat, req_id)
    dates_str, date_count = get_multi_date_string(req_info["OFF DATES"])
    msg = (
        "*REQUEST APPROVED*\n"
        f"Hi {req_info['REQUESTER']}, your request to take {date_count} {req_info['DURATION'].lower()}\(s\) on"
    )
    if date_count > 1:
        msg += f":\n\n{dates_str}\n\n"
    else:
        msg += f" {dates_str} "
    msg += "has been approved\. Enjoy your off\(s\)\!"
    return msg


def RejectionNotif(plat, req_id, reason):
    req_info = crud.getReqInfo(plat, req_id)
    dates_str, date_count = get_multi_date_string(req_info["OFF DATES"])
    msg = (
        "*REQUEST REJECTED*\n"
        f"Hi {req_info['REQUESTER']}, your request to take {date_count} {req_info['DURATION'].lower()}\(s\) on"
    )
    if date_count > 1:
        msg += f":\n\n{dates_str}\n\n"
    else:
        msg += f" {dates_str} "
    msg += (
        "has been rejected\.\n\n"
        f"_Reason: {MarkdownParser(reason)}_"
    )
    return msg


def MemberViewReqListMsg(num_req, status):
    msg = (
        f"You have {num_req} {status.lower()} requests. "
        "Select one to view it in detail"
    )
    if status == "PENDING":
        msg += " or cancel it"
    msg += "."
    return msg
