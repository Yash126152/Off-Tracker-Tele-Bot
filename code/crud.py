import pygsheets, os
from datetime import datetime
from date_handling import get_date_claimed_list, is_expired, get_time_now

gc = pygsheets.authorize(service_file="cred/service_account_credentials.json")
sheet_map = {
    "A": os.environ.get("A_ID"),
    "C": os.environ.get("C_ID"),
}


def validLogin(plat, givenMNRIC, chatid=None):
    sh = gc.open_by_key(sheet_map[plat])
    info_wk = sh.worksheet_by_title("login_info")
    df = info_wk.get_as_df()
    if givenMNRIC in df["MASKED NRIC"].values:
        user_sn = df.loc[df["MASKED NRIC"] == givenMNRIC, "S/N"].iloc[0]
        user_name = df.loc[df["MASKED NRIC"] == givenMNRIC, "NAME"].iloc[0]
        if chatid:
            df.loc[df["S/N"] == user_sn, "CHAT ID"] = chatid
        info_wk.set_dataframe(df, (1, 1))
        return (user_sn, user_name)
    else:
        return None


def validAdminLogin(plat, givenMNRIC):
    sh = gc.open_by_key(sheet_map[plat])
    info_wk = sh.worksheet_by_title("login_info")
    df = info_wk.get_as_df()
    isAdmin = df.loc[df["MASKED NRIC"] == givenMNRIC, "ROLE"].iloc[0] == "A"
    if (admin_info := validLogin(plat, givenMNRIC)) and isAdmin:
        return admin_info


def getSNbyNAME(plat, givenName):
    sh = gc.open_by_key(sheet_map[plat])
    info_wk = sh.worksheet_by_title("login_info")
    df = info_wk.get_as_df()
    return df.loc[df["NAME"] == givenName, "S/N"].iloc[0]


def getName(plat, givenSN):
    sh = gc.open_by_key(sheet_map[plat])
    info_wk = sh.worksheet_by_title("login_info")
    df = info_wk.get_as_df()
    # print(df)
    return df.loc[df["S/N"] == givenSN, "NAME"].iloc[0]


def set_admin_chat_id(plat, givenSN, chatid):
    sh = gc.open_by_key(sheet_map[plat])
    info_wk = sh.worksheet_by_title("login_info")
    df = info_wk.get_as_df()
    admin_name = df.loc[df["S/N"] == givenSN, "NAME"].iloc[0]
    df.loc[df["S/N"] == givenSN, "CHAT ID"] = chatid
    info_wk.set_dataframe(df, (1, 1))
    return admin_name


def getAdmins(plat):
    sh = gc.open_by_key(sheet_map[plat])
    info_wk = sh.worksheet_by_title("login_info")
    df = info_wk.get_as_df()
    return df.loc[df["ROLE"] == "A", "NAME"].tolist()


def update_expiry(wk):
    df = wk.get_as_df()
    for index, row in df.iterrows():
        if (
            row["OFF STATUS"] == "Not Yet Claimed"
            or row["OFF STATUS"] == "Half Day Claimed"
        ):
            expr_date = row["OFF EXPIRE ON"]
            if is_expired(expr_date):
                df.at[index, "OFF STATUS"] = "Expired"
    wk.set_dataframe(df, (1, 1))


def get_offs_remaining(plat, givenSN):
    sh = gc.open_by_key(sheet_map[plat])
    update_expiry(sh.worksheet_by_title(getName(plat, givenSN)))
    info_wk = sh.worksheet_by_title("Platoon Overview")
    df = info_wk.get_as_df()
    return df.loc[df["S/N"] == givenSN, "Total Off Remaining"].iloc[0]


def get_offs_remaining_expiry(plat, givenSN):
    sh = gc.open_by_key(sheet_map[plat])
    wk = sh.worksheet_by_title(getName(plat, givenSN))
    df = wk.get_as_df()
    queriedDF = df.loc[
        (
            (df["OFF STATUS"] == "Not Yet Claimed")
            | (df["OFF STATUS"] == "Half Day Claimed")
        ),
        ["OFF STATUS", "OFF EXPIRE ON"],
    ]
    expiry_dates = queriedDF.set_index("OFF EXPIRE ON").to_dict()["OFF STATUS"].keys()
    sorted_exp_dates = sorted(expiry_dates, key=lambda x: datetime.strptime(x, "%d %B %Y"))
    ret_dict = {}
    for exp_date in sorted_exp_dates:
        off_count = len(queriedDF.loc[(df["OFF STATUS"] == "Not Yet Claimed") & (df["OFF EXPIRE ON"] == exp_date)])
        off_count += 0.5 * len(queriedDF.loc[(df["OFF STATUS"] == "Half Day Claimed") & (df["OFF EXPIRE ON"] == exp_date)])
        ret_dict[exp_date] = off_count

    return(ret_dict, sorted_exp_dates)

