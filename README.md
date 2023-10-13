# Off-Tracker-Tele-Bot
A telegram bot coded using the python-telegram-bot library. It helps to track offs in a specifically formatted Google Sheet and facilitate the request and approval of offs by members and admins respectively.

## Dependencies
The application was written in, and is run on, Python 3.11.6. The required libraries and their versions are specified in the [requirements.txt](https://github.com/noahseethorcodes/Off-Tracker-Tele-Bot/blob/main/requirements.txt) file. 

## Application Outline
### Setup
* All information pertaining to offs are stored in a Google Sheet which is freely available for those with the link to view
* The bot itself is a regular telegram bot created via Telegram's @BotFather.

### Functions
1. For Members
  - Validate Login (validates the user's identity and ensures he is a member of the group)
  - View Offs (shows how many offs the user has, when they expire as well as a link to their individual sheet)
  - Request Off Date (help to draft a request to take an off and notify the selected admin)
  - View Submitted Requests (view such requests, whether they have been approved, rejected, cancelled or are pending)

2. For Admins
  - Validate Login (validates the user's identity and ensures he is an admin of the group)
  - View Pending Requests (shows the current pending requests the admin has)
  - Approve/Reject Off Request (approve/reject requests and notify the applier)
  - Auto Update Sheet (once an off is approved, the Google Sheet is immediately updated to reflect that the off has been taken)

## Hosting
The application is hosted on a Google Cloud Run service. It makes use of python-telegram-bot's *integrated webhook server* to start a HTTP server on the service to listen for webhook connections.
