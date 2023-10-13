import logging, os, html, traceback, json
from datetime import date
from telegram import Update, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)

import crud, craftmsg, date_handling
from constants import (
    PlatoonOptions, 
    PlatoonOptionsMarkup, 
    MemberCommandList, 
    MemberViewOptionsList,
    RequestInfoList,
    OffDuraList,
    AdminReqOptions,
    MemberReqOptions,
    ApprOfficerList
)

# GET DEVELOPMENT CONSTANTS
#TEST_TOKEN = "5674753016:AAEJnzteWiu7OURrikxrJwEOH9wDe-wgPbA"

# DEPLOYMNET CONSTANTS
TOKEN = os.environ.get("TOKEN")
PORT = int(os.environ.get("PORT", 443))
WEBHOST = os.environ.get("WEBHOST")
ADMIN_PW = os.environ.get("ADMIN_PW","test_pw")
DEV_CHAT_ID = os.environ.get("DEV_CHAT_ID","1234")

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

PLATOON_SELECT, LOGIN, MEMBER_MENU = range(3)  # Member Login and Menu
REQ_DISPLAY, REQ_MENU = range(3, 5)  # Member Request Func
(
    ADMIN_LOGIN,
    ADMIN_REQ_VIEW,
    ADMIN_APP_REJ,
    ADMIN_APPR_OFFICER,
    ADMIN_REJ_REASON,
) = range(5, 10)  # Admin Login and M
VIEW_FAQS = 10
MEMBER_VIEW_OPTIONS, MEMBER_REQ_VIEW, MEMBER_REQ_OPTIONS, MEMBER_CANCEL_CONFIRM = range(11, 15)

MEMBER_MENU_REPLY_MARKUP = ReplyKeyboardMarkup(
    MemberCommandList, one_time_keyboard=True, resize_keyboard=True
)
REQUEST_MENU_REPLY_MARKUP = ReplyKeyboardMarkup(
    RequestInfoList, one_time_keyboard=True, resize_keyboard=True
)
MEMBER_VIEW_OPTIONS_MARKUP = ReplyKeyboardMarkup(
    MemberViewOptionsList, one_time_keyboard=True, resize_keyboard=True
)
DURA_LIST_REPLY_MARKUP = ReplyKeyboardMarkup(
    OffDuraList, one_time_keyboard=True, resize_keyboard=True
)
APPROVE_REJECT_REPLY_MARKUP = ReplyKeyboardMarkup(
    AdminReqOptions, one_time_keyboard=True, resize_keyboard=True
)
CANCEL_REQ_REPLY_MARKUP = ReplyKeyboardMarkup(
    MemberReqOptions, one_time_keyboard=True, resize_keyboard=True
)
APPR_OFFICER_REPLY_MARKUP = ReplyKeyboardMarkup(
    ApprOfficerList, one_time_keyboard=True, resize_keyboard=True
)


class ReqCodes:
    REQ_DATE, REQ_DURA, REQ_REASON, REQ_ADMIN = range(1, 5)


class ReqStatusCodes:
    MemberViewOptions = [
        "View Pending Requests \U000023F3",
        "View Approved Requests \U0001F973",
        "View Rejected Requests \U0001F622",
        "View Cancelled Requests \U0000274C",
    ]
    STATUSES = ["PENDING", "APPROVED", "REJECTED", "CANCELLED"]
    option_status_map = {
        option: status for option, status in zip(MemberViewOptions, STATUSES)
    }


class FAQs:
    def __init__(self, faq_set=None):
        if faq_set:
            self.faq_dict = {}
            self.q_list = []
            size = len(faq_set) // 2
            for i in range(1, 1 + size):
                self.faq_dict[faq_set[f"Q{i}"]] = faq_set[f"A{i}"]
                self.q_list.append([faq_set[f"Q{i}"]])
            self.q_list.append(["Back"])
        else:
            return None


class Reset:
    def req_data(context: ContextTypes.DEFAULT_TYPE):
        context.chat_data["req_date"] = ""
        context.chat_data["req_dur"] = ""
        context.chat_data["req_reason"] = ""
        context.chat_data["req_admin"] = ""
        context.chat_data["prev_state"] = 0

    def member_view_req_data(context: ContextTypes.DEFAULT_TYPE):
        context.chat_data["member_view_req_status"] = None
        context.chat_data["member_view_req_dict"] = None

    def user_data(context: ContextTypes.DEFAULT_TYPE):
        context.chat_data.clear()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    Reset.user_data(context)
    context.chat_data["is_admin"] = "Not Logged In"
    context.chat_data["admin_view_req_dict"] = None
    msg = "Welcome to ME Coy Off Tracker!\nPlease select your platoon."
    PlatoonOptionsMarkup = ReplyKeyboardMarkup(
        PlatoonOptions, one_time_keyboard=True, resize_keyboard=True
    )
    await update.message.reply_text(msg, reply_markup=PlatoonOptionsMarkup)
    return PLATOON_SELECT


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "is_admin" in context.chat_data:
        if context.chat_data["is_admin"] == "Not Logged In":
            msg = "There's nothing to cancel.\n Please select your platoon to login."
            await update.message.reply_text(msg, reply_markup=PlatoonOptionsMarkup)
            return PLATOON_SELECT
        elif context.chat_data["is_admin"]:
            msg = "Returning to list of pending offs...\n\n"
            if context.chat_data["admin_view_req_dict"]:
                num_req = len(context.chat_data["admin_view_req_dict"])
                msg += f"You have {num_req} pending request(s). Select one to view it in detail, approve or reject it."
                admin_req_list_reply_markup = craftmsg.getReqListMarkup(
                    req_dict=context.chat_data["admin_view_req_dict"], 
                    back_button=False
                )
                await update.message.reply_text(msg, reply_markup=admin_req_list_reply_markup)
                return ADMIN_REQ_VIEW
            else:
                msg += "You have no pending requests. Logging out... Have a break, Have a kitkat \U0001F36B"
                await update.message.reply_text(msg)
                return PLATOON_SELECT
        else:
            Reset.req_data(context)
            Reset.member_view_req_data(context=context)
            await update.message.reply_text(
                "Cancelled. Returning to main menu", reply_markup=MEMBER_MENU_REPLY_MARKUP
            )
            return MEMBER_MENU
    else:
        await update.message.reply_text("The bot encountered some difficulties. Need to semula.")
        Reset.user_data(context)
        context.chat_data["is_admin"] = "Not Logged In"
        context.chat_data["admin_view_req_dict"] = None
        msg = "Welcome to ME Coy Off Tracker!\nPlease select your platoon."
        await update.message.reply_text(msg, reply_markup=PlatoonOptionsMarkup)
        return PLATOON_SELECT