def get_wk_link(plat, givenSN):
    sh = gc.open_by_key(sheet_map[plat])
    wk = sh.worksheet_by_title(getName(plat, givenSN))
    return wk.url


def setNewRequest(plat, givenSN, date, date_count, duration, reason, admin):
    sh = gc.open_by_key(sheet_map[plat])
    rq_wk = sh.worksheet_by_title("requests")
    last_id = max([int(id) for id in rq_wk.get_col(1)[1:]])
    # REQUESTER S/N,NAME,OFF DATES,DURATION,REASON,STATUS,ADMIN S/N,APPROVING ADMIN,DATETIME OF REQUEST
    # values = (givenSN, getName(plat, givenSN), date, duration, reason, admin)
    values = {}
    values["REQUEST ID"] = str(last_id + 1)
    values["REQUESTER S/N"] = givenSN
    values["REQUESTER"] = getName(plat, givenSN)
    values["OFF DATES"] = date + ","
    values["NO. OFF DATES"] = date_count
    values["DURATION"] = duration.upper()
    values["REASON"] = reason
    values["STATUS"] = "PENDING"
    values["ADMIN S/N"] = getSNbyNAME(plat, admin)
    values["APPROVING ADMIN"] = admin
    values["DATETIME OF REQUEST"] = get_time_now().strftime("%d%m%y, %H:%M")
    values["LAST MODIFIED"] = get_time_now().strftime("%d%m%y, %H:%M")
    valueList = [str(x) for x in values.values()]
    rq_wk.insert_rows(1, values=valueList)


def getAdminPendingReqDict(plat, givenSN):
    sh = gc.open_by_key(sheet_map[plat])
    rq_wk = sh.worksheet_by_title("requests")
    df = rq_wk.get_as_df()
    queriedDF = df.loc[
        ((df["ADMIN S/N"] == givenSN) & (df["STATUS"] == "PENDING")),
        ["REQUEST ID", "REQUESTER", "OFF DATES", "DURATION"],
    ]
    retDict = {}
    for index, row in queriedDF.iterrows():
        reqStr = (
            f"{row['REQUESTER']} | {row['OFF DATES'].rstrip(',')} | {row['DURATION']}"
        )
        retDict[row["REQUEST ID"]] = reqStr
    return retDict


def getMemberReqDict(plat, givenSN, status):
    sh = gc.open_by_key(sheet_map[plat])
    rq_wk = sh.worksheet_by_title("requests")
    df = rq_wk.get_as_df()
    queriedDF = df.loc[
        ((df["REQUESTER S/N"] == givenSN) & (df["STATUS"] == status)),
        ["REQUEST ID", "OFF DATES", "DURATION"],
    ]
    retDict = {}
    for index, row in queriedDF.iterrows():
        reqStr = f"{row['OFF DATES'].rstrip(',')} | {row['DURATION']}"
        retDict[row["REQUEST ID"]] = reqStr
    return retDict


def getReqInfo(plat, req_id):
    sh = gc.open_by_key(sheet_map[plat])
    rq_wk = sh.worksheet_by_title("requests")
    df = rq_wk.get_as_df()
    return df.loc[(df["REQUEST ID"] == req_id)].iloc[0]


def check_off_count_for_approval(plat, req_id):
    sh = gc.open_by_key(sheet_map[plat])
    rq_wk = sh.worksheet_by_title("requests")
    df = rq_wk.get_as_df()
    # Retrieving Info
    requester_sn = df.loc[(df["REQUEST ID"] == req_id), "REQUESTER S/N"].iloc[0]
    date_count = df.loc[(df["REQUEST ID"] == req_id), "NO. OFF DATES"].iloc[0]
    duration = df.loc[(df["REQUEST ID"] == req_id), "DURATION"].iloc[0]

    offs_remaning = get_offs_remaining(plat, requester_sn)
    offs_needed = date_count if (duration == "Full Day Off") else date_count * 0.5
    return (offs_remaning, offs_needed)


