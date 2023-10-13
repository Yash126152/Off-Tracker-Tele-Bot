from telegram import ReplyKeyboardMarkup

PlatoonOptions = [["ME Alpha"], ["ME Charlie"]]
PlatoonOptionsMarkup = ReplyKeyboardMarkup(
            PlatoonOptions, one_time_keyboard=True, resize_keyboard=True
        )
MemberCommandList = [
    ["View Offs \N{eyes}"],
    ["View Submitted Requests \U0001F4EB"],
    ["Request Off Date \U0001F64F"],
    ["FAQs \U0001f64b"],
]
MemberViewOptionsList = [
    ["View Pending Requests \U000023F3"],
    ["View Approved Requests \U0001F973"],
    ["View Rejected Requests \U0001F622"],
    ["View Cancelled Requests \U0000274C"],
    ["Back to Main Menu"],
]
RequestInfoList = [
    ["Off Date", "Off Duration"],
    ["Reason", "Approving Admin"],
    ["Submit \U0001F4E8"],
]
OffDuraList = [["AM Off", "PM Off"], ["Full Day Off"]]
AdminReqOptions = [["Approve \U00002705", "Reject \U0000274C"], ["Back"]]
MemberReqOptions = ["Cancel Request \U0000274C"], ["Back"]
ApprOfficerList = [["PC", "PS"], ["Other (Please Specify)"], ["Back"]]