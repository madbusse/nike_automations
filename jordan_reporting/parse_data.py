import pandas as pd

file_path = "data.csv"
df = pd.read_csv(file_path)

df['retail_week'] = df['retail_week'].ffill()
df['fop'] = df['fop'].ffill()
df['cp_general_creative_name'] = df['cp_general_creative_name'].ffill()

df = df[~df['retail_week'].astype(str).str.contains('Total', na=False)]
df = df[~df['fop'].astype(str).str.contains('Total', na=False)]
df = df[df['cp_general_creative_name'] != "dynamic"]

df['retail_week'] = df['retail_week'].astype(int)
current_week = df['retail_week'].max() # this will not work when current_week = 1
previous_week = df['retail_week'].min()

df['Media Spend'] = df['Media Spend'].replace('[\$,]', '', regex=True).astype(float)
df['ROAS'] = df['ROAS'].replace('[\$,]', '', regex=True).astype(float)
df['CPV'] = df['CPV'].replace('[\$,]', '', regex=True).astype(float)
df['CTR'] = df['CTR'].str.replace('%', '').astype(float)
df['Demand'] = df['Demand'].replace('[\$,]', '', regex=True).astype(float)
df['Impressions'] = df['Impressions'].replace(',', '', regex=True).astype(float)
df['Clicks'] = df['Clicks'].replace(',', '', regex=True).astype(float)
df['Visits (Adobe)'] = df['Visits (Adobe)'].replace(',', '', regex=True).astype(float)
df['Opens (App)'] = df['Opens (App)'].replace(',', '', regex=True).astype(float)

curr_df = df[df['retail_week'] == current_week]
prev_df = df[df['retail_week'] == previous_week]

current_demand = curr_df['Demand'].sum()
current_spend = curr_df['Media Spend'].sum()
current_ROAS = (current_demand/current_spend).round(2)
previous_demand = prev_df['Demand'].sum()
previous_spend = prev_df['Media Spend'].sum()
previous_ROAS = (previous_demand/previous_spend).round(2)
WoW_ROAS = ((current_ROAS - previous_ROAS)/previous_ROAS*100).astype(int)

current_clicks = curr_df['Clicks'].sum()
current_imps = curr_df['Impressions'].sum()
current_CTR = (current_clicks/current_imps*100).round(2)
previous_clicks = prev_df['Clicks'].sum()
previous_imps = prev_df['Impressions'].sum()
previous_CTR = (previous_clicks/previous_imps*100).round(2)
WoW_CTR = ((current_CTR - previous_CTR)/previous_CTR*100).astype(int)

current_spend = curr_df['Media Spend'].sum().astype(int)
previous_spend = prev_df['Media Spend'].sum().astype(int)
WoW_spend = ((current_spend - previous_spend)/previous_spend*100).astype(int)

current_CPV = (current_spend/(curr_df['Visits (Adobe)'].sum() + curr_df['Opens (App)'].sum())).round(2)
previous_CPV = (previous_spend/(prev_df['Visits (Adobe)'].sum() + prev_df['Opens (App)'].sum())).round(2)
WoW_CPV = ((current_CPV - previous_CPV)/previous_CPV).round(2)

current_CPM = (current_spend/curr_df['Impressions'].sum()*1000).round(2)
previous_CPM = (previous_spend/prev_df['Impressions'].sum()*1000).round(2)
WoW_CPM = ((current_CPM - previous_CPM)/previous_CPM).round(2)

sport_demand = curr_df.loc[curr_df['fop'] == "sport", 'Demand'].sum().astype(int)
sport_visits = curr_df.loc[curr_df['fop'] == "sport", 'Visits (Adobe)'].sum().astype(int)
top_sport_creative = curr_df.loc[curr_df[(curr_df['fop'] == "sport") & (curr_df['Demand'] != 0)]['CTR'].idxmax(), 'cp_general_creative_name']
sport_creative_CTR = curr_df.loc[curr_df['cp_general_creative_name'] == top_sport_creative, 'CTR'].iloc[0].round(2)

streetwear_demand = curr_df.loc[curr_df['fop'] == "streetwear", 'Demand'].sum().astype(int)
streetwear_visits = curr_df.loc[curr_df['fop'] == "streetwear", 'Visits (Adobe)'].sum().astype(int)
top_streetwear_creative = curr_df.loc[curr_df[(curr_df['fop'] == "streetwear") & (curr_df['Demand'] != 0)]['CTR'].idxmax(), 'cp_general_creative_name']
streetwear_creative_CTR = curr_df.loc[curr_df['cp_general_creative_name'] == top_streetwear_creative, 'CTR'].iloc[0].round(2)

if current_week != 1:
    output = f"""
    Week {current_week} Jordan Performance Metrics (Excluding Dynamic)

    WK {current_week} Spend = ${current_spend}; WK {previous_week} Spend = ${previous_spend}; Spend Change WoW = {WoW_spend}%
    WK {current_week} ROAS = ${current_ROAS}; WK {previous_week} ROAS = ${previous_ROAS}; ROAS Change WoW = {WoW_ROAS}%
    WK {current_week} CTR = {current_CTR}%; WK {previous_week} CTR = {previous_CTR}%; CTR Change WoW = {WoW_CTR}%
    WK {current_week} CPV = ${current_CPV}; WK {previous_week} CPV = ${previous_CPV}; CPV Change WoW = {WoW_CPV}%
    WK {current_week} CPM = ${current_CPM}; WK {previous_week} CPM = ${previous_CPM}; CPM Change WoW = {WoW_CPM}%

    WK {current_week} Sport generated ${sport_demand} in Demand and {sport_visits} Visits
    The top performing Sport creative by CTR in WK {current_week} was {top_sport_creative} ({sport_creative_CTR}% CTR)

    WK {current_week} Streetwear generated ${streetwear_demand} in Demand and {streetwear_visits} Visits
    The top performing Streetwear creative by CTR in WK {current_week} was {top_streetwear_creative} ({streetwear_creative_CTR}% CTR)
    """
else: 
    output = "Oops, this automation does not work in Week 1!"

with open("summary.txt", "a") as f:
    f.write(output + "\n")