def approve_req(plat, req_id, appr_officer):
    sh = gc.open_by_key(sheet_map[plat])
    rq_wk = sh.worksheet_by_title("requests")
    df = rq_wk.get_as_df()
    # Get req info
    requester = df.loc[(df["REQUEST ID"] == req_id), "REQUESTER"].iloc[0]
    off_dates = df.loc[(df["REQUEST ID"] == req_id), "OFF DATES"].iloc[0]
    duration = df.loc[(df["REQUEST ID"] == req_id), "DURATION"].iloc[0]
    # Set to APPROVED
    df.loc[(df["REQUEST ID"] == req_id), "STATUS"] = "APPROVED"
    df.loc[(df["REQUEST ID"] == req_id), "LAST MODIFIED"] = get_time_now().strftime(
        "%d%m%y, %H:%M"
    )
    rq_wk.set_dataframe(df, (1, 1))
    # Deduct off in personnel sheet
    date_claimed_list = get_date_claimed_list(off_dates, duration)
    update_approval(
        wk=sh.worksheet_by_title(requester),
        date_claimed_list=date_claimed_list,
        appr_officer=appr_officer,
    )


def update_approval(wk, date_claimed_list, appr_officer):
    df = wk.get_as_df()
    for date_claimed in date_claimed_list:
        expiry_date_list = df.loc[
            (
                (df["OFF STATUS"] == "Not Yet Claimed")
                | (df["OFF STATUS"] == "Half Day Claimed")
            )
        ]["OFF EXPIRE ON"].tolist()
        earliest_expiry_date = min(
            expiry_date_list, key=lambda x: datetime.strptime(x, "%d %B %Y")
        )
        res_index = df.loc[
            (df["OFF EXPIRE ON"] == earliest_expiry_date) &
            (df["OFF STATUS"] != "Claimed")
        ].first_valid_index()
        if df.iloc[res_index]["OFF STATUS"] == "Half Day Claimed":
            df.at[res_index, "OFF STATUS"] = "Claimed"
            df.at[res_index, "SECOND HALF CLAIMED ON"] = date_claimed
            df.at[res_index, "SECOND HALF AUTH BY"] = appr_officer
        else:
            df.at[res_index, "OFF STATUS"] = "Half Day Claimed"
            df.at[res_index, "FIRST HALF CLAIMED ON"] = date_claimed
            df.at[res_index, "FIRST HALF AUTH BY"] = appr_officer
    wk.set_dataframe(df, (1, 1))


def reject_req(plat, req_id):
    sh = gc.open_by_key(sheet_map[plat])
    rq_wk = sh.worksheet_by_title("requests")
    df = rq_wk.get_as_df()
    df.loc[(df["REQUEST ID"] == req_id), "STATUS"] = "REJECTED"
    df.loc[(df["REQUEST ID"] == req_id), "LAST MODIFIED"] = get_time_now().strftime(
        "%d%m%y, %H:%M"
    )
    rq_wk.set_dataframe(df, (1, 1))


def cancel_req(plat, req_id):
    sh = gc.open_by_key(sheet_map[plat])
    rq_wk = sh.worksheet_by_title("requests")
    df = rq_wk.get_as_df()
    df.loc[(df["REQUEST ID"] == req_id), "STATUS"] = "CANCELLED"
    df.loc[(df["REQUEST ID"] == req_id), "LAST MODIFIED"] = get_time_now().strftime(
        "%d%m%y, %H:%M"
    )
    rq_wk.set_dataframe(df, (1, 1))


def get_requester_chat_id(plat, req_id):
    sh = gc.open_by_key(sheet_map[plat])
    rq_wk = sh.worksheet_by_title("requests")
    df = rq_wk.get_as_df()
    requester_sn = df.loc[(df["REQUEST ID"] == req_id), "REQUESTER S/N"].iloc[0]
    info_wk = sh.worksheet_by_title("login_info")
    df = info_wk.get_as_df()
    return int(df.loc[df["S/N"] == requester_sn, "CHAT ID"].iloc[0])


def get_req_admin_chat_id(plat, req_id):
    sh = gc.open_by_key(sheet_map[plat])
    rq_wk = sh.worksheet_by_title("requests")
    df = rq_wk.get_as_df()
    admin_name = df.loc[(df["REQUEST ID"] == req_id), "APPROVING ADMIN"].iloc[0]
    return get_admin_chat_id(plat, admin_name)


def get_admin_chat_id(plat, admin_name):
    sh = gc.open_by_key(sheet_map[plat])
    info_wk = sh.worksheet_by_title("login_info")
    df = info_wk.get_as_df()
    return int(df.loc[df["NAME"] == admin_name, "CHAT ID"].iloc[0])
