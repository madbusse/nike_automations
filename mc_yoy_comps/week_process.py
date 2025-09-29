import pandas as pd
import sys
import math
import datetime

#TODO: fix '>' error when there is no data for current data (could happen if data report fails)

### INPUTS
breakdown_platforms = ['meta'] # not currently used - would use for generalization (loop)
breakdown_campaigns = ['dynamic', 'promo']  # not currently used - would use for generalization (loop)
kpis = ['ROAS', 'CPV', 'CVR', 'AOV', 'CPM', 'CPC']
topline_kpis = ['ROAS', 'CPV', 'CPM']
yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
thisyear = yesterday.year
lastyear = thisyear - 1

def black_friday(year: int) -> datetime.date:
    """
    Gets the date, as a datetime date, of Black Friday for the given year.
    """
    nov1 = datetime.date(year, 11, 1)
    days_until_thursday = (3 - nov1.weekday()) % 7
    first_thursday = nov1 + datetime.timedelta(days=days_until_thursday)
    tgiving = first_thursday + datetime.timedelta(weeks=3)
    bf = tgiving + datetime.timedelta(days=1)
    return bf

def load_df(year: int) -> pd.DataFrame:
    """
    Loads data (csv) into a dataframe.
    """
    filename = str(year) + '.csv'
    df = pd.read_csv(filename)
    return df

def get_bf_week(bf_date: int) -> int:
    """
    Calculates bf_week, which represents which week before BF a bf_date is.
    
    NB: As with bf_dates, sign implies directionality

    Also NB: Weeks are Sunday to Saturday, with week of Thanksgiving = 0 and
    Cyber Week = 1.
    """
    return math.ceil((bf_date - 1) / 7)