async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "is_admin" in context.chat_data:
        await update.message.reply_text("Waking the bot up...")
        if context.chat_data["is_admin"] == "Not Logged In":
            await update.message.reply_text("Refreshing login function...")
            msg = "Bot just woke up. It'll sign 7 extras later \U0001F622\nPlease select your platoon to login."
            await update.message.reply_text(msg, reply_markup=PlatoonOptionsMarkup)
            return PLATOON_SELECT
        elif context.chat_data["is_admin"]:
            await update.message.reply_text("Refreshing to pending offs list...")
            msg = "Bot just woke up. It'll sign 7 extras later \U0001F622\n\n"
            if context.chat_data["admin_view_req_dict"]:
                num_req = len(context.chat_data["admin_view_req_dict"])
                msg += f"You have {num_req} pending request(s). Select one to view it in detail, approve or reject it."
                admin_req_list_reply_markup = craftmsg.getReqListMarkup(
                    req_dict=context.chat_data["admin_view_req_dict"], 
                    back_button=False
                )
                await update.message.reply_text(msg, reply_markup=admin_req_list_reply_markup)
                return ADMIN_REQ_VIEW
            else:
                msg += "You have no pending requests. Logging out... Have a break, Have a kitkat \U0001F36B"
                await update.message.reply_text(msg)
                return PLATOON_SELECT
        else:
            await update.message.reply_text("Refreshing to main menu...")
            msg = "Bot just woke up. It'll sign 7 extras later \U0001F622\n\nPlease select an option."
            Reset.req_data(context)
            await update.message.reply_text(msg, reply_markup=MEMBER_MENU_REPLY_MARKUP)
            return MEMBER_MENU
    else:
        await update.message.reply_text("The bot encountered some difficulties. Need to semula.")
        Reset.user_data(context)
        context.chat_data["is_admin"] = "Not Logged In"
        context.chat_data["admin_view_req_dict"] = None
        msg = "Welcome to ME Coy Off Tracker!\nPlease select your platoon."
        await update.message.reply_text(msg, reply_markup=PlatoonOptionsMarkup)
        return PLATOON_SELECT


async def platoon_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if [update.message.text] in PlatoonOptions:
        context.chat_data["plat"] = update.message.text[3]
        msg = f"{update.message.text} selected.\nPlease enter your masked NRIC."
        await update.message.reply_text(msg)
        return LOGIN
    else:
        msg = f"Not a valid option.\n Please try again."
        await update.message.reply_text(msg, reply_markup=PlatoonOptionsMarkup)
        return PLATOON_SELECT


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Verifying...")
    if update.message.text[0] == "A":
        givenMNRIC = update.message.text.lstrip("A")
        if user_info := crud.validAdminLogin(context.chat_data["plat"], givenMNRIC):
            # Saving Chat Data
            context.chat_data["is_admin"] = True
            context.chat_data["mnric"] = givenMNRIC
            context.chat_data["S/N"] = user_info[0]
            await update.message.reply_text("Please enter the admin password.")
            return ADMIN_LOGIN
        else:
            await update.message.reply_text(
                "No admin with the given masked NRIC was found. Please try again."
            )
            return LOGIN
    elif user_info := crud.validLogin(
        context.chat_data["plat"], update.message.text, context._chat_id
    ):
        # Saving Chat Data
        context.chat_data["is_admin"] = False
        context.chat_data["mnric"] = update.message.text
        context.chat_data["S/N"], name = user_info
        # Menu Options
        msg = f"Logged in as {name}. What would you like to do?"
        await update.message.reply_text(msg, reply_markup=MEMBER_MENU_REPLY_MARKUP)
        return MEMBER_MENU
    else:
        msg = "No personnel with the given masked NRIC was found. Please try again."
        await update.message.reply_text(msg)
        return LOGIN


