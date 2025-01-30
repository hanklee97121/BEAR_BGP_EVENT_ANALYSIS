# BEAR: BGP Event Analysis and Reporting
Use LLM to explain a BGP anomaly event and create a report

LLM_BGP_Anomaly_Explaination_few_collector.ipynb:
  Code of the framework using partial data

**LLM_BGP_Anomaly_Explaination_multi_step_multi_agent.ipynb:**
  Code of the framework with multi-step CoT and self-consistency to generate BGP event report. Best Approach

LLM_generate_BGP_Event_Data.ipynb
  Code of the framework to generate synthetic BGP anomaly event

Data/
  Event data saved in this directory
  BGP_explain_data.csv: csv file record BGP events
  BGP_explain_data_xx.xlsx: since csv doesn't support hyperlink, we save another data file in xlsx with hyperlink
  Synthetic_events.zip: Event description for all GPT generated BGP event
  synthetic_history_rib.json: Valid ribs used to generate synthetic BGP anomaly event

Experiments/
  experiment results saved in this directory
  Experiment_Detail.xlsx: detailed config information for each experiment