def prepare_df(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    Shortens the names of relevant columns, converts dates to datetimes, and
    adds Black Friday date to each row based on the given year.
    
    A Black Friday date is an integer representing the number of days from that
    calendar date to Black Friday of that year.
    
    NB: BF dates imply directionality in their signage.
    """
    df["date"] = pd.to_datetime(df["date_day"], format="%m/%d/%Y")
    bf = black_friday(year)
    df["bf_date"] = (df["date"] - pd.to_datetime(bf)).dt.days
    df["bf_week"] = df["bf_date"].apply(get_bf_week)
    df = df.rename(columns={
        "lc_demand_digital_web_app_adobe": "demand",
        "lc_orders_digital_web_app_adobe": "orders",
        "lc_visits_digital_web_app_adobe": "visits",
        "media_spend": "spend",
    })
    df = df.drop(columns=['date_day'])
    return df

def get_date_from_bf_date(year: int, bf_date: int) -> datetime.date:
    """
    Gets a datetime date from the BF date in a given year.
    """
    bf = black_friday(year)
    return bf + datetime.timedelta(days=bf_date)

def filter_platform(df: pd.DataFrame, platform: str) -> pd.DataFrame:
    """
    Filters a dataframe down to only contain data from the given platform.
    """
    platform_df = df[df["platform"] == platform]
    return platform_df

def filter_campaign(df: pd.DataFrame, keyword: str) -> pd.DataFrame:
    """
    Filters a dataframe down to only contain data from the given campaign.

    NB: campaign should be entered as a keyword that appears in campaign_name -
    make sure the keyword is unique to only that campaign!
    
    e.g. for Mens 18+ campaigns, I would use "mens_18+" rather than just "mens"
    """
    campaign_df = df[df["campaign_name"].str.contains(keyword, case=False, na=False)]
    return campaign_df

def aggregate_by_day(df: pd.DataFrame, kpis: list[str]) -> pd.DataFrame:
    """
    Aggregates a dataframe so that there is only one row per date. 

    Sums every column except date and bf_date, which it groups by. 
    """
    df = df.groupby(["date", "bf_date"], as_index=False).sum()
    for kpi in kpis:
        if kpi == 'ROAS':
            df[kpi] = df['demand']/df['spend']
        elif kpi == 'CPV':
            df[kpi] = df['spend']/df['visits']
        elif kpi == 'CVR':
            df[kpi] = df['orders']/df['visits']
        elif kpi == 'AOV':
            df[kpi] = df['demand']/df['orders']
        elif kpi == 'CPM':
            df[kpi] = df['spend']/df['impressions']*1000
        elif kpi == 'CPC':
            df[kpi] = df['spend']/df['clicks']
    return df

def aggregate_by_week(df: pd.DataFrame, kpis: list[str]) -> pd.DataFrame:
    """
    Aggregates days in a df by their bf_week.

    NB: logic requires this be run on a df that has NOT been aggregated by day.
    """
    df = df.drop(columns=['date', 'bf_date'])
    df = df.groupby(["bf_week"], as_index=False).sum()
    for kpi in kpis:
        if kpi == 'ROAS':
            df[kpi] = df['demand']/df['spend']
        elif kpi == 'CPV':
            df[kpi] = df['spend']/df['visits']
        elif kpi == 'CVR':
            df[kpi] = df['orders']/df['visits']
        elif kpi == 'AOV':
            df[kpi] = df['demand']/df['orders']
        elif kpi == 'CPM':
            df[kpi] = df['spend']/df['impressions']*1000
        elif kpi == 'CPC':
            df[kpi] = df['spend']/df['clicks']
    return df

def percent_change(current: float, former: float) -> int:
    """
    Calculates percent change between a current and former value.
    """
    if former == 0 or math.isinf(former) or math.isnan(former):
        return "no data for last year"
    elif current == 0 or math.isinf(former) or math.isnan(current):
        return "no data for this year"
    else:
        return (((current - former)/former)*100).astype(int)

def get_sign(metric: float) -> str:
    """
    Gets the sign of the given metric and returns the appropriate prefix.

    NB: only returns '+' because the negative sign is stuck to neg values.
    """
    if metric > 0:
        sign = '+'
    else:
        sign = ''
    return sign

def print_header(ty_date: datetime.date, ly_date: datetime.date, bf_date: int) -> None:
    """
    Prints a header with the current date, bf_date, and last year's comp date.

    INPUTS:
        ty_date: this year's date
        ly_date: last year's date (the comp with same bf_date)
        bf_date: the bf_date of both ty_date and ly_date

    OUTPUT: None, prints header for the given date.
    """
    suffix = ''
    if bf_date > 0:
        suffix = 'after'
    elif bf_date < 0:
        suffix = 'before'
    else:
        suffix = 'from'

    print(f"Reporting for {ty_date.strftime('%a')} {ty_date}, {abs(bf_date)} days {suffix} Black Friday.")
    print(f"(Comping with {ly_date.strftime('%a')} {ly_date})")

def print_metrics(thisyear_df: pd.DataFrame, lastyear_df: pd.DataFrame, kpis: list[str], bf_date: int) -> None:
    """
    Prints metrics with YoY comps for the given KPIs. 

    INPUTS:
        thisyear_df: dataframe representing the current year's data
        lastyear_df: dataframe representing the last year's data
        kpis: list of kpis (as strings with proper capitalization) to be printed
        bf_date: int that represents the bf_date that metrics are wanted for (consistent across years)

    OUTPUT: None, prints kpi metrics given for the given date
    """
    thisyear_today = thisyear_df[thisyear_df['bf_date'] == bf_date]
    lastyear_today = lastyear_df[lastyear_df['bf_date'] == bf_date]

    for kpi in kpis:
        change = percent_change(thisyear_today[kpi].iloc[0], lastyear_today[kpi].iloc[0])
        if kpi in ['ROAS', 'CPV', 'AOV', 'CPM', 'CPC']:
            print(f'{kpi} Actual ${thisyear_today[kpi].iloc[0].round(2)}, {get_sign(change)}{change}% YoY')
        elif kpi in ['CVR']:
            print(f'{kpi} Actual {thisyear_today[kpi].iloc[0].round(2)}%, {get_sign(change)}{change}% YoY')
        else:
            return ''
        
def make_metric_df(thisyear_df: pd.DataFrame, lastyear_df: pd.DataFrame, kpis: list[str], timeframe: str, bf_date_or_week: int, row_name: str) -> pd.DataFrame:
    """
    Makes a dataframe including all kpis given for the given date, including cols
    for actuals and YoY values. Requires a row name.

    NB: timeframe is bf_date or bf_week; choose O&OO as str 
    """
    output_df = pd.DataFrame()
    for kpi in kpis:
        output_df[kpi] = ""
        output_df[f'{kpi} YoY'] = ""

    if timeframe == "bf_date":
        thisyear_data = thisyear_df[thisyear_df['bf_date'] == bf_date_or_week]
        lastyear_data = lastyear_df[lastyear_df['bf_date'] == bf_date_or_week]
    elif timeframe == "bf_week":
        thisyear_data = thisyear_df[thisyear_df['bf_week'] == bf_date_or_week]
        lastyear_data = lastyear_df[lastyear_df['bf_week'] == bf_date_or_week]
    
    for kpi in kpis:
        change = percent_change(thisyear_data[kpi].iloc[0], lastyear_data[kpi].iloc[0])
        if kpi in ['ROAS', 'CPV', 'AOV', 'CPM', 'CPC']:
            output_df.loc[row_name, kpi] = f'${thisyear_data[kpi].iloc[0].round(2)}'
        elif kpi in ['CVR']:
            output_df.loc[row_name, kpi] = f'{thisyear_data[kpi].iloc[0].round(2)}%'
        output_df.loc[row_name, f'{kpi} YoY'] = f'{get_sign(change)}{change}% YoY'

    return output_df

# defaults to yesterday for data
yesterday_bf_date = (yesterday.date() - black_friday(yesterday.year)).days
yesterday_bf_week = get_bf_week(yesterday_bf_date)
yesterday_lastyear = get_date_from_bf_date(lastyear, yesterday_bf_date)

### Make dfs
thisyear_df = prepare_df(load_df(thisyear), thisyear)
lastyear_df = prepare_df(load_df(lastyear), lastyear)

### ALLUP 
thisyear_allup = aggregate_by_day(thisyear_df, kpis)
lastyear_allup = aggregate_by_day(lastyear_df, kpis)
thisyear_weekly_allup = aggregate_by_week(thisyear_df, kpis)
lastyear_weekly_allup = aggregate_by_week(lastyear_df, kpis)

### META
thisyear_meta = filter_platform(thisyear_df, 'meta')
lastyear_meta = filter_platform(lastyear_df, 'meta')
thisyear_meta_dynamic = aggregate_by_day(filter_campaign(thisyear_meta, 'dynamic'), kpis)
lastyear_meta_dynamic = aggregate_by_day(filter_campaign(lastyear_meta, 'dynamic'), kpis)
thisyear_weekly_meta_dynamic = aggregate_by_week(filter_campaign(thisyear_meta, 'dynamic'), kpis)
lastyear_weekly_meta_dynamic = aggregate_by_week(filter_campaign(lastyear_meta, 'dynamic'), kpis)
thisyear_meta_promo = aggregate_by_day(filter_campaign(thisyear_meta, 'promo'), kpis)
thisyear_weekly_meta_promo = aggregate_by_week(filter_campaign(thisyear_meta, 'promo'), kpis)
if thisyear_meta_promo.empty:
    pass
else:
    lastyear_meta_promo = aggregate_by_day(filter_campaign(lastyear_meta, 'promo'), kpis)
    lastyear_weekly_meta_promo = aggregate_by_week(filter_campaign(lastyear_meta, 'promo'), kpis)

## SLACK MESSAGE
with open("slack_message.txt", "w") as f:
    sys.stdout = f
    print_header(yesterday.date(), yesterday_lastyear, yesterday_bf_date)
    if yesterday.weekday() == 6:
        print(' *Today is Monday!* Find data from last week <https://docs.google.com/spreadsheets/d/1Ahs7x0vivQktKV1pLOu5RwobhAIRBEfzQOTn7W1NHig/edit?gid=510339820#gid=510339820|here>.')
    print("\n *=== ALLUP SOCIAL COMMERCE ===* ")
    print_metrics(thisyear_allup, lastyear_allup, topline_kpis, yesterday_bf_date)
    print("\n *=== META DYNAMIC ===* ")
    print_metrics(thisyear_meta_dynamic, lastyear_meta_dynamic, topline_kpis, yesterday_bf_date)
    if thisyear_meta_promo.empty:
        print("\nNo Meta Promo data from this year.")
    else:
        print("\n *=== META PROMO ===* ")
        print_metrics(thisyear_meta_promo, lastyear_meta_promo, topline_kpis, yesterday_bf_date)
sys.stdout = sys.__stdout__
f.close()

### OUTPUT CSV
allup_df = make_metric_df(thisyear_allup, lastyear_allup, kpis, "bf_date", yesterday_bf_date, f'ALLUP ({yesterday.date()})')
meta_dynamic_df = make_metric_df(thisyear_meta_dynamic, lastyear_meta_dynamic, kpis, "bf_date", yesterday_bf_date, f'META DYNAMIC ({yesterday.date()})')
merge1 = pd.concat([allup_df, meta_dynamic_df])
if thisyear_meta_promo.empty:
    merge1.to_csv("full_metrics.csv", index=True)
else:
    meta_promo_df = make_metric_df(thisyear_meta_promo, lastyear_meta_promo, kpis, "bf_date", yesterday_bf_date, f'META PROMO ({yesterday.date()})')
    merge2 = pd.concat([merge1, meta_promo_df])
    merge2.to_csv("full_metrics.csv", index=True)
### WEEKLY 
if yesterday.weekday() == 6:
    allup_weekly_df = make_metric_df(thisyear_weekly_allup, lastyear_weekly_allup, kpis, "bf_week", yesterday_bf_week, f'ALLUP (last week)')
    meta_dynamic_weekly_df = make_metric_df(thisyear_weekly_meta_dynamic, lastyear_weekly_meta_dynamic, kpis, "bf_week", yesterday_bf_week, f'META DYNAMIC (last week)')
    merge1weekly = pd.concat([allup_weekly_df, meta_dynamic_weekly_df])
    if thisyear_weekly_meta_promo.empty:
        merge1weekly.to_csv("full_metrics_weekly.csv", index=True)
    else:
        meta_promo_weekly_df = make_metric_df(thisyear_weekly_meta_promo, lastyear_weekly_meta_promo, kpis, "bf_week", yesterday_bf_week, f'META PROMO (last week)')
        merge2weekly = pd.concat([merge1weekly, meta_promo_weekly_df])
        merge2weekly.to_csv("full_metrics_weekly.csv", index=True)