async def admin_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.text == ADMIN_PW:
        await update.message.reply_text("Checking to see if you're capping...")
        # Getting name and saving chatid in sheet
        name = crud.set_admin_chat_id(
            context.chat_data["plat"], context.chat_data["S/N"], context._chat_id
        )
        # Show List of Pending Requests
        msg = f"Logged in as ADMIN {name}\n"

        # Getting Pending Off Info
        context.chat_data["admin_view_req_dict"] = crud.getAdminPendingReqDict(
            context.chat_data["plat"], context.chat_data["S/N"]
        )
        if context.chat_data["admin_view_req_dict"]:
            num_req = len(context.chat_data["admin_view_req_dict"])
            msg += f"You have {num_req} pending request(s). Select one to view it in detail, approve or reject it."
            admin_req_list_reply_markup = craftmsg.getReqListMarkup(
                req_dict=context.chat_data["admin_view_req_dict"], 
                back_button=False
            )
            await update.message.reply_text(msg, reply_markup=admin_req_list_reply_markup)
            return ADMIN_REQ_VIEW
        else:
            msg += "You have no pending requests. Logging out... Have a break, Have a kitkat \U0001F36B"
            await update.message.reply_text(msg)
            return PLATOON_SELECT
    else:
        msg = f"Access Denied. Enter your Masked NRIC again."
        await update.message.reply_text(msg)
        return LOGIN


async def view_offs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Retrieving your off information...")
    offs_remaining = crud.get_offs_remaining(
        context.chat_data["plat"], context.chat_data["S/N"]
    )

    msg = f"You have {offs_remaining} off(s) remaning.\n"
    if offs_remaining > 0:
        msg += "Here's a brief breakdown:\n\n"
        off_expiry_dict, exp_date_list = crud.get_offs_remaining_expiry(context.chat_data["plat"], context.chat_data["S/N"])
        for expiry_date in exp_date_list:
            msg += f"{off_expiry_dict[expiry_date]} off(s) expiring on {expiry_date}\n"
    msg += (
        f"\nFor a more detailed look, access your sheet at this link: "
        f"{crud.get_wk_link(context.chat_data['plat'],context.chat_data['S/N'])}"
    )
    await update.message.reply_text(msg, reply_markup=MEMBER_MENU_REPLY_MARKUP)
    return MEMBER_MENU


async def view_faqs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    faq_dict = FAQs(faq_set=json.load(open("faq.json"))).faq_dict
    q_list = FAQs(faq_set=json.load(open("faq.json"))).q_list
    if user_input in faq_dict:
        msg = faq_dict[user_input]
    else:
        match user_input:
            case "FAQs \U0001f64b":
                msg = "Please select a question to view it's answer\."
            case "Back":
                msg = "Returning to main menu..."
                await update.message.reply_text(
                    msg, reply_markup=MEMBER_MENU_REPLY_MARKUP
                )
                return MEMBER_MENU
            case _:
                msg = "Not a valid option\."

    FAQ_REPLY_MARKUP = ReplyKeyboardMarkup(
        q_list, one_time_keyboard=True, resize_keyboard=True
    )
    await update.message.reply_text(
        msg, reply_markup=FAQ_REPLY_MARKUP, parse_mode="MarkdownV2"
    )
    return VIEW_FAQS


async def show_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    prev_state = (
        context.chat_data["prev_state"] if "prev_state" in context.chat_data else 0
    )
    match prev_state:
        case ReqCodes.REQ_DATE:
            if date_handling.is_valid_dates(update.message.text):
                context.chat_data["req_date"] = date_handling.reorder_date_string(
                    update.message.text
                )
            else:
                msg = f"'{update.message.text}' is an invalid date. Please try again using the correct format."
                await update.message.reply_text(msg)
                return REQ_DISPLAY
        case ReqCodes.REQ_DURA:
            if ([update.message.text] in OffDuraList) or (
                update.message.text in OffDuraList[0]
            ):
                context.chat_data["req_dur"] = update.message.text
            else:
                msg = f"'{update.message.text}' is an invalid option. Please try again."
                await update.message.reply_text(
                    msg, reply_markup=DURA_LIST_REPLY_MARKUP
                )
                return REQ_DISPLAY
        case ReqCodes.REQ_REASON:
            context.chat_data["req_reason"] = update.message.text
        case ReqCodes.REQ_ADMIN:
            if update.message.text in crud.getAdmins(context.chat_data["plat"]):
                context.chat_data["req_admin"] = update.message.text
            else:
                msg = f"'{update.message.text}' is an invalid option. Please try again."
                AdminList = [
                    [admin] for admin in crud.getAdmins(context.chat_data["plat"])
                ]
                AdminListReplyMarkup = ReplyKeyboardMarkup(
                    AdminList, one_time_keyboard=True, resize_keyboard=True
                )
                await update.message.reply_text(msg, reply_markup=AdminListReplyMarkup)
                return REQ_DISPLAY

    req_date = context.chat_data["req_date"] if "req_date" in context.chat_data else ""
    req_dur = context.chat_data["req_dur"] if "req_dur" in context.chat_data else ""
    req_reason = (
        context.chat_data["req_reason"] if "req_reason" in context.chat_data else ""
    )
    req_admin = (
        context.chat_data["req_admin"] if "req_admin" in context.chat_data else ""
    )

    msg = craftmsg.request_msg(
        dates=req_date, duration=req_dur, reason=req_reason, admin=req_admin
    )
    await update.message.reply_text(
        msg, reply_markup=REQUEST_MENU_REPLY_MARKUP, parse_mode="MarkdownV2"
    )
    return REQ_MENU


