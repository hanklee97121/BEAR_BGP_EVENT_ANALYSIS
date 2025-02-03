import pandas as pd
from BEAR import BEAR

#repeat our experiment
data = 'Data/BGP_explain_data.csv' #path to event data
rcc_collector_lists = ["rrc00", "rrc01", "rrc03", "rrc04", "rrc05", "rrc06", "rrc07", "rrc10", "rrc11", "rrc12", "rrc10", "rrc11",
                      "rrc12", "rrc13", "rrc14", "rrc15", "rrc16", "rrc17", "rrc18", "rrc19", "rrc20", "rrc21", "rrc22", "rrc23",
                      "rrc24", "rrc25", "rrc26"] #since we use rcc, the collector list includes all rcc collectors
#initialize generator, need to download e_1 for reading BGP data. remember to change the save path to where you want to save the results
#if change llm to non-openai llm, remember to change functions in LLM_module.py.
generator = BEAR(collector_list=rcc_collector_lists, model = "gpt-4o", project = "rcc", save_path = "e_8/", read_path = "e_1/")
#generate event report
generator.generate_multi_event(data)

#To generate report for your customized BGP anomaly event, you can use generate_single_event function after initializing
#the BEAR generator

#generator.generate_single_event(self, start_time, file_save_prefix="", IP=None, AS=None, end_time=None, Event_Type=None)
#Must provide event start time, report save prefix, target IP
#AS and Event_Type are not used in current BEAR generator so you don't have to provide it
#end_time is optional
