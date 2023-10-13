from datetime import datetime
import pandas, pytz

# TZ=Asia/Singapore


def is_valid_date(given_date):
    if len(given_date) != 6:
        return None
    try:
        return datetime.strptime(given_date, "%d%m%y").date()
    except ValueError:
        return None


def is_valid_dates(given_dates):
    date_count = 0
    date_grps = str(given_dates.rstrip(",")).split(",")
    for date_grp in date_grps:
        dates = date_grp.split("-")
        if len(dates) > 1:
            start_date = is_valid_date(dates[0])
            end_date = is_valid_date(dates[-1])
            if start_date and end_date and end_date > start_date:
                date_count += (end_date - start_date).days + 1
            else:
                return None
        else:
            if is_valid_date(date_grp):
                date_count += 1
            else:
                return None
    return date_count


def reorder_date_string(given_dates):
    date_list = get_date_list(given_dates)
    sorted_date_list = sorted(date_list, key=lambda x: datetime.strptime(x, "%d%m%y"))
    i = 0
    while i < len(sorted_date_list) - 1:
        date1 = is_valid_date(sorted_date_list[i].split("-")[-1])
        date2 = is_valid_date(sorted_date_list[i + 1].split("-")[-1])
        if (date2 - date1).days == 1:
            sorted_date_list[
                i
            ] = f"{sorted_date_list[i].split('-')[0]}-{sorted_date_list[i+1].split('-')[-1]}"
            del sorted_date_list[i + 1]
        else:
            i += 1
    return ",".join(sorted_date_list)


def get_date_list(given_dates):
    date_list = []
    date_grps = str(given_dates.rstrip(",")).split(",")
    for date_grp in date_grps:
        dates = date_grp.split("-")
        if len(dates) > 1:
            start_date = is_valid_date(dates[0])
            end_date = is_valid_date(dates[-1])
            if start_date and end_date and end_date > start_date:
                date_list.extend(
                    pandas.date_range(start_date, end_date, freq="d")
                    .strftime("%d%m%y")
                    .tolist()
                )
            else:
                return None
        else:
            if cur_date := is_valid_date(date_grp):
                date_list.append(cur_date.strftime("%d%m%y"))
            else:
                return None
    return date_list


def get_date_claimed_list(given_dates, duration):
    date_claimed_list = []
    if duration == "FULL DAY OFF":
        for date in get_date_list(given_dates.rstrip(",")):
            date_formatted = is_valid_date(date).strftime("%d %B %Y")
            date_claimed_list.append(f"{date_formatted} (AM OFF)")
            date_claimed_list.append(f"{date_formatted} (PM OFF)")
    else:
        for date in get_date_list(given_dates.rstrip(",")):
            date_formatted = is_valid_date(date).strftime("%d %B %Y")
            date_claimed_list.append(f"{date_formatted} ({duration})")
    return date_claimed_list


def is_expired(expr_date):
    expr_date = datetime.strptime(expr_date, "%d %B %Y").date()
    return expr_date < get_time_now().date()


def get_time_now():
    return datetime.now(pytz.timezone("Asia/Singapore"))