async def edit_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text
    match choice:
        case "Off Date":
            msg = f"Enter the date in DDMMYY format. For example, today's date would be {date.today().strftime('%d%m%y')}"
            context.chat_data["prev_state"] = ReqCodes.REQ_DATE
            await update.message.reply_text(msg)
            return REQ_DISPLAY
        case "Off Duration":
            msg = "Please select the off duration\.\n\n"
            msg += craftmsg.OffDurationExplanation()
            context.chat_data["prev_state"] = ReqCodes.REQ_DURA
            await update.message.reply_text(
                msg, reply_markup=DURA_LIST_REPLY_MARKUP, parse_mode="MarkdownV2"
            )
            return REQ_DISPLAY
        case "Reason":
            msg = f"Please enter the reason why you wish to take the off."
            context.chat_data["prev_state"] = ReqCodes.REQ_REASON
            await update.message.reply_text(msg)
            return REQ_DISPLAY
        case "Approving Admin":
            await update.message.reply_text(
                "Checking which commanders are not skiving..."
            )
            msg = f"Please select the Approving Admin."
            context.chat_data["prev_state"] = ReqCodes.REQ_ADMIN
            AdminList = [[admin] for admin in crud.getAdmins(context.chat_data["plat"])]
            AdminListReplyMarkup = ReplyKeyboardMarkup(
                AdminList, one_time_keyboard=True, resize_keyboard=True
            )
            await update.message.reply_text(msg, reply_markup=AdminListReplyMarkup)
            return REQ_DISPLAY
        case "Submit \U0001F4E8":
            req_date = (
                context.chat_data["req_date"] if "req_date" in context.chat_data else ""
            )
            req_dur = (
                context.chat_data["req_dur"] if "req_dur" in context.chat_data else ""
            )
            req_reason = (
                context.chat_data["req_reason"]
                if "req_reason" in context.chat_data
                else ""
            )
            req_admin = (
                context.chat_data["req_admin"]
                if "req_admin" in context.chat_data
                else ""
            )
            requestIsComplete = not ("" in (req_date, req_dur, req_reason, req_admin))

            if requestIsComplete:
                await update.message.reply_text("Checking if you have enough offs...")
                # Check if got enough offs remaining to satisfy request
                offs_remaining = crud.get_offs_remaining(
                    context.chat_data["plat"], context.chat_data["S/N"]
                )
                date_count = date_handling.is_valid_dates(req_date)
                offs_needed = (
                    date_count if (req_dur == "Full Day Off") else date_count * 0.5
                )
                if offs_needed > offs_remaining:
                    msg = f"Bruh how are ya going to take {date_count} {req_dur}(s) when you only got {offs_remaining} off(s) left???"
                    await update.message.reply_text(msg)

                    req_msg = craftmsg.request_msg(
                        dates=req_date,
                        duration=req_dur,
                        reason=req_reason,
                        admin=req_admin,
                    )
                    await update.message.reply_text(
                        req_msg,
                        reply_markup=REQUEST_MENU_REPLY_MARKUP,
                        parse_mode="MarkdownV2",
                    )
                    return REQ_MENU
                else:
                    await update.message.reply_text("Submitting your request...")
                    crud.setNewRequest(
                        plat=context.chat_data["plat"],
                        givenSN=context.chat_data["S/N"],
                        date=req_date,
                        date_count=date_count,
                        duration=req_dur,
                        reason=req_reason,
                        admin=req_admin,
                    )
                    # Notify Admin
                    admin_id = crud.get_admin_chat_id(
                        context.chat_data["plat"], req_admin
                    )
                    if admin_id != "":
                        requester = crud.getName(
                            context.chat_data["plat"], context.chat_data["S/N"]
                        )
                        admin_msg = craftmsg.ReqSubmissionNotif(
                            req_admin, requester, req_dur, req_date, date_count
                        )
                        await context.bot.send_message(
                            chat_id=admin_id, text=admin_msg, parse_mode="MarkdownV2"
                        )
                    Reset.req_data(context)

                    await update.message.reply_text(
                        "Your off request has been successfully submitted!"
                    )
                    await update.message.reply_text(
                        "Heading back to the main menu...",
                        reply_markup=MEMBER_MENU_REPLY_MARKUP,
                    )
                    return MEMBER_MENU
            else:
                msg = "One or more of the fields have been left empty. Please fill up all the info before submitting."
                await update.message.reply_text(
                    msg, reply_markup=REQUEST_MENU_REPLY_MARKUP
                )
                return REQ_MENU
        case _:
            msg = "Invalid Option. Please try again."
            await update.message.reply_text(msg, reply_markup=REQUEST_MENU_REPLY_MARKUP)
            return REQ_MENU


