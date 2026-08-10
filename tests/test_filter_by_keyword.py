import pandas as pd
from services.event_search import filter_events_by_keywords

events = pd.read_excel(r"C:\Users\USER\vscodeProjects\csm\event_scout_mcp\data\ieee_pes_public_events_2026-08-03.xlsx")

filtered_events = filter_events_by_keywords(events, "인공지능, AI, 머신러닝")
print(filtered_events)