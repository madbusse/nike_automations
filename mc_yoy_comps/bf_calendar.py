import pandas as pd
import math
import datetime
# from datetime import datetime, date, timedelta
from dateutil.relativedelta import TH, relativedelta

### INPUTS
breakdown_platforms = ['meta']
breakdown_campaigns = ['dynamic']
kpis = ['ROAS', 'CPV', 'CVR', 'AOV', 'CPM', 'CPC']
topline_kpis = ['ROAS', 'CPV', 'CPM']
thisyear = 2025
lastyear = thisyear - 1

def black_friday(year: int) -> datetime.date:
    """
    Gets the date, as a datetime date, of Black Friday for the given year.
    """
    tgiving = datetime.date(year, 11, 1) + relativedelta(weekday=TH(4))
    bf = tgiving + datetime.timedelta(days=1)
    return bf

def load_df(year: int) -> pd.DataFrame:
    """
    Loads data (csv) into a dataframe.
    """
    filename = str(year) + '.csv'
    df = pd.read_csv(filename)
    return df

def rename_cols(df: pd.DataFrame) -> pd.DataFrame:
    """
    Shortens the names of relevant columns and converts dates to datetimes.
    """
    df["date"] = pd.to_datetime(df["date_day"], format="%m/%d/%Y")
    df = df.rename(columns={
        "lc_demand_digital_web_app_adobe": "demand",
        "lc_orders_digital_web_app_adobe": "orders",
        "lc_visits_digital_web_app_adobe": "visits",
        "media_spend": "spend",
    })
    df = df.drop(columns=['date_day'])
    return df

def filter_platform(df: pd.DataFrame, platform: str) -> pd.DataFrame:
    """
    Filters a dataframe down to only contain data from the given platform.
    """
    #TODO
    #groupby platform
    return

def filter_campaign(df: pd.DataFrame, keyword: str) -> pd.DataFrame:
    """
    Filters a dataframe down to only contain data from the given campaign.

    NB: campaign should be entered as a keyword that appears in campaign_name -
    make sure the keyword is unique to only that campaign!
    
    e.g. for Mens 18+ campaigns, I would use "mens_18+" rather than just "mens"
    """
    #TODO
    #groupby campaign name
    #sortby contains keyword
    return

def aggregate_by_day(df: pd.DataFrame, kpis: list[str]) -> pd.DataFrame:
    """
    Aggregates a dataframe so that there is only one row per date. 
    """
    df = df.groupby("date", as_index=False).sum()
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

def add_bf_dates(year: int, df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds Black Friday dates into a new column in the dataframe.
    
    A Black Friday date is an integer representing the number of days from that
    calendar date to Black Friday of that year.
    
    NB: BF dates imply directionality in their signage.
    """
    bf = black_friday(year)
    df["bf_date"] = (df["date"] - pd.to_datetime(bf)).dt.days
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
    """
    if metric > 0:
        sign = '+'
    elif metric < 0:
        sign = '-'
    else:
        sign = ''
    return sign

def print_header(lastyear_df: pd.DataFrame, bf_date: int) -> None:
    """
    Prints a header with the current date, bf_date, and last year's comp date.

    INPUTS:
        thisyear_df: dataframe representing the current year's data
        lastyear_df: dataframe representing the last year's data
        kpis: list of kpis (as strings with proper capitalization) to be printed
        bf_date: int that represents the bf_date that metrics are wanted for (consistent across years)

    OUTPUT: None, prints kpi metrics given for the given date
    """
    suffix = ''
    if bf_date > 0:
        suffix = 'after'
    elif bf_date < 0:
        suffix = 'before'
    else:
        suffix = 'from'

    lastyear_today = lastyear_df[lastyear_df['bf_date'] == bf_date]
    lastyear_date = lastyear_today['date'].iloc[0]

    print(f"Reporting for {yesterday.strftime('%a')} {yesterday.date()}, {abs(bf_date)} days {suffix} Black Friday.")
    print(f"(Comping with {lastyear_date.strftime('%a')} {lastyear_date.date()})\n")

#TODO: decompose this guy lol he getting long
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
            print(f'{kpi} Actual ${thisyear_today[kpi].iloc[0].round(2)}, {change}% YoY')
        elif kpi in ['CVR']:
            print(f'{kpi} Actual {thisyear_today[kpi].iloc[0].round(2)}%, {change}% YoY')
        else:
            return ''

### Pre-processing
thisyear_df = rename_cols(load_df(thisyear))



### ALLUP 
thisyear_df = rename_cols(load_df(thisyear))
thisyear_allup = add_bf_dates(thisyear, aggregate_by_day(thisyear_df, kpis))
lastyear_df = rename_cols(load_df(lastyear))
lastyear_allup = add_bf_dates(lastyear, aggregate_by_day(lastyear_df, kpis))
yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
yesterday_bf_date = (yesterday.date() - black_friday(yesterday.year)).days
print('\n')
print_header(lastyear_allup, yesterday_bf_date)
print('=== ALLUP SOCIAL COMMERCE ===')
print_metrics(thisyear_allup, lastyear_allup, topline_kpis, yesterday_bf_date)
print('\n')
print('=== META DYNAMIC ===')
#TODO - but dont change anything big lol
print('=== META PROMO ===')
#TODO


### OUTPUTS
# text message (slack)
# pd.df -> csv -> upload to google sheets