async def member_view_options(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    user_input = update.message.text
    context.chat_data["member_view_req_status"] = (
        ReqStatusCodes.option_status_map[user_input]
        if user_input in ReqStatusCodes.option_status_map
        else None
    )
    if user_input == "View Submitted Requests \U0001F4EB":
        Reset.member_view_req_data(context=context)
        msg = "Please select what kind of request you wish to view."
        await update.message.reply_text(msg, reply_markup=MEMBER_VIEW_OPTIONS_MARKUP)
        return MEMBER_VIEW_OPTIONS
    elif user_input == "Back to Main Menu":
        Reset.member_view_req_data(context=context)
        await update.message.reply_text(
            "Heading back to the main menu...", reply_markup=MEMBER_MENU_REPLY_MARKUP
        )
        return MEMBER_MENU
    elif context.chat_data["member_view_req_status"]:
        await update.message.reply_text(
            f"Retrieving your {context.chat_data['member_view_req_status'].lower()} requests..."
        )
        context.chat_data["member_view_req_dict"] = crud.getMemberReqDict(
            plat=context.chat_data["plat"],
            givenSN=context.chat_data["S/N"],
            status=context.chat_data["member_view_req_status"],
        )
        if context.chat_data["member_view_req_dict"]:
            msg = craftmsg.MemberViewReqListMsg(
                num_req=len(context.chat_data["member_view_req_dict"]),
                status=context.chat_data["member_view_req_status"],
            )
            req_list_reply_markup = craftmsg.getReqListMarkup(
                context.chat_data["member_view_req_dict"]
            )
            await update.message.reply_text(msg, reply_markup=req_list_reply_markup)
            return MEMBER_REQ_VIEW
        else:
            msg = f"You have no {context.chat_data['member_view_req_status'].lower()} requests."
            await update.message.reply_text(
                msg, reply_markup=MEMBER_VIEW_OPTIONS_MARKUP
            )
            return MEMBER_VIEW_OPTIONS
    else:
        msg = "Not a valid option."
        await update.message.reply_text(msg, reply_markup=MEMBER_VIEW_OPTIONS_MARKUP)
        return MEMBER_VIEW_OPTIONS


async def member_req_view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    if user_input == "Refresh \U0001F503":
        await update.message.reply_text(
            f"Refreshing {context.chat_data['member_view_req_status'].lower()} requests..."
        )
        context.chat_data["member_view_req_dict"] = crud.getMemberReqDict(
            plat=context.chat_data["plat"],
            givenSN=context.chat_data["S/N"],
            status=context.chat_data["member_view_req_status"],
        )
        if context.chat_data["member_view_req_dict"]:
            msg = craftmsg.MemberViewReqListMsg(
                num_req=len(context.chat_data["member_view_req_dict"]),
                status=context.chat_data["member_view_req_status"],
            )
            req_list_reply_markup = craftmsg.getReqListMarkup(
                context.chat_data["member_view_req_dict"]
            )
            await update.message.reply_text(msg, reply_markup=req_list_reply_markup)
            return MEMBER_REQ_VIEW
        else:
            msg = f"You have no {context.chat_data['member_view_req_status'].lower()} requests."
            await update.message.reply_text(
                msg, reply_markup=MEMBER_VIEW_OPTIONS_MARKUP
            )
            return MEMBER_VIEW_OPTIONS
    elif user_input == "Back":
        Reset.member_view_req_data(context=context)
        msg = "Please select what kind of request you wish to view."
        await update.message.reply_text(msg, reply_markup=MEMBER_VIEW_OPTIONS_MARKUP)
        return MEMBER_VIEW_OPTIONS
    elif user_input in context.chat_data["member_view_req_dict"].values():
        await update.message.reply_text("Retrieving Off Request details...")
        req_id = [
            key
            for key in context.chat_data["member_view_req_dict"]
            if context.chat_data["member_view_req_dict"][key] == user_input
        ][0]
        context.chat_data["req_id"] = req_id
        msg = craftmsg.ViewReq(context.chat_data["plat"], req_id)
        if context.chat_data["member_view_req_status"] == "PENDING":
            await update.message.reply_text(
                msg, reply_markup=CANCEL_REQ_REPLY_MARKUP, parse_mode="MarkdownV2"
            )
        else:
            BackButton = ReplyKeyboardMarkup(
                [["Back"]], one_time_keyboard=True, resize_keyboard=True
            )
            await update.message.reply_text(
                msg, reply_markup=BackButton, parse_mode="MarkdownV2"
            )
        return MEMBER_REQ_OPTIONS
    else:
        msg = "Not a valid request option.\n\n"
        # Return to menu
        msg += craftmsg.MemberViewReqListMsg(
            num_req=len(context.chat_data["member_view_req_dict"]),
            status=context.chat_data["member_view_req_status"],
        )
        req_list_reply_markup = craftmsg.getReqListMarkup(
            context.chat_data["member_view_req_dict"]
        )
        await update.message.reply_text(msg, reply_markup=req_list_reply_markup)
        return MEMBER_REQ_VIEW


async def member_req_options(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    match (user_input):
        case "Cancel Request \U0000274C":
            msg = "Are you sure you wish to cancel?"
            CONFIRM_REPLY_MARKUP = ReplyKeyboardMarkup(
                [["Yes \U00002705"], ["Back"]],
                one_time_keyboard=True,
                resize_keyboard=True,
            )
            await update.message.reply_text(msg, reply_markup=CONFIRM_REPLY_MARKUP)
            return MEMBER_CANCEL_CONFIRM
        case "Back":
            msg = f"Returning to list of {context.chat_data['member_view_req_status'].lower()} offs...\n\n"
            # Return to menu
            msg += craftmsg.MemberViewReqListMsg(
                num_req=len(context.chat_data["member_view_req_dict"]),
                status=context.chat_data["member_view_req_status"],
            )
            req_list_reply_markup = craftmsg.getReqListMarkup(
                context.chat_data["member_view_req_dict"]
            )
            await update.message.reply_text(msg, reply_markup=req_list_reply_markup)
            return MEMBER_REQ_VIEW
        case _:
            msg = "Not a valid option."
            if context.chat_data["member_view_req_status"] == "PENDING":
                await update.message.reply_text(
                    msg, reply_markup=CANCEL_REQ_REPLY_MARKUP, parse_mode="MarkdownV2"
                )
            else:
                BackButton = ReplyKeyboardMarkup(
                    [["Back"]], one_time_keyboard=True, resize_keyboard=True
                )
                await update.message.reply_text(
                    msg, reply_markup=BackButton, parse_mode="MarkdownV2"
                )
            return MEMBER_REQ_OPTIONS


async def member_req_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    match (user_input):
        case "Yes \U00002705":
            await update.message.reply_text("Cancelling Request...")
            crud.cancel_req(context.chat_data["plat"], context.chat_data["req_id"])
            msg = "Off Request successfully cancelled.\n\n"
            del context.chat_data["member_view_req_dict"][context.chat_data["req_id"]]

            # Notify Admin
            await update.message.reply_text("Notifying your admin...")
            admin_id = crud.get_req_admin_chat_id(
                context.chat_data["plat"], context.chat_data["req_id"]
            )
            await context.bot.send_message(
                chat_id=admin_id,
                text=craftmsg.ReqCancelNotif(
                    context.chat_data["plat"], context.chat_data["req_id"]
                ),
                parse_mode="MarkdownV2",
            )
        case "Back":
            msg = "Off request has not been cancelled."
            await update.message.reply_text(msg, reply_markup=CANCEL_REQ_REPLY_MARKUP)
            return MEMBER_REQ_OPTIONS
        case _:
            msg = "Not a valid option."
            CONFIRM_REPLY_MARKUP = ReplyKeyboardMarkup(
                [["Yes \U00002705"], ["Back"]],
                one_time_keyboard=True,
                resize_keyboard=True,
            )
            await update.message.reply_text(msg, reply_markup=CONFIRM_REPLY_MARKUP)
            return MEMBER_CANCEL_CONFIRM

    # Return to menu
    if context.chat_data["member_view_req_dict"]:
        num_req = len(context.chat_data["member_view_req_dict"])
        MemberViewReqList = [
            [context.chat_data["member_view_req_dict"][key]]
            for key in context.chat_data["member_view_req_dict"]
        ]
        MemberViewReqList.append(["Refresh \U0001F503"])
        MemberViewReqList.append(["Back"])
        msg = f"You have {num_req} {context.chat_data['member_view_req_status'].lower()} request(s). "
        msg += "Select one to view it in detail or cancel it."
        MEMBER_REQ_LIST_REPLY_MARKUP = ReplyKeyboardMarkup(
            MemberViewReqList, one_time_keyboard=True, resize_keyboard=True
        )
        await update.message.reply_text(msg, reply_markup=MEMBER_REQ_LIST_REPLY_MARKUP)
        return MEMBER_REQ_VIEW
    else:
        msg = f"You have no {context.chat_data['member_view_req_status'].lower()} requests."
        await update.message.reply_text(msg, reply_markup=MEMBER_VIEW_OPTIONS_MARKUP)
        return MEMBER_VIEW_OPTIONS


async def admin_req_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    if user_input == "Refresh \U0001F503":
        await update.message.reply_text("Refreshing...")
        msg = "Requests Refreshed!\n\n"
        context.chat_data["admin_view_req_dict"] = crud.getAdminPendingReqDict(
            context.chat_data["plat"], context.chat_data["S/N"]
        )
        if context.chat_data["admin_view_req_dict"]:
            num_req = len(context.chat_data["admin_view_req_dict"])
            msg += f"You have {num_req} pending request(s). Select one to view it in detail, approve or reject it."
            admin_req_list_reply_markup = craftmsg.getReqListMarkup(
                req_dict=context.chat_data["admin_view_req_dict"], 
                back_button=False
            )
            await update.message.reply_text(msg, reply_markup=admin_req_list_reply_markup)
            return ADMIN_REQ_VIEW
        else:
            msg += f"You have no pending requests. Logging out... Have a break, Have a kitkat \U0001F36B"
            await update.message.reply_text(msg, reply_markup=PlatoonOptionsMarkup)
            return PLATOON_SELECT
    elif user_input in context.chat_data["admin_view_req_dict"].values():
        await update.message.reply_text("Retrieving Off Request details...")
        req_id = [
            key
            for key in context.chat_data["admin_view_req_dict"]
            if context.chat_data["admin_view_req_dict"][key] == user_input
        ][0]
        context.chat_data["req_id"] = req_id
        msg = craftmsg.ViewReq(context.chat_data["plat"], req_id)
        msg += "Please select if you would like to approve or reject this request\."
        await update.message.reply_text(
            msg, reply_markup=APPROVE_REJECT_REPLY_MARKUP, parse_mode="MarkdownV2"
        )
        return ADMIN_APP_REJ
    else:
        msg = "Not a valid request option.\n"
        if context.chat_data["admin_view_req_dict"]:
            num_req = len(context.chat_data["admin_view_req_dict"])
            msg += f"You have {num_req} pending request(s). Select one to view it in detail, approve or reject it."
            admin_req_list_reply_markup = craftmsg.getReqListMarkup(
                req_dict=context.chat_data["admin_view_req_dict"], 
                back_button=False
            )
            await update.message.reply_text(msg, reply_markup=admin_req_list_reply_markup)
            return ADMIN_REQ_VIEW
        else:
            msg += f"You have no pending requests. Logging out... Have a break, Have a kitkat \U0001F36B"
            await update.message.reply_text(msg, reply_markup=PlatoonOptionsMarkup)
            return PLATOON_SELECT


async def admin_approve_reject(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    user_input = update.message.text
    match (user_input):
        case "Approve \U00002705":
            await update.message.reply_text(
                "Checking if your pioneer has enough offs..."
            )
            # Check if got enough offs remaining to satisfy request
            offs_remaning, offs_needed = crud.check_off_count_for_approval(
                context.chat_data["plat"], context.chat_data["req_id"]
            )
            if offs_remaning >= offs_needed:
                await update.message.reply_text(
                    "Please select the approving officer.",
                    reply_markup=APPR_OFFICER_REPLY_MARKUP,
                )
                return ADMIN_APPR_OFFICER
            else:
                msg = "Unfortunately you cannot approve this request yet as your pioneer wants to take "
                msg += f"{offs_needed} off(s) but only has {offs_remaning} offs."
                await update.message.reply_text(msg)
                return ADMIN_APP_REJ
        case "Reject \U0000274C":
            msg = "Please enter the reason for rejection."
            await update.message.reply_text(msg)
            return ADMIN_REJ_REASON
        case "Back":
            msg = "Returning to list of pending offs...\n\n"
        case _:
            msg = "Not a valid option."
            await update.message.reply_text(
                msg, reply_markup=APPROVE_REJECT_REPLY_MARKUP
            )
            return ADMIN_APP_REJ

    # Return to pending request menu
    if context.chat_data["admin_view_req_dict"]:
        num_req = len(context.chat_data["admin_view_req_dict"])
        msg += f"You have {num_req} pending request(s). Select one to view it in detail, approve or reject it."
        admin_req_list_reply_markup = craftmsg.getReqListMarkup(
            req_dict=context.chat_data["admin_view_req_dict"], 
            back_button=False
        )
        await update.message.reply_text(msg, reply_markup=admin_req_list_reply_markup)
        return ADMIN_REQ_VIEW
    else:
        msg += f"You have no pending requests. Logging out... Have a break, Have a kitkat \U0001F36B"
        await update.message.reply_text(msg, reply_markup=PlatoonOptionsMarkup)
        return PLATOON_SELECT


async def admin_approving_officer(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    user_input = update.message.text
    match (user_input):
        case "Back":
            msg = "Back to options..."
            await update.message.reply_text(
                msg, reply_markup=APPROVE_REJECT_REPLY_MARKUP
            )
            return ADMIN_APP_REJ
        case "Other (Please Specify)":
            msg = "Please enter the approving officer.\n(Enter 'Back' to cancel)"
            await update.message.reply_text(msg)
            return ADMIN_APPR_OFFICER
        case _:
            appr_officer = user_input
            await update.message.reply_text("Updating Excel Sheet...")
            crud.approve_req(
                context.chat_data["plat"], context.chat_data["req_id"], appr_officer
            )
            await update.message.reply_text("Telling your pioneer the good news...")
            requester_id = crud.get_requester_chat_id(
                context.chat_data["plat"], context.chat_data["req_id"]
            )
            await context.bot.send_message(
                chat_id=requester_id,
                text=craftmsg.ApprovalNotif(
                    context.chat_data["plat"], context.chat_data["req_id"]
                ),
                parse_mode="MarkdownV2",
            )
            del context.chat_data["admin_view_req_dict"][context.chat_data["req_id"]]
            msg = "Off Request successfully approved!\n\n"

            if context.chat_data["admin_view_req_dict"]:
                num_req = len(context.chat_data["admin_view_req_dict"])
                msg += f"You have {num_req} pending request(s). Select one to view it in detail, approve or reject it."
                admin_req_list_reply_markup = craftmsg.getReqListMarkup(
                    req_dict=context.chat_data["admin_view_req_dict"], 
                    back_button=False
                )
                await update.message.reply_text(msg, reply_markup=admin_req_list_reply_markup)
                return ADMIN_REQ_VIEW
            else:
                msg += f"You have no pending requests. Logging out... Have a break, Have a kitkat \U0001F36B"
                await update.message.reply_text(msg, reply_markup=PlatoonOptionsMarkup)
                return PLATOON_SELECT


async def admin_reject_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    crud.reject_req(context.chat_data["plat"], context.chat_data["req_id"])
    msg = "Off Request has been rejected.\n\n"
    del context.chat_data["admin_view_req_dict"][context.chat_data["req_id"]]

    # Notify Requester
    await update.message.reply_text("Telling your poor pioneer...")
    reason = update.message.text
    requester_id = crud.get_requester_chat_id(
        context.chat_data["plat"], context.chat_data["req_id"]
    )
    await context.bot.send_message(
        chat_id=requester_id,
        text=craftmsg.RejectionNotif(
            context.chat_data["plat"], context.chat_data["req_id"], reason
        ),
        parse_mode="MarkdownV2",
    )
    # Return to menu
    if context.chat_data["admin_view_req_dict"]:
        num_req = len(context.chat_data["admin_view_req_dict"])
        msg += f"You have {num_req} pending requests. Select one to view it in detail, approve or reject it."
        admin_req_list_reply_markup = craftmsg.getReqListMarkup(
            req_dict=context.chat_data["admin_view_req_dict"], 
            back_button=False
        )
        await update.message.reply_text(msg, reply_markup=admin_req_list_reply_markup)
        return ADMIN_REQ_VIEW
    else:
        msg += f"You have no pending requests. Logging out... Have a break, Have a kitkat \U0001F36B"
        await update.message.reply_text(msg, reply_markup=PlatoonOptionsMarkup)
        return PLATOON_SELECT
    
async def approveall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if "is_admin" in context.chat_data:
        if context.chat_data["is_admin"] == "Not Logged In":
            msg = "Approve what approve!? Log in first lah. Choose your platoon:"
            await update.message.reply_text(msg, reply_markup=PlatoonOptionsMarkup)
            return PLATOON_SELECT
        elif context.chat_data["is_admin"]:
            appr_officer = " ".join(context.args)
            approved_req_ids = []
            for req_id in context.chat_data["admin_view_req_dict"].keys():
                await update.message.reply_text(
                f"Approving request: {context.chat_data['admin_view_req_dict'][req_id]}"
                )
                await update.message.reply_text(
                "Checking if your pioneer has enough offs..."
                )
                # Check if got enough offs remaining to satisfy request
                offs_remaning, offs_needed = crud.check_off_count_for_approval(
                    context.chat_data["plat"], req_id
                )
                if offs_remaning >= offs_needed:
                    await update.message.reply_text("Updating Excel Sheet...")
                    crud.approve_req(
                        context.chat_data["plat"], req_id, appr_officer
                    )
                    await update.message.reply_text("Telling your pioneer the good news...")
                    requester_id = crud.get_requester_chat_id(
                        context.chat_data["plat"], req_id
                    )
                    await context.bot.send_message(
                        chat_id=requester_id,
                        text=craftmsg.ApprovalNotif(
                            context.chat_data["plat"], req_id
                        ),
                        parse_mode="MarkdownV2",
                    )
                    approved_req_ids.append(req_id)
                    msg = "Off Request successfully approved!\n\n"
                    await update.message.reply_text(msg)
                else:
                    msg = "Unfortunately you cannot approve this request yet as your pioneer wants to take "
                    msg += f"{offs_needed} off(s) but only has {offs_remaning} offs."
                    await update.message.reply_text(msg)
            
            for req_id in approved_req_ids:
                del context.chat_data["admin_view_req_dict"][req_id]
                
            # Return to pending request menu
            if context.chat_data["admin_view_req_dict"]:
                num_req = len(context.chat_data["admin_view_req_dict"])
                msg += f"You have {num_req} pending request(s). Select one to view it in detail, approve or reject it."
                admin_req_list_reply_markup = craftmsg.getReqListMarkup(
                    req_dict=context.chat_data["admin_view_req_dict"], 
                    back_button=False
                )
                await update.message.reply_text(msg, reply_markup=admin_req_list_reply_markup)
                return ADMIN_REQ_VIEW
            else:
                msg = f"You have no pending requests. Logging out... Have a break, Have a kitkat \U0001F36B"
                await update.message.reply_text(msg, reply_markup=PlatoonOptionsMarkup)
                return PLATOON_SELECT
        else:
            msg = "You not admin don't try and be funny."
            await update.message.reply_text(msg, reply_markup=MEMBER_MENU_REPLY_MARKUP)
            return MEMBER_MENU
    else:
        await update.message.reply_text("The bot encountered some difficulties. Need to semula.")
        Reset.user_data(context)
        context.chat_data["is_admin"] = "Not Logged In"
        context.chat_data["admin_view_req_dict"] = None
        msg = "Welcome to ME Coy Off Tracker!\nPlease select your platoon."
        await update.message.reply_text(msg, reply_markup=PlatoonOptionsMarkup)
        return PLATOON_SELECT


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message
    await context.bot.send_message(
        chat_id=DEV_CHAT_ID, text=message, parse_mode=ParseMode.HTML
    )


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    #application = Application.builder().token(TOKEN).build()
    if 'TEST_TOKEN' in globals():
        application = Application.builder().token(TEST_TOKEN).build()
    else:
        application = Application.builder().token(TOKEN).read_timeout(10).build()

    util_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("logout", start),
            CommandHandler("cancel", cancel),
            CommandHandler("refresh", refresh),
        ],
        states={
            PLATOON_SELECT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, platoon_select)
            ],
            LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, login)],
            ADMIN_LOGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_login)],
            MEMBER_MENU: [
                MessageHandler(filters.Regex("^View Offs"), view_offs),
                MessageHandler(
                    filters.Regex("^View Submitted Requests"), member_view_options
                ),
                MessageHandler(filters.Regex("^Request Off Date"), show_request),
                MessageHandler(filters.Regex("^FAQs"), view_faqs),
            ],
            VIEW_FAQS: [MessageHandler(filters.TEXT & ~filters.COMMAND, view_faqs)],
            REQ_DISPLAY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, show_request)
            ],
            REQ_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_request)],
            ADMIN_REQ_VIEW: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_req_list)
            ],
            ADMIN_APP_REJ: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_approve_reject)
            ],
            ADMIN_APPR_OFFICER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_approving_officer)
            ],
            ADMIN_REJ_REASON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_reject_reason)
            ],
            MEMBER_VIEW_OPTIONS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, member_view_options)
            ],
            MEMBER_REQ_VIEW: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, member_req_view)
            ],
            MEMBER_REQ_OPTIONS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, member_req_options)
            ],
            MEMBER_CANCEL_CONFIRM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, member_req_cancel)
            ],
        },
        fallbacks=[
            CommandHandler("approveall", approveall),
        ],
        allow_reentry=True,
    )

    application.add_handler(util_handler)
    application.add_error_handler(error_handler)
    # Run the bot until the user presses Ctrl-C
    if 'TEST_TOKEN' in globals():
        application.run_polling()  # for development
    else:
        application.run_webhook(
            listen='0.0.0.0',
            port=PORT,
            url_path=TOKEN,
            webhook_url=f"https://{WEBHOST}/{TOKEN}"
        )


if __name__ == "__main__":
    main()